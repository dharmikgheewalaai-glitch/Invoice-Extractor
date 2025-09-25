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

# -------- Header Normalization Map --------
HEADER_MAP = {
    "invoice no": "Invoice No", "invoice #": "Invoice No", "inv. no.": "Invoice No",
    "bill no": "Invoice No", "voucher no": "Invoice No", "document no": "Invoice No",

    "supplier gstin": "Supplier GSTIN", "seller gstin": "Supplier GSTIN", "vendor gstin": "Supplier GSTIN",
    "supplier gst no": "Supplier GSTIN", "seller tax id": "Supplier GSTIN", "vendor tax id": "Supplier GSTIN",

    "customer gstin": "Customer GSTIN", "buyer gstin": "Customer GSTIN", "client gstin": "Customer GSTIN",
    "recipient gstin": "Customer GSTIN", "customer gst no": "Customer GSTIN", "buyer tax id": "Customer GSTIN",

    "source file": "Source File", "upload name": "Source File", "source document": "Source File",
    "file reference": "Source File", "document source": "Source File", "file path": "Source File",

    "hsn": "HSN", "hsn code": "HSN", "hsn/sac": "HSN", "hsn code no": "HSN", "hsn classification": "HSN",
    "hsn/sac code": "HSN", "harmonized code": "HSN",

    "item": "Item Name", "item name": "Item Name", "description": "Item Name", "product": "Item Name",
    "product name": "Item Name", "service name": "Item Name", "goods/service description": "Item Name",
    "material name": "Item Name", "particulars": "Item Name", "item description": "Item Name",
    "product details": "Item Name",

    "qty": "Quantity", "quantity": "Quantity", "no. of units": "Quantity", "nos.": "Quantity",
    "packets": "Quantity", "pcs": "Quantity", "units": "Quantity", "order quantity": "Quantity",

    "rate": "Rate", "price": "Rate", "unit cost": "Rate", "unit price": "Rate",
    "per unit rate": "Rate", "selling price": "Rate", "unit value": "Rate", "rate per item": "Rate",

    "gross amount": "Gross Amount", "total value": "Gross Amount", "total before tax": "Gross Amount",
    "amount before tax": "Gross Amount", "subtotal": "Gross Amount", "line total": "Gross Amount",

    "discount%": "Discount%", "discount": "Discount%", "disc%": "Discount%", "rebate %": "Discount%",
    "offer %": "Discount%", "deduction %": "Discount%", "allowance %": "Discount%",

    "discount amount": "Discount Amount", "disc amt": "Discount Amount", "rebate amount": "Discount Amount",
    "deduction value": "Discount Amount", "offer amount": "Discount Amount", "concession": "Discount Amount",
    "discounted amount": "Discount Amount", "total discount": "Discount Amount",

    "igst%": "IGST%", "igst rate %": "IGST%", "integrated tax %": "IGST%", "igst duty %": "IGST%", "int. gst %": "IGST%",

    "igst amount": "IGST Amount", "igst value": "IGST Amount", "integrated tax amount": "IGST Amount",
    "igst duty amount": "IGST Amount", "igst charges": "IGST Amount", "igst total": "IGST Amount", "igst": "IGST Amount",

    "cgst%": "CGST%", "cgst rate %": "CGST%", "central tax %": "CGST%", "c. gst %": "CGST%", "central gst rate": "CGST%",

    "cgst amount": "CGST Amount", "cgst value": "CGST Amount", "central tax amount": "CGST Amount",
    "cgst charges": "CGST Amount", "cgst duty amount": "CGST Amount", "cgst total": "CGST Amount", "cgst": "CGST Amount",

    "sgst%": "SGST%", "sgst rate %": "SGST%", "state tax %": "SGST%", "s. gst %": "SGST%", "state gst rate": "SGST%",

    "sgst amount": "SGST Amount", "sgst value": "SGST Amount", "state tax amount": "SGST Amount",
    "sgst charges": "SGST Amount", "sgst duty amount": "SGST Amount", "sgst total": "SGST Amount", "sgst": "SGST Amount",

    "net amount": "Net Amount", "grand total": "Net Amount", "invoice total": "Net Amount",
    "total payable": "Net Amount", "amount due": "Net Amount", "final total": "Net Amount",
}

def normalize_headers(headers):
    return [HEADER_MAP.get(h.lower().strip(), h.strip()) for h in headers]

# -------- Helpers --------
def clean_text(text):
    return re.sub(r"\s+", " ", text.strip()) if text else ""

def safe_float(value):
    try:
        if value is None or str(value).strip() == "":
            return 0.0
        return float(str(value).replace(",", "").strip())
    except Exception:
        return 0.0

def parse_invoice(pdf, text, filename):
    all_tables = []
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            if table and len(table) > 1:
                df = pd.DataFrame(table[1:], columns=normalize_headers(table[0]))
                all_tables.append(df)

    df = pd.concat(all_tables, ignore_index=True) if all_tables else pd.DataFrame(columns=EXPECTED_COLUMNS)

    # clean numbers
    for col in df.columns:
        if any(key in col.lower() for key in ["amount", "rate", "qty", "igst", "cgst", "sgst", "discount", "net", "gross"]):
            df[col] = df[col].apply(safe_float)

    # invoice meta
    inv_match = re.search(r"Invoice\s*No[:\-]?\s*(\S+)", text, re.I)
    invoice_no = inv_match.group(1) if inv_match else "Unknown"
    gstins = re.findall(r"\b\d{2}[A-Z]{5}\d{4}[A-Z][0-9A-Z]Z[0-9A-Z]\b", text)
    supplier_gstin = gstins[0] if len(gstins) > 0 else "Unknown"
    customer_gstin = gstins[1] if len(gstins) > 1 else "Unknown"

    # add info cols
    df["Invoice No"] = invoice_no
    df["Supplier GSTIN"] = supplier_gstin
    df["Customer GSTIN"] = customer_gstin
    df["Source File"] = filename

    # ensure all cols exist
    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            df[col] = "" if col in ["Invoice No", "Supplier GSTIN", "Customer GSTIN", "Source File", "HSN", "Item Name"] else 0.0

    # ---------- Auto calculations ----------
    # Gross
    df["Gross Amount"] = df.apply(
        lambda x: safe_float(x["Gross Amount"]) if safe_float(x["Gross Amount"]) > 0
        else safe_float(x["Quantity"]) * safe_float(x["Rate"]),
        axis=1)

    # Discount Amount
    df["Discount Amount"] = df.apply(
        lambda x: safe_float(x["Discount Amount"]) if safe_float(x["Discount Amount"]) > 0
        else safe_float(x["Gross Amount"]) * safe_float(x["Discount%"]) / 100,
        axis=1)

    # Discount %
    df["Discount%"] = df.apply(
        lambda x: safe_float(x["Discount%"]) if safe_float(x["Discount%"]) > 0
        else (safe_float(x["Discount Amount"]) / safe_float(x["Gross Amount"]) * 100 if safe_float(x["Gross Amount"]) > 0 else 0),
        axis=1)

    # IGST
    df["IGST Amount"] = df.apply(
        lambda x: safe_float(x["IGST Amount"]) if safe_float(x["IGST Amount"]) > 0
        else (safe_float(x["Gross Amount"]) - safe_float(x["Discount Amount"])) * safe_float(x["IGST%"]) / 100,
        axis=1)
    df["IGST%"] = df.apply(
        lambda x: safe_float(x["IGST%"]) if safe_float(x["IGST%"]) > 0
        else (safe_float(x["IGST Amount"]) / max((safe_float(x["Gross Amount"]) - safe_float(x["Discount Amount"])), 1) * 100 if safe_float(x["IGST Amount"]) > 0 else 0),
        axis=1)

    # CGST
    df["CGST Amount"] = df.apply(
        lambda x: safe_float(x["CGST Amount"]) if safe_float(x["CGST Amount"]) > 0
        else (safe_float(x["Gross Amount"]) - safe_float(x["Discount Amount"])) * safe_float(x["CGST%"]) / 100,
        axis=1)
    df["CGST%"] = df.apply(
        lambda x: safe_float(x["CGST%"]) if safe_float(x["CGST%"]) > 0
        else (safe_float(x["CGST Amount"]) / max((safe_float(x["Gross Amount"]) - safe_float(x["Discount Amount"])), 1) * 100 if safe_float(x["CGST Amount"]) > 0 else 0),
        axis=1)

    # SGST
    df["SGST Amount"] = df.apply(
        lambda x: safe_float(x["SGST Amount"]) if safe_float(x["SGST Amount"]) > 0
        else (safe_float(x["Gross Amount"]) - safe_float(x["Discount Amount"])) * safe_float(x["SGST%"]) / 100,
        axis=1)
    df["SGST%"] = df.apply(
        lambda x: safe_float(x["SGST%"]) if safe_float(x["SGST%"]) > 0
        else (safe_float(x["SGST Amount"]) / max((safe_float(x["Gross Amount"]) - safe_float(x["Discount Amount"])), 1) * 100 if safe_float(x["SGST Amount"]) > 0 else 0),
        axis=1)

    # Net
    df["Net Amount"] = df.apply(
        lambda x: safe_float(x["Net Amount"]) if safe_float(x["Net Amount"]) > 0
        else safe_float(x["Gross Amount"]) - safe_float(x["Discount Amount"]) +
             safe_float(x["IGST Amount"]) + safe_float(x["CGST Amount"]) + safe_float(x["SGST Amount"]),
        axis=1)

    return df[EXPECTED_COLUMNS]
