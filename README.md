# 📑 Invoice Extractor

A Streamlit app to extract **structured invoice data** from PDF invoices and export results to **CSV, Excel, or PDF**.

---

## 🚀 Features
- Upload one or multiple PDF invoices
- Extracts tables directly from invoices
- Normalizes headers (HSN, Item, Quantity, Rate, Amounts, Taxes, etc.)
- Extracts **Invoice No, Supplier GSTIN, Customer GSTIN**
- Adds **Source File** column (if multiple PDFs uploaded)
- Cleans numeric fields (removes ₹, %, commas)
- Export results to:
  - CSV
  - Excel
  - PDF

---

## ⚙️ Setup & Run
```bash
git clone https://github.com/your-username/invoice-extractor.git
cd invoice-extractor
pip install -r requirements.txt
streamlit run app.py
