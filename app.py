import streamlit as st
import pandas as pd
import pdfplumber
from extractor import parse_invoice

st.set_page_config(page_title="Invoice Extractor", layout="wide")
st.title("📑 PDF Invoice Extractor")

uploaded_file = st.file_uploader("Upload Invoice PDF", type=["pdf"])

if uploaded_file:
    with pdfplumber.open(uploaded_file) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"

    # Extract structured data
    df, meta = parse_invoice(text)

    st.subheader("Extracted Invoice Details")
    st.json(meta)

    st.subheader("Invoice Line Items")
    st.dataframe(df, use_container_width=True)

    # Export buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("⬇ Export to CSV"):
            df.to_csv("outputs/invoice_data.csv", index=False)
            st.success("Exported to outputs/invoice_data.csv ✅")

    with col2:
        if st.button("⬇ Export to Excel"):
            df.to_excel("outputs/invoice_data.xlsx", index=False)
            st.success("Exported to outputs/invoice_data.xlsx ✅")

    with col3:
        if st.button("⬇ Export to PDF"):
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
            from reportlab.lib import colors

            pdf_file = "outputs/invoice_data.pdf"
            doc = SimpleDocTemplate(pdf_file)
            table_data = [df.columns.to_list()] + df.values.tolist()
            table = Table(table_data)
            style = TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ])
            table.setStyle(style)
            doc.build([table])
            st.success("Exported to outputs/invoice_data.pdf ✅")
