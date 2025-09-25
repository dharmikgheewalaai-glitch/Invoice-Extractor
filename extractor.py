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
    "Discount(%)",
    "Discount Amount",
    "IGST(%)",
    "IGST Amount",
    "CGST(%)",
    "CGST Amount",
    "SGST(%)",
    "SGST Amount",
    "Net Amount",
]

def normalize_headers(headers):
    """Map detected headers to exact expected names"""
HEADER_MAP = {
    # Invoice No
    "invoice no": "Invoice No",
    "invoice #": "Invoice No",
    "inv. no.": "Invoice No",
    "bill no": "Invoice No",
    "voucher no": "Invoice No",
    "document no": "Invoice No",

    # Supplier GSTIN
    "supplier gstin": "Supplier GSTIN",
    "seller gstin": "Supplier GSTIN",
    "vendor gstin": "Supplier GSTIN",
    "supplier gst no": "Supplier GSTIN",
    "seller tax id": "Supplier GSTIN",
    "vendor tax id": "Supplier GSTIN",

    # Customer GSTIN
    "customer gstin": "Customer GSTIN",
    "buyer gstin": "Customer GSTIN",
    "client gstin": "Customer GSTIN",
    "recipient gstin": "Customer GSTIN",
    "customer gst no": "Customer GSTIN",
    "buyer tax id": "Customer GSTIN",

    # Source File
    "source file": "Source File",
    "upload name": "Source File",
    "source document": "Source File",
    "file reference": "Source File",
    "document source": "Source File",
    "file path": "Source File",

    # HSN
    "hsn": "HSN",
    "hsn code": "HSN",
    "hsn/sac": "HSN",
    "hsn code no": "HSN",
    "hsn classification": "HSN",
    "hsn/sac code": "HSN",
    "harmonized code": "HSN",

    # Item Name
    "item": "Item Name",
    "item name": "Item Name",
    "description": "Item Name",
    "product": "Item Name",
    "product name": "Item Name",
    "service name": "Item Name",
    "goods/service description": "Item Name",
    "material name": "Item Name",
    "particulars": "Item Name",
    "item description": "Item Name",
    "product details": "Item Name",

    # Quantity
    "qty": "Quantity",
    "quantity": "Quantity",
    "no. of units": "Quantity",
    "nos.": "Quantity",
    "packets": "Quantity",
    "pcs": "Quantity",
    "units": "Quantity",
    "order quantity": "Quantity",

    # Rate
    "rate": "Rate",
    "price": "Rate",
    "unit cost": "Rate",
    "unit price": "Rate",
    "per unit rate": "Rate",
    "selling price": "Rate",
    "unit value": "Rate",
    "rate per item": "Rate",

    # Gross Amount
    "gross amount": "Gross Amount",
    "total value": "Gross Amount",
    "total before tax": "Gross Amount",
    "amount before tax": "Gross Amount",
    "subtotal": "Gross Amount",
    "line total": "Gross Amount",

    # Discount %
    "discount%": "Discount(%)",
    "discount": "Discount(%)",
    "disc%": "Discount(%)",
    "rebate %": "Discount(%)",
    "offer %": "Discount(%)",
    "deduction %": "Discount(%)",
    "allowance %": "Discount(%)",

    # Discount Amount
    "discount amount": "Discount Amount",
    "disc amt": "Discount Amount",
    "rebate amount": "Discount Amount",
    "deduction value": "Discount Amount",
    "offer amount": "Discount Amount",
    "concession": "Discount Amount",
    "discounted amount": "Discount Amount",
    "total discount": "Discount Amount",

    # IGST %
    "igst%": "IGST(%)",
    "igst rate %": "IGST(%)",
    "integrated tax %": "IGST(%)",
    "igst duty %": "IGST(%)",
    "int. gst %": "IGST(%)",

    # IGST Amount
    "igst amount": "IGST Amount",
    "igst value": "IGST Amount",
    "integrated tax amount": "IGST Amount",
    "igst duty amount": "IGST Amount",
    "igst charges": "IGST Amount",
    "igst total": "IGST Amount",
    "igst": "IGST Amount",

    # CGST %
    "cgst%": "CGST(%)",
    "cgst rate %": "CGST(%)",
    "central tax %": "CGST(%)",
    "c. gst %": "CGST(%)",
    "central gst rate": "CGST(%)",

    # CGST Amount
    "cgst amount": "CGST Amount",
    "cgst value": "CGST Amount",
    "central tax amount": "CGST Amount",
    "cgst charges": "CGST Amount",
    "cgst duty amount": "CGST Amount",
    "cgst total": "CGST Amount",
    "cgst": "CGST Amount",

    # SGST %
    "sgst%": "SGST(%)",
    "sgst rate %": "SGST(%)",
    "state tax %": "SGST(%)",
    "s. gst %": "SGST(%)",
    "state gst rate": "SGST(%)",

    # SGST Amount
    "sgst amount": "SGST Amount",
    "sgst value": "SGST Amount",
    "state tax amount": "SGST Amount",
    "sgst charges": "SGST Amount",
    "sgst duty amount": "SGST Amount",
    "sgst total": "SGST Amount",
    "sgst": "SGST Amount",

    # Net Amount
    "net amount": "Net Amount",
    "grand total": "Net Amount",
    "invoice total": "Net Amount",
    "total payable": "Net Amount",
    "amount due": "Net Amount",
    "final total": "Net Amount",
}
    return [header_map.get(h.lower().strip(), h.strip()) for h in headers]

def clean_numeric(value):
    """Remove unwanted symbols from numbers (₹, %, commas, etc.)"""
    if isinstance(value, str):
        value = re.sub(r"[^\d.\-]", "", value)  # keep only numbers, dot, minus
    return value

def parse_invoice(pdf, text, filename):
    """Extracts invoice table data and adds Invoice No, GSTIN, and Source File"""
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
        df = pd.DataFrame(columns=EXPECTED_COLUMNS)

    # Clean numeric values
    for col in df.columns:
        if any(key in col.lower() for key in ["amount", "rate", "qty", "igst", "cgst", "sgst", "discount", "net"]):
            df[col] = df[col].apply(clean_numeric)

    # Extract Invoice No
    invoice_no = re.findall(r"Invoice\s*No[:\-]?\s*([A-Za-z0-9\-\/]+)", text, re.IGNORECASE)
    invoice_no = invoice_no[0] if invoice_no else "Unknown"

    # Extract Supplier & Customer GSTIN
    gstins = re.findall(r"\b\d{2}[A-Z]{5}\d{4}[A-Z][0-9A-Z]Z[0-9A-Z]\b", text)
    supplier_gstin = gstins[0] if len(gstins) > 0 else "Unknown"
    customer_gstin = gstins[1] if len(gstins) > 1 else "Unknown"

    # Add Info columns
    df["Invoice No"] = invoice_no
    df["Supplier GSTIN"] = supplier_gstin
    df["Customer GSTIN"] = customer_gstin
    df["Source File"] = filename

    # Ensure all expected columns exist
    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    # Reorder columns
    df = df[EXPECTED_COLUMNS]

    return df
