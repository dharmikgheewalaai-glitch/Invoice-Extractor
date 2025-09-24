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
    if pd.isna(value): return None
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
    if gross:
        # Discount
        if row.get("Discount(%)") and not row.get("Discount Amount"):
            row["Discount Amount"] = gross * row["Discount(%)"] / 100
        elif row.get("Discount Amount") and not row.get("Discount(%)"):
            row["Discount(%)"] = (row["Discount Amount"] / gross) * 100

        # IGST
        if row.get("IGST(%)") and not row.get("IGST Amount"):
            row["IGST Amount"] = gross * row["IGST(%)"] / 100
        elif row.get("IGST Amount") and not row.get("IGST(%)"):
            if row["IGST Amount"] <= gross:
                row["IGST(%)"] = (row["IGST Amount"] / gross) * 100

        # CGST
        if row.get("CGST(%)") and not row.get("CGST Amount"):
            row["CGST Amount"] = gross * row["CGST(%)"] / 100
        elif row.get("CGST Amount") and not row.get("CGST(%)"):
            if row["CGST Amount"] <= gross:
                row["CGST(%)"] = (row["CGST Amount"] / gross) * 100

        # SGST
        if row.get("SGST(%)") and not row.get("SGST Amount"):
            row["SGST Amount"] = gross * row["SGST(%)"] / 100
        elif row.get("SGST Amount") and not row.get("SGST(%)"):
            if row["SGST Amount"] <= gross:
                row["SGST(%)"] = (row["SGST Amount"] / gross) * 100

        # Net
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
    if len(gstins) == 1: supplier_gstin = gstins[0]
    elif len(gstins) >= 2: supplier_gstin, customer_gstin = gstins[0], gstins[1]
    return supplier_gstin, customer_gstin

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

    df = df.apply(calculate_missing_fields, axis=1)

    invoice_no = re.findall(r"Invoice\s*No[:\-]?\s*([A-Za-z0-9\-\/]+)", text, re.IGNORECASE)
    invoice_no = invoice_no[0] if invoice_no else "Unknown"

    supplier_gstin, customer_gstin = extract_gstins(text)

    df["Invoice No"] = invoice_no
    df["Supplier GSTIN"] = supplier_gstin
    df["Customer GSTIN"] = customer_gstin
    df["Source File"] = filename

    return df
