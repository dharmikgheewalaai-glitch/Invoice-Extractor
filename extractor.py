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

    # Customer GSTIN
    "customer gstin": "Customer GSTIN",
    "buyer gstin": "Customer GSTIN",
    "client gstin": "Customer GSTIN",
    "recipient gstin": "Customer GSTIN",

    # Source File
    "source file": "Source File",
    "upload name": "Source File",

    # HSN
    "hsn": "HSN",
    "hsn code": "HSN",

    # Item Name
    "item": "Item Name",
    "description": "Item Name",
    "product": "Item Name",

    # Quantity
    "qty": "Quantity",
    "quantity": "Quantity",

    # Rate
    "rate": "Rate",
    "price": "Rate",
    "unit cost": "Rate",

    # Gross Amount
    "gross amount": "Gross Amount",
    "total value": "Gross Amount",

    # Discount %
    "discount%": "Discount%",
    "discount": "Discount%",

    # Discount Amount
    "discount amount": "Discount Amount",
    "disc amt": "Discount Amount",

    # IGST %
    "igst%": "IGST%",
    "igst rate %": "IGST%",

    # IGST Amount
    "igst amount": "IGST Amount",
    "igst value": "IGST Amount",

    # CGST %
    "cgst%": "CGST%",
    "cgst rate %": "CGST%",

    # CGST Amount
    "cgst amount": "CGST Amount",
    "cgst value": "CGST Amount",

    # SGST %
    "sgst%": "SGST%",
    "sgst rate %": "SGST%",

    # SGST Amount
    "sgst amount": "SGST Amount",
    "sgst value": "SGST Amount",

    # Net Amount
    "net amount": "Net Amount",
    "grand total": "Net Amount",
    "invoice total": "Net Amount",
}


def normalize_headers(headers):
    """Map detected headers to exact expected names"""
    return [HEADER_MAP.get(h.lower().strip(), h.strip()) for h in headers]


def clean_numeric(value):
    """Remove unwanted symbols from numbers (₹, %, commas, etc.)"""
    if isinstance(value, str):
        value = re.sub(r"[^\d.\-]", "", value)
    try:
        return float(value) if value not in ("", None) else 0.0
    except:
        return 0.0


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
        if any(key in col.lower() for key in ["amount", "rate", "qty", "igst", "cgst", "sgst", "discount", "net", "gross"]):
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
            df[col] = 0 if "Amount" in col or "%" in col or col in ["Quantity", "Rate", "Gross Amount", "Net Amount"] else ""

    # ----------- Auto Calculations ------------
    df["Gross Amount"] = df.apply(
        lambda x: x["Quantity"] * x["Rate"] if (x.get("Gross Amount", 0) in [0, None, ""]) else x["Gross Amount"],
        axis=1,
    )

    df["Discount Amount"] = df.apply(
        lambda x: (x["Gross Amount"] * (x["Discount%"] / 100)) if (x.get("Discount Amount", 0) in [0, None, ""]) else x["Discount Amount"],
        axis=1,
    )

    df["IGST Amount"] = df.apply(
        lambda x: (x["Gross Amount"] - x["Discount Amount"]) * (x["IGST%"] / 100) if (x.get("IGST Amount", 0) in [0, None, ""]) else x["IGST Amount"],
        axis=1,
    )

    df["CGST Amount"] = df.apply(
        lambda x: (x["Gross Amount"] - x["Discount Amount"]) * (x["CGST%"] / 100) if (x.get("CGST Amount", 0) in [0, None, ""]) else x["CGST Amount"],
        axis=1,
    )

    df["SGST Amount"] = df.apply(
        lambda x: (x["Gross Amount"] - x["Discount Amount"]) * (x["SGST%"] / 100) if (x.get("SGST Amount", 0) in [0, None, ""]) else x["SGST Amount"],
        axis=1,
    )

    df["Net Amount"] = df.apply(
        lambda x: (x["Gross Amount"] - x["Discount Amount"] + x["IGST Amount"] + x["CGST Amount"] + x["SGST Amount"])
        if (x.get("Net Amount", 0) in [0, None, ""])
        else x["Net Amount"],
        axis=1,
    )
    # ------------------------------------------

    # Reorder columns
    df = df[EXPECTED_COLUMNS]

    return df
