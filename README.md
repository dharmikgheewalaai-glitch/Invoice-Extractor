# GST Invoice Extractor

A Streamlit app to extract invoice data (HSN, GST, quantities, taxes, totals, etc.)
from **PDF invoices** (text & scanned) and **image invoices** (JPG/PNG).
Exports are available in **CSV, Excel, and PDF**.

---

## 🚀 Features
- Extracts:
  - Invoice No
  - Supplier GSTIN
  - Customer GSTIN
  - Item details (HSN, Quantity, Rate, Tax, etc.)
- Handles:
  - Normal PDFs with text
  - Scanned PDFs (OCR using Tesseract)
  - Image invoices (JPG, PNG)
- Auto-calculates missing % or Amount for Discount/IGST/CGST/SGST
- Download results as CSV, Excel, or PDF

---

## 📦 Installation
```bash
pip install -r requirements.txt
