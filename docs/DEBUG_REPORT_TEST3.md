# SolidFlow UX beta 13 test 3 verifica e limiti

## Ambito
Revisione statica di tutti i moduli Python presenti nel runtime, verifica del
manifest, test automatici di regressione e pipeline Windows dell'installer.
Questo non equivale a provare ogni comando dentro FreeCAD.

## Difetti corretti
- Modifica rapida Pad/Pocket/Revolution: la conferma ora controlla validità della
  geometria; gli errori non chiudono la finestra come se l'operazione fosse riuscita.
- Mesh Doctor: un errore durante l'aggiornamento della preview blocca conferma e
  conversione, evitando l'uso di un risultato precedente.
- Incluse le correzioni precedenti di installazione, backup, SideType, visibilità
  Undo, pulizia preview e durata della barra delle viste.
- Linea assistita: guide tratteggiate per prolungamenti e direzioni parallele o
  perpendicolari, suggerimenti confermati al clic; solver nativo con scarto dei
  nuovi vincoli conflittuali. Comando dedicato, segmenti interni, vista ortografica.

## Evidenza automatica
32 casi nella suite, inclusi i nuovi test per modifica rapida e Mesh Doctor.
Gli 8 test Qt richiedono PySide6; la CI lo installa e li esegue.
Compilazione sintattica dell'intero runtime. Analisi Pyflakes: nessun nome
indefinito rilevato; 3 import inutilizzati nei moduli legacy, senza impatto funzionale.
La distribuzione test.3 viene effettuata solo dopo il successo del job Windows,
che costruisce l'EXE e confronta gli hash di tutti i file dopo installazione.

## Matrice di copertura
| Area | Controllo eseguito | Prova nativa ancora necessaria |
| --- | --- | --- |
| Installer e diagnostica | test backup, rollback, file, build Windows | avvio addon nei profili reali |
| Sketch e Linea assistita | geometria 2D delle inferenze, priorità, solver simulato | mouse, guide Coin, solver reale e Undo |
| Pad Pocket Revolution | compatibilità proprietà, gestione preview, blocco conferma invalida | forme, direzioni, salvataggio e riapertura |
| Fillet e Profile Picker | revisione transazioni e pulizia | spigoli obliqui, regioni multiple, Cancel |
| Sweep Loft Helix Thread | revisione codice, test Qt Sweep/visibilità | geometrie e vincoli del kernel |
| Pattern Sketch e 3D | sintassi e revisione dei percorsi nativi | righe colonne angoli feature compatibili |
| Mesh | blocco preview fallita, revisione conversione | mesh reali, riparazione e solidità |
| Import Appearance Studio | revisione statica | formati, materiali, texture e ombre |
| Barra viste e palette | eventi Qt simulati con Qt reale | contesto FreeCAD e prestazioni |

## Limiti da non nascondere
FreeCAD non è disponibile nell'ambiente di sviluppo: nessuna certificazione
end-to-end della GUI o del kernel. Il modulo Linea assistita è sperimentale e
va collaudato prima di considerarlo stabile. Archi, cerchi e geometria esterna
non sono ancora inclusi nelle nuove inferenze. La protezione dai conflitti della
Linea assistita non copre automaticamente ogni comando nativo della S palette.
Le altre priorità P1/P2 del brief restano aperte.

Usare copie dei progetti e riferire anche i casi non provati. Non interpretare
un test non eseguito come un successo. Il questionario Word accompagna la build.
