# SolidFlow UX — Ricerca display, rivoluzione e raccordi

Data: 2026-09-15
Target: FreeCAD 1.1.3 / SolidFlow UX

## 1. Obiettivo visuale SolidWorks-like

La documentazione SOLIDWORKS 2026 conferma che:
- l'area grafica usa tipicamente un gradiente blu;
- l'interfaccia circostante usa come default il tema Light;
- il background grafico può essere Plain, Gradient, Image oppure Scene;
- sono disponibili Shadows in Shaded Mode, Ambient Occlusion, RealView, scene e floor shadows;
- il pavimento della scena può essere allineato a un piano;
- i colori di sketch predefiniti includono: under-defined blu, fully-defined nero, invalid giallo, unsolvable rosso; la selezione usa un colore distinto.

Non esiste un solo set RGB universale e immutabile: SOLIDWORKS permette schemi colore e scene differenti. Per un clone visuale molto fedele di una specifica installazione serve campionare screenshot o esportare le impostazioni della versione di riferimento. SolidFlow deve quindi offrire un preset `SolidWorks-like 2026` reversibile e, in futuro, un import/calibrazione palette.

### Da implementare
- gradiente blu SolidWorks-like;
- oggetti shaded grigio chiaro;
- bordi scuri;
- sketch under-defined blu;
- sketch fully-defined nero;
- errori/unsolvable rossi;
- invalid/conflict gialli;
- geometria esterna con colore separato;
- selezione/preselezione ad alto contrasto;
- modalità `Shadows` nella barra sotto il cubo;
- ground/floor plane opzionale, allineabile XY/XZ/YZ o a faccia selezionata;
- preset scena Technical / SolidWorks-like / Product;
- sfruttare l'illuminazione a tre punti nativa di FreeCAD 1.1.

### Vincolo tecnico
FreeCAD 1.1.3 ha illuminazione a tre punti nativa, ma non espone in modo equivalente a SOLIDWORKS un sistema semplice e completo di floor shadows + AO nella vista standard. Va quindi prototipato un overlay/scene manager SolidFlow e, dove necessario, un backend di rendering più avanzato.

## 2. Rivoluzione su asse esistente

Verifica sul sorgente FreeCAD 1.1/main:
`TaskRevolutionParameters` supporta già:
- asse verticale dello sketch (`V_Axis`);
- asse orizzontale dello sketch (`H_Axis`);
- linee di costruzione dello sketch (`AxisN`);
- assi X/Y/Z dell'origine del Body;
- riferimento selezionato dall'utente;
- selezione di EDGE / PLANAR / CIRCLE come riferimento.

`PartDesign::Revolved` espone `ReferenceAxis` come `App::PropertyLinkSub`.

### Implementazione SolidFlow prevista
Nel dialogo semplificato di Rivoluzione:
- `Asse: Automatico | H sketch | V sketch | Asse costruzione | Spigolo selezionato | Asse Body | Seleziona...`;
- se l'utente ha già selezionato profilo + spigolo/asse, precompilare automaticamente;
- permettere linea di costruzione dello stesso sketch;
- permettere edge lineare del solido;
- permettere asse di una superficie cilindrica/circolare quando valido;
- preview live dell'angolo;
- inverti / simmetrico / due lati.

Workflow obiettivo:
1. seleziona profilo;
2. Ctrl+seleziona asse/spigolo;
3. `S -> Rivoluzione`;
4. asse già riconosciuto;
5. trascina/entra angolo;
6. OK.

## 3. Problema raccordo: 4° spigolo non accettato

Il sorgente `PartDesign::Fillet` usa il kernel OpenCascade tramite `makeElementFillet(...)`. Il codice FreeCAD gestisce esplicitamente il caso in cui un gruppo di spigoli non possa essere raccordato insieme e suggerisce di provare gli spigoli individualmente o un raggio più piccolo.

Quindi il problema può dipendere da:
- interazione tra raccordi ai vertici;
- raggio troppo grande per la combinazione selezionata;
- degenerazione/tangenza locale del risultato;
- topologia prodotta dalla feature precedente;
- limitazione/instabilità del kernel OpenCascade su quella combinazione.

Su un parallelepipedo semplice quattro bordi di una faccia dovrebbero normalmente essere raccordabili con un raggio compatibile. Se 3 passano e il 4° no, SolidFlow deve diagnosticare quale combinazione o raggio fa fallire il kernel invece di mostrare solo un errore generico.

### `Fillet Doctor` previsto
- selezione multipla edges;
- preview live;
- test incrementale della selezione;
- identificazione edge che fa fallire il risultato;
- ricerca automatica del massimo raggio valido;
- messaggio del tipo `Edge4 incompatibile a R=5.0 mm; prova <= 3.8 mm`;
- pulsante `Raccorda perimetro faccia` che raccoglie i bordi della faccia selezionata;
- fallback `Raccordi sequenziali` solo quando il raccordo simultaneo non è possibile;
- evidenziazione del bordo problematico;
- possibilità `Use all edges` dove ha senso.

## 4. Priorità di sviluppo aggiornata

1. completare test beta.4 Quick Constraints + tema;
2. calibrare preset grafico SolidWorks-like;
3. aggiungere modalità Shadows + ground plane;
4. estendere Rivoluzione con asse selezionabile/automatico;
5. costruire Fillet Doctor e selezione perimetro faccia;
6. proseguire con Sweep / Loft / Helix / Thread Wizard;
7. Materials & Appearance Studio con texture scalabili;
8. Mesh/Import/3D Print Studio.

## 5. Nota su fedeltà colori

SolidFlow deve replicare il comportamento e la leggibilità, non dipendere da asset proprietari. Per avere valori RGB praticamente identici a una specifica configurazione SOLIDWORKS, acquisire in seguito:
- screenshot pulito della viewport e dello sketch;
- screenshot delle opzioni `System Options > Colors`;
- nome della scena predefinita;
- eventuale schema colore selezionato.

Questi dati permetteranno una calibrazione numerica 1:1 del preset SolidFlow.
