"""Offline installer used by the self-contained FreeCAD macro.

No FreeCAD/Qt imports here: filesystem replacement and rollback are testable
without touching a real user's FreeCAD profile.
"""
import hashlib
import io
import os
from pathlib import Path
import shutil
import tempfile
import uuid
import zipfile
from datetime import datetime


def unpack_runtime(archive, expected_sha256):
    if hashlib.sha256(archive).hexdigest() != expected_sha256:
        raise ValueError("Pacchetto danneggiato: checksum non valido.")
    with zipfile.ZipFile(io.BytesIO(archive)) as package:
        names = package.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Il pacchetto contiene file duplicati.")
        if any('/' in n or '\\' in n or ':' in n or n in ('', '.', '..') for n in names):
            raise ValueError("Percorso non valido nel pacchetto.")
        if sum(info.file_size for info in package.infolist()) > 10 * 1024 * 1024:
            raise ValueError("Pacchetto runtime troppo grande.")
        manifest = package.read('manifest.txt').decode('utf-8-sig')
        required = [n.strip() for n in manifest.splitlines()
                    if n.strip() and not n.lstrip().startswith('#')]
        if not {'Init.py', 'InitGui.py', 'solidflow_ui.py'}.issubset(required):
            raise ValueError("Manifest incompleto.")
        if set(names) != set(required) | {'manifest.txt'}:
            raise ValueError("Il contenuto del pacchetto non coincide con il manifest.")
        return {name: package.read(name) for name in names}


def _is_link(path):
    if not path.exists() and not path.is_symlink():
        return False
    # Windows junctions also redirect a path; is_symlink alone misses these.
    return path.is_symlink() or bool(getattr(path.lstat(), 'st_file_attributes', 0) & 0x400)


def install_runtime(archive, expected_sha256, user_data, version, replace=None):
    """Install into the profile supplied by App.getUserAppDataDir().

    Stage and verify first; move the old tree outside Mod; swap the new tree;
    restore the complete old tree if that final swap fails.
    """
    replace = replace or os.replace
    files = unpack_runtime(archive, expected_sha256)
    root = Path(user_data).expanduser().absolute()
    if not root.is_dir():
        raise ValueError("Cartella dati FreeCAD non trovata: " + str(root))
    mod = root / 'Mod'
    target = mod / 'SolidFlowUX'
    if _is_link(mod) or _is_link(target):
        raise ValueError("Mod o SolidFlowUX è un collegamento: verifica il percorso prima di installare.")
    if target.exists() and not target.is_dir():
        raise ValueError("La destinazione SolidFlowUX non è una cartella.")
    mod.mkdir(exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.solidflow-stage-', dir=str(root)))
    backup = None
    try:
        for name, content in files.items():
            path = staging / name
            path.write_bytes(content)
            if path.read_bytes() != content:
                raise OSError("Verifica scrittura fallita: " + name)
        # Keep an existing Inno uninstaller usable after a macro update.
        if target.is_dir():
            for path in target.glob('unins*'):
                if path.is_file() and not _is_link(path) and path.suffix.lower() in ('.exe', '.dat', '.msg'):
                    shutil.copy2(str(path), str(staging / path.name))
            backup_root = root / 'SolidFlowUX_Backups'
            if _is_link(backup_root):
                raise ValueError("La cartella backup è un collegamento.")
            backup_root.mkdir(exist_ok=True)
            name = datetime.now().strftime('before_%Y%m%d_%H%M%S_') + uuid.uuid4().hex[:8]
            backup = backup_root / name
            replace(str(target), str(backup))
        try:
            replace(str(staging), str(target))
        except Exception as install_error:
            if backup is not None:
                try:
                    replace(str(backup), str(target))
                except Exception as restore_error:
                    raise RuntimeError("Installazione e ripristino falliti. Copia precedente conservata in %s. %s" %
                                       (backup, restore_error)) from install_error
            raise
        return {'target': str(target), 'backup': str(backup) if backup else None,
                'version': version, 'files': len(files)}
    finally:
        if staging.exists():
            shutil.rmtree(str(staging))
