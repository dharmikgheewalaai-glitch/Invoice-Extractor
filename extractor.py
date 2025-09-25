import pdfplumber
import pandas as pd
import re

# Expected columns in final DataFrame
EXPECTED_COLUMNS = [
    "Invoice No", "Supplier GSTIN", "Customer GSTIN", "Source File",
    "HSN", "Item Name", "Quantity", "Rate", "Gross Amount",
    "Discount%", "Discount Amount",
    "IGST%", "IGST Amount", "CGST%", "CGST Amount", "SGST%", "SGST Amount",
    "Net Amount"
]

# --- Helpers ---
def safe_float(val):
    try:
        if val is None or str(val).strip() == "":
            return 0.0
        return float(str(val).replace(",", "").strip())
    except:
        return 0.0

def normalize_headers(headers):
    normalized = []
    for h in headers:
        if h is None:
            normalized.append("")
            continue
        h_clean = h.strip().lower()
        if "invoice" in h_clean and "no" in h_clean:
            normalized.append("Invoice No")
        elif "gstin" in h_clean and "supplier" in h_clean:
            normalized.append("Supplier GSTIN")
        elif "gstin" in h_clean and "customer" in h_clean:
            normalized.append("Customer GSTIN")
        elif "hsn" in h_clean:
            normalized.append("HSN")
        elif "item" in h_clean or "desc" in h_clean:
            normalized.append("Item Name")
        elif "qty" in h_clean or "quantity" in h_clean:
            normalized.append("Quantity")
        elif "rate" in h_clean or "price" in h_clean:
            normalized.append("Rate")
        elif "gross" in h_clean:
            normalized.append("Gross Amount")
        elif "discount" in h_clean and "%" in h_clean:
            normalized.append("Discount%")
        elif "discount" in h_clean:
            normalized.append("Discount Amount")
        elif "igst" in h_clean and "%" in h_clean:
            normalized.append("IGST%")
        elif "igst" in h_clean:
            normalized.append("IGST Amount")
        elif "cgst" in h_clean and "%" in h_clean:
            normalized.append("CGST%")
        elif "cgst" in h_clean:
            normalized.append("CGST Amount")
        elif "sgst" in h_clean and "%" in h_clean:
            normalized.append("SGST%")
        elif "sgst" in h_clean:
            normalized.append("SGST Amount")
        elif "net" in h_clean or "total" in h_clean:
            normalized.append("Net Amount")
        else:
            normalized.append(h.strip())
    return normalized

# --- Main Extractor ---
def parse_invoice(pdf, text, filename):
    all_tables = []

    # Step 1: Try extracting tables
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

    # Step 2: Clean numeric fields
    for col in df.columns:
        if any(key in col.lower() for key in ["amount", "rate", "qty", "igst", "cgst", "sgst", "discount", "net", "gross"]):
            df[col] = df[col].apply(safe_float)

    # Step 3: Extract metadata from text
    inv_match = re.search(r"(Invoice\s*No|Inv\s*No|Bill\s*No|Voucher\s*No)[:\-]?\s*([A-Za-z0-9\-\/]+)", text, re.I)
    invoice_no = inv_match.group(2) if inv_match else "Unknown"

    gstins = re.findall(r"\b\d{2}[A-Z]{5}\d{4}[A-Z][0-9A-Z]Z[0-9A-Z]\b", text)
    supplier_gstin = gstins[0] if len(gstins) > 0 else "Unknown"
    customer_gstin = gstins[1] if len(gstins) > 1 else "Unknown"

    net_match = re.search(r"(Net\s*Amount|Grand\s*Total|Invoice\s*Total)[:\-]?\s*([\d,]+\.?\d*)", text, re.I)
    net_amount_from_text = safe_float(net_match.group(2)) if net_match else 0.0

    gross_match = re.search(r"(Gross\s*Amount|Subtotal|Total\s*Before\s*Tax)[:\-]?\s*([\d,]+\.?\d*)", text, re.I)
    gross_from_text = safe_float(gross_match.group(2)) if gross_match else 0.0

    # Step 4: Insert info into DataFrame
    df["Invoice No"] = invoice_no
    df["Supplier GSTIN"] = supplier_gstin
    df["Customer GSTIN"] = customer_gstin
    df["Source File"] = filename

    # Step 5: Ensure all expected cols exist
    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            if col in ["Invoice No","Supplier GSTIN","Customer GSTIN","Source File","HSN","Item Name"]:
                df[col] = ""
            else:
                df[col] = 0.0

    # Step 6: If no table, still create 1 row from text
    if df.empty:
        df = pd.DataFrame([{
            "Invoice No": invoice_no,
            "Supplier GSTIN": supplier_gstin,
            "Customer GSTIN": customer_gstin,
            "Source File": filename,
            "HSN": "",
            "Item Name": "NA",
            "Quantity": 0,
            "Rate": 0,
            "Gross Amount": gross_from_text,
            "Discount%": 0,
            "Discount Amount": 0,
            "IGST%": 0,
            "IGST Amount": 0,
            "CGST%": 0,
            "CGST Amount": 0,
            "SGST%": 0,
            "SGST Amount": 0,
            "Net Amount": net_amount_from_text
        }], columns=EXPECTED_COLUMNS)

    # Step 7: Auto-calculate missing values
    df["Gross Amount"] = df.apply(
        lambda x: safe_float(x["Gross Amount"]) if safe_float(x["Gross Amount"]) != 0
        else safe_float(x["Quantity"]) * safe_float(x["Rate"]),
        axis=1
    )

    df["Net Amount"] = df.apply(
        lambda x: safe_float(x["Net Amount"]) if safe_float(x["Net Amount"]) != 0
        else (safe_float(x["Gross Amount"]) - safe_float(x["Discount Amount"])
              + safe_float(x["IGST Amount"]) + safe_float(x["CGST Amount"]) + safe_float(x["SGST Amount"])),
        axis=1
    )

    # Step 8: Auto-calc % if amount available but % missing
    for tax in ["IGST", "CGST", "SGST", "Discount"]:
        df[f"{tax}%"] = df.apply(
            lambda x: safe_float(x[f"{tax}%"]) if safe_float(x[f"{tax}%"]) != 0
            else (safe_float(x[f"{tax} Amount"]) * 100 / safe_float(x["Gross Amount"])
                  if safe_float(x["Gross Amount"]) else 0),
            axis=1
        )

    return df[EXPECTED_COLUMNS]
