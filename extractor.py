import pandas as pd
import re

def safe_float(val):
    """Convert string to float safely."""
    try:
        return float(val)
    except:
        return 0.0

def parse_invoice(pdf, text, source_file):
    """
    Extract invoice details into a structured dataframe.
    """

    # ------------------------
    # Extract Invoice No
    # ------------------------
    invoice_no = None
    match = re.search(r"(?:Invoice\s*No\.?|Invoice\s*Number)[:\s]*([\w/-]+)", text, re.IGNORECASE)
    if match:
        invoice_no = match.group(1).strip()

    # ------------------------
    # Extract GSTINs
    # ------------------------
    supplier_gstin = None
    customer_gstin = None

    supplier_match = re.search(r"Supplier\s*GSTIN[:\s]*([0-9A-Z]{15})", text, re.IGNORECASE)
    customer_match = re.search(r"Customer\s*GSTIN[:\s]*([0-9A-Z]{15})", text, re.IGNORECASE)
    generic_match = re.findall(r"\b[0-9A-Z]{15}\b", text)

    if supplier_match:
        supplier_gstin = supplier_match.group(1).strip()
    elif len(generic_match) > 0:
        supplier_gstin = generic_match[0]

    if customer_match:
        customer_gstin = customer_match.group(1).strip()
    elif len(generic_match) > 1:
        customer_gstin = generic_match[1]

    # ------------------------
    # Extract line items
    # ------------------------
    rows = []
    for line in text.split("\n"):
        parts = line.split()

        # crude HSN detection (4+ digits)
        if any(re.match(r"\d{4,}", p) for p in parts):
            hsn = next((p for p in parts if re.match(r"\d{4,}", p)), "")

            # Try to capture qty and rate
            qty = next((p for p in parts if re.match(r"^\d+(\.\d+)?$", p)), "0")
            rate = "0"
            if len(parts) > 2:
                rate = parts[-2] if re.match(r"^\d+(\.\d+)?$", parts[-2]) else "0"

            qty = safe_float(qty)
            rate = safe_float(rate)
            gross = qty * rate

            # ------------------------
            # Discounts
            # ------------------------
            disc_percent = ""
            disc_amount = ""

            disc_match = re.search(r"(\d+(\.\d+)?)\s*%", line)
            if disc_match:
                disc_percent = safe_float(disc_match.group(1))
                disc_amount = round((gross * disc_percent) / 100, 2)
            else:
                disc_amt_match = re.search(r"Disc(?:ount)?[:\s]*([\d.]+)", line, re.IGNORECASE)
                if disc_amt_match:
                    disc_amount = safe_float(disc_amt_match.group(1))
                    disc_percent = round((disc_amount / gross) * 100, 2) if gross else ""

            gross_after_disc = gross - safe_float(disc_amount)

            # ------------------------
            # GST handling
            # ------------------------
            igst_percent = igst_amount = ""
            cgst_percent = cgst_amount = ""
            sgst_percent = sgst_amount = ""

            # IGST
            igst_match = re.search(r"IGST[:\s]*([\d.]+)%?", line, re.IGNORECASE)
            if igst_match:
                val = safe_float(igst_match.group(1))
                if "%" in igst_match.group(0):
                    igst_percent = val
                    igst_amount = round((gross_after_disc * igst_percent) / 100, 2)
                else:
                    igst_amount = val
                    igst_percent = round((igst_amount / gross_after_disc) * 100, 2) if gross_after_disc else ""

            # CGST
            cgst_match = re.search(r"CGST[:\s]*([\d.]+)%?", line, re.IGNORECASE)
            if cgst_match:
                val = safe_float(cgst_match.group(1))
                if "%" in cgst_match.group(0):
                    cgst_percent = val
                    cgst_amount = round((gross_after_disc * cgst_percent) / 100, 2)
                else:
                    cgst_amount = val
                    cgst_percent = round((cgst_amount / gross_after_disc) * 100, 2) if gross_after_disc else ""

            # SGST
            sgst_match = re.search(r"SGST[:\s]*([\d.]+)%?", line, re.IGNORECASE)
            if sgst_match:
                val = safe_float(sgst_match.group(1))
                if "%" in sgst_match.group(0):
                    sgst_percent = val
                    sgst_amount = round((gross_after_disc * sgst_percent) / 100, 2)
                else:
                    sgst_amount = val
                    sgst_percent = round((sgst_amount / gross_after_disc) * 100, 2) if gross_after_disc else ""

            # ------------------------
            # Net Amount
            # ------------------------
            net_amount = gross_after_disc + safe_float(igst_amount) + safe_float(cgst_amount) + safe_float(sgst_amount)

            rows.append([
                invoice_no,
                supplier_gstin,
                customer_gstin,
                source_file,
                hsn,
                "Item",  # placeholder
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

    # ------------------------
    # Create DataFrame
    # ------------------------
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
