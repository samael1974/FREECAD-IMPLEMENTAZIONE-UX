# SolidFlow UX — TEST BETA.7

## Avvio

- Premi `S`: la palette deve aprirsi.
- In Vista report deve comparire `solidflow_beta7: OK` nel riepilogo dei layer.

## Fillet dalla palette S

- Seleziona una faccia o uno spigolo di un solido.
- Premi `S`.
- Il comando deve essere `Fillet Doctor`, non il vecchio `Fillet` nativo.
- Sul parallelepipedo prova direttamente la faccia interessata e raggio 1 mm.

## Sweep / Loft / Elica dalla palette S

- Due Sketch selezionati: `S` deve proporre `Sweep` e `Loft`.
- Uno Sketch selezionato: deve comparire anche `Elica`.
- Una faccia selezionata: deve comparire `Thread Wizard` (se la faccia non è cilindrica il Wizard deve spiegare perché non può procedere).

## Mesh Doctor

1. Importa un STL o OBJ come mesh.
2. Seleziona la mesh e premi `S` oppure usa `SolidFlow > Mesh & Aspetto > Mesh Doctor…`.
3. Verifica il report: vertici, triangoli, dimensioni, solidità, non-manifold, self-intersection, normali, componenti.
4. Premi `Anteprima riparazione`.
5. L'originale deve restare intatto/nascosto e deve comparire una copia preview.
6. Annulla: la copia preview deve sparire e l'originale deve tornare visibile.
7. Ripeti e conferma: deve restare una nuova mesh `— Repaired`.

Prova `Converti copia in solido faccettato` solo su una mesh chiusa. È una conversione triangolata, non reverse engineering parametrico.

## Appearance Studio

1. Seleziona un solido o una mesh.
2. `S > Aspetto` oppure `SolidFlow > Mesh & Aspetto > Appearance Studio…`.
3. Prova i preset: PLA opaco, PETG satinato, Alluminio, Acciaio, Rame, Ottone, Legno, Ceramica, Vetro.
4. Cambia colore, lucentezza e trasparenza.
5. Annulla: deve tornare l'aspetto precedente.
6. Conferma: l'aspetto deve restare.

## Texture riscalabile

1. In Appearance Studio seleziona una PNG/JPG.
2. Prova `Planare`, `Box`, `Cilindrica`, `Sferica`.
3. Cambia `Scala X/Y`: 200% deve rendere la texture visivamente più grande, 50% più piccola/ripetuta.
4. Prova rotazione e offset.
5. Salva il documento, chiudilo e riaprilo.
6. SolidFlow deve ricostruire la preview texture dai parametri salvati.

Nota: questa è la prima implementazione Coin3D per-oggetto. Non è ancora PBR e non modifica la geometria o l'export STL/STEP.

## Se qualcosa fallisce

Invia screenshot + ultime righe della Vista report. Il bootstrap stampa anche il percorso reale di `InitGui.py` e lo stato di ogni layer caricato.
