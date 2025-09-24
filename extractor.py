import pandas as pd
import re

def parse_invoice(pdf, text, source_file):
    """
    Extract invoice details into a structured dataframe
    """

    # Try to extract Invoice No
    invoice_no = None
    match = re.search(r"(?:Invoice\s*No\.?|Invoice\s*Number)[:\s]*([\w/-]+)", text, re.IGNORECASE)
    if match:
        invoice_no = match.group(1).strip()

    # Try to extract GSTINs
    supplier_gstin = None
    customer_gstin = None

    supplier_match = re.search(r"Supplier\s*GSTIN[:\s]*([0-9A-Z]{15})", text, re.IGNORECASE)
    customer_match = re.search(r"Customer\s*GSTIN[:\s]*([0-9A-Z]{15})", text, re.IGNORECASE)
    generic_match = re.findall(r"\b[0-9A-Z]{15}\b", text)  # fallback

    if supplier_match:
        supplier_gstin = supplier_match.group(1).strip()
    elif len(generic_match) > 0:
        supplier_gstin = generic_match[0]

    if customer_match:
        customer_gstin = customer_match.group(1).strip()
    elif len(generic_match) > 1:
        customer_gstin = generic_match[1]

    # Extract line items (HSN, description, qty, rate, etc.)
    rows = []
    for line in text.split("\n"):
        parts = line.split()
        if any(p.isdigit() for p in parts) and any(re.match(r"\d{4}", p) for p in parts):  # crude HSN check
            hsn = next((p for p in parts if re.match(r"\d{4,}", p)), "")
            qty = next((p for p in parts if re.match(r"^\d+(\.\d+)?$", p)), "0")
            rate = next((p for p in parts if re.match(r"^\d+(\.\d+)?$", p)), "0")

            # Defaults
            gross = float(qty) * float(rate)
            disc_percent = ""
            disc_amount = ""
            igst_percent, igst_amount = "", ""
            cgst_percent, cgst_amount = "", ""
            sgst_percent, sgst_amount = "", ""
            net_amount = gross

            rows.append([
                invoice_no,
                supplier_gstin,
                customer_gstin,
                source_file,
                hsn,
                "Item",  # placeholder for Item Name
                qty,
                rate,
                gross,
                disc_percent,
                disc_amount,
                igst_percent,
                igst_amount,
                cgst_percent,
                cgst_amount,
                sgst_percent,
                sgst_amount,
                net_amount
            ])

    df = pd.DataFrame(rows, columns=[
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
        "Net Amount"
    ])

    return df
