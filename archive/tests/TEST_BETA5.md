# SolidFlow UX — TEST beta.5

Target: FreeCAD 1.1.3 / Windows / Python 3.11

## 1. Regressione base

1. Avvia FreeCAD.
2. Premi `S` in area grafica: la palette SolidFlow deve aprirsi.
3. Verifica Home, Wire, Solido, Bordi, Nascoste, Render, Materiale.
4. Entra in uno Sketch e verifica che i Quick Constraints beta.4 siano ancora presenti.

## 2. Fillet Doctor — test prioritario

### Caso A — faccia del cubo

1. Crea un parallelepipedo/cubo in Part Design.
2. Seleziona **una faccia** soltanto.
3. Apri `SolidFlow > Fillet Doctor…`.
4. Il dialogo deve indicare `perimetro completo della faccia`.
5. Imposta un raggio piccolo (es. 1 mm) e premi `Analizza`.
6. Se valido, premi `Crea raccordo`.
7. Verifica che vengano raccordati tutti e quattro i bordi del perimetro della faccia.

Questa modalità serve apposta a evitare la difficoltà di selezionare/accettare il quarto spigolo.

### Caso B — quattro spigoli selezionati

1. Seleziona con Ctrl i quattro bordi dello stesso perimetro.
2. Apri Fillet Doctor.
3. `Analizza` deve testare l'intera combinazione.
4. Se il raggio è eccessivo, il dialogo deve:
   - segnalare che la combinazione non è valida;
   - verificare gli spigoli singolarmente;
   - tentare di individuare l'elemento/combinazione critica;
   - mostrare un `Massimo sicuro stimato`.
5. Premi `Trova massimo sicuro` e poi `Crea raccordo`.

### Caso C — tutti gli spigoli

Spunta `Raccorda tutti gli spigoli del solido`, analizza e crea.

## 3. Rivoluzione+

### Asse di costruzione nello Sketch

1. Crea uno Sketch con un profilo chiuso.
2. Aggiungi una linea di costruzione da usare come asse.
3. Chiudi lo Sketch.
4. Seleziona lo Sketch e apri `SolidFlow > Rivoluzione+…`.
5. Nel menu Asse devono comparire:
   - Asse verticale Sketch;
   - Asse orizzontale Sketch;
   - Linea di costruzione 1 (e successive).
6. Scegli la linea di costruzione.
7. Modifica Angolo / Inverti / Simmetrica e verifica la preview live.
8. OK deve lasciare una normale feature `PartDesign::Revolution` nell'albero.

### Spigolo del solido come asse

1. Ctrl+seleziona lo Sketch del profilo e uno spigolo lineare di un solido.
2. Apri `Rivoluzione+…`.
3. Lo `Spigolo selezionato` deve apparire come prima scelta dell'asse.
4. Verifica preview e OK.

## 4. Ombre + piano

1. Con un solido visibile, premi `Ombre` vicino agli stili di visualizzazione; se il pulsante non è presente, usa `SolidFlow > Ombre + piano d'appoggio`.
2. Deve apparire un piano chiaro sotto il modello e una morbida ombra di contatto.
3. Dal menu `SolidFlow > Piano d'appoggio` prova XY / XZ / YZ.
4. Disattivando Ombre, piano e ombra devono sparire senza aggiungere oggetti all'albero del documento.

Nota: in beta.5 si tratta di una **preview di studio / ombra di contatto**, non ancora di un renderer fisico con cast shadows ray-traced.

## 5. Cosa riportare

Per ogni anomalia bastano:

- operazione eseguita;
- cosa ti aspettavi;
- cosa è accaduto;
- screenshot, se possibile;
- per Fillet: dimensioni del solido e raggio richiesto.
