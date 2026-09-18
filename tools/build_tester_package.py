"""Build an offline FreeCAD installer macro plus standalone diagnostics."""
import ast
import base64
import hashlib
import io
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def build(output=None):
    runtime = ROOT / 'SolidFlowUX'
    dest = Path(output) if output else ROOT / 'dist'
    dest.mkdir(parents=True, exist_ok=True)
    version = re.search(r'#define MyAppVersion "([^"]+)"',
                        (ROOT / 'installer/SolidFlowUX.iss').read_text(encoding='utf-8-sig')).group(1)
    names = [n.strip() for n in (runtime / 'manifest.txt').read_text().splitlines()
             if n.strip() and not n.lstrip().startswith('#')]
    data = io.BytesIO()
    with zipfile.ZipFile(data, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in names + ['manifest.txt']:
            if Path(name).name != name:
                raise ValueError('Manifest path must be a filename: ' + name)
            content = (runtime / name).read_bytes()
            if name.endswith('.py'):
                compile(content, name, 'exec')
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, content)
    payload = data.getvalue()
    support = (ROOT / 'installer/install_support.py').read_text(encoding='utf-8')
    macro = '''# -*- coding: utf-8 -*-
# SolidFlow UX offline installer. No downloads or external executables.
import base64
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtWidgets

VERSION = %r
PAYLOAD_SHA256 = %r
PAYLOAD = %r
SUPPORT = %r

def install_solidflow():
    parent = Gui.getMainWindow()
    try:
        version = tuple(int(x) for x in App.Version()[:2])
        if version < (1, 1):
            raise RuntimeError('Questa versione di SolidFlow UX richiede FreeCAD 1.1 o successivo. Target verificato: 1.1.x.')
        root = App.getUserAppDataDir()
        answer = QtWidgets.QMessageBox.question(parent, 'Installa SolidFlow UX ' + VERSION,
            'Installare nel profilo FreeCAD attualmente aperto?\\n\\n' + str(root) +
            '\\nMod/SolidFlowUX\\n\\nLa copia precedente sara conservata in SolidFlowUX_Backups.\\n'
            'Chiudi le altre istanze di FreeCAD. Dopo l’installazione salva il lavoro e riavvia FreeCAD.',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        if answer != QtWidgets.QMessageBox.Yes:
            return
        namespace = {'__name__': 'solidflow_offline_installer'}
        exec(compile(SUPPORT, 'SolidFlowUX/install_support.py', 'exec'), namespace)
        result = namespace['install_runtime'](base64.b64decode(PAYLOAD), PAYLOAD_SHA256, root, VERSION)
        text = 'File installati in:\\n' + result['target']
        if result['backup']:
            text += '\\n\\nBackup precedente:\\n' + result['backup']
        text += '\\n\\nSalva il lavoro, chiudi completamente FreeCAD e riaprilo.\\nCerca il menu SolidFlow (non un nuovo workbench).'
        QtWidgets.QMessageBox.information(parent, 'Installazione completata — riavvio necessario', text)
    except Exception as exc:
        QtWidgets.QMessageBox.critical(parent, 'Installazione non completata', str(exc) +
            '\\n\\nAllega questo messaggio e il rapporto SolidFlowUX-Diagnostica.FCMacro alla segnalazione.')

install_solidflow()
''' % (version, hashlib.sha256(payload).hexdigest(), base64.b64encode(payload).decode('ascii'), support)
    diagnostic = (runtime / 'solidflow_diagnostics.py').read_text(encoding='utf-8') + '\nshow_report()\n'
    assets = {'SolidFlowUX-Installa.FCMacro': macro.encode('utf-8'),
              'SolidFlowUX-Diagnostica.FCMacro': diagnostic.encode('utf-8'),
              'LEGGIMI.txt': (ROOT / 'installer/INSTALLAZIONE.txt').read_bytes()}
    for name, content in assets.items():
        if name.endswith('.FCMacro'):
            ast.parse(content)
        (dest / name).write_bytes(content)
    checksum = ''.join(hashlib.sha256(content).hexdigest() + '  ' + name + '\n' for name, content in assets.items())
    assets['SHA256SUMS.txt'] = checksum.encode('ascii')
    archive_path = dest / ('SolidFlowUX-Tester-v' + version + '.zip')
    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, content in assets.items():
            archive.writestr(name, content)
    print(archive_path)
    return archive_path


if __name__ == '__main__':
    build()
