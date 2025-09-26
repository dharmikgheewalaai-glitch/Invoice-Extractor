import pdfplumber
import pandas as pd

# -------------------------------
# Header Normalization Map
# -------------------------------
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

# -------------------------------
# Normalize Headers
# -------------------------------
def normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    new_cols = []
    for col in df.columns:
        if col is None:
            new_cols.append("Unnamed")
            continue
        key = str(col).strip().lower()
        mapped = HEADER_MAP.get(key, col)
        new_cols.append(mapped)
    df.columns = new_cols
    return df

# -------------------------------
# Extract Tables
# -------------------------------
def extract_table_from_pdf(pdf_path: str) -> pd.DataFrame:
    all_tables = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if table:
                    df = pd.DataFrame(table[1:], columns=table[0])
                    df = normalize_headers(df)
                    all_tables.append(df)

    return pd.concat(all_tables, ignore_index=True) if all_tables else pd.DataFrame()

# -------------------------------
# Auto Calculate Missing Values
# -------------------------------
def auto_calculate_missing(df: pd.DataFrame) -> pd.DataFrame:
    numeric_cols = [
        "Quantity", "Rate", "Gross Amount",
        "Discount%", "Discount Amount",
        "IGST%", "IGST Amount",
        "CGST%", "CGST Amount",
        "SGST%", "SGST Amount",
        "Net Amount"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Gross Amount
    if "Gross Amount" in df.columns and df["Gross Amount"].isnull().any():
        if "Quantity" in df.columns and "Rate" in df.columns:
            df["Gross Amount"] = df["Gross Amount"].fillna(df["Quantity"] * df["Rate"])

    # Discount Amount
    if "Discount Amount" in df.columns and df["Discount Amount"].isnull().any():
        if "Discount%" in df.columns:
            df["Discount Amount"] = df["Discount Amount"].fillna(
                df["Gross Amount"] * (df["Discount%"] / 100)
            )

    # IGST Amount
    if "IGST Amount" in df.columns and df["IGST Amount"].isnull().any():
        if "IGST%" in df.columns:
            df["IGST Amount"] = df["IGST Amount"].fillna(
                (df["Gross Amount"] - df.get("Discount Amount", 0)) * (df["IGST%"] / 100)
            )

    # CGST Amount
    if "CGST Amount" in df.columns and df["CGST Amount"].isnull().any():
        if "CGST%" in df.columns:
            df["CGST Amount"] = df["CGST Amount"].fillna(
                (df["Gross Amount"] - df.get("Discount Amount", 0)) * (df["CGST%"] / 100)
            )

    # SGST Amount
    if "SGST Amount" in df.columns and df["SGST Amount"].isnull().any():
        if "SGST%" in df.columns:
            df["SGST Amount"] = df["SGST Amount"].fillna(
                (df["Gross Amount"] - df.get("Discount Amount", 0)) * (df["SGST%"] / 100)
            )

    # Net Amount
    if "Net Amount" in df.columns and df["Net Amount"].isnull().any():
        df["Net Amount"] = df["Net Amount"].fillna(
            df["Gross Amount"].fillna(0)
            - df.get("Discount Amount", 0).fillna(0)
            + df.get("IGST Amount", 0).fillna(0)
            + df.get("CGST Amount", 0).fillna(0)
            + df.get("SGST Amount", 0).fillna(0)
        )

    return df
