# SolidFlow UX v0.4 beta.4 — test rapido

Target: FreeCAD 1.1.3 / Windows / Python 3.11.

## Installazione patch

1. Chiudere FreeCAD.
2. Fare una copia di sicurezza dell'attuale `InitGui.py` (es. `InitGui_beta3_backup.py`).
3. Copiare nella cartella `SolidFlowUX`:
   - `InitGui.py`
   - `solidflow_beta4.py`
4. Riavviare FreeCAD.

Cartella target:

`C:\Users\corfe\AppData\Roaming\FreeCAD\v1-1\Mod\SolidFlowUX`

## Test 1 — regressione beta.3

Verificare che restino funzionanti:

- tasto `S` e palette;
- Schizzo su faccia;
- riferimenti esterni automatici;
- Pad/Pocket/Revolution;
- barra sotto il cubo;
- Home;
- stili di visualizzazione.

## Test 2 — tema

All'avvio deve apparire il preset chiaro SolidFlow/SolidWorks-like:

- sfondo azzurro/grigio;
- solidi grigio chiaro;
- spigoli scuri;
- Sketch sotto-vincolato blu;
- Sketch completamente vincolato quasi nero;
- geometria esterna viola/magenta;
- geometria non valida rossa.

Dal menu SolidFlow deve essere possibile disattivare il tema e ripristinare l'aspetto precedente.

## Test 3 — cerchio tangente allo spigolo del parallelepipedo

Questo è il test prioritario.

1. Creare un parallelepipedo.
2. Selezionare una faccia.
3. `S → Schizzo su faccia`.
4. Disegnare un cerchio.
5. Selezionare il bordo del cerchio.
6. `Ctrl` + selezione di uno spigolo esterno/proiettato della faccia.
7. Deve apparire vicino al cursore la barra Quick Constraints con **Tangente** come prima proposta.
8. Premere **Tangente**.
9. Il cerchio deve diventare tangente al bordo tramite il vincolo nativo Sketcher.

## Test 4 — coppie di geometrie

- due cerchi → `Concentrico`, `Tangente`, `Uguale`;
- due linee → `Collin./Tang.`, `Parallelo`, `Perpend.`, `Uguale`;
- punto + linea → `Punto su`, `Coincidente`;
- due punti → `Coincidente`, `Orizz.`, `Vert.`, `Quota`;
- linea singola → `H/V`, `Orizz.`, `Vert.`, `Quota`;
- cerchio singolo → `Raggio`, `Diametro`.

Il pulsante `⋯` deve mostrare gli altri vincoli disponibili.

## Test 5 — Smart Snap nativo

Il ritardo dell'auto-vincolo durante il trascinamento è portato a circa 150 ms. Verificare se i suggerimenti risultano:

- più rapidi;
- leggibili;
- non troppo aggressivi.

## Cosa riportare in caso di errore

Bastano:

1. operazione eseguita;
2. cosa era selezionato;
3. risultato atteso;
4. risultato reale;
5. screenshot se utile;
6. eventuali righe rosse nella Vista report di FreeCAD.
