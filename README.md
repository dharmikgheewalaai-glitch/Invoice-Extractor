# Invoice Extractor

A simple Streamlit app to extract key details from **GST Invoices (PDF only)**  
and export them into **Excel, CSV, or PDF**.

---

## Features
- Upload one or multiple invoice PDFs
- Extracts:
  - Invoice No
  - Supplier GSTIN
  - Customer GSTIN
  - HSN, Item Name, Quantity, Rate
  - Gross Amount, Discounts
  - IGST, CGST, SGST (% and Amounts)
  - Net Amount
- GST values without `%` → treated as **Amount**
- Download results as **Excel, CSV, or PDF**

---

## Installation
```bash
git clone https://github.com/yourusername/invoice-extractor.git
cd invoice-extractor
pip install -r requirements.txt
