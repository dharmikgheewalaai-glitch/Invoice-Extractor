import streamlit as st
import pandas as pd
import pdfplumber
from extractor import parse_invoice
from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

st.set_page_config(page_title="Invoice Extractor", layout="wide")
st.title("Invoice Extractor")

uploaded_files = st.file_uploader(
    "Upload Invoice PDFs", type=["pdf"], accept_multiple_files=True
)

def create_pdf(df):
    """Generate PDF file (table format) from dataframe"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    data = [df.columns.tolist()] + df.astype(str).values.tolist()
    table = Table(data, repeatRows=1)

    style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
    ])
    table.setStyle(style)

    doc.build([table])
    buffer.seek(0)
    return buffer

if uploaded_files:
    all_data = []

    for uploaded_file in uploaded_files:
        with pdfplumber.open(uploaded_file) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""

            df = parse_invoice(pdf, text, uploaded_file.name)
            all_data.append(df)

    final_df = pd.concat(all_data, ignore_index=True)

    st.subheader("Extracted Invoice Data")
    st.dataframe(final_df, use_container_width=True)

    # ----------------------------
    # Downloads in one row
    # ----------------------------
    excel_buffer = BytesIO()
    final_df.to_excel(excel_buffer, index=False, engine="openpyxl")

    csv_data = final_df.to_csv(index=False).encode("utf-8")
    pdf_buffer = create_pdf(final_df)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button(
            "Download Excel File",
            data=excel_buffer.getvalue(),
            file_name="invoices.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    with col2:
        st.download_button(
            "Download CSV File",
            data=csv_data,
            file_name="invoices.csv",
            mime="text/csv",
        )

    with col3:
        st.download_button(
            "Download PDF File",
            data=pdf_buffer,
            file_name="invoices.pdf",
            mime="application/pdf",
        )
