# ing-mt940-camt053
ING csv van een niet zakelijke rekening converteren naar mt940 of camt.053 bestand welke geimporteerd kan worden in moneybird

Als je een zakelijke rekening hebt kan je gelijk vanuit je zakelijke mijn ing omgeving exporteren als mt940 of camt.053 bestand.
Vanaf een niet zakelijke rekening kan je alleen een csv bestand exporteren
Let op exporteer als punt komma gescheiden csv bestand met saldo na mutatie veld

Login op je mijn ing
Ga naar service
Overzicht en downloads
Af- en bijschrijvingen downloaden
Kies een rekening  (kies niet alle rekeningen de standaard)
Selecteer de juiste begin en eind datum
Selecteer CSV
Selecteer Puntkommagescheiden CSV
Klik op downloaden

Dit bestand wordt het input bestand voor de conversie

run program:
python3 csv_to_mt940.py ./NL91INGB0004386274_01-01-2025_21-12-2025.csv
python3 csv_to_camt053.py ./NL91INGB0004386274_01-01-2025_21-12-2025.csv

output bestandsnaam is gelijk aan de input bestandsnaam met de extensie mt940 of camt053.xml
