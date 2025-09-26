import pdfplumber
import pandas as pd

from math import isnan

# (Keep the same HEADER_MAP and normalize_headers as in the last version)

def extract_table_from_pdf(pdf_path: str) -> pd.DataFrame:
    """Extract tables from PDF invoices using pdfplumber"""
    all_tables = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if table:
                    df = pd.DataFrame(table[1:], columns=table[0])

                    # handle missing headers
                    if df.columns.isnull().any():
                        df.columns = [
                            f"Unnamed_{i}" if col is None else col
                            for i, col in enumerate(df.columns)
                        ]

                    df = normalize_headers(df)
                    all_tables.append(df)

    if all_tables:
        return pd.concat(all_tables, ignore_index=True)
    else:
        return pd.DataFrame()  # empty if no tables found


def auto_calculate_missing(df: pd.DataFrame) -> pd.DataFrame:
    """
    Auto calculate missing financial values:
    - Gross Amount = Quantity * Rate
    - Discount Amount = Gross * (Discount% / 100)
    - IGST/CGST/SGST Amount = (Net before tax * % / 100)
    - Net Amount = Gross - Discount + Taxes
    """
    # Ensure numeric
    for col in ["Quantity", "Rate", "Gross Amount", "Discount%", "Discount Amount",
                "IGST%", "IGST Amount", "CGST%", "CGST Amount",
                "SGST%", "SGST Amount", "Net Amount"]:
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
                (df["Gross Amount"] * df["Discount%"] / 100)
            )

    # IGST Amount
    if "IGST Amount" in df.columns and df["IGST Amount"].isnull().any():
        if "IGST%" in df.columns:
            df["IGST Amount"] = df["IGST Amount"].fillna(
                (df["Gross Amount"] - df.get("Discount Amount", 0)) * df["IGST%"] / 100
            )

    # CGST Amount
    if "CGST Amount" in df.columns and df["CGST Amount"].isnull().any():
        if "CGST%" in df.columns:
            df["CGST Amount"] = df["CGST Amount"].fillna(
                (df["Gross Amount"] - df.get("Discount Amount", 0)) * df["CGST%"] / 100
            )

    # SGST Amount
    if "SGST Amount" in df.columns and df["SGST Amount"].isnull().any():
        if "SGST%" in df.columns:
            df["SGST Amount"] = df["SGST Amount"].fillna(
                (df["Gross Amount"] - df.get("Discount Amount", 0)) * df["SGST%"] / 100
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
