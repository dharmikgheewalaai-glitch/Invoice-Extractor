import pandas as pd
import re

EXPECTED_COLUMNS = [
    "Invoice No",
    "Supplier GSTIN",
    "Customer GSTIN",
    "Source File",
    "HSN",
    "Item Name",
    "Quantity",
    "Rate",
    "Gross Amount",
    "Discount(%)",
    "Discount Amount",
    "IGST(%)",
    "IGST Amount",
    "CGST(%)",
    "CGST Amount",
    "SGST(%)",
    "SGST Amount",
    "Net Amount",
]

def normalize_headers(headers):
    """Map detected headers to exact expected names"""
    header_map = {
        "hsn": "HSN",
        "hsn code": "HSN",
        "item": "Item Name",
        "description": "Item Name",
        "product": "Item Name",
        "qty": "Quantity",
        "quantity": "Quantity",
        "rate": "Rate",
        "price": "Rate",
        "gross": "Gross Amount",
        "amount": "Gross Amount",
        "total": "Net Amount",
        "net amount": "Net Amount",
        "discount": "Discount%",
        "discount %": "Discount%",
        "igst": "IGST%",
        "igst amount": "IGST Amount",
        "cgst": "CGST%",
        "cgst amount": "CGST Amount",
        "sgst": "SGST%",
        "sgst amount": "SGST Amount",
    }
    return [header_map.get(h.lower().strip(), h.strip()) for h in headers]

def clean_numeric(value):
    """Remove unwanted symbols from numbers (₹, %, commas, etc.)"""
    if isinstance(value, str):
        value = re.sub(r"[^\d.\-]", "", value)  # keep only numbers, dot, minus
    return value

def parse_invoice(pdf, text, filename):
    """Extracts invoice table data and adds Invoice No, GSTIN, and Source File"""
    all_tables = []

    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            if table and len(table) > 1:
                df = pd.DataFrame(table[1:], columns=normalize_headers(table[0]))
                all_tables.append(df)

    if all_tables:
        df = pd.concat(all_tables, ignore_index=True)
    else:
        df = pd.DataFrame(columns=EXPECTED_COLUMNS)

    # Clean numeric values
    for col in df.columns:
        if any(key in col.lower() for key in ["amount", "rate", "qty", "igst", "cgst", "sgst", "discount", "net"]):
            df[col] = df[col].apply(clean_numeric)

    # Extract Invoice No
    invoice_no = re.findall(r"Invoice\s*No[:\-]?\s*([A-Za-z0-9\-\/]+)", text, re.IGNORECASE)
    invoice_no = invoice_no[0] if invoice_no else "Unknown"

    # Extract Supplier & Customer GSTIN
    gstins = re.findall(r"\b\d{2}[A-Z]{5}\d{4}[A-Z][0-9A-Z]Z[0-9A-Z]\b", text)
    supplier_gstin = gstins[0] if len(gstins) > 0 else "Unknown"
    customer_gstin = gstins[1] if len(gstins) > 1 else "Unknown"

    # Add Info columns
    df["Invoice No"] = invoice_no
    df["Supplier GSTIN"] = supplier_gstin
    df["Customer GSTIN"] = customer_gstin
    df["Source File"] = filename

    # Ensure all expected columns exist
    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    # Reorder columns
    df = df[EXPECTED_COLUMNS]

    return df
