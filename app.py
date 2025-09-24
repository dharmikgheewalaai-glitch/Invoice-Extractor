import streamlit as st
import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
from io import BytesIO
from extractor import parse_invoice

st.set_page_config(page_title="Invoice Extractor", layout="wide")
st.title("GST Invoice Extractor")

uploaded_files = st.file_uploader(
    "Upload Invoice PDF(s) or Image(s)", 
    type=["pdf", "jpg", "jpeg", "png"], 
    accept_multiple_files=True
)

if uploaded_files:
    all_data = []

    for uploaded_file in uploaded_files:
        file_type = uploaded_file.type

        text = ""
        pdf_obj = None

        if "pdf" in file_type:
            pdf_obj = pdfplumber.open(uploaded_file)
            for page in pdf_obj.pages:
                page_text = page.extract_text()
                if not page_text:
                    # OCR for scanned PDF page
                    images = convert_from_bytes(uploaded_file.read())
                    for img in images:
                        ocr_text = pytesseract.image_to_string(img)
                        text += ocr_text + "\n"
                else:
                    text += page_text + "\n"

        elif "image" in file_type or file_type in ["image/jpeg", "image/png"]:
            image = Image.open(uploaded_file)
            text = pytesseract.image_to_string(image)

        df = parse_invoice(pdf_obj, text, uploaded_file.name)
        all_data.append(df)

    final_df = pd.concat(all_data, ignore_index=True)

    # enforce column order
    column_order = [
        "Invoice No", "Supplier GSTIN", "Customer GSTIN", "Source File",
        "HSN", "Item Name", "Quantity", "Rate", "Gross Amount",
        "Discount(%)", "Discount Amount",
        "IGST(%)", "IGST Amount",
        "CGST(%)", "CGST Amount",
        "SGST(%)", "SGST Amount",
        "Net Amount"
    ]
    for col in column_order:
        if col not in final_df.columns:
            final_df[col] = None
    final_df = final_df[column_order]

    st.subheader("Extracted Invoice Data")
    st.dataframe(final_df, use_container_width=True)

    # ---- Download options ----
    csv = final_df.to_csv(index=False).encode("utf-8")

    excel_buffer = BytesIO()
    final_df.to_excel(excel_buffer, index=False, engine="openpyxl")
    excel_data = excel_buffer.getvalue()

    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
    from reportlab.lib import colors
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer)
    table_data = [final_df.columns.to_list()] + final_df.values.tolist()
    table = Table(table_data)
    style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ])
    table.setStyle(style)
    doc.build([table])
    pdf_data = pdf_buffer.getvalue()

    st.download_button("⬇ Download CSV", csv, "invoice_data.csv", "text/csv")
    st.download_button("⬇ Download Excel", excel_data, "invoice_data.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.download_button("⬇ Download PDF", pdf_data, "invoice_data.pdf", "application/pdf")
