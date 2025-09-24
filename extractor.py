import pandas as pd
import re

# ----------------------------
# Header Normalization
# ----------------------------
def normalize_headers(headers):
    header_map = {
        "invoice no": "Invoice No", "inv no": "Invoice No",
        "invoice number": "Invoice No", "bill no": "Invoice No",

        "supplier gstin": "Supplier GSTIN", "seller gstin": "Supplier GSTIN",
        "our gstin": "Supplier GSTIN",

        "customer gstin": "Customer GSTIN", "buyer gstin": "Customer GSTIN",
        "recipient gstin": "Customer GSTIN",

        "hsn code": "HSN", "hsn": "HSN",

        "item": "Item Name", "description": "Item Name",
        "product": "Item Name", "item name": "Item Name",

        "qty": "Quantity", "quantity": "Quantity", "qnty": "Quantity",

        "rate": "Rate", "price": "Rate", "unit price": "Rate",

        "amount": "Gross Amount", "gross": "Gross Amount",
        "gross amount": "Gross Amount", "taxable value": "Gross Amount",

        "discount": "Discount(%)", "discount%": "Discount(%)",
        "disc%": "Discount(%)", "disc amount": "Discount Amount",
        "discount amount": "Discount Amount",

        "igst": "IGST(%)", "igst%": "IGST(%)", "igst amount": "IGST Amount",
        "cgst": "CGST(%)", "cgst%": "CGST(%)", "cgst amount": "CGST Amount",
        "sgst": "SGST(%)", "sgst%": "SGST(%)", "sgst amount": "SGST Amount",

        "net amount": "Net Amount", "total": "Net Amount",
        "invoice total": "Net Amount", "grand total": "Net Amount",
        "total amount": "Net Amount",
    }
    normalized = []
    for h in headers:
        if not h:
            normalized.append("Unknown")
            continue
        h_clean = h.lower().strip().replace(":", "")
        normalized.append(header_map.get(h_clean, h.strip()))
    return normalized

# ----------------------------
# Data Cleaning
# ----------------------------
def clean_number(value):
    if pd.isna(value): 
        return None
    if isinstance(value, str):
        value = re.sub(r"[^\d.\-]", "", value)
    try:
        return float(value) if value != "" else None
    except:
        return None

# ----------------------------
# Auto-calculation
# ----------------------------
def calculate_missing_fields(row):
    gross = row.get("Gross Amount")

    # ✅ Discount calculation
    if gross:
        if row.get("Discount(%)") and not row.get("Discount Amount"):
            row["Discount Amount"] = gross * row["Discount(%)"] / 100
        elif row.get("Discount Amount") and not row.get("Discount(%)"):
            row["Discount(%)"] = (row["Discount Amount"] / gross) * 100

    # ✅ GST calculation
    for tax in ["IGST", "CGST", "SGST"]:
        perc_col = f"{tax}(%)"
        amt_col = f"{tax} Amount"

        if gross:
            if row.get(perc_col) and not row.get(amt_col):
                row[amt_col] = gross * row[perc_col] / 100
            # ❌ Do not calculate % if only amount is given → leave % blank

    # ✅ Net Amount calculation
    if gross:
        calc_net = gross - (row.get("Discount Amount") or 0) \
                   + (row.get("IGST Amount") or 0) \
                   + (row.get("CGST Amount") or 0) \
                   + (row.get("SGST Amount") or 0)
        if not row.get("Net Amount"):
            row["Net Amount"] = calc_net
    return row

# ----------------------------
# GSTIN Extraction
# ----------------------------
def extract_gstins(text):
    gstins = re.findall(r"\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[0-9A-Z]{1}Z[0-9A-Z]{1}\b", text)
    supplier_gstin, customer_gstin = "Unknown", "Unknown"
    if len(gstins) == 1: 
        supplier_gstin = gstins[0]
    elif len(gstins) >= 2: 
        supplier_gstin, customer_gstin = gstins[0], gstins[1]
    return supplier_gstin, customer_gstin

# ----------------------------
# HSN Extraction
# ----------------------------
def extract_hsn(value):
    """Extract only numeric HSN (4–8 digits)."""
    if not isinstance(value, str):
        return None
    match = re.search(r"\b\d{4,8}\b", value)
    return match.group(0) if match else None

# ----------------------------
# Main Parse
# ----------------------------
def parse_invoice(pdf, text, filename):
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
        df = pd.DataFrame(columns=[
            "HSN", "Item Name", "Quantity", "Rate", "Gross Amount",
            "Discount(%)", "Discount Amount",
            "IGST(%)", "IGST Amount",
            "CGST(%)", "CGST Amount",
            "SGST(%)", "SGST Amount",
            "Net Amount"
        ])

    # Clean numerics
    numeric_cols = [
        "Quantity", "Rate", "Gross Amount",
        "Discount(%)", "Discount Amount",
        "IGST(%)", "IGST Amount",
        "CGST(%)", "CGST Amount",
        "SGST(%)", "SGST Amount",
        "Net Amount"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].apply(clean_number)

    # ✅ Extract only valid HSN codes
    if "HSN" in df.columns:
        df["HSN"] = df["HSN"].apply(extract_hsn)
    else:
        df["HSN"] = None

    # Recalculate dependent fields
    df = df.apply(calculate_missing_fields, axis=1)

    # Invoice No
    invoice_no = re.findall(r"Invoice\s*No[:\-]?\s*([A-Za-z0-9\-\/]+)", text, re.IGNORECASE)
    invoice_no = invoice_no[0] if invoice_no else "Unknown"

    # GSTINs
    supplier_gstin, customer_gstin = extract_gstins(text)

    # Attach meta
    df["Invoice No"] = invoice_no
    df["Supplier GSTIN"] = supplier_gstin
    df["Customer GSTIN"] = customer_gstin
    df["Source File"] = filename

    return df
