# Beta 13 — primo incremento di stabilità

Base: `8a97df39f6805683b1ff7a64a89d9a2b846d40d2` (brief del 18 settembre).
Questa PR non modifica la versione e non pubblica installer. La PR #1 con le
correzioni di installazione resta separata; nessuna sua modifica viene annullata.

## Implementato

- P0.1: Pad/Pocket usano `SideType` con i nomi nativi `One side` e `Symmetric`.
  `Midplane` è usato solo se manca SideType; Reversed rimane indipendente.
  Fonte API verificata: FreeCAD `src/Mod/PartDesign/App/FeatureExtrude.cpp`.
- P0.2: la viewbar appartiene alla finestra principale, non al documento che può
  essere distrutto. Eventi MDI/resize/show/attivazione aggiornano la posizione;
  il timer a 2 secondi è solo recupero. Non vengono create nuove barre al cambio documento.
- P0.3, flussi principali: helper condiviso PreviewTransaction per Pad/Pocket/
  Revolution, Fillet Doctor e Profile Picker. Cancel ripristina visibilità e Tip;
  il raccordo nasconde l'origine prima del commit, nella stessa operazione Undo.
  La selezione delle regioni crea una preview Part temporanea in una transazione
  abortita anche con OK: nessuna preview da resuscitare con Undo. Tolto il cambio
  di visibilità dello sketch dopo il commit della lavorazione.
- Chiusura immediata della finestra: il callback differito non crea più una feature.
- Manifest e sorgenti Inno includono il nuovo helper.

## Verifica e limiti

`python -m unittest discover -s tests -v`: test dello stato di rollback (20 cicli,
visibilità di oggetti estranei, Tip, commit, errori) e della vera gestione eventi Qt
(cambio/chiusura documento, resize, massimizzazione, preferenze). I documenti
FreeCAD di questi test sono simulati: questo non dimostra la correttezza del kernel.
La CI usa Python 3.11 e Qt offscreen, senza generare un installer.

`FreeCADCmd tests/freecad_smoke.py`: aggiunto smoke test nativo di volumi e direzioni
Pad, Pocket e 20 cicli Cancel/OK/Undo. **Non eseguito nell'ambiente di sviluppo,
che non dispone di FreeCAD.** Eseguire con FreeCAD 1.1.3 prima della pubblicazione.
Restano da verificare in GUI FreeCAD: raccordi, Profile Picker, Undo della visibilità,
Sketch edit, cambio workbench, salvataggio/riapertura e barra sulle viste reali.

## Audit delle altre scritture di visibilità

- `solidflow_paths.py`: Sweep modifica profilo/percorso dopo commit; da migrare.
- `solidflow_mesh.py`: conversione mesh modifica visibilità dopo commit; da migrare.
- `solidflow_beta5.py`: vecchio Fillet Doctor nasconde la base dopo commit;
  vecchia Revolution lo fa prima. Consolidare i percorsi legacy prima di eliminarli.
- `solidflow_beta6.py`: framework già conserva visibilità/Tip, ma Thread cambia
  la base dopo `_commit_feature`; da consolidare con l'helper condiviso.

P0.3 quindi **non completo per tutti i flussi**. P0.4 (vincoli), P1 (palette Sketch,
colori, navigazione, pattern, quadranti, raccordi) e P2 restano da implementare.
Prima di pubblicare beta.13 completare P0 e la checklist nativa del brief.
