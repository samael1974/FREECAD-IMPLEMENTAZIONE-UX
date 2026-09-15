# SolidFlow UX beta.8 — Test Serie / Pattern

## 1. Sketch — serie rettangolare
1. Crea/apri uno Sketch.
2. Disegna un cerchio o un rettangolo.
3. Seleziona la geometria da ripetere.
4. Premi `S`.
5. Deve comparire `Serie X/Y` nella sezione `VINCOLI / SERIE`.
6. Apri il comando e crea almeno 3 colonne e 2 righe.

Atteso: FreeCAD usa il comando nativo `Sketcher_RectangularArray` e la geometria resta nello Sketch.

## 2. Sketch — serie polare
1. Nello stesso Sketch seleziona una geometria interna.
2. Premi `S`.
3. Seleziona `Serie polare`.
4. Imposta più copie attorno al centro desiderato.

Atteso: viene usato `Sketcher_Rotate` / Polar Transform nativo.

## 3. Geometria esterna
1. Crea uno Sketch su faccia con riferimenti esterni.
2. Seleziona soltanto un bordo esterno viola.
3. Premi `S`.

Atteso: SolidFlow non propone di replicare quel riferimento esterno come geometria dello Sketch.

## 4. Feature 3D — serie lineare
1. Esci dallo Sketch.
2. Crea un Pad/Pocket o altra feature Part Design.
3. Seleziona la feature nell'albero.
4. Premi `S`.
5. Deve comparire `Serie lineare 3D`.

Atteso: viene lanciato `PartDesign_LinearPattern`; la direzione può essere scelta rispetto agli assi/riferimenti 3D, inclusi X/Y/Z quando disponibili.

## 5. Feature 3D — serie polare
1. Seleziona una feature Part Design.
2. Premi `S`.
3. Seleziona `Serie polare 3D`.

Atteso: viene lanciato `PartDesign_PolarPattern`.

## 6. Menu di emergenza
Verifica anche:

`SolidFlow → Serie & Trasformazioni → Dentro Sketch / Feature 3D`

Le quattro funzioni devono essere sempre raggiungibili da qui.

## 7. Diagnostica avvio
Nella Report view deve comparire tra i layer caricati:

`solidflow_patterns: OK 0.4.0-beta.8`
