# SolidFlow UX — Roadmap, Stato e Memoria Ricognitiva

**Progetto:** SolidFlow UX per FreeCAD 1.1.x  
**Ultimo aggiornamento:** 2026-09-15  
**Target attuale:** FreeCAD 1.1.3 su Windows  
**Cartella add-on:** `C:\Users\corfe\AppData\Roaming\FreeCAD\v1-1\Mod\SolidFlowUX`

---

## 1. Visione

SolidFlow UX deve trasformare FreeCAD in un ambiente CAD parametrico più rapido, leggibile e coerente, mantenendo sotto il cofano i motori nativi di FreeCAD, Sketcher, Part Design, Part, Mesh, Surface, Material e OpenCascade.

Obiettivo:

- workflow parametrico rapido e predittivo;
- esperienza vicina a SolidWorks per sketch, feature e modifica diretta;
- immediatezza visiva vicina a SketchUp;
- strumenti dedicati alla stampa 3D;
- mesh, superfici e reverse engineering;
- materiali, texture scalabili e preview realistica;
- rendering rapido integrato e rendering fotorealistico tramite bridge esterno;
- riduzione progressiva della necessità di conoscere i singoli Workbench di FreeCAD.

Principio guida:

> **L'utente deve scegliere cosa vuole ottenere, non quale Workbench deve imparare.**

---

## 2. Principi architetturali

1. Non forcare FreeCAD core finché non è necessario.
2. SolidFlow crea e modifica, quando possibile, oggetti e feature native FreeCAD.
3. Prima si valida il workflow in Python/Qt; C++ solo quando prestazioni o integrazione profonda lo richiedono.
4. Le operazioni importanti devono avere selezione contestuale, preview live, OK/Annulla e transazioni FreeCAD.
5. Gli errori devono essere comprensibili e collegati alla geometria interessata.
6. Le funzioni invasive devono essere reversibili/disattivabili.
7. Ridurre menu annidati e comandi duplicati.
8. Mantenere una UX coerente tra Sketch, solidi, superfici, mesh e materiali.

---

## 3. Stato attuale — v0.4 beta

### Implementato / in validazione

- Palette contestuale con tasto `S`.
- Dimensioni palette approvate:
  - icone 28 × 28 px;
  - altezza pulsanti 56 px;
  - larghezza minima 120 px;
  - font 13 px.
- Selezione contestuale Sketch / Part Design.
- Schizzo su faccia.
- Pad / Pocket / Revolution con preview.
- Import Assistant iniziale.
- Supporto iniziale ai profili / contorni.
- Smart Snap / suggerimenti vincoli in sviluppo.
- Mini-toolbar contestuale in sviluppo.
- Quick edit / Instant3D-like in sviluppo.
- Doppio clic feature per modifica rapida.
- Geometria esterna automatica del perimetro quando si crea uno Sketch su faccia.
- Proiezione geometria / riferimenti esterni.
- Barra visualizzazione sotto il cubo di navigazione.
- Pulsante `Home`:
  - clic = isometrica + Fit All;
  - Shift + clic = Fit All mantenendo l'orientamento.
- Stili visualizzazione:
  - Wireframe;
  - Solido / Shaded;
  - Solido con bordi / Flat Lines;
  - Hidden Line;
  - Render preview;
  - Materiale.

### Punto critico corrente

Lo Sketcher deve diventare molto più rapido nell'uso dei vincoli, soprattutto verso geometria esterna della faccia/solido.

Caso prioritario:

> cerchio su una faccia → selezione cerchio + spigolo esterno → proposta immediata `Tangente`.

---

## 4. v0.4 beta.4 — Smart Sketch & SolidWorks-like UX

### 4.1 Tema grafico SolidFlow / SolidWorks-like

Creare un preset grafico reversibile:

- sfondo 3D chiaro azzurro/grigio;
- contrasto migliore dei bordi;
- colori coerenti per selezione e pre-selezione;
- Sketch più leggibile;
- distinzione tra geometria libera, vincolata, esterna ed errore;
- assi e griglia meno invasivi;
- pannelli Qt coerenti;
- ritorno rapido al tema FreeCAD standard.

Non copiare risorse proprietarie SolidWorks: replicare solo la filosofia visiva.

### 4.2 Quick Constraints contestuali

#### Una linea

- Orizzontale;
- Verticale;
- Lunghezza;
- Angolo;
- Fissa.

#### Due linee

- Parallelo;
- Perpendicolare;
- Collineare;
- Uguale;
- Angolo;
- Distanza.

#### Cerchio singolo

- Raggio;
- Diametro;
- Centro;
- Fissa.

#### Due cerchi / archi

- Concentrico;
- Uguale;
- Tangente;
- distanza centri.

#### Cerchio + linea / bordo esterno

- **Tangente**;
- distanza;
- punto su oggetto quando coerente.

#### Punto + punto

- Coincidente;
- distanza;
- orizzontale;
- verticale.

#### Punto + linea

- Punto su oggetto;
- coincidente con estremo;
- punto medio.

Gli stessi vincoli devono funzionare verso la geometria esterna del solido.

### 4.3 Smart Snap

Priorità:

1. endpoint;
2. centro;
3. punto medio;
4. intersezione;
5. punto su oggetto;
6. tangente;
7. allineamento H/V;
8. geometria esterna;
9. proiezioni/riferimenti.

Non aumentare semplicemente la tolleranza: attribuire un punteggio ai candidati in base a distanza, tipo di geometria e intento del comando corrente.

### 4.4 Auto-constraint suggerito

Durante il disegno:

- linea quasi orizzontale → Orizzontale;
- linea quasi verticale → Verticale;
- estremi vicini → Coincidente;
- geometrie quasi parallele → Parallelo;
- geometrie quasi perpendicolari → Perpendicolare;
- linea/circonferenza in contatto → Tangente;
- segmenti quasi uguali → Uguale;
- cerchi quasi concentrici → Concentrico.

Il suggerimento deve apparire **prima del clic**.

### 4.5 External Geometry

`Schizzo su faccia` deve:

- importare automaticamente il perimetro della faccia come geometria esterna;
- evitare duplicati;
- mantenere il legame parametrico;
- rendere i riferimenti disponibili per snap e vincoli.

Comando:

`S → Proietta`

con:

- Spigolo;
- Intera faccia;
- Altri bordi;
- Vertici;
- Cancella riferimento.

---

## 5. v0.5 — Advanced Features

### 5.1 Sweep / Pipe

Interfaccia semplificata:

- Profilo;
- Percorso;
- orientamento Automatico / Frenet / Fisso;
- preview live;
- Additivo / Sottrattivo.

Applicazioni:

- tubazioni;
- guarnizioni;
- scanalature;
- gole;
- cavi;
- maniglie;
- profili complessi;
- filettature custom.

### 5.2 Loft

Supportare:

- Additive Loft;
- Subtractive Loft;
- Surface Loft in fase successiva.

UX:

- selezione multipla Sketch;
- ordinamento automatico sezioni;
- drag & drop dell'ordine;
- anteprima live;
- controllo compatibilità;
- errori leggibili.

### 5.3 Helix

Parametri:

- passo;
- altezza;
- numero giri;
- angolo cono;
- direzione;
- destra / sinistra;
- profilo.

### 5.4 Thread Wizard

Obiettivo: filettature senza costruzione manuale di eliche/profili.

Parametri:

- ISO metrica;
- M3 ... M60 e oltre;
- diametro;
- passo;
- lunghezza;
- interna / esterna;
- destra / sinistra;
- gioco/tolleranza stampa 3D;
- smusso ingresso;
- preview.

Modalità:

- **Cosmetic / Preview** — leggera;
- **Physical / Print** — geometria reale.

Preset:

- FDM standard;
- FDM preciso;
- resin;
- custom clearance.

Prevedere modalità `Robust Thread` per evitare coincidenze geometriche problematiche.

---

## 6. v0.6 — Import & Mesh Studio

### Import Assistant universale

Formati prioritari:

#### CAD / solidi
- FCStd;
- STEP / STP / STPZ;
- IGES;
- BREP.

#### 2D
- DXF;
- DWG;
- SVG.

#### Mesh / stampa 3D
- STL;
- OBJ;
- 3MF;
- AMF.

#### Interoperabilità/render
- OBJ;
- GLTF / GLB;
- DAE dove disponibile.

#### Raster reference
- PNG;
- JPG;
- BMP.

### DXF / SVG

- unità;
- layer/gruppi;
- scala;
- calibrazione con distanza nota;
- pulizia duplicati;
- chiusura piccoli gap;
- conversione a Sketch;
- selezione contorni;
- preview.

### DWG

Gestione guidata backend:

- LibreDWG;
- ODA File Converter;
- altri backend supportati.

Se assente: messaggio chiaro e guida.

### Mesh Doctor

Analisi:

- numero triangoli;
- dimensioni;
- mesh aperta;
- buchi;
- non-manifold;
- normali;
- facce degeneri;
- self-intersection;
- componenti isolate;
- duplicati;
- unità probabili.

Azioni:

- Ripara;
- chiudi fori;
- correggi normali;
- elimina degenerazioni;
- semplifica / decima;
- separa shell;
- unisci;
- taglia;
- scala;
- orienta.

### Reverse Engineering

Pipeline:

`Mesh → riconoscimento primitive → superfici → feature CAD`

Riconoscimenti iniziali:

- piani;
- cilindri;
- coni;
- sfere;
- fori;
- assi;
- raccordi semplici.

Integrare/adattare add-on affidabili quando conveniente (es. MeshToFeatures, Detessellate) invece di duplicare codice.

---

## 7. v0.7 — Materials & Appearance Studio

### Materiale fisico vs aspetto

Esempio:

- Materiale: PETG
- Aspetto: nero satinato

oppure:

- Materiale: Alluminio
- Aspetto: anodizzato spazzolato.

### Material Library

Categorie:

- PLA;
- PETG;
- ABS / ASA;
- TPU;
- resina;
- alluminio;
- acciaio;
- ottone;
- rame;
- legno;
- pietra;
- ceramica;
- vetro;
- gomma;
- tessuto;
- vernici.

Parametri visivi:

- colore base;
- metallico;
- rugosità;
- trasparenza;
- emissione;
- specularità quando disponibile.

Parametri fisici opzionali:

- densità;
- elasticità;
- conducibilità;
- costo/kg.

### Texture Library

Le texture devono essere riscalabili senza editing esterno.

Controlli:

- scala X/Y;
- mantieni proporzioni;
- rotazione;
- offset X/Y;
- ripetizione;
- specchio;
- Fit to Object.

Mapping:

- Planare;
- Box;
- Cilindrico;
- Sferico;
- Triplanare.

Mappe PBR:

- Base Color;
- Roughness;
- Metallic;
- Normal;
- Height/Bump;
- AO;
- Emission;
- Alpha.

### Preview realtime

Preset:

- Technical;
- Softbox;
- Product;
- Dark Studio;
- Outdoor;
- Neutral;
- White Studio.

Controlli:

- intensità;
- direzione luce;
- ombre;
- ambiente;
- pavimento;
- colore sfondo;
- prospettiva;
- qualità preview.

### Rendering

Strategia:

- preview realtime interna;
- bridge Blender per render finale.

Preset:

- Veloce;
- Prodotto;
- Fotorealistico.

Backend possibili:

- Eevee;
- Cycles.

Export preferenziale:

- GLTF / GLB con materiali.

---

## 8. v0.8 — Surface / Organic Studio

Strumenti:

- Fill Surface;
- Patch;
- Loft Surface;
- Sweep Surface;
- Blend;
- Extend;
- Trim;
- Join;
- Thicken;
- Offset Surface.

Sfruttare Surface Workbench, Curves Workbench e NURBS/OpenCascade.

UX:

- selezione bordi;
- preview live;
- continuità G0 / G1 / G2;
- maniglie e punti controllo.

### Sculpt — fase successiva

Da valutare solo dopo Surface Studio:

- Push/Pull;
- Smooth;
- Inflate;
- Grab;
- relax mesh;
- symmetry.

Probabile componente C++ dedicato per prestazioni.

---

## 9. v0.9 — 3D Print Studio

Comando:

`PREPARA PER STAMPA`

Analisi:

- manifold;
- mesh chiusa;
- pareti sottili;
- volumi separati;
- overhang;
- ponti;
- fori piccoli;
- clearance;
- dettagli minimi;
- orientamento;
- volume;
- dimensioni.

Funzioni:

- auto-orient;
- split model;
- pin di centraggio;
- tolleranza incastri;
- compensazione foro;
- shrinkage compensation;
- controllo filettature fisiche;
- qualità mesh export.

Preset:

- Bozza;
- Standard;
- Alta qualità.

Formato preferito:

- 3MF.

Compatibilità:

- STL;
- OBJ.

---

## 10. v1.0 — SolidFlow unificato

### CREATE
- Sketch
- Solid
- Surface
- Mesh

### FEATURE
- Extrude
- Cut
- Revolve
- Sweep
- Loft
- Thread

### MODIFY
- Fillet
- Chamfer
- Shell
- Draft
- Pattern
- Mirror

### APPEARANCE
- Material
- Texture
- Studio
- Render

### MAKE
- Inspect
- Repair
- Prepare Print
- Export

L'utente non dovrebbe dover conoscere i Workbench sottostanti.

---

## 11. Design Intent Engine

Suggerimenti basati sulla selezione.

### Cilindro selezionato
- Filetta;
- foro coassiale;
- smusso;
- raccordo.

### Due Sketch
- Loft;
- Sweep;
- confronta profili.

### STL
- Ripara;
- semplifica;
- converti CAD;
- prepara stampa.

### Faccia
- Sketch;
- Pocket;
- Offset;
- Shell.

### Bordo
- Fillet;
- Chamfer;
- Proietta.

### Cerchio nello Sketch + bordo esterno
- **Tangente** come prima proposta.

---

## 12. Regole UX

Una funzione SolidFlow è considerata finita quando:

1. parte dalla selezione corretta senza cercare menu;
2. mostra preview quando applicabile;
3. usa OK / Annulla coerenti;
4. produce feature native FreeCAD quando possibile;
5. presenta errori comprensibili;
6. supporta Undo;
7. non lascia oggetti temporanei;
8. non rompe il workflow standard FreeCAD;
9. un'operazione comune richiede idealmente selezione + 1–2 clic + eventuale valore numerico.

---

## 13. Strategia GitHub e backup

Repository dedicato:

`FREECAD-IMPLEMENTAZIONE-UX`

Regola: creare un backup almeno:

- prima di modifiche strutturali;
- dopo una milestone stabile;
- prima di cambiare architettura;
- dopo una sessione di sviluppo importante;
- prima di generare una release distribuita.

### Branch suggeriti

- `main` → ultima versione stabile;
- `develop` → sviluppo integrato;
- `feature/smart-sketch`;
- `feature/thread-wizard`;
- `feature/mesh-studio`;
- `feature/materials`;
- `feature/surface-studio`.

### Tag release

- `v0.4.0-beta.3`
- `v0.4.0-beta.4`
- `v0.5.0-beta.1`

### File da versionare sempre

- `Init.py`
- `InitGui.py`
- `solidflow_ui.py`
- `solidflow_features.py`
- `solidflow_import.py`
- nuovi moduli SolidFlow;
- `README.md`
- `CHANGELOG.md`
- `SOLIDFLOW_ROADMAP.md`
- test.

### Non versionare

- `__pycache__/`
- `.pyc`
- file temporanei;
- cache;
- configurazioni locali;
- credenziali/token.

### Checkpoint operativo

```text
git status
git add .
git commit -m "SolidFlow: descrizione modifica"
git push
```

Prima di modifiche ad alto rischio:

```text
git tag backup-YYYYMMDD-HHMM
git push --tags
```

---

## 14. Ordine di sviluppo operativo

### Adesso

1. completare v0.4 beta.4;
2. Quick Constraints;
3. Smart Snap verso geometria esterna;
4. tema grafico SolidWorks-like;
5. test workflow completo.

### Subito dopo

6. Sweep;
7. Loft;
8. Helix;
9. Thread Wizard.

### Terzo blocco

10. Import universale;
11. Mesh Doctor;
12. STL/OBJ/3MF;
13. reverse engineering.

### Quarto blocco

14. Material Library;
15. texture riscalabili;
16. PBR;
17. preview studio;
18. Blender bridge.

### Quinto blocco

19. Surface Studio;
20. Organic tools;
21. 3D Print Studio.

---

## 15. Backlog funzionale

### Sketch

- [ ] Quick Constraints completi
- [ ] Tangente cerchio ↔ external edge
- [ ] Concentrico
- [ ] Collineare
- [ ] Punto medio
- [ ] Simmetria
- [ ] Smart Dimension
- [ ] regione chiusa cliccabile
- [ ] Trim / Extend semplificati
- [ ] Offset
- [ ] Mirror Sketch
- [ ] Project Geometry

### Part Design

- [x] Pad base
- [x] Pocket base
- [x] Revolution base
- [ ] Sweep Additive
- [ ] Sweep Subtractive
- [ ] Loft Additive
- [ ] Loft Subtractive
- [ ] Helix Additive
- [ ] Helix Subtractive
- [ ] Thread Wizard
- [ ] Shell semplificato
- [ ] Draft
- [ ] Pattern semplificati
- [ ] Mirror
- [ ] Hole Wizard

### UI

- [x] Palette S
- [x] barra vista sotto cubo
- [x] Home / Fit All
- [ ] tema SolidWorks-like
- [ ] toolbar vincoli contestuale
- [ ] mouse gestures definitivi
- [ ] Instant3D manipolatore 3D reale
- [ ] Property Manager SolidFlow

### Import

- [x] DXF iniziale
- [x] DWG iniziale
- [x] SVG iniziale
- [x] raster reference
- [ ] STEP
- [ ] IGES
- [ ] STL
- [ ] OBJ
- [ ] 3MF
- [ ] GLTF/GLB
- [ ] Import Assistant universale

### Mesh

- [ ] Mesh Doctor
- [ ] Repair
- [ ] decimate
- [ ] normals
- [ ] holes
- [ ] manifold check
- [ ] split shells
- [ ] mesh → CAD
- [ ] reverse engineering

### Appearance

- [ ] material library
- [ ] texture library
- [ ] scale texture
- [ ] rotate / offset texture
- [ ] planar mapping
- [ ] box mapping
- [ ] cylindrical mapping
- [ ] spherical mapping
- [ ] triplanar
- [ ] PBR maps
- [ ] preview studio
- [ ] Blender bridge

### Surface

- [ ] Fill
- [ ] Patch
- [ ] Surface Loft
- [ ] Surface Sweep
- [ ] Blend
- [ ] Trim
- [ ] Extend
- [ ] Join
- [ ] Thicken
- [ ] G0/G1/G2

### 3D Print

- [ ] Print Inspector
- [ ] wall thickness
- [ ] overhang
- [ ] clearance
- [ ] hole compensation
- [ ] auto orientation
- [ ] split
- [ ] pins
- [ ] 3MF presets
- [ ] physical threads check

---

## 16. Integrare o riscrivere?

Prima di sviluppare una funzione:

1. verificare se FreeCAD core la possiede già;
2. verificare se esiste un add-on affidabile;
3. se esiste, preferire wrapper/adattatore e mantenere output nativo;
4. riscrivere solo se UX, API, prestazioni o manutenzione lo rendono necessario.

---

## 17. Nota per le sessioni future

Prima di modificare il codice:

1. leggere questo file;
2. leggere `CHANGELOG`;
3. verificare versione FreeCAD target;
4. verificare stato ultima beta;
5. fare backup Git se la modifica è strutturale;
6. evitare regressioni nelle funzioni approvate;
7. aggiornare questo documento dopo ogni milestone significativa.

Questo file è la **memoria ricognitiva tecnica ufficiale del progetto SolidFlow UX**.
