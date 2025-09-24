import pandas as pd
import re

def parse_invoice(text: str):
    """
    Parse invoice text and return DataFrame with invoice line items.
    Includes Invoice No and GSTIN as columns.
    """

    # Extract Invoice Number
    invoice_no = re.findall(r"Invoice\s*No[:\-]?\s*([A-Za-z0-9\-\/]+)", text, re.IGNORECASE)
    invoice_no = invoice_no[0] if invoice_no else "Unknown"

    # Extract GSTIN (15 characters: 2 digits + 10 PAN chars + 1 entity + 1Z + 1 check digit)
    gstin = re.findall(r"\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b", text)
    gstin = gstin[0] if gstin else "Unknown"

    # ⚠️ Replace with real parsing logic using pdfplumber.extract_table
    data = {
        "Invoice No": [invoice_no, invoice_no],
        "GSTIN": [gstin, gstin],
        "HSN": ["1234", "5678"],
        "Item Name": ["Product A", "Product B"],
        "Quantity": [2, 5],
        "Rate": [100, 200],
        "Gross Amount": [200, 1000],
        "Discount(%)": [5, 10],
        "Discount Amount": [10, 100],
        "IGST(%)": [18, 18],
        "IGST Amount": [34.2, 162],
        "CGST(%)": [9, 9],
        "CGST Amount": [17.1, 81],
        "SGST(%)": [9, 9],
        "SGST Amount": [17.1, 81],
        "Net Amount": [224.2, 962],
    }

    df = pd.DataFrame(data)
    return df
