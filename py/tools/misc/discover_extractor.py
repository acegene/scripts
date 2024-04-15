#!/usr/bin/env python3
#
# python3 -m pip install pypdf

import glob
import re

from pypdf import PdfReader

month_to_int = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}


def force_to_float(s):
    str_reduced = s.replace("$", "").replace(",", "")
    return float(str_reduced)


def get_pdf_year(pdf):
    pattern_year = r"[^\d]*\d\d(\d\d).*"
    match = re.match(pattern_year, pdf)
    assert match
    return match[1]


def get_pdf_date(pdf):
    pattern_year = r"[^\d]*\d\d(\d\d\d\d\d\d).*"
    match = re.match(pattern_year, pdf)
    assert match
    return match[1]


def get_trans_list_from_pdf(pdf):
    # TODO: negative
    pattern_trans = r"(\d{2}/\d{2})([^/].*?)(-?\$[\d.,]+\.\d\d)"
    reader = PdfReader(pdf)
    transactions = []
    for page in reader.pages:
        text = page.extract_text()
        matches = re.findall(pattern_trans, text, re.MULTILINE)
        for match in matches:
            t = (
                f"{get_pdf_year(pdf)}/{match[0]}",
                f"{get_pdf_year(pdf)}/{match[0]}",
                match[1],
                force_to_float(match[2]),
            )
            transactions.append(t)
    return transactions


def get_trans_list_from_pdf2(pdf):
    pattern = r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d+) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d+) (.*?)(-?[\d,]+\.\d\d)$"  # pylint: disable=[line-too-long]
    reader = PdfReader(pdf)
    transactions = []
    for page in reader.pages:
        text = page.extract_text()
        for line in text.split("\n"):
            match = re.match(pattern, line)
            if match:
                t = (
                    f"{get_pdf_year(pdf)}/{month_to_int[match[1]]}/{match[2]}",
                    f"{get_pdf_year(pdf)}/{month_to_int[match[3]]}/{match[4]}",
                    match[5],
                    force_to_float(match[6]),
                )
                transactions.append((t))
    return transactions


def get_transactions_text_from_pdf(pdf):
    pattern_beg = r"Cashback Bonus [+-]\$([\d.,]+\.\d\d)(.*)"
    pattern_end = r"(.*?)PREVIOUS BALANCE \$([\d,]+\.\d\d)"

    transactions_texts = []
    trasactions_found = False
    reader = PdfReader(pdf)
    for page in reader.pages:
        text = page.extract_text()
        if "Transactions" in text:
            assert trasactions_found is False
            trasactions_found = True
            matches_beg = re.findall(pattern_beg, text, re.MULTILINE | re.DOTALL)
            if len(matches_beg) == 1:
                for match_beg in matches_beg:
                    matches_end = re.findall(pattern_end, match_beg[1], re.MULTILINE | re.DOTALL)
                    assert len(matches_end) == 1
                    transactions_texts.append(matches_end[0][0])
            else:
                print(f"ERROR: matches = {len(matches_beg)}")
                return []

    assert len(transactions_texts) == 1
    return transactions_texts[0]


def split_trasactions_text_to_list(transactions_text):
    pattern_transaction = r"^\d{2}/\d{2}"

    transactions = []
    for line in transactions_text.split("\n"):
        line_transaction_start = re.match(pattern_transaction, line)
        if line_transaction_start:
            transactions.append(line)
        else:
            transactions[-1] += "\n" + line

    return transactions


def main():
    transaction_pdfs = glob.glob("Discover*.pdf")
    transactions_dict = {}
    for pdf in transaction_pdfs:
        print(f"################## {pdf}")
        transactions = get_trans_list_from_pdf2(pdf)
        if len(transactions) == 0:
            transactions = get_trans_list_from_pdf(pdf)
            if len(transactions) == 0:
                print("ERROR: NO TRANSACTIONS")
                continue
            for transaction in transactions:
                print(transaction)
        else:
            for transaction in transactions:
                print(transaction)
        date = get_pdf_date(pdf)
        assert date not in transactions_dict
        transactions_dict[date] = transactions

    terms = ["blizzard", "activision", "hearth"]

    total = 0.0
    for date, transactions in transactions_dict.items():
        print(f"################## {date} MATCHES")
        for transaction in transactions:
            for term in terms:
                if re.search(term, transaction[2], re.IGNORECASE):
                    print(transaction)
                    total += transaction[3]
                    break
    print(f"total: {total}")


if __name__ == "__main__":
    main()
