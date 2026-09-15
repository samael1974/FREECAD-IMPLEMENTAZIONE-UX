# SolidFlow UX — TEST BETA.6

Target: FreeCAD 1.1.3 / Windows / Python 3.11

Questa checklist serve a verificare il comportamento reale delle nuove feature avanzate. Non serve eseguire tutti i test insieme: partire dai primi quattro.

## 0. Avvio

1. Avvia FreeCAD.
2. Premi `S`: la palette SolidFlow deve ancora aprirsi normalmente.
3. Apri `Visualizza > Pannelli > Vista report` solo se qualcosa non funziona.
4. Nel report dovrebbe comparire una riga `SolidFlow bootstrap:` e lo stato dei layer beta4/beta5/beta6.

## 1. Sweep additivo

1. Crea due Sketch nello stesso Body.
2. Sketch A: profilo chiuso semplice, ad esempio un cerchio.
3. Sketch B: percorso semplice, ad esempio una linea o una polilinea su piano opportuno.
4. Seleziona prima A e poi B con Ctrl.
5. `SolidFlow > Feature avanzate > Sweep`.
6. Verifica l'anteprima.
7. Prova `Standard`, `Fisso`, `Frenet`.
8. Conferma.

Atteso: nell'albero resta una normale feature `PartDesign::AdditivePipe` modificabile.

## 2. Sweep Cut

Ripeti il test dentro un Body che contiene già un solido e scegli `Sweep Cut`.

Atteso: normale `PartDesign::SubtractivePipe` e sottrazione valida.

## 3. Loft

1. Crea almeno due Sketch chiusi nello stesso Body su piani/quote differenti.
2. Selezionali tutti con Ctrl.
3. `SolidFlow > Feature avanzate > Loft`.
4. Usa `Su/Giù` per cambiare ordine delle sezioni.
5. Prova `Superficie rigata`.
6. Conferma.

Atteso: normale `PartDesign::AdditiveLoft` con `Profile` e `Sections` ancora editabili.

## 4. Elica

1. Seleziona uno Sketch chiuso adatto a un'elica.
2. `SolidFlow > Feature avanzate > Elica`.
3. Prova asse verticale/orizzontale o una linea di costruzione.
4. Prova `Passo + altezza + angolo`.
5. Prova filettatura sinistrorsa.
6. Conferma.

Atteso: normale `PartDesign::AdditiveHelix` parametrica.

## 5. Elica Cut

Su un Body con un solido, usa un profilo chiuso e `Elica Cut`.

Atteso: normale `PartDesign::SubtractiveHelix`.

## 6. Thread Wizard — prima prova

Per questa beta usare un cilindro con asse parallelo all'asse globale Z.

1. Crea un cilindro/pad cilindrico.
2. Seleziona la faccia cilindrica laterale.
3. `SolidFlow > Feature avanzate > Thread Wizard…`.
4. Verifica che diametro e lunghezza siano rilevati.
5. Se il diametro è vicino a una misura ISO, verifica il preset automatico.
6. Prova un passo ragionevole e `Aggiorna anteprima`.
7. Conferma solo se l'anteprima è valida.

Atteso: `ThreadProfile` + normale `PartDesign::SubtractiveHelix` chiamata `Thread`.

Nota: questa è ancora una filettatura V 60° semplificata per prototipazione/stampa 3D; crest/root ISO completi e asse cilindrico arbitrario verranno sviluppati nelle revisioni successive.

## 7. Cancel / sicurezza anteprima

Per Sweep, Loft ed Elica:

1. Apri il dialogo e attendi la preview.
2. Premi `Annulla` oppure chiudi con `X`.
3. Controlla l'albero.

Atteso: la feature preview non deve restare nel Body e il Tip precedente deve essere ripristinato.

## 8. Fillet Doctor

Il comando `S > Fillet` può ancora richiamare il comando FreeCAD classico. Per diagnosticare il problema dei quattro spigoli usare per ora:

`SolidFlow > Fillet Doctor…`

Test consigliato:

1. seleziona direttamente una faccia del parallelepipedo;
2. apri Fillet Doctor;
3. raggio 1 mm;
4. `Analizza`;
5. se valido, `Crea raccordo`;
6. se non valido, `Trova massimo sicuro`.

Segnalare: dimensioni del box, faccia/spigoli selezionati, raggio e testo prodotto dal Doctor.

## Cosa inviare in caso di errore

Bastano:

- operazione eseguita;
- screenshot;
- ultime righe della Vista report che iniziano con `SolidFlow` o mostrano traceback Python.
