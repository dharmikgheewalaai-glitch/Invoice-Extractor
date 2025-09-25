import pdfplumber
import pandas as pd
import re

EXPECTED_COLUMNS = [
    "Invoice No", "Supplier GSTIN", "Customer GSTIN", "Source File",
    "HSN", "Item Name", "Quantity", "Rate", "Gross Amount",
    "Discount%", "Discount Amount",
    "IGST%", "IGST Amount", "CGST%", "CGST Amount", "SGST%", "SGST Amount",
    "Net Amount"
]

HEADER_MAP = {
    "invoice": "Invoice No", "inv no": "Invoice No", "bill no": "Invoice No",
    "supplier gstin": "Supplier GSTIN", "seller gstin": "Supplier GSTIN",
    "customer gstin": "Customer GSTIN", "buyer gstin": "Customer GSTIN",
    "hsn": "HSN", "description": "Item Name", "item": "Item Name", "product": "Item Name",
    "qty": "Quantity", "quantity": "Quantity",
    "rate": "Rate", "price": "Rate",
    "gross": "Gross Amount", "amount": "Gross Amount",
    "discount%": "Discount%", "disc%": "Discount%",
    "discount": "Discount Amount",
    "igst%": "IGST%", "igst": "IGST Amount",
    "cgst%": "CGST%", "cgst": "CGST Amount",
    "sgst%": "SGST%", "sgst": "SGST Amount",
    "net": "Net Amount", "total": "Net Amount", "grand total": "Net Amount"
}

def safe_float(val):
    try:
        if val is None or str(val).strip() == "":
            return 0.0
        return float(str(val).replace(",", "").strip())
    except:
        return 0.0

def map_headers(headers):
    mapped = []
    for h in headers:
        if not h:
            mapped.append("")
            continue
        h_clean = str(h).strip().lower()
        mapped.append(HEADER_MAP.get(h_clean, h.strip()))
    return mapped

def parse_from_text(text, filename):
    """Fallback extraction directly from text using regex."""
    inv_match = re.search(r"(Invoice\s*No|Inv\s*No|Bill\s*No)[:\-]?\s*([A-Za-z0-9\-\/]+)", text, re.I)
    invoice_no = inv_match.group(2) if inv_match else "Unknown"

    gstins = re.findall(r"\b\d{2}[A-Z]{5}\d{4}[A-Z][0-9A-Z]Z[0-9A-Z]\b", text)
    supplier_gstin = gstins[0] if len(gstins) > 0 else "Unknown"
    customer_gstin = gstins[1] if len(gstins) > 1 else "Unknown"

    gross_match = re.search(r"(Gross\s*Amount|Subtotal)[:\-]?\s*([\d,]+\.?\d*)", text, re.I)
    gross = safe_float(gross_match.group(2)) if gross_match else 0.0

    net_match = re.search(r"(Net\s*Amount|Grand\s*Total|Invoice\s*Total)[:\-]?\s*([\d,]+\.?\d*)", text, re.I)
    net = safe_float(net_match.group(2)) if net_match else 0.0

    return pd.DataFrame([{
        "Invoice No": invoice_no,
        "Supplier GSTIN": supplier_gstin,
        "Customer GSTIN": customer_gstin,
        "Source File": filename,
        "HSN": "",
        "Item Name": "NA",
        "Quantity": 0,
        "Rate": 0,
        "Gross Amount": gross,
        "Discount%": 0,
        "Discount Amount": 0,
        "IGST%": 0,
        "IGST Amount": 0,
        "CGST%": 0,
        "CGST Amount": 0,
        "SGST%": 0,
        "SGST Amount": 0,
        "Net Amount": net
    }], columns=EXPECTED_COLUMNS)

def parse_invoice(pdf, text, filename):
    all_tables = []

    # Step 1: Try extracting structured tables
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            if table and len(table) > 1:
                df = pd.DataFrame(table[1:], columns=map_headers(table[0]))
                all_tables.append(df)

    if all_tables:
        df = pd.concat(all_tables, ignore_index=True)
    else:
        # Step 2: Fallback: extract from text
        return parse_from_text(text, filename)

    # Step 3: Ensure all expected columns exist
    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            df[col] = "" if col in ["Invoice No","Supplier GSTIN","Customer GSTIN","Source File","HSN","Item Name"] else 0.0

    # Step 4: Clean numbers
    for col in ["Quantity","Rate","Gross Amount","Discount%","Discount Amount",
                "IGST%","IGST Amount","CGST%","CGST Amount","SGST%","SGST Amount","Net Amount"]:
        df[col] = df[col].apply(safe_float)

    # Step 5: Extract meta from text
    inv_match = re.search(r"(Invoice\s*No|Inv\s*No|Bill\s*No)[:\-]?\s*([A-Za-z0-9\-\/]+)", text, re.I)
    invoice_no = inv_match.group(2) if inv_match else "Unknown"
    gstins = re.findall(r"\b\d{2}[A-Z]{5}\d{4}[A-Z][0-9A-Z]Z[0-9A-Z]\b", text)
    supplier_gstin = gstins[0] if len(gstins) > 0 else "Unknown"
    customer_gstin = gstins[1] if len(gstins) > 1 else "Unknown"

    df["Invoice No"] = invoice_no
    df["Supplier GSTIN"] = supplier_gstin
    df["Customer GSTIN"] = customer_gstin
    df["Source File"] = filename

    # Step 6: Auto-calc only if missing
    df["Gross Amount"] = df.apply(
        lambda x: x["Gross Amount"] if safe_float(x["Gross Amount"]) != 0
        else safe_float(x["Quantity"]) * safe_float(x["Rate"]),
        axis=1
    )
    df["Net Amount"] = df.apply(
        lambda x: x["Net Amount"] if safe_float(x["Net Amount"]) != 0
        else (x["Gross Amount"] - x["Discount Amount"] + x["IGST Amount"] + x["CGST Amount"] + x["SGST Amount"]),
        axis=1
    )

    return df[EXPECTED_COLUMNS]
