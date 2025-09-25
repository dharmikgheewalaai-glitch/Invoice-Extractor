import pdfplumber
import pandas as pd
import re
import os

# ✅ Header mapping (covers all variants)
HEADER_MAP = {
    "Invoice No": ["invoice no", "inv no", "bill no", "invoice number"],
    "Supplier GSTIN": ["supplier gstin", "from gstin", "seller gstin"],
    "Customer GSTIN": ["customer gstin", "to gstin", "buyer gstin"],
    "Source File": ["source file"],

    "HSN": ["hsn", "hsn code"],
    "Item Name": ["item", "description", "product", "item name", "particulars"],
    "Quantity": ["qty", "quantity", "qnty"],
    "Rate": ["rate", "price", "unit price", "per unit"],
    "Gross Amount": ["gross", "amount", "total", "taxable value", "line total"],

    "Discount%": ["discount%", "disc%", "discount percent"],
    "Discount Amount": ["discount", "disc amt", "discount amount"],

    "IGST%": ["igst%", "igst rate"],
    "IGST Amount": ["igst", "igst amount"],
    "CGST%": ["cgst%", "cgst rate"],
    "CGST Amount": ["cgst", "cgst amount"],
    "SGST%": ["sgst%", "sgst rate"],
    "SGST Amount": ["sgst", "sgst amount"],

    "Net Amount": ["net", "total amount", "grand total", "net amount", "invoice total"]
}

# ✅ Utility: clean numeric values
def clean_numeric(val):
    try:
        if val in [None, "", " "]:
            return 0.0
        return float(str(val).replace(",", "").replace("₹", "").replace("Rs.", "").strip())
    except:
        return 0.0

# ✅ Normalize headers
def normalize_header(h):
    return re.sub(r"[^a-z0-9]", "", str(h).strip().lower())

# ✅ Match headers with HEADER_MAP
def map_headers(columns):
    mapped = {}
    for col in columns:
        norm = normalize_header(col)
        mapped_name = None
        for key, variants in HEADER_MAP.items():
            for v in variants:
                if normalize_header(v) == norm:
                    mapped_name = key
                    break
            if mapped_name:
                break
        if mapped_name:
            mapped[col] = mapped_name
        else:
            mapped[col] = col  # keep as is if not mapped
    return mapped

# ✅ Auto recalc logic
def recalc_values(df):
    # Ensure numeric conversion
    for col in ["Quantity", "Rate", "Gross Amount", "Discount%", "Discount Amount",
                "IGST%", "IGST Amount", "CGST%", "CGST Amount", "SGST%", "SGST Amount", "Net Amount"]:
        if col in df.columns:
            df[col] = df[col].apply(clean_numeric)

    # Gross = Qty * Rate
    if "Quantity" in df.columns and "Rate" in df.columns:
        df["Gross Amount"] = df.apply(
            lambda x: x["Quantity"] * x["Rate"] if x["Gross Amount"] == 0 else x["Gross Amount"], axis=1
        )

    # Discount Amount & %
    if "Discount%" in df.columns and "Discount Amount" in df.columns:
        df["Discount Amount"] = df.apply(
            lambda x: (x["Gross Amount"] * x["Discount%"] / 100)
            if (x["Discount Amount"] == 0 and x["Discount%"] > 0) else x["Discount Amount"], axis=1
        )
        df["Discount%"] = df.apply(
            lambda x: (x["Discount Amount"] / x["Gross Amount"] * 100)
            if (x["Discount%"] == 0 and x["Gross Amount"] > 0) else x["Discount%"], axis=1
        )

    taxable = df["Gross Amount"] - df["Discount Amount"]

    # Tax % and Amounts
    for tax in ["IGST", "CGST", "SGST"]:
        if f"{tax}%" in df.columns and f"{tax} Amount" in df.columns:
            df[f"{tax} Amount"] = df.apply(
                lambda x: (taxable.loc[x.name] * x[f"{tax}%"] / 100)
                if (x[f"{tax} Amount"] == 0 and x[f"{tax}%"] > 0) else x[f"{tax} Amount"], axis=1
            )
            df[f"{tax}%"] = df.apply(
                lambda x: (x[f"{tax} Amount"] / taxable.loc[x.name] * 100)
                if (x[f"{tax}%"] == 0 and taxable.loc[x.name] > 0) else x[f"{tax}%"], axis=1
            )

    # Net Amount
    if all(col in df.columns for col in ["Gross Amount", "Discount Amount", "IGST Amount", "CGST Amount", "SGST Amount"]):
        df["Net Amount"] = df.apply(
            lambda x: x["Gross Amount"] - x["Discount Amount"] + x["IGST Amount"] + x["CGST Amount"] + x["SGST Amount"]
            if x["Net Amount"] == 0 else x["Net Amount"], axis=1
        )

    return df

# ✅ Main function
def parse_invoice(pdf, text, source_file):
    all_data = []

    with pdfplumber.open(pdf) as pdf_file:
        for page in pdf_file.pages:
            table = page.extract_table()
            if table:
                headers = table[0]
                mapped_headers = map_headers(headers)

                df = pd.DataFrame(table[1:], columns=headers)
                df = df.rename(columns=mapped_headers)

                # Ensure all expected columns exist
                for col in HEADER_MAP.keys():
                    if col not in df.columns:
                        df[col] = 0

                df["Source File"] = source_file
                df = recalc_values(df)

                all_data.append(df)

    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
    else:
        # If no table found, return empty structured DataFrame
        final_df = pd.DataFrame(columns=list(HEADER_MAP.keys()))

    return final_df
