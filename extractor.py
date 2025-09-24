import pandas as pd
import re

def parse_invoice(text: str):
    """
    Parse invoice text and return:
    - df: pandas DataFrame with line item details
    - meta: dict with Invoice Number & Totals
    """

    # Extract Invoice Number
    invoice_no = re.findall(r"Invoice\s*No[:\-]?\s*(\w+)", text, re.IGNORECASE)
    invoice_no = invoice_no[0] if invoice_no else "Not Found"

    # ⚠️ Replace this with real parsing logic using pdfplumber.extract_table
    data = {
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

    meta = {
        "Invoice No": invoice_no,
        "Total Net Amount": df["Net Amount"].sum()
    }

    return df, meta
