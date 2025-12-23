import csv
from datetime import datetime
from collections import defaultdict

INPUT_FILE = "NL91INGB0004386274_01-01-2025_21-12-2025.csv"
OUTPUT_FILE = "NL91INGB0004386274_01-01-2025_21-12-2025.mt940"

# Helper to format date for MT940

def format_date(date_str):
    # ING CSV: YYYYMMDD -> MT940: YYMMDD
    try:
        dt = datetime.strptime(date_str, "%Y%m%d")
        return dt.strftime("%y%m%d")
    except Exception:
        return date_str

def format_amount(amount, af_bij):
    amt = amount.replace(".", ",")
    sign = "D" if af_bij.strip().lower() == "af" else "C"
    return sign, amt

def build_61_line(tx, idx):
    value_date = format_date(tx["Datum"])
    entry_date = value_date[2:6]
    sign, amt = format_amount(tx["Bedrag (EUR)"], tx["Af Bij"])
    ref = f"{value_date}{str(idx+1).zfill(8)}"
    return f":61:{value_date}{entry_date}{sign}{amt}NTRFNONREF//{ref}\n/TRCD/00100/"

def build_86_line(tx):
    parts = []
    if tx["Tegenrekening"]:
        parts.append(f"/CNTP/{tx['Tegenrekening']}//{tx['Naam / Omschrijving']}")
    else:
        parts.append(f"/CNTP///{tx['Naam / Omschrijving']}")
    if tx["Mededelingen"]:
        med = tx["Mededelingen"].replace(":", ".")
        parts.append(f"///REMI/USTD//{med}")
    return f":86:{''.join(parts)}/"

def determine_default_saldo(transactions):
    if not transactions:
        return "0.00"
    last_tx = transactions[-1]
    saldo_na_mutatie = float(last_tx["Saldo na mutatie"].replace(",", "."))
    bedrag = float(last_tx["Bedrag (EUR)"].replace(",", "."))
    af_bij = last_tx["Af Bij"].strip().lower()
    if af_bij == "af":
        return f"{saldo_na_mutatie + bedrag:.2f}"
    else:
        return f"{saldo_na_mutatie - bedrag:.2f}"

def convert_csv_to_mt940(input_path, output_path):
    with open(input_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        transactions = list(reader)

    # Group transactions by date
    blocks = defaultdict(list)
    for tx in transactions:
        blocks[tx["Datum"].strip('"')] .append(tx)

    with open(output_path, 'w', encoding='utf-8') as outfile:
        sorted_dates = sorted(blocks.keys())
        # Ask user for starting balance, default to previous value
        default_saldo = determine_default_saldo(transactions)
        user_input = input(f"Enter starting balance (default: {default_saldo}): ").strip()

        saldo_open = user_input if user_input else default_saldo
        previous_saldo = saldo_open
        for i, block_date in enumerate(sorted_dates):
            block = blocks[block_date]
            outfile.write("{1:F01INGBNL2ABXXX0000000000}\n")
            outfile.write("{2:I940INGBNL2AXXXN}\n")
            outfile.write("{4:\n")
            outfile.write(":20:P251208000000001\n")
            outfile.write(":25:NL91INGB0004386274EUR\n")
            outfile.write(":28C:00000\n")
            # Use previous day's closing balance as opening balance
            outfile.write(f":60F:C{format_date(block_date)}EUR{previous_saldo}\n")
            af_count = 0
            bij_count = 0
            af_sum = 0.0
            bij_sum = 0.0
            for idx, tx in enumerate(block):
                line61 = build_61_line(tx, idx)
                line86 = build_86_line(tx)
                outfile.write(line61 + "\n")
                outfile.write(line86 + "\n")
                if tx["Af Bij"].strip().lower() == "af":
                    af_count += 1
                    af_sum += float(tx["Bedrag (EUR)"].replace(",", "."))
                elif tx["Af Bij"].strip().lower() == "bij":
                    bij_count += 1
                    bij_sum += float(tx["Bedrag (EUR)"].replace(",", "."))
            saldo_end = "{:.2f}".format(float(previous_saldo.replace(",", ".")) - af_sum + bij_sum).replace(".", ",")
            outfile.write(f":62F:C{format_date(block_date)}EUR{saldo_end}\n")
            outfile.write(f":64:C{format_date(block_date)}EUR{saldo_end}\n")
            outfile.write(f":65:C{format_date(block_date)}EUR{saldo_end}\n")
            outfile.write(f":65:C{format_date(block_date)}EUR{saldo_end}\n")
            outfile.write(f":86:/SUM/{af_count}/{bij_count}/{af_sum:.2f}/{bij_sum:.2f}/\n")
            outfile.write("-}\n")
            previous_saldo = saldo_end

if __name__ == "__main__":
    convert_csv_to_mt940(INPUT_FILE, OUTPUT_FILE)
