# SolidFlow UX

SolidFlow UX è un'estensione UX per FreeCAD 1.1.x pensata per rendere Sketcher e Part Design più rapidi, contestuali e vicini a un flusso di lavoro CAD moderno.

## Installazione consigliata

Per l'utente normale non è necessario copiare file, usare PowerShell o conoscere la cartella `Mod`.

1. Aprire **Releases** nella pagina GitHub del progetto.
2. Aprire la release più recente.
3. Scaricare `SolidFlowUX-Setup-v<versione>.exe`.
4. Chiudere completamente FreeCAD.
5. Eseguire il setup e seguire la procedura guidata.

L'installer installa SolidFlow UX nella cartella utente di FreeCAD:

`%APPDATA%\FreeCAD\v1-1\Mod\SolidFlowUX`

## Controllare il codice prima di installare

Chi preferisce verificare personalmente i sorgenti può usare il normale pulsante GitHub **Code > Download ZIP**, oppure scaricare il pacchetto sorgente associato a una Release.

Dopo aver estratto il repository:

```powershell
powershell -ExecutionPolicy Bypass -File .\CHECK_SOURCE.ps1
```

Lo script controlla che il runtime sia completo e prova a compilare sintatticamente tutti i file Python del manifest senza installare nulla.

## Costruire l'EXE sul proprio PC

Prerequisiti:

- Windows 10/11 x64
- Inno Setup 6
- Python 3.11 oppure Python incluso in FreeCAD 1.1, se disponibile

Poi eseguire:

```powershell
powershell -ExecutionPolicy Bypass -File .\BUILD_INSTALLER_LOCAL.ps1
```

Lo script esegue prima `CHECK_SOURCE.ps1`, quindi compila `installer\SolidFlowUX.iss` e genera l'EXE nella cartella `dist` insieme al relativo SHA-256.

## Struttura repository

- `SolidFlowUX/` — runtime corrente installato dall'EXE
- `installer/` — progetto Inno Setup e manutenzione pre-installazione
- `.github/workflows/` — CI e build automatica Windows
- `docs/` — roadmap, ricerca e documentazione corrente
- `archive/` — vecchi layer, vecchi updater e test storici; **non fanno parte del runtime corrente**

## Nota sulle vecchie beta

I file storici non più caricati dal runtime vengono conservati in `archive/` per audit e confronto, ma non vengono installati nelle release correnti.
