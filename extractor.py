import pdfplumber
import pandas as pd
import re

# -------- Expected Columns --------
EXPECTED_COLUMNS = [
    "Invoice No","Supplier GSTIN","Customer GSTIN","Source File",
    "HSN","Item Name","Quantity","Rate","Gross Amount",
    "Discount%","Discount Amount","IGST%","IGST Amount",
    "CGST%","CGST Amount","SGST%","SGST Amount","Net Amount",
]

# -------- Header Normalization --------
HEADER_MAP = {
    "invoice no": "Invoice No","invoice #": "Invoice No","inv. no.": "Invoice No",
    "bill no": "Invoice No","voucher no": "Invoice No","document no": "Invoice No",
    "supplier gstin": "Supplier GSTIN","seller gstin": "Supplier GSTIN","vendor gstin": "Supplier GSTIN",
    "customer gstin": "Customer GSTIN","buyer gstin": "Customer GSTIN","recipient gstin": "Customer GSTIN",
    "hsn": "HSN","hsn code": "HSN","hsn/sac": "HSN",
    "item": "Item Name","description": "Item Name","product": "Item Name","particulars": "Item Name",
    "qty": "Quantity","quantity": "Quantity","pcs": "Quantity","units": "Quantity",
    "rate": "Rate","price": "Rate","unit cost": "Rate",
    "gross amount": "Gross Amount","subtotal": "Gross Amount","total value": "Gross Amount",
    "discount%": "Discount%","disc%": "Discount%","discount (%)": "Discount%",
    "discount amount": "Discount Amount","disc amt": "Discount Amount",
    "igst%": "IGST%","igst rate %": "IGST%","integrated tax %": "IGST%",
    "igst amount": "IGST Amount","igst value": "IGST Amount",
    "cgst%": "CGST%","cgst rate %": "CGST%","central tax %": "CGST%",
    "cgst amount": "CGST Amount","cgst value": "CGST Amount",
    "sgst%": "SGST%","sgst rate %": "SGST%","state tax %": "SGST%",
    "sgst amount": "SGST Amount","sgst value": "SGST Amount",
    "net amount": "Net Amount","grand total": "Net Amount","invoice total": "Net Amount",
}

def normalize_headers(headers):
    return [HEADER_MAP.get(h.lower().strip(), h.strip()) for h in headers]

def clean_numeric(value):
    """Remove symbols and convert to float"""
    if isinstance(value, str):
        value = re.sub(r"[^\d.\-]", "", value)
    try:
        return float(value) if value not in ("", None, "") else 0.0
    except:
        return 0.0

# -------- Main Parser --------
def parse_invoice(pdf_path, filename, text=""):
    all_tables = []
    with pdfplumber.open(pdf_path) as pdf:
        full_text = " ".join([p.extract_text() or "" for p in pdf.pages])
        if text.strip() == "":
            text = full_text
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

    # Clean numeric columns
    for col in df.columns:
        if any(k in col.lower() for k in ["amount","rate","qty","igst","cgst","sgst","discount","net","gross"]):
            df[col] = df[col].apply(clean_numeric)

    # -------- Metadata from text --------
    inv_match = re.search(r"Invoice\s*No[:\-]?\s*([A-Za-z0-9\-\/]+)", text, re.I)
    invoice_no = inv_match.group(1) if inv_match else "Unknown"
    gstins = re.findall(r"\b\d{2}[A-Z]{5}\d{4}[A-Z][0-9A-Z]Z[0-9A-Z]\b", text)
    supplier_gstin = gstins[0] if len(gstins) > 0 else "Unknown"
    customer_gstin = gstins[1] if len(gstins) > 1 else "Unknown"

    # Add metadata
    df["Invoice No"] = invoice_no
    df["Supplier GSTIN"] = supplier_gstin
    df["Customer GSTIN"] = customer_gstin
    df["Source File"] = filename

    # Ensure all expected columns exist
    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            df[col] = 0.0 if col not in ["Invoice No","Supplier GSTIN","Customer GSTIN","Source File","HSN","Item Name"] else ""

    # -------- Auto-calculations --------
    def auto_calc(row):
        q, r = row["Quantity"], row["Rate"]
        gross, disc_pct, disc_amt = row["Gross Amount"], row["Discount%"], row["Discount Amount"]
        igst_pct, igst_amt = row["IGST%"], row["IGST Amount"]
        cgst_pct, cgst_amt = row["CGST%"], row["CGST Amount"]
        sgst_pct, sgst_amt = row["SGST%"], row["SGST Amount"]
        net = row["Net Amount"]

        # Gross
        if gross == 0 and q and r:
            gross = q * r

        # Discount
        if disc_amt == 0 and gross and disc_pct:
            disc_amt = gross * disc_pct / 100
        if disc_pct == 0 and gross and disc_amt:
            disc_pct = (disc_amt / gross) * 100

        taxable = gross - disc_amt

        # IGST
        if igst_amt == 0 and taxable and igst_pct:
            igst_amt = taxable * igst_pct / 100
        if igst_pct == 0 and taxable and igst_amt:
            igst_pct = (igst_amt / taxable) * 100

        # CGST
        if cgst_amt == 0 and taxable and cgst_pct:
            cgst_amt = taxable * cgst_pct / 100
        if cgst_pct == 0 and taxable and cgst_amt:
            cgst_pct = (cgst_amt / taxable) * 100

        # SGST
        if sgst_amt == 0 and taxable and sgst_pct:
            sgst_amt = taxable * sgst_pct / 100
        if sgst_pct == 0 and taxable and sgst_amt:
            sgst_pct = (sgst_amt / taxable) * 100

        # Net
        if net == 0 and gross:
            net = taxable + igst_amt + cgst_amt + sgst_amt

        return pd.Series([
            row["Invoice No"], row["Supplier GSTIN"], row["Customer GSTIN"], row["Source File"],
            row["HSN"], row["Item Name"], q, r, gross, disc_pct, disc_amt,
            igst_pct, igst_amt, cgst_pct, cgst_amt, sgst_pct, sgst_amt, net
        ], index=EXPECTED_COLUMNS)

    df = df.apply(auto_calc, axis=1)
    return df[EXPECTED_COLUMNS]
