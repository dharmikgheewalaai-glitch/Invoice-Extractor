import pandas as pd
import re

# ----------------------------
# Header Normalization
# ----------------------------
def normalize_headers(headers):
    header_map = {
        "invoice no": "Invoice No", "inv no": "Invoice No", "invoice number": "Invoice No", "bill no": "Invoice No",
        "supplier gstin": "Supplier GSTIN", "seller gstin": "Supplier GSTIN", "our gstin": "Supplier GSTIN",
        "customer gstin": "Customer GSTIN", "buyer gstin": "Customer GSTIN", "recipient gstin": "Customer GSTIN",
        "hsn code": "HSN", "hsn": "HSN",
        "item": "Item Name", "description": "Item Name", "product": "Item Name", "item name": "Item Name",
        "qty": "Quantity", "quantity": "Quantity", "qnty": "Quantity",
        "rate": "Rate", "price": "Rate", "unit price": "Rate",
        "amount": "Gross Amount", "gross": "Gross Amount", "taxable value": "Gross Amount",
        "discount": "Discount(%)", "discount%": "Discount(%)", "disc%": "Discount(%)",
        "disc amount": "Discount Amount", "discount amount": "Discount Amount",
        "igst": "IGST(%)", "igst%": "IGST(%)", "igst amount": "IGST Amount",
        "cgst": "CGST(%)", "cgst%": "CGST(%)", "cgst amount": "CGST Amount",
        "sgst": "SGST(%)", "sgst%": "SGST(%)", "sgst amount": "SGST Amount",
        "net amount": "Net Amount", "total": "Net Amount", "grand total": "Net Amount",
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
# Cleaning
# ----------------------------
def clean_number(value, is_gst_percent=False):
    if pd.isna(value):
        return None
    if isinstance(value, str):
        value = value.strip()
        if "%" in value and is_gst_percent:
            try:
                return float(re.sub(r"[^\d.\-]", "", value))
            except:
                return None
        if "%" not in value and not is_gst_percent:
            value = re.sub(r"[^\d.\-]", "", value)
            try:
                return float(value) if value != "" else None
            except:
                return None
        return None
    try:
        return float(value)
    except:
        return None

def calculate_missing_fields(row):
    gross = row.get("Gross Amount")
    if gross:
        if row.get("Discount(%)") and not row.get("Discount Amount"):
            row["Discount Amount"] = gross * row["Discount(%)"] / 100
        elif row.get("Discount Amount") and not row.get("Discount(%)"):
            row["Discount(%)"] = (row["Discount Amount"] / gross) * 100

        for tax in ["IGST", "CGST", "SGST"]:
            if row.get(f"{tax}(%)") and not row.get(f"{tax} Amount"):
                row[f"{tax} Amount"] = gross * row[f"{tax}(%)"] / 100
            elif row.get(f"{tax} Amount") and not row.get(f"{tax}(%)"):
                # Already amount → keep as is, don’t convert back
                pass

        calc_net = gross - (row.get("Discount Amount") or 0) \
                   + (row.get("IGST Amount") or 0) \
                   + (row.get("CGST Amount") or 0) \
                   + (row.get("SGST Amount") or 0)
        if not row.get("Net Amount"):
            row["Net Amount"] = calc_net
    return row

def extract_gstins(text):
    gstins = re.findall(r"\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[0-9A-Z]{1}Z[0-9A-Z]{1}\b", text)
    supplier_gstin, customer_gstin = "Unknown", "Unknown"
    if len(gstins) == 1:
        supplier_gstin = gstins[0]
    elif len(gstins) >= 2:
        supplier_gstin, customer_gstin = gstins[0], gstins[1]
    return supplier_gstin, customer_gstin

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

    for col in df.columns:
        if col in ["Quantity", "Rate", "Gross Amount", "Discount Amount",
                   "IGST Amount", "CGST Amount", "SGST Amount", "Net Amount"]:
            df[col] = df[col].apply(lambda x: clean_number(x, is_gst_percent=False))
        elif col in ["Discount(%)", "IGST(%)", "CGST(%)", "SGST(%)"]:
            df[col] = df[col].apply(lambda x: clean_number(x, is_gst_percent=True))

    df = df.apply(calculate_missing_fields, axis=1)

    invoice_no = re.findall(r"Invoice\s*No[:\-]?\s*([A-Za-z0-9\-\/]+)", text, re.IGNORECASE)
    invoice_no = invoice_no[0] if invoice_no else "Unknown"

    supplier_gstin, customer_gstin = extract_gstins(text)

    df["Invoice No"] = invoice_no
    df["Supplier GSTIN"] = supplier_gstin
    df["Customer GSTIN"] = customer_gstin
    df["Source File"] = filename

    fixed_columns = [
        "Invoice No", "Supplier GSTIN", "Customer GSTIN", "Source File", "HSN", "Item Name",
        "Quantity", "Rate", "Gross Amount", "Discount(%)", "Discount Amount",
        "IGST(%)", "IGST Amount", "CGST(%)", "CGST Amount", "SGST(%)", "SGST Amount", "Net Amount"
    ]
    for col in fixed_columns:
        if col not in df.columns:
            df[col] = None
    return df[fixed_columns]
