# Invoice Extractor

A Python tool to extract invoice data from **multiple PDF files**, normalize headers, 
auto-calculate missing values, and export results to Excel.

## Features
- Supports multiple PDFs at once.
- Normalizes different header names using `HEADER_MAP`.
- Auto-calculates missing values:
  - Gross = Quantity × Rate
  - Discount Amount from Discount %
  - IGST / CGST / SGST from %
  - Net Amount = Gross – Discount + Taxes
- Exports consolidated data to `merged_output.xlsx`.

## Installation
```bash
pip install -r requirements.txt
