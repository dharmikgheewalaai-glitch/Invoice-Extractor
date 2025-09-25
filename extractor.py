import pdfplumber
import pandas as pd
import re

# -------- Expected Columns --------
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
    "Discount%",
    "Discount Amount",
    "IGST%",
    "IGST Amount",
    "CGST%",
    "CGST Amount",
    "SGST%",
    "SGST Amount",
    "Net Amount",
]

# -------- Header Map --------
HEADER_MAP = {
    "invoice no": "Invoice No", "invoice #": "Invoice No", "inv. no.": "Invoice No",
    "bill no": "Invoice No", "voucher no": "Invoice No", "document no": "Invoice No",

    "supplier gstin": "Supplier GSTIN", "seller gstin": "Supplier GSTIN",
    "vendor gstin": "Supplier GSTIN", "supplier gst no": "Supplier GSTIN",

    "customer gstin": "Customer GSTIN", "buyer gstin": "Customer GSTIN",
    "recipient gstin": "Customer GSTIN", "client gstin": "Customer GSTIN",

    "hsn": "HSN", "hsn code": "HSN", "hsn/sac": "HSN",

    "item": "Item Name", "item name": "Item Name", "description": "Item Name",
    "product": "Item Name", "product name": "Item Name", "particulars": "Item Name",

    "qty": "Quantity", "quantity": "Quantity", "no. of units": "Quantity", "pcs": "Quantity",

    "rate": "Rate", "price": "Rate", "unit cost": "Rate", "unit price": "Rate",

    "gross amount": "Gross Amount", "total value": "Gross Amount", "subtotal": "Gross Amount",

    "discount%": "Discount%", "discount": "Discount%", "disc%": "Discount%",

    "discount amount": "Discount Amount", "disc amt": "Discount Amount",

    "igst%": "IGST%", "igst rate %": "IGST%", "integrated tax %": "IGST%",
    "igst amount": "IGST Amount", "igst value": "IGST Amount",

    "cgst%": "CGST%", "cgst rate %": "CGST%", "central tax %": "CGST%",
    "cgst amount": "CGST Amount", "cgst value": "CGST Amount",

    "sgst%": "SGST%", "sgst rate %": "SGST%", "state tax %": "SGST%",
    "sgst amount": "SGST Amount", "sgst value": "SGST Amount",

    "net amount": "Net Amount", "grand total": "Net Amount", "invoice total": "Net Amount",
}

def normalize_headers(headers):
    return [HEADER_MAP.get(str(h).lower().strip(), str(h).strip()) for h in headers]

# -------- Helpers --------
def safe_float(value):
    try:
        return float(str(value).replace(",", "").strip())
    except Exception:
        return 0.0

# -------- Main Parser --------
def parse_invoice(pdf_path, text, filename):
    all_tables = []
    with pdfplumber.open(pdf_path) as pdf_file:
        for page in pdf_file.pages:
            tables = page.extract_tables()
            for table in tables:
                if table and len(table) > 1:
                    df = pd.DataFrame(table[1:], columns=normalize_headers(table[0]))
                    all_tables.append(df)

    if all_tables:
        df = pd.concat(all_tables, ignore_index=True)
    else:
        df = pd.DataFrame(columns=EXPECTED_COLUMNS)

    # Convert number-like cols
    for col in df.columns:
        if any(key in col.lower() for key in ["amount", "rate", "qty", "igst", "cgst", "sgst", "discount", "net", "gross"]):
            df[col] = df[col].apply(safe_float)

    # Meta info
    inv_match = re.search(r"Invoice\s*No[:\-]?\s*(\S+)", text, re.I)
    invoice_no = inv_match.group(1) if inv_match else "Unknown"
    gstins = re.findall(r"\b\d{2}[A-Z]{5}\d{4}[A-Z][0-9A-Z]Z[0-9A-Z]\b", text)
    supplier_gstin = gstins[0] if len(gstins) > 0 else "Unknown"
    customer_gstin = gstins[1] if len(gstins) > 1 else "Unknown"

    # Ensure all cols exist
    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            df[col] = 0.0 if col not in ["Invoice No","Supplier GSTIN","Customer GSTIN","Source File","HSN","Item Name"] else ""

    df["Invoice No"] = invoice_no
    df["Supplier GSTIN"] = supplier_gstin
    df["Customer GSTIN"] = customer_gstin
    df["Source File"] = filename

    # ---------- Auto-calculations (only if missing) ----------
    df["Gross Amount"] = df.apply(
        lambda x: safe_float(x["Quantity"]) * safe_float(x["Rate"])
        if safe_float(x["Gross Amount"]) == 0 else safe_float(x["Gross Amount"]),
        axis=1
    )

    df["Discount Amount"] = df.apply(
        lambda x: safe_float(x["Gross Amount"]) * safe_float(x["Discount%"]) / 100
        if safe_float(x["Discount Amount"]) == 0 and safe_float(x["Discount%"]) != 0 else safe_float(x["Discount Amount"]),
        axis=1
    )
    df["Discount%"] = df.apply(
        lambda x: (safe_float(x["Discount Amount"]) / safe_float(x["Gross Amount"]) * 100)
        if safe_float(x["Discount%"]) == 0 and safe_float(x["Gross Amount"]) != 0 else safe_float(x["Discount%"]),
        axis=1
    )

    for tax, amt in [("IGST%", "IGST Amount"), ("CGST%", "CGST Amount"), ("SGST%", "SGST Amount")]:
        df[amt] = df.apply(
            lambda x: (safe_float(x["Gross Amount"]) - safe_float(x["Discount Amount"])) * safe_float(x[tax]) / 100
            if safe_float(x[amt]) == 0 and safe_float(x[tax]) != 0 else safe_float(x[amt]),
            axis=1
        )
        df[tax] = df.apply(
            lambda x: (safe_float(x[amt]) / max((safe_float(x["Gross Amount"]) - safe_float(x["Discount Amount"])), 1) * 100)
            if safe_float(x[tax]) == 0 and safe_float(x[amt]) != 0 else safe_float(x[tax]),
            axis=1
        )

    df["Net Amount"] = df.apply(
        lambda x: safe_float(x["Gross Amount"]) - safe_float(x["Discount Amount"]) +
                  safe_float(x["IGST Amount"]) + safe_float(x["CGST Amount"]) + safe_float(x["SGST Amount"])
        if safe_float(x["Net Amount"]) == 0 else safe_float(x["Net Amount"]),
        axis=1
    )

    return df[EXPECTED_COLUMNS]
