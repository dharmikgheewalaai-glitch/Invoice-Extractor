import pdfplumber
import pandas as pd

# ✅ Extended Header Map
HEADER_MAP = {
    # Invoice No
    "invoice no": "Invoice No", "invoice #": "Invoice No", "inv. no.": "Invoice No",
    "bill no": "Invoice No", "voucher no": "Invoice No", "document no": "Invoice No",
    # Supplier GSTIN
    "supplier gstin": "Supplier GSTIN", "seller gstin": "Supplier GSTIN",
    "vendor gstin": "Supplier GSTIN", "supplier gst no": "Supplier GSTIN",
    "seller tax id": "Supplier GSTIN", "vendor tax id": "Supplier GSTIN",
    # Customer GSTIN
    "customer gstin": "Customer GSTIN", "buyer gstin": "Customer GSTIN",
    "client gstin": "Customer GSTIN", "recipient gstin": "Customer GSTIN",
    "customer gst no": "Customer GSTIN", "buyer tax id": "Customer GSTIN",
    # Source File
    "source file": "Source File", "upload name": "Source File",
    "source document": "Source File", "file reference": "Source File",
    "document source": "Source File", "file path": "Source File",
    # HSN
    "hsn": "HSN", "hsn code": "HSN", "hsn/sac": "HSN",
    "hsn code no": "HSN", "hsn classification": "HSN",
    "hsn/sac code": "HSN", "harmonized code": "HSN",
    # Item Name
    "item": "Item Name", "item name": "Item Name", "description": "Item Name",
    "product": "Item Name", "product name": "Item Name",
    "service name": "Item Name", "goods/service description": "Item Name",
    "material name": "Item Name", "particulars": "Item Name",
    "item description": "Item Name", "product details": "Item Name",
    # Quantity
    "qty": "Quantity", "quantity": "Quantity", "no. of units": "Quantity",
    "nos.": "Quantity", "packets": "Quantity", "pcs": "Quantity",
    "units": "Quantity", "order quantity": "Quantity",
    # Rate
    "rate": "Rate", "price": "Rate", "unit cost": "Rate",
    "unit price": "Rate", "per unit rate": "Rate", "selling price": "Rate",
    "unit value": "Rate", "rate per item": "Rate",
    # Gross Amount
    "gross amount": "Gross Amount", "total value": "Gross Amount",
    "total before tax": "Gross Amount", "amount before tax": "Gross Amount",
    "subtotal": "Gross Amount", "line total": "Gross Amount",
    # Discount %
    "discount%": "Discount%", "discount": "Discount%",
    "disc%": "Discount%", "rebate %": "Discount%",
    "offer %": "Discount%", "deduction %": "Discount%",
    "allowance %": "Discount%",
    # Discount Amount
    "discount amount": "Discount Amount", "disc amt": "Discount Amount",
    "rebate amount": "Discount Amount", "deduction value": "Discount Amount",
    "offer amount": "Discount Amount", "concession": "Discount Amount",
    "discounted amount": "Discount Amount", "total discount": "Discount Amount",
    # IGST %
    "igst%": "IGST%", "igst rate %": "IGST%", "integrated tax %": "IGST%",
    "igst duty %": "IGST%", "int. gst %": "IGST%",
    # IGST Amount
    "igst amount": "IGST Amount", "igst value": "IGST Amount",
    "integrated tax amount": "IGST Amount", "igst duty amount": "IGST Amount",
    "igst charges": "IGST Amount", "igst total": "IGST Amount", "igst": "IGST Amount",
    # CGST %
    "cgst%": "CGST%", "cgst rate %": "CGST%", "central tax %": "CGST%",
    "c. gst %": "CGST%", "central gst rate": "CGST%",
    # CGST Amount
    "cgst amount": "CGST Amount", "cgst value": "CGST Amount",
    "central tax amount": "CGST Amount", "cgst charges": "CGST Amount",
    "cgst duty amount": "CGST Amount", "cgst total": "CGST Amount", "cgst": "CGST Amount",
    # SGST %
    "sgst%": "SGST%", "sgst rate %": "SGST%", "state tax %": "SGST%",
    "s. gst %": "SGST%", "state gst rate": "SGST%",
    # SGST Amount
    "sgst amount": "SGST Amount", "sgst value": "SGST Amount",
    "state tax amount": "SGST Amount", "sgst charges": "SGST Amount",
    "sgst duty amount": "SGST Amount", "sgst total": "SGST Amount", "sgst": "SGST Amount",
    # Net Amount
    "net amount": "Net Amount", "grand total": "Net Amount",
    "invoice total": "Net Amount", "total payable": "Net Amount",
    "amount due": "Net Amount", "final total": "Net Amount",
}

def normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    """Rename dataframe columns using HEADER_MAP"""
    new_columns = {}
    for col in df.columns:
        key = col.strip().lower()
        new_columns[col] = HEADER_MAP.get(key, col)
    df = df.rename(columns=new_columns)
    return df

def extract_table_from_pdf(pdf_path: str) -> pd.DataFrame:
    """Extract tables from PDF invoices using pdfplumber"""
    all_tables = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if table:
                    df = pd.DataFrame(table[1:], columns=table[0])
                    df = normalize_headers(df)
                    all_tables.append(df)

    if all_tables:
        return pd.concat(all_tables, ignore_index=True)
    else:
        return pd.DataFrame()  # empty if no tables found
