# Beta 13 — primo incremento di stabilità

Base: `8a97df39f6805683b1ff7a64a89d9a2b846d40d2` (brief del 18 settembre).
Aggiornamento: integrate in questo branch le correzioni di installazione della PR #1.
Versione di prova `0.4.0-beta.13-test.1`, richiesta per i test locali: la CI genera
un artifact con EXE e macro offline. Non viene creata una Release GitHub e il
job di pubblicazione esclude esplicitamente le versioni `-test.`.

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
La CI usa Python 3.11 e Qt offscreen. Il job Windows costruisce l’EXE e ne
verifica l’installazione in un profilo temporaneo confrontando gli hash dei file.
21 test automatici includono installazione/backup, rollback e dialogo Sweep.

`FreeCADCmd tests/freecad_smoke.py`: aggiunto smoke test nativo di volumi e direzioni
Pad, Pocket e 20 cicli Cancel/OK/Undo. **Non eseguito nell'ambiente di sviluppo,
che non dispone di FreeCAD.** Eseguire con FreeCAD 1.1.3 prima della pubblicazione.
Restano da verificare in GUI FreeCAD: raccordi, Profile Picker, Undo della visibilità,
Sketch edit, cambio workbench, salvataggio/riapertura e barra sulle viste reali.

## Ulteriori correzioni incluse nella build test.1

- Sweep su elica: PreviewTransaction condiviso per Cancel; validazione geometria
  prima di OK; visibilità di profilo e percorso registrata prima del commit.
- Mesh: visibilità della conversione in solido registrata prima del commit.
- Vecchio Fillet Doctor e Thread: nascondono gli input dentro la transazione Undo.
- Test Qt del dialogo Sweep verificano Cancel e stato visibilità al commit.

## Ancora da completare

La migrazione completa dei flussi legacy all’helper resta aperta. P0.4 (vincoli),
P1 (palette Sketch, colori, navigazione, pattern, quadranti, raccordi) e P2 restano
pianificati. Non dichiarare P0 completato finché non sono passate anche le prove
native; la build test.1 serve a raccogliere proprio queste verifiche.
