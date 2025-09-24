import re
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
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

def clean_number(value):
    """Remove symbols like ₹, %, commas and convert to float"""
    if not value:
        return 0.0
    return float(re.sub(r"[^\d.]", "", str(value)) or 0)

def calculate_dynamic_fields(item):
    """Auto calculate missing % or Amount for GST & Discount"""

    gross = item.get("Gross Amount", 0)
    net = item.get("Net Amount", 0)

    # Discount
    if item["Discount(%)"] == 0 and item["Discount Amount"] > 0:
        item["Discount(%)"] = round((item["Discount Amount"] / gross) * 100, 2)
    elif item["Discount Amount"] == 0 and item["Discount(%)"] > 0:
        item["Discount Amount"] = round((item["Discount(%)"] / 100) * gross, 2)

    # IGST
    if item["IGST(%)"] == 0 and item["IGST Amount"] > 0:
        item["IGST(%)"] = round((item["IGST Amount"] / gross) * 100, 2)
    elif item["IGST Amount"] == 0 and item["IGST(%)"] > 0:
        item["IGST Amount"] = round((item["IGST(%)"] / 100) * gross, 2)

    # CGST
    if item["CGST(%)"] == 0 and item["CGST Amount"] > 0:
        item["CGST(%)"] = round((item["CGST Amount"] / gross) * 100, 2)
    elif item["CGST Amount"] == 0 and item["CGST(%)"] > 0:
        item["CGST Amount"] = round((item["CGST(%)"] / 100) * gross, 2)

    # SGST
    if item["SGST(%)"] == 0 and item["SGST Amount"] > 0:
        item["SGST(%)"] = round((item["SGST Amount"] / gross) * 100, 2)
    elif item["SGST Amount"] == 0 and item["SGST(%)"] > 0:
        item["SGST Amount"] = round((item["SGST(%)"] / 100) * gross, 2)

    # Recalculate Net Amount if missing
    if net == 0:
        item["Net Amount"] = gross - item["Discount Amount"] + item["IGST Amount"] + item["CGST Amount"] + item["SGST Amount"]

    return item

def process_file(file_path):
    if file_path.lower().endswith(".pdf"):
        text = extract_text_from_pdf(file_path)
    else:
        text = extract_text_from_image(file_path)

    data = []
    # Extract invoice metadata
    invoice_no = re.search(r"Invoice\s*No[:\-]?\s*(\S+)", text, re.IGNORECASE)
    supplier_gstin = re.search(r"Supplier\s*GSTIN[:\-]?\s*(\S+)", text, re.IGNORECASE)
    customer_gstin = re.search(r"Customer\s*GSTIN[:\-]?\s*(\S+)", text, re.IGNORECASE)

    # Dummy example line item (replace with actual parsing logic)
    item = {
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
        "IGST Amount": 0,  # Will be auto-calculated
        "CGST(%)": 0,
        "CGST Amount": 0,
        "SGST(%)": 0,
        "SGST Amount": 0,
        "Net Amount": 0
    }

    # Apply dynamic calculation
    item = calculate_dynamic_fields(item)

    data.append(item)
    return data
