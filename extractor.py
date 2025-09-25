import pdfplumber
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

HEADER_MAP = {
    "invoice no": "Invoice No", "invoice #": "Invoice No", "inv. no.": "Invoice No",
    "bill no": "Invoice No", "voucher no": "Invoice No", "document no": "Invoice No",
    "supplier gstin": "Supplier GSTIN", "seller gstin": "Supplier GSTIN", "vendor gstin": "Supplier GSTIN",
    "customer gstin": "Customer GSTIN", "buyer gstin": "Customer GSTIN", "recipient gstin": "Customer GSTIN",
    "hsn": "HSN", "hsn code": "HSN", "hsn/sac": "HSN",
    "item": "Item Name", "item name": "Item Name", "description": "Item Name",
    "product": "Item Name", "product name": "Item Name", "particulars": "Item Name",
    "qty": "Quantity", "quantity": "Quantity", "pcs": "Quantity", "units": "Quantity",
    "rate": "Rate", "price": "Rate", "unit cost": "Rate", "unit price": "Rate",
    "gross amount": "Gross Amount", "total value": "Gross Amount", "subtotal": "Gross Amount",
    "discount%": "Discount%", "disc%": "Discount%", "discount (%)": "Discount%",
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
    return [HEADER_MAP.get(h.lower().strip(), h.strip()) for h in headers]

def clean_numeric(value):
    """Remove unwanted symbols and convert to float."""
    if isinstance(value, str):
        value = re.sub(r"[^\d.\-]", "", value)
    try:
        return float(value) if value not in ("", None) else 0.0
    except:
        return 0.0

def parse_invoice(pdf_path, filename, text=""):
    """Extract invoice data from PDF file path."""
    all_tables = []
    with pdfplumber.open(pdf_path) as pdf:
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

    # Clean numeric fields
    for col in df.columns:
        if any(key in col.lower() for key in ["amount", "rate", "qty", "igst", "cgst", "sgst", "discount", "net", "gross"]):
            df[col] = df[col].apply(clean_numeric)

    # Extract Invoice No
    invoice_no = re.findall(r"Invoice\s*No[:\-]?\s*([A-Za-z0-9\-\/]+)", text, re.IGNORECASE)
    invoice_no = invoice_no[0] if invoice_no else "Unknown"

    # Extract GSTINs
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
            df[col] = 0.0 if col not in ["Invoice No", "Supplier GSTIN", "Customer GSTIN", "Source File", "HSN", "Item Name"] else ""

    return df[EXPECTED_COLUMNS]
