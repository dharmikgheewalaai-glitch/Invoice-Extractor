import pdfplumber
import pandas as pd
import re

EXPECTED_COLUMNS = [
    "Invoice No","Supplier GSTIN","Customer GSTIN","Source File",
    "HSN","Item Name","Quantity","Rate","Gross Amount",
    "Discount%","Discount Amount","IGST%","IGST Amount",
    "CGST%","CGST Amount","SGST%","SGST Amount","Net Amount",
]

HEADER_MAP = {
    "invoice no": "Invoice No","invoice #": "Invoice No","bill no": "Invoice No",
    "supplier gstin": "Supplier GSTIN","seller gstin": "Supplier GSTIN",
    "customer gstin": "Customer GSTIN","buyer gstin": "Customer GSTIN",
    "hsn": "HSN","hsn code": "HSN",
    "item": "Item Name","description": "Item Name",
    "qty": "Quantity","quantity": "Quantity",
    "rate": "Rate","price": "Rate",
    "gross amount": "Gross Amount","subtotal": "Gross Amount",
    "discount%": "Discount%","disc%": "Discount%",
    "discount amount": "Discount Amount","disc amt": "Discount Amount",
    "igst%": "IGST%","igst amount": "IGST Amount",
    "cgst%": "CGST%","cgst amount": "CGST Amount",
    "sgst%": "SGST%","sgst amount": "SGST Amount",
    "net amount": "Net Amount","grand total": "Net Amount",
}

def normalize_headers(headers):
    return [HEADER_MAP.get(h.lower().strip(), h.strip()) for h in headers]

def clean_numeric(value):
    if isinstance(value, str):
        value = re.sub(r"[^\d.\-]", "", value)
    try:
        return float(value) if value not in ("", None) else 0.0
    except:
        return 0.0

def ensure_columns(df):
    """Guarantee all expected columns exist"""
    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            if col in ["Invoice No","Supplier GSTIN","Customer GSTIN","Source File","HSN","Item Name"]:
                df[col] = ""
            else:
                df[col] = 0.0
    return df

def parse_invoice(pdf_path, filename):
    all_tables = []
    text_data = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text_data += page.extract_text() or ""
            tables = page.extract_tables()
            for table in tables:
                if table and len(table) > 1:
                    df = pd.DataFrame(table[1:], columns=normalize_headers(table[0]))
                    all_tables.append(df)

    # Merge tables or create empty
    if all_tables:
        df = pd.concat(all_tables, ignore_index=True)
    else:
        df = pd.DataFrame(columns=EXPECTED_COLUMNS)

    # Clean numbers
    for col in df.columns:
        if any(k in col.lower() for k in ["amount","rate","qty","igst","cgst","sgst","discount","net","gross"]):
            df[col] = df[col].apply(clean_numeric)

    # Metadata
    inv_match = re.search(r"Invoice\s*No[:\-]?\s*([A-Za-z0-9\-\/]+)", text_data, re.I)
    invoice_no = inv_match.group(1) if inv_match else "Unknown"

    gstins = re.findall(r"\b\d{2}[A-Z]{5}\d{4}[A-Z][0-9A-Z]Z[0-9A-Z]\b", text_data)
    supplier_gstin = gstins[0] if len(gstins) > 0 else "Unknown"
    customer_gstin = gstins[1] if len(gstins) > 1 else "Unknown"

    # Always ensure all columns exist before checks
    df = ensure_columns(df)

    # Fallback if still blank/zero
    if df[["Gross Amount","Net Amount"]].sum().sum() == 0:
        qty = re.search(r"Qty[:\-]?\s*(\d+)", text_data, re.I)
        rate = re.search(r"Rate[:\-]?\s*([\d,.]+)", text_data, re.I)
        gross = re.search(r"Gross\s*Amount[:\-]?\s*([\d,.]+)", text_data, re.I)
        net = re.search(r"(Net\s*Amount|Total\s*Payable)[:\-]?\s*([\d,.]+)", text_data, re.I)

        row = {
            "Invoice No": invoice_no,
            "Supplier GSTIN": supplier_gstin,
            "Customer GSTIN": customer_gstin,
            "Source File": filename,
            "HSN": "",
            "Item Name": "",
            "Quantity": clean_numeric(qty.group(1)) if qty else 0,
            "Rate": clean_numeric(rate.group(1)) if rate else 0,
            "Gross Amount": clean_numeric(gross.group(1)) if gross else 0,
            "Discount%": 0,"Discount Amount": 0,
            "IGST%": 0,"IGST Amount": 0,
            "CGST%": 0,"CGST Amount": 0,
            "SGST%": 0,"SGST Amount": 0,
            "Net Amount": clean_numeric(net.group(2)) if net else 0,
        }
        df = pd.DataFrame([row])

    # Ensure again after fallback
    df = ensure_columns(df)

    # Assign metadata
    df["Invoice No"] = invoice_no
    df["Supplier GSTIN"] = supplier_gstin
    df["Customer GSTIN"] = customer_gstin
    df["Source File"] = filename

    return df[EXPECTED_COLUMNS]
