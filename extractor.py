import pandas as pd
import re

def normalize_headers(headers):
    """Map invoice headers to standard names"""
    header_map = {
        "hsn code": "HSN",
        "hsn": "HSN",
        "item": "Item Name",
        "description": "Item Name",
        "product": "Item Name",
        "qty": "Quantity",
        "quantity": "Quantity",
        "rate": "Rate",
        "price": "Rate",
        "amount": "Gross Amount",
        "gross": "Gross Amount",
        "discount": "Discount(%)",
        "igst": "IGST(%)",
        "igst amount": "IGST Amount",
        "cgst": "CGST(%)",
        "cgst amount": "CGST Amount",
        "sgst": "SGST(%)",
        "sgst amount": "SGST Amount",
        "net amount": "Net Amount",
        "total": "Net Amount",
    }
    return [header_map.get(h.lower().strip(), h) for h in headers]

def parse_invoice(pdf, text, filename):
    """
    Extracts invoice data:
    - Reads tables with pdfplumber
    - Normalizes headers
    - Adds Invoice No, GSTIN, and Source File columns
    """
    all_tables = []

    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            if table and len(table) > 1:
                df = pd.DataFrame(table[1:], columns=normalize_headers(table[0]))
                all_tables.append(df)

    # Combine all detected tables
    if all_tables:
        df = pd.concat(all_tables, ignore_index=True)
    else:
        df = pd.DataFrame(columns=[
            "HSN", "Item Name", "Quantity", "Rate", "Gross Amount",
            "Discount(%)", "Discount Amount",
            "IGST(%)", "IGST Amount",
            "CGST(%)", "CGST Amount",
            "SGST(%)", "SGST Amount",
            "Net Amount"
        ])

    # Extract Invoice No & GSTIN
    invoice_no = re.findall(r"Invoice\s*No[:\-]?\s*([A-Za-z0-9\-\/]+)", text, re.IGNORECASE)
    invoice_no = invoice_no[0] if invoice_no else "Unknown"

    gstin = re.findall(r"\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[0-9A-Z]{1}Z[0-9A-Z]{1}\b", text)
    gstin = gstin[0] if gstin else "Unknown"

    # Add Invoice Info to every row
    df["Invoice No"] = invoice_no
    df["GSTIN"] = gstin
    df["Source File"] = filename

    return df
