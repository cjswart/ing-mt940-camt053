# ing-mt940-camt053
ING csv van een niet zakelijke rekening converteren naar mt940 of camt.053 bestand welke geimporteerd kan worden in moneybird<br>

Als je een zakelijke rekening hebt kan je gelijk vanuit je zakelijke mijn ing omgeving exporteren als mt940 of camt.053 bestand.<br>
Vanaf een niet zakelijke rekening kan je alleen een csv bestand exporteren<br>
Let op exporteer als punt komma gescheiden csv bestand met saldo na mutatie veld<br>

Login op je mijn ing<br>
Ga naar service<br>
Overzicht en downloads<br>
Af- en bijschrijvingen downloaden<br>
Kies een rekening  (kies niet alle rekeningen de standaard)<br>
Selecteer de juiste begin en eind datum<br>
Selecteer CSV<br>
Selecteer Puntkommagescheiden CSV<br>
Klik op downloaden<br>

Dit bestand wordt het input bestand voor de conversie<br>

run program:<br>
python3 csv_to_mt940.py ./NL91INGB0004386274_01-01-2025_21-12-2025.csv<br>
python3 csv_to_camt053.py ./NL91INGB0004386274_01-01-2025_21-12-2025.csv<br>

output bestandsnaam is gelijk aan de input bestandsnaam met de extensie mt940 of camt053.xml<br>
