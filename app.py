import streamlit as st
import pandas as pd
import pdfplumber
import os
from extractor import parse_invoice

st.set_page_config(page_title="Invoice Extractor", layout="wide")
st.title("Invoice Extractor")

# Ensure outputs folder exists
os.makedirs("outputs", exist_ok=True)

uploaded_files = st.file_uploader(
    "Upload Invoice PDF(s)", type=["pdf"], accept_multiple_files=True
)

if uploaded_files:
    all_data = []

    for uploaded_file in uploaded_files:
        with pdfplumber.open(uploaded_file) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"

        df = parse_invoice(text)
        all_data.append(df)

    # Combine all invoices
    final_df = pd.concat(all_data, ignore_index=True)

    st.subheader("Invoice Line Items")
    st.dataframe(final_df, use_container_width=True)

    # Export buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("⬇ Export to CSV"):
            final_df.to_csv("outputs/invoice_data.csv", index=False)
            st.success("Exported to outputs/invoice_data.csv ✅")

    with col2:
        if st.button("⬇ Export to Excel"):
            final_df.to_excel("outputs/invoice_data.xlsx", index=False)
            st.success("Exported to outputs/invoice_data.xlsx ✅")

    with col3:
        if st.button("⬇ Export to PDF"):
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
            from reportlab.lib import colors

            pdf_file = "outputs/invoice_data.pdf"
            doc = SimpleDocTemplate(pdf_file)
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
            st.success("Exported to outputs/invoice_data.pdf ✅")
