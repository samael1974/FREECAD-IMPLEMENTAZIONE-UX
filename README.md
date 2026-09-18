# SolidFlow UX

SolidFlow UX è un'estensione UX per FreeCAD 1.1.x pensata per rendere Sketcher e Part Design più rapidi, contestuali e vicini a un flusso di lavoro CAD moderno.

## Installazione per i tester — beta.13

Prerequisito: **FreeCAD 1.1.x**. SolidFlow UX aggiunge un menu e una palette a FreeCAD; non è un programma separato o un nuovo workbench.

Scaricare `SolidFlowUX-Tester-v0.4.0-beta.13.zip` dalla relativa release o dagli artifact della build e leggere `LEGGIMI.txt`.

1. Estrarre lo ZIP e aprire FreeCAD con il proprio profilo.
2. **File > Apri** → `SolidFlowUX-Installa.FCMacro`.
3. **Macro > Esegui macro**, controllare la destinazione e confermare.
4. Salvare il lavoro, chiudere completamente FreeCAD e riaprirlo.
5. Cercare il menu **SolidFlow** e premere **S** nella vista 3D.

La macro contiene il runtime completo, usa `FreeCAD.getUserAppDataDir()`, conserva un backup fuori da `Mod` e ripristina la copia precedente se la sostituzione finale fallisce. Non richiede Python esterno, PowerShell o download aggiuntivi. Chiudere eventuali altre istanze di FreeCAD prima di eseguirla.

### Setup Windows

Quando disponibile nella stessa release, `SolidFlowUX-Setup-v0.4.0-beta.13.exe` può essere usato a FreeCAD chiuso. La destinazione è sempre visibile e modificabile; il backup segue il percorso scelto. Il setup si interrompe se il backup fallisce. Per profili portabili o personalizzati è preferibile la macro.

### Se non funziona

Eseguire `SolidFlowUX-Diagnostica.FCMacro` da FreeCAD e premere **Copia rapporto**. Funziona anche senza il menu SolidFlow. Allegare il rapporto e il messaggio/screenshot esatto del problema. Non disattivare antivirus o protezioni di Windows.

I sorgenti beta.13 non implicano che la release beta.12 già scaricata sia stata aggiornata: verificare il nome del pacchetto.

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

## Verifiche riproducibili

`python -m unittest discover -s tests -v`

La CI verifica inoltre su Windows il backup PowerShell, la compilazione Inno Setup e l’installazione silenziosa in un profilo temporaneo. Queste verifiche non sostituiscono il collaudo della GUI di FreeCAD 1.1 sui PC dei tester.
