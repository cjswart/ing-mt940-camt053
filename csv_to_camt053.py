import csv
from datetime import datetime, timedelta
from collections import defaultdict

INPUT_FILE = "NL91INGB0004386274_01-01-2025_21-12-2025.csv"
OUTPUT_FILE = "NL91INGB0004386274_01-01-2025_21-12-2025.camt053.xml"

HEADER = """<?xml version='1.0' encoding='UTF-8'?>

<Document xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" xmlns=\"urn:iso:std:iso:20022:tech:xsd:camt.053.001.02\" xsi:schemaLocation=\"urn:iso:std:iso:20022:tech:xsd:camt.053.001.02 camt.053.001.02.xsd\">
	<BkToCstmrStmt>
		<GrpHdr>
			<MsgId>{msgid}</MsgId>
			<CreDtTm>{created}</CreDtTm>
		</GrpHdr>
"""
FOOTER = """	</BkToCstmrStmt>
</Document>
"""

def format_date(date_str):
    try:
        if '-' in date_str:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        else:
            dt = datetime.strptime(date_str, "%Y%m%d")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return date_str

def now_iso():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000+01:00")

def make_ntry_ref(date, idx):
    d = datetime.strptime(date, "%Y%m%d") if len(date) == 8 else datetime.strptime(date, "%Y-%m-%d")
    return d.strftime("%y%m%d") + str(idx+1).zfill(21)

def make_acct_svcr_ref(date, idx):
    d = datetime.strptime(date, "%Y%m%d") if len(date) == 8 else datetime.strptime(date, "%Y-%m-%d")
    return d.strftime("%y%m%d") + str(idx+1).zfill(26)

def get_bic(tegenrekening):
    bank_bics = {
        "RABO": "RABONL2U",
        "ABNA": "ABNANL2A",
        "INGB": "INGBNL2A",
        "SNSB": "SNSBNL2A",
        "TRIO": "TRIONL2U",
        "KNAB": "KNABNL2H",
        "BUNQ": "BUNQNL2A",
        "ASN ": "ASNBNL21",
        "REGI": "REGNL2R1",
        "FVLN": "FVLNNL22",
        "MOYO": "MOYONL21",
        "HAND": "HANDNL2A",
        "DEUT": "DEUTNL2A",
        "FRGH": "FRGHNL2L",
        "SNSR": "SNSRNLR2",
        "TRIS": "TRISNL2A",
        "VOWA": "VOWANL21",
        "BCDM": "BCDMNL22",
        "BICK": "BICKNL2A",
        "BMEU": "BMEUNL21",
        "CITC": "CITCNL2A",
        "FINTRO": "FINTROB1",
        "NWBK": "NWBKNL2G",
        "RBRB": "RBRBNL21",
        "SNSG": "SNSGNLR2",
        "SOGE": "SOGENL2A",
        "STAL": "STALNL21",
        "VANL": "VANLNL21",
        "BIC": "BICNL2A",  # fallback
    }
    if tegenrekening.startswith("NL") and len(tegenrekening) >= 8:
        bank_code = tegenrekening[4:8]
        return bank_bics.get(bank_code, "INGBNL2A")

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

def convert_csv_to_camt053_full(input_path, output_path):
    with open(input_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        transactions = list(reader)

    blocks = defaultdict(list)
    for tx in transactions:
        blocks[tx["Datum"].strip('"')].append(tx)

    # Calculate end balance per day
    day_end_balances = {}
    for date in blocks:
        saldo = blocks[date][0]["Saldo na mutatie"].replace(",", ".")
        day_end_balances[date] = saldo
        print(f"End saldo for {date}: {saldo}")
    sorted_dates = sorted(blocks.keys())
    default_saldo = determine_default_saldo(transactions)
    print(f"Begin Saldo: {default_saldo}")
    print(f"Eind  Saldo: {day_end_balances[sorted_dates[-1]]}")

    msgid = datetime.now().strftime("%Y%m%d0000000_%Y%m%d%H%M%S000")
    with open(output_path, 'w', encoding='utf-8') as outfile:
        outfile.write(HEADER.format(msgid=msgid, created=now_iso()))
        stmt_counter = 1
        for i, block_date in enumerate(sorted_dates):
            block = blocks[block_date]
            stmt_id = datetime.now().strftime("%Y%m%d%H%M%S%f")[:17] + str(stmt_counter).zfill(7)
            stmt_counter += 1
            outfile.write(f"\t\t<Stmt>\n")
            outfile.write(f"\t\t\t<Id>{stmt_id}</Id>\n")
            outfile.write(f"\t\t\t<CreDtTm>{now_iso()}</CreDtTm>\n")
            outfile.write(f"\t\t\t<FrToDt>\n")
            outfile.write(f"\t\t\t\t<FrDtTm>{format_date(block_date)}T00:00:00</FrDtTm>\n")
            outfile.write(f"\t\t\t\t<ToDtTm>{format_date(block_date)}T23:59:59</ToDtTm>\n")
            outfile.write(f"\t\t\t</FrToDt>\n")
            outfile.write(f"\t\t\t<Acct>\n")
            outfile.write(f"\t\t\t\t<Id>\n")
            outfile.write(f"\t\t\t\t\t<IBAN>NL91INGB0004386274</IBAN>\n")
            outfile.write(f"\t\t\t\t</Id>\n")
            outfile.write(f"\t\t\t\t<Tp>\n")
            outfile.write(f"\t\t\t\t\t<Cd>CACC</Cd>\n")
            outfile.write(f"\t\t\t\t</Tp>\n")
            outfile.write(f"\t\t\t\t<Ccy>EUR</Ccy>\n")
            outfile.write(f"\t\t\t\t<Svcr>\n")
            outfile.write(f"\t\t\t\t\t<FinInstnId>\n")
            outfile.write(f"\t\t\t\t\t\t<BIC>INGBNL2A</BIC>\n")
            outfile.write(f"\t\t\t\t\t</FinInstnId>\n")
            outfile.write(f"\t\t\t\t</Svcr>\n")
            outfile.write(f"\t\t\t</Acct>\n")
            saldo_end = day_end_balances[block_date]
            if i == 0:
                saldo_open = default_saldo
            else:
                prev_date = sorted_dates[i-1]
                saldo_open = day_end_balances[prev_date]
            prev_date_str = (datetime.strptime(block_date, "%Y%m%d") - timedelta(days=1)).strftime("%Y-%m-%d")
            for code, bal_amt, bal_date in [
                ("PRCD", saldo_open, prev_date_str),
                ("OPBD", saldo_open, prev_date_str),
                ("CLBD", saldo_end, format_date(block_date)),
                ("CLAV", saldo_end, format_date(block_date)),
                ("FWAV", saldo_end, format_date(block_date)),
                ("FWAV", saldo_end, format_date(block_date)),
            ]:
                outfile.write(f"\t\t\t<Bal>\n")
                outfile.write(f"\t\t\t\t<Tp>\n")
                outfile.write(f"\t\t\t\t\t<CdOrPrtry>\n")
                outfile.write(f"\t\t\t\t\t\t<Cd>{code}</Cd>\n")
                outfile.write(f"\t\t\t\t\t</CdOrPrtry>\n")
                outfile.write(f"\t\t\t\t</Tp>\n")
                outfile.write(f"\t\t\t\t<Amt Ccy=\"EUR\">{bal_amt}</Amt>\n")
                outfile.write(f"\t\t\t\t<CdtDbtInd>CRDT</CdtDbtInd>\n")
                outfile.write(f"\t\t\t\t<Dt>\n")
                outfile.write(f"\t\t\t\t\t<Dt>{bal_date}</Dt>\n")
                outfile.write(f"\t\t\t\t</Dt>\n")
                outfile.write(f"\t\t\t</Bal>\n")
            nb_of_ntries = len(block)
            sum_ntries = sum(float(tx["Bedrag (EUR)"].replace(",", ".")) for tx in block)
            nb_of_crdt = sum(1 for tx in block if tx["Af Bij"].strip().lower() == "af")
            sum_crdt = sum(float(tx["Bedrag (EUR)"].replace(",", ".")) for tx in block if tx["Af Bij"].strip().lower() == "af")
            nb_of_dbit = sum(1 for tx in block if tx["Af Bij"].strip().lower() == "bij")
            sum_dbit = sum(float(tx["Bedrag (EUR)"].replace(",", ".")) for tx in block if tx["Af Bij"].strip().lower() == "bij")
            outfile.write(f"\t\t\t<TxsSummry>\n")
            outfile.write(f"\t\t\t\t<TtlNtries>\n")
            outfile.write(f"\t\t\t\t\t<NbOfNtries>{nb_of_ntries}</NbOfNtries>\n")
            outfile.write(f"\t\t\t\t\t<Sum>{sum_ntries:.2f}</Sum>\n")
            outfile.write(f"\t\t\t\t</TtlNtries>\n")
            outfile.write(f"\t\t\t\t<TtlCdtNtries>\n")
            outfile.write(f"\t\t\t\t\t<NbOfNtries>{nb_of_crdt}</NbOfNtries>\n")
            outfile.write(f"\t\t\t\t\t<Sum>{sum_crdt:.2f}</Sum>\n")
            outfile.write(f"\t\t\t\t</TtlCdtNtries>\n")
            outfile.write(f"\t\t\t\t<TtlDbtNtries>\n")
            outfile.write(f"\t\t\t\t\t<NbOfNtries>{nb_of_dbit}</NbOfNtries>\n")
            outfile.write(f"\t\t\t\t\t<Sum>{sum_dbit:.2f}</Sum>\n")
            outfile.write(f"\t\t\t\t</TtlDbtNtries>\n")
            outfile.write(f"\t\t\t</TxsSummry>\n")
            for idx, tx in enumerate(block):
                amount = tx["Bedrag (EUR)"].replace(",", ".")
                credit_debit = "DBIT" if tx["Af Bij"].strip().lower() == "af" else "CRDT"
                ntryref = make_ntry_ref(block_date, idx)
                acctsvcrref = make_acct_svcr_ref(block_date, idx)
                outfile.write(f"\t\t\t<Ntry>\n")
                outfile.write(f"\t\t\t\t<NtryRef>{ntryref}</NtryRef>\n")
                outfile.write(f"\t\t\t\t<Amt Ccy=\"EUR\">{amount}</Amt>\n")
                outfile.write(f"\t\t\t\t<CdtDbtInd>{credit_debit}</CdtDbtInd>\n")
                outfile.write(f"\t\t\t\t<Sts>BOOK</Sts>\n")
                outfile.write(f"\t\t\t\t<BookgDt>\n")
                outfile.write(f"\t\t\t\t\t<Dt>{format_date(tx['Datum'])}</Dt>\n")
                outfile.write(f"\t\t\t\t</BookgDt>\n")
                outfile.write(f"\t\t\t\t<ValDt>\n")
                outfile.write(f"\t\t\t\t\t<Dt>{format_date(tx['Datum'])}</Dt>\n")
                outfile.write(f"\t\t\t\t</ValDt>\n")
                outfile.write(f"\t\t\t\t<AcctSvcrRef>{acctsvcrref}</AcctSvcrRef>\n")
                outfile.write(f"\t\t\t\t<BkTxCd>\n")
                outfile.write(f"\t\t\t\t\t<Domn>\n")
                outfile.write(f"\t\t\t\t\t\t<Cd>PMNT</Cd>\n")
                outfile.write(f"\t\t\t\t\t\t<Fmly>\n")
                outfile.write(f"\t\t\t\t\t\t\t<Cd>{'RCDT' if credit_debit == 'CRDT' else 'ICDT'}</Cd>\n")
                outfile.write(f"\t\t\t\t\t\t\t<SubFmlyCd>ESCT</SubFmlyCd>\n")
                outfile.write(f"\t\t\t\t\t\t</Fmly>\n")
                outfile.write(f"\t\t\t\t\t</Domn>\n")
                outfile.write(f"\t\t\t\t\t<Prtry>\n")
                outfile.write(f"\t\t\t\t\t\t<Cd>00100</Cd>\n")
                outfile.write(f"\t\t\t\t\t\t<Issr>ING Group</Issr>\n")
                outfile.write(f"\t\t\t\t\t</Prtry>\n")
                outfile.write(f"\t\t\t\t</BkTxCd>\n")
                outfile.write(f"\t\t\t\t<NtryDtls>\n")
                outfile.write(f"\t\t\t\t\t<TxDtls>\n")
                if credit_debit == 'CRDT':
                    outfile.write(f"\t\t\t\t\t\t<RltdPties>\n")
                    outfile.write(f"\t\t\t\t\t\t\t<Dbtr>\n")
                    outfile.write(f"\t\t\t\t\t\t\t\t<Nm>{tx.get('Naam / Omschrijving','')}</Nm>\n")
                    outfile.write(f"\t\t\t\t\t\t\t</Dbtr>\n")
                    if tx.get('Tegenrekening'):
                        outfile.write(f"\t\t\t\t\t\t\t<DbtrAcct>\n")
                        outfile.write(f"\t\t\t\t\t\t\t\t<Id>\n")
                        outfile.write(f"\t\t\t\t\t\t\t\t\t<IBAN>{tx['Tegenrekening']}</IBAN>\n")
                        outfile.write(f"\t\t\t\t\t\t\t\t</Id>\n")
                        outfile.write(f"\t\t\t\t\t\t\t\t<Tp>\n")
                        outfile.write(f"\t\t\t\t\t\t\t\t\t<Prtry>General</Prtry>\n")
                        outfile.write(f"\t\t\t\t\t\t\t\t</Tp>\n")
                        outfile.write(f"\t\t\t\t\t\t\t\t<Ccy>EUR</Ccy>\n")
                        outfile.write(f"\t\t\t\t\t\t\t</DbtrAcct>\n")
                    outfile.write(f"\t\t\t\t\t\t</RltdPties>\n")
                    if tx.get('Tegenrekening'):
                        bic = get_bic(tx.get('Tegenrekening', ''))
                        if bic is not None:
                            outfile.write(f"\t\t\t\t\t\t<RltdAgts>\n")
                            outfile.write(f"\t\t\t\t\t\t\t<DbtrAgt>\n")
                            outfile.write(f"\t\t\t\t\t\t\t\t<FinInstnId>\n")
                            outfile.write(f"\t\t\t\t\t\t\t\t\t<BIC>{bic}</BIC>\n")
                            outfile.write(f"\t\t\t\t\t\t\t\t</FinInstnId>\n")
                            outfile.write(f"\t\t\t\t\t\t\t</DbtrAgt>\n")
                            outfile.write(f"\t\t\t\t\t\t</RltdAgts>\n")
                else:
                    outfile.write(f"\t\t\t\t\t\t<RltdPties>\n")
                    outfile.write(f"\t\t\t\t\t\t\t<Cdtr>\n")
                    outfile.write(f"\t\t\t\t\t\t\t\t<Nm>{tx.get('Naam / Omschrijving','')}</Nm>\n")
                    outfile.write(f"\t\t\t\t\t\t\t</Cdtr>\n")
                    if tx.get('Tegenrekening'):
                        outfile.write(f"\t\t\t\t\t\t\t<CdtrAcct>\n")
                        outfile.write(f"\t\t\t\t\t\t\t\t<Id>\n")
                        outfile.write(f"\t\t\t\t\t\t\t\t\t<IBAN>{tx['Tegenrekening']}</IBAN>\n")
                        outfile.write(f"\t\t\t\t\t\t\t\t</Id>\n")
                        outfile.write(f"\t\t\t\t\t\t\t\t<Tp>\n")
                        outfile.write(f"\t\t\t\t\t\t\t\t\t<Prtry>General</Prtry>\n")
                        outfile.write(f"\t\t\t\t\t\t\t\t</Tp>\n")
                        outfile.write(f"\t\t\t\t\t\t\t\t<Ccy>EUR</Ccy>\n")
                        outfile.write(f"\t\t\t\t\t\t\t</CdtrAcct>\n")
                    outfile.write(f"\t\t\t\t\t\t</RltdPties>\n")
                    if tx.get('Tegenrekening'):
                        bic = get_bic(tx.get('Tegenrekening', ''))
                        if bic is not None:
                            outfile.write(f"\t\t\t\t\t\t<RltdAgts>\n")
                            outfile.write(f"\t\t\t\t\t\t\t<CdtrAgt>\n")
                            outfile.write(f"\t\t\t\t\t\t\t\t<FinInstnId>\n")
                            bic = get_bic(tx.get('Tegenrekening', ''))
                            outfile.write(f"\t\t\t\t\t\t\t\t\t<BIC>{bic}</BIC>\n")
                            outfile.write(f"\t\t\t\t\t\t\t\t</FinInstnId>\n")
                            outfile.write(f"\t\t\t\t\t\t\t</CdtrAgt>\n")
                            outfile.write(f"\t\t\t\t\t\t</RltdAgts>\n")

                outfile.write(f"\t\t\t\t\t\t<RmtInf>\n")
                outfile.write(f"\t\t\t\t\t\t\t<Ustrd>{tx['Mededelingen'][:140]}</Ustrd>\n")
                outfile.write(f"\t\t\t\t\t\t</RmtInf>\n")
                outfile.write(f"\t\t\t\t\t</TxDtls>\n")
                outfile.write(f"\t\t\t\t</NtryDtls>\n")
                outfile.write(f"\t\t\t\t<AddtlNtryInf>{tx['Mededelingen']}</AddtlNtryInf>\n")
                outfile.write(f"\t\t\t</Ntry>\n")
            outfile.write(f"\t\t</Stmt>\n")
        outfile.write(FOOTER)

if __name__ == "__main__":
    convert_csv_to_camt053_full(INPUT_FILE, OUTPUT_FILE)
