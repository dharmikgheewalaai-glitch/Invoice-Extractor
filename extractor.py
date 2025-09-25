import pdfplumber
import pandas as pd
import re

# ---------- Utility ----------
def safe_float(val):
    try:
        if val is None or str(val).strip() == "":
            return 0.0
        return float(str(val).replace(",", "").strip())
    except:
        return 0.0

def extract_number_from_text(text, keyword):
    """Finds a number near a keyword in invoice text."""
    pattern = rf"{keyword}\s*[:\-]?\s*([\d,]+\.?\d*)"
    match = re.search(pattern, text, re.I)
    return safe_float(match.group(1)) if match else 0.0

# ---------- Header Mapping ----------
HEADER_MAP = {
    "invoice no": "Invoice No",
    "invoice number": "Invoice No",
    "supplier gstin": "Supplier GSTIN",
    "customer gstin": "Customer GSTIN",
    "gstin": "Customer GSTIN",
    "source file": "Source File",
    "hsn": "HSN",
    "item": "Item Name",
    "item name": "Item Name",
    "description": "Item Name",
    "qty": "Quantity",
    "quantity": "Quantity",
    "rate": "Rate",
    "price": "Rate",
    "gross": "Gross Amount",
    "gross amount": "Gross Amount",
    "subtotal": "Gross Amount",
    "discount%": "Discount(%)",
    "discount (%)": "Discount(%)",
    "disc%": "Discount(%)",
    "discount amount": "Discount Amount",
    "igst%": "IGST(%)",
    "igst": "IGST Amount",
    "igst amount": "IGST Amount",
    "cgst%": "CGST(%)",
    "cgst": "CGST Amount",
    "cgst amount": "CGST Amount",
    "sgst%": "SGST(%)",
    "sgst": "SGST Amount",
    "sgst amount": "SGST Amount",
    "net": "Net Amount",
    "net amount": "Net Amount",
    "total": "Net Amount",
    "grand total": "Net Amount",
}

def normalize_headers(columns):
    return [HEADER_MAP.get(str(col).strip().lower(), col) for col in columns]

# ---------- Fill Missing ----------
def fill_missing_from_text(df, text):
    """Fill numeric columns if they are zero, using regex on raw text."""
    for idx, row in df.iterrows():
        if safe_float(row.get("Gross Amount", 0)) == 0:
            df.at[idx, "Gross Amount"] = extract_number_from_text(text, "Gross Amount|Subtotal|Total Value")

        if safe_float(row.get("Discount Amount", 0)) == 0:
            df.at[idx, "Discount Amount"] = extract_number_from_text(text, "Discount")

        if safe_float(row.get("IGST Amount", 0)) == 0:
            df.at[idx, "IGST Amount"] = extract_number_from_text(text, "IGST")

        if safe_float(row.get("CGST Amount", 0)) == 0:
            df.at[idx, "CGST Amount"] = extract_number_from_text(text, "CGST")

        if safe_float(row.get("SGST Amount", 0)) == 0:
            df.at[idx, "SGST Amount"] = extract_number_from_text(text, "SGST")

        if safe_float(row.get("Net Amount", 0)) == 0:
            df.at[idx, "Net Amount"] = extract_number_from_text(text, "Net Amount|Grand Total|Invoice Total")
    return df

# ---------- Main Parser ----------
def parse_invoice(pdf, text, source_file=""):
    with pdfplumber.open(pdf) as pdf_file:
        tables = []
        for page in pdf_file.pages:
            tables.extend(page.extract_tables())

    df_list = []
    for table in tables:
        if not table:
            continue
        df = pd.DataFrame(table[1:], columns=normalize_headers(table[0]))
        df_list.append(df)

    if not df_list:
        return pd.DataFrame()

    df = pd.concat(df_list, ignore_index=True)

    # Ensure expected columns
    for col in [
        "Invoice No", "Supplier GSTIN", "Customer GSTIN", "Source File", "HSN",
        "Item Name", "Quantity", "Rate", "Gross Amount", "Discount(%)",
        "Discount Amount", "IGST(%)", "IGST Amount", "CGST(%)", "CGST Amount",
        "SGST(%)", "SGST Amount", "Net Amount"
    ]:
        if col not in df.columns:
            df[col] = 0

    # Convert numerics
    num_cols = [
        "Quantity", "Rate", "Gross Amount", "Discount(%)", "Discount Amount",
        "IGST(%)", "IGST Amount", "CGST(%)", "CGST Amount",
        "SGST(%)", "SGST Amount", "Net Amount"
    ]
    for col in num_cols:
        df[col] = df[col].apply(safe_float)

    # ---------- Auto-calculations ----------
    df["Gross Amount"] = df.apply(
        lambda x: x["Quantity"] * x["Rate"] if x["Gross Amount"] == 0 else x["Gross Amount"],
        axis=1,
    )

    df["Discount Amount"] = df.apply(
        lambda x: (x["Gross Amount"] * x["Discount(%)"] / 100)
        if x["Discount Amount"] == 0 and x["Discount(%)"] > 0
        else x["Discount Amount"],
        axis=1,
    )

    for tax in ["IGST", "CGST", "SGST"]:
        df[f"{tax} Amount"] = df.apply(
            lambda x: (x["Gross Amount"] - x["Discount Amount"]) * x[f"{tax}(%)"] / 100
            if x[f"{tax} Amount"] == 0 and x[f"{tax}(%)"] > 0
            else x[f"{tax} Amount"],
            axis=1,
        )

    df["Net Amount"] = df.apply(
        lambda x: (x["Gross Amount"] - x["Discount Amount"]
                   + x["IGST Amount"] + x["CGST Amount"] + x["SGST Amount"])
        if x["Net Amount"] == 0 else x["Net Amount"],
        axis=1,
    )

    # Fill missing using text
    df = fill_missing_from_text(df, text)

    # Add source file info
    df["Source File"] = source_file

    return df
