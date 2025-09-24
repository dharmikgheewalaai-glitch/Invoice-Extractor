import pandas as pd
import re

def safe_float(val):
    """Convert string/None to float safely."""
    try:
        return float(str(val).replace(",", "").strip())
    except:
        return 0.0

def parse_invoice(pdf, text, source_file):
    """
    Extract structured invoice data from PDF into dataframe.
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
    # Extract table rows from PDF
    # ------------------------
    rows = []
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            for row in table:
                clean_row = [str(cell).strip() if cell else "" for cell in row]

                # Detect if row has HSN (4+ digit code) → likely an item row
                if any(re.match(r"\d{4,}", c) for c in clean_row):
                    hsn = next((c for c in clean_row if re.match(r"\d{4,}", c)), "")

                    # Try Qty, Rate, Gross
                    qty = safe_float(next((c for c in clean_row if re.match(r"^\d+(\.\d+)?$", c)), 0))
                    rate = 0.0
                    gross = 0.0

                    if len(clean_row) >= 5:
                        rate = safe_float(clean_row[-3])
                        gross = safe_float(clean_row[-2])

                    if not gross:
                        gross = qty * rate

                    # ------------------------
                    # Discounts
                    # ------------------------
                    disc_percent = ""
                    disc_amount = ""

                    for c in clean_row:
                        if "%" in c and "GST" not in c.upper():
                            val = safe_float(c.replace("%", ""))
                            disc_percent = val
                            disc_amount = round((gross * val) / 100, 2)
                        elif re.search(r"disc", c, re.IGNORECASE):
                            val = safe_float(re.sub(r"[^\d.]", "", c))
                            disc_amount = val
                            disc_percent = round((val / gross) * 100, 2) if gross else ""

                    gross_after_disc = gross - safe_float(disc_amount)

                    # ------------------------
                    # GST extraction
                    # ------------------------
                    igst_percent = igst_amount = ""
                    cgst_percent = cgst_amount = ""
                    sgst_percent = sgst_amount = ""

                    for c in clean_row:
                        if "IGST" in c.upper():
                            num = safe_float(re.sub(r"[^\d.]", "", c))
                            if "%" in c:
                                igst_percent = num
                                igst_amount = round((gross_after_disc * num) / 100, 2)
                            else:
                                igst_amount = num
                                igst_percent = round((igst_amount / gross_after_disc) * 100, 2) if gross_after_disc else ""
                        if "CGST" in c.upper():
                            num = safe_float(re.sub(r"[^\d.]", "", c))
                            if "%" in c:
                                cgst_percent = num
                                cgst_amount = round((gross_after_disc * num) / 100, 2)
                            else:
                                cgst_amount = num
                                cgst_percent = round((cgst_amount / gross_after_disc) * 100, 2) if gross_after_disc else ""
                        if "SGST" in c.upper():
                            num = safe_float(re.sub(r"[^\d.]", "", c))
                            if "%" in c:
                                sgst_percent = num
                                sgst_amount = round((gross_after_disc * num) / 100, 2)
                            else:
                                sgst_amount = num
                                sgst_percent = round((sgst_amount / gross_after_disc) * 100, 2) if gross_after_disc else ""

                    # ------------------------
                    # Net Amount (check if present directly)
                    # ------------------------
                    net_amount = gross_after_disc + safe_float(igst_amount) + safe_float(cgst_amount) + safe_float(sgst_amount)

                    net_match = [c for c in clean_row if re.search(r"\d+\.\d{2}", c)]
                    if net_match:
                        last_val = safe_float(net_match[-1])
                        if last_val > 0 and abs(last_val - net_amount) > 1:
                            net_amount = last_val

                    # Item Name = text after HSN up to Qty
                    try:
                        hsn_index = clean_row.index(hsn)
                        item_name = " ".join(clean_row[hsn_index+1:-3]) if len(clean_row) > hsn_index+3 else "Item"
                    except:
                        item_name = "Item"

                    # ------------------------
                    # Append row
                    # ------------------------
                    rows.append([
                        invoice_no,
                        supplier_gstin,
                        customer_gstin,
                        source_file,
                        hsn,
                        item_name,
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
    # Build DataFrame
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
