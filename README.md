# GST Invoice Extractor 📑

A Streamlit-based tool to extract **invoice line items** from PDF invoices and export them into **CSV, Excel, and PDF**.

## 🚀 Features
- Upload **one or multiple invoice PDFs**
- Extract fields:
  - Invoice No  
  - Supplier GSTIN  
  - Customer GSTIN  
  - Source File  
  - HSN  
  - Item Name  
  - Quantity  
  - Rate  
  - Gross Amount  
  - Discount(%) / Discount Amount  
  - IGST(%), IGST Amount  
  - CGST(%), CGST Amount  
  - SGST(%), SGST Amount  
  - Net Amount  
- Auto-calculates GST % or Amount if missing
- Normalizes invoice headers (`Bill No` → `Invoice No`, `Taxable Value` → `Gross Amount`, etc.)
- Export final data to **CSV, Excel, PDF**

## 📦 Installation
```bash
pip install -r requirements.txt
