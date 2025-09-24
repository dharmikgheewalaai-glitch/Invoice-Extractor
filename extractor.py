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
        "discount%": "Discount(%)",
        "discount amount": "Discount Amount",
        "igst": "IGST(%)",
        "igst%": "IGST(%)",
        "igst amount": "IGST Amount",
        "cgst": "CGST(%)",
        "cgst%": "CGST(%)",
        "cgst amount": "CGST Amount",
        "sgst": "SGST(%)",
        "sgst%": "SGST(%)",
        "sgst amount": "SGST Amount",
        "net amount": "Net Amount",
        "total": "Net Amount",
    }
    return [header_map.get(h.lower().strip(), h) for h in headers]

def clean_number(value):
    """Remove symbols (₹,$,%,,) and convert to float if possible"""
    if pd.isna(value):
        return None
    if isinstance(value, str):
        value = re.sub(r"[^\d.\-]", "", value)  # keep only numbers, dot, minus
    try:
        return float(value) if value != "" else None
    except:
        return None

def calculate_missing_fields(row):
    """Auto-calculate missing % or Amount fields for Discount, IGST, CGST, SGST"""
    gross = row.get("Gross Amount")
    net = row.get("Net Amount") or gross

    # --- Discount ---
    if gross:
        if row.get("Discount(%)") and not row.get("Discount Amount"):
            row["Discount Amount"] = gross * row["Discount(%)"] / 100
        elif row.get("Discount Amount") and not row.get("Discount(%)"):
            row["Discount(%)"] = (row["Discount Amount"] / gross) * 100

    # --- IGST ---
    if gross:
        if row.get("IGST(%)") and not row.get("IGST Amount"):
            row["IGST Amount"] = gross * row["IGST(%)"] / 100
        elif row.get("IGST Amount") and not row.get("IGST(%)"):
            row["IGST(%)"] = (row["IGST Amount"] / gross) * 100

    # --- CGST ---
    if gross:
        if row.get("CGST(%)") and not row.get("CGST Amount"):
            row["CGST Amount"] = gross * row["CGST(%)"] / 100
        elif row.get("CGST Amount") and not row.get("CGST(%)"):
            row["CGST(%)"] = (row["CGST Amount"] / gross) * 100

    # --- SGST ---
    if gross:
        if row.get("SGST(%)") and not row.get("SGST Amount"):
            row["SGST Amount"] = gross * row["SGST(%)"] / 100
        elif row.get("SGST Amount") and not row.get("SGST(%)"):
            row["SGST(%)"] = (row["SGST Amount"] / gross) * 100

    return row

def parse_invoice(pdf, text, filename):
    """
    Extracts invoice data:
    - Reads tables with pdfplumber
    - Normalizes headers
    - Cleans numbers (removes symbols)
    - Auto-calculates missing %/Amount fields
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

    # Clean numeric columns
    numeric_cols = [
        "Quantity", "Rate", "Gross Amount", "Discount(%)", "Discount Amount",
        "IGST(%)", "IGST Amount",
        "CGST(%)", "CGST Amount",
        "SGST(%)", "SGST Amount",
        "Net Amount"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].apply(clean_number)

    # Auto-calculate missing % or Amounts
    df = df.apply(calculate_missing_fields, axis=1)

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
