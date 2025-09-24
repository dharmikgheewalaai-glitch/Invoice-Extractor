import pandas as pd

# Header mapping dictionary
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
    "discount%": "Discount%",
    "discount": "Discount%",
    "disc%": "Discount%",
    "rebate %": "Discount%",
    "offer %": "Discount%",
    "deduction %": "Discount%",
    "allowance %": "Discount%",

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
    "igst%": "IGST%",
    "igst rate %": "IGST%",
    "integrated tax %": "IGST%",
    "igst duty %": "IGST%",
    "int. gst %": "IGST%",

    # IGST Amount
    "igst amount": "IGST Amount",
    "igst value": "IGST Amount",
    "integrated tax amount": "IGST Amount",
    "igst duty amount": "IGST Amount",
    "igst charges": "IGST Amount",
    "igst total": "IGST Amount",
    "igst": "IGST Amount",

    # CGST %
    "cgst%": "CGST%",
    "cgst rate %": "CGST%",
    "central tax %": "CGST%",
    "c. gst %": "CGST%",
    "central gst rate": "CGST%",

    # CGST Amount
    "cgst amount": "CGST Amount",
    "cgst value": "CGST Amount",
    "central tax amount": "CGST Amount",
    "cgst charges": "CGST Amount",
    "cgst duty amount": "CGST Amount",
    "cgst total": "CGST Amount",
    "cgst": "CGST Amount",

    # SGST %
    "sgst%": "SGST%",
    "sgst rate %": "SGST%",
    "state tax %": "SGST%",
    "s. gst %": "SGST%",
    "state gst rate": "SGST%",

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


def normalize_headers(headers):
    """Normalize headers using HEADER_MAP"""
    return [HEADER_MAP.get(h.lower().strip(), h.strip()) for h in headers]


def parse_invoice(pdf, text, source_file=None):
    """
    Parse invoice PDF (with extracted text + tables).
    pdf  -> pdfplumber object
    text -> full extracted text
    source_file -> file name
    """
    data = []

    # Extract tables from PDF
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            if not table:
                continue

            headers = normalize_headers(table[0])  # first row = headers
            rows = table[1:]

            for row in rows:
                if any(cell for cell in row):  # skip empty rows
                    record = dict(zip(headers, row))
                    if source_file:
                        record["Source File"] = source_file
                    data.append(record)

    # Build DataFrame
    df = pd.DataFrame(data)

    # Ensure all required columns exist
    required_columns = [
        "Invoice No", "Supplier GSTIN", "Customer GSTIN", "Source File",
        "HSN", "Item Name", "Quantity", "Rate", "Gross Amount",
        "Discount%", "Discount Amount", "IGST%", "IGST Amount",
        "CGST%", "CGST Amount", "SGST%", "SGST Amount", "Net Amount"
    ]
    for col in required_columns:
        if col not in df.columns:
            df[col] = None

    # Convert numeric columns safely
    num_cols = ["Gross Amount", "Discount Amount", "IGST Amount", "CGST Amount", "SGST Amount"]
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Calculate Net Amount
    df["Net Amount"] = (
        df["Gross Amount"]
        - df["Discount Amount"]
        - df["IGST Amount"]
        - df["CGST Amount"]
        - df["SGST Amount"]
    )

    # Reorder columns
    df = df[required_columns]

    return df
