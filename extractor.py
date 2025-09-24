import re
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import pandas as pd
import io

def extract_text_from_pdf(file_path):
    text = ""
    doc = fitz.open(file_path)
    for page in doc:
        text += page.get_text()
    if not text.strip():
        # OCR for scanned PDFs
        for page in doc:
            pix = page.get_pixmap()
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            text += pytesseract.image_to_string(img)
    return text

def extract_text_from_image(file_path):
    img = Image.open(file_path)
    return pytesseract.image_to_string(img)

def process_file(file_path):
    if file_path.lower().endswith(".pdf"):
        text = extract_text_from_pdf(file_path)
    else:
        text = extract_text_from_image(file_path)

    data = []
    # Example parsing logic (very simplified)
    invoice_no = re.search(r"Invoice\s*No[:\-]?\s*(\S+)", text, re.IGNORECASE)
    supplier_gstin = re.search(r"Supplier\s*GSTIN[:\-]?\s*(\S+)", text, re.IGNORECASE)
    customer_gstin = re.search(r"Customer\s*GSTIN[:\-]?\s*(\S+)", text, re.IGNORECASE)

    # Dummy line item (in real use: parse tables properly)
    data.append({
        "Invoice No": invoice_no.group(1) if invoice_no else "",
        "Supplier GSTIN": supplier_gstin.group(1) if supplier_gstin else "",
        "Customer GSTIN": customer_gstin.group(1) if customer_gstin else "",
        "HSN": "1234",
        "Item Name": "Sample Item",
        "Quantity": 1,
        "Rate": 100,
        "Gross Amount": 100,
        "Discount(%)": 0,
        "Discount Amount": 0,
        "IGST(%)": 18,
        "IGST Amount": 18,
        "CGST(%)": 0,
        "CGST Amount": 0,
        "SGST(%)": 0,
        "SGST Amount": 0,
        "Net Amount": 118
    })
    return data
