# README

## Voci dal braccio della morte: un'indagine tra linguaggio ed emozioni

## Abstract
Il progetto è stato sviluppato per applicare le tecnologie studiate durante il corso, 
ampliando le competenze acquisite. L’obiettivo principale era esplorare un progetto 
linguistico, concentrandosi sulle ultime dichiarazioni dei condannati a morte in Texas. 
Abbiamo utilizzato il sito del Texas Department of Criminal Justice (TDCJ) per raccogliere
dati tramite web scraping, creando un dataset che includesse informazioni anagrafiche e 
i riassunti dei crimini. Abbiamo quindi analizzato le emozioni espresse nelle ultime 
parole dei condannati, utilizzando le API di OpenAI per estrarre sentimenti e riconoscere
eventuali dichiarazioni di colpevolezza o innocenza. Il progetto ha permesso di 
realizzare un’analisi linguistica profonda, combinando strumenti tecnici con un’indagine
sulle condizioni psicologiche ed emotive degli imputati. Per concludere, è stato 
effettuato un campionamento manuale per valutare le prestazioni del modello,
misurando l’accuratezza delle predizioni rispetto alle emozioni e al plea status.

## Research questions
Questo progetto si propone di esplorare le emozioni espresse dai condannati a morte nei 
loro ultimi attimi di vita e di determinare se, tra di loro, vi siano dichiarazioni di 
colpevolezza o innocenza.

## Dataset
Il dataset è stato creato da zero, attraverso tecniche di web scraping, OCR e le API di 
OpenAI dal sito https://www.tdcj.texas.gov/death_row/dr_executed_offenders.html, dove 
sono raccolte informazioni dettagliate sui condannati nel braccio della morte dal 1982 al 
2024 del Texas.

## A tentative list of milestones for the project
Il progetto è stato sviluppato in diverse fasi: prima tra tutte quella di web scraping, 
per poter creare il dataset su cui basare la fase successiva, ovvero quella delle analisi
dei dati demografici e lessicali. L'ultima fase è stata quella della valutazione delle
performance del modello. 

## Documentation
Documentazione per la riproduzione dei risultati:
1. **web_scraping.py**: è il primo file da aprire in assoluto, in quanto al suo interno 
c'è il codice da utilizzare per estrarre dal sito tutte le informazioni necessarie alla 
creazione di un primo dataset (in formato CSV).
2. **sentiment_plea_exaction.py**: in questo file c'è il codice che si occupa di prendere in 
input il file CSV precedentemente creato e di aggiornarlo con i dati estratti utilizzando
le API di OpenAI, ovvero il riconoscimento delle emozioni e dell'eventuale dichiarazione
di colpevolezza dell'imputato. 
3. **evaluation.py**: questo codice elabora il CSV creato in precedenza e genera un nuovo 
file CSV contenente un campione casuale del 10% del dataset. Il campione viene annotato 
manualmente per creare un Gold Standard utile per valutare le performance del modello. 
Vengono aggiunte due colonne per le annotazioni relative alle emozioni e alla dichiarazione 
di colpevolezza.
4. **data_analysis.ipynb**: questo notebook è utilizzato per analizzare i dati ottenuti 
dallo scraping insieme ai risultati delle API di OpenAI. Passo per passo si effettuano delle 
analisi dei dati demografici e lessicali presenti nel dataset e si fa anche una valutazione 
finale sulle performance del modello, con relativi grafici per ogni sezione.