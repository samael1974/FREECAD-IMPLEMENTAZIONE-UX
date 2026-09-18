## SolidFlow UX con Linea assistita
**Versione sperimentale per Windows e FreeCAD 1.1.x.**

Scarica **SolidFlowUX-Setup-v0.4.0-beta.13-test.3.exe** dagli Assets, chiudi
FreeCAD ed esegui il setup. Per il profilo standard lascia la cartella proposta.
Poi riapri FreeCAD. Non serve scaricare Source code o avere un account GitHub.
Per FreeCAD portabile/profili personalizzati usa il pacchetto ZIP con la macro offline.

### Come provare le guide
1. Apri uno Sketch in modifica e disegna una linea obliqua di riferimento.
2. Menu **SolidFlow > Sketch intelligente > Linea assistita — guide tratteggiate**.
3. Clicca il primo punto, poi avvicina il cursore al prolungamento di una linea
   o a una direzione parallela/perpendicolare rispetto a una linea esistente.
4. La guida arancione tratteggiata e il pannello mostrano il suggerimento.
5. Clicca per creare il segmento. Con la casella attiva il vincolo viene confermato
   al clic, se il solver lo accetta. Shift permette un punto libero senza snap né
   vincolo suggerito. Esc o clic destro termina; Undo annulla l'ultimo segmento.

È un **comando dedicato**, non una modifica al comando Linea nativo. All'avvio
termina l'eventuale operazione di disegno in corso e riapre lo Sketch, mantenendo
le geometrie già confermate. Le geometrie create sono segmenti Sketcher nativi.
Prima versione: segmenti interni, anche obliqui; archi e geometria esterna esclusi.
Usare la vista ortografica. Le guide sono temporanee e non si salvano nel modello.

### Verifiche e limiti
Distribuzione subordinata al successo di test automatici, compilazione Windows,
installazione effettiva dell'EXE in un profilo temporaneo e verifica dei file.
L'interazione Coin/FreeCAD e la geometria nel programma nativo devono ancora
essere provate: questa build serve ai tester, su copie dei progetti.
L'EXE non è firmato: se viene bloccato, allega l'errore senza disabilitare protezioni.

Per assistenza: versione FreeCAD, nome build, passi esatti, risultato atteso,
screenshot e rapporto **SolidFlow > Diagnostica SolidFlow**.

### Correzioni di debugging aggiuntive
Modifica rapida: impedita la conferma di una geometria non valida.
Mesh Doctor: un errore di riparazione blocca la conferma/conversione
dell’anteprima precedente. Nessuna modifica ai documenti originali durante
i controlli statici. Tutti i moduli runtime inclusi nel controllo sintattico.
