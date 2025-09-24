import streamlit as st
import pandas as pd
import pdfplumber
from io import BytesIO
from extractor import parse_invoice
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

st.set_page_config(page_title="Invoice Extractor", layout="wide")
st.header("Invoice Extractor")

uploaded_files = st.file_uploader(
    "Upload Invoice PDF(s)", type=["pdf"], accept_multiple_files=True
)

if uploaded_files:
    all_data = []

    for uploaded_file in uploaded_files:
        with pdfplumber.open(uploaded_file) as pdf:
            text = ""
            for page in pdf.pages:
                text += (page.extract_text() or "") + "\n"

            df = parse_invoice(pdf, text, uploaded_file.name)
            all_data.append(df)

    # Combine
    final_df = pd.concat(all_data, ignore_index=True)

    # Final column order
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

    # Download CSV
    csv = final_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇ Download CSV", csv, "invoice_data.csv", "text/csv")

    # Download Excel
    excel_buffer = BytesIO()
    final_df.to_excel(excel_buffer, index=False, engine="openpyxl")
    st.download_button(
        "⬇ Download Excel",
        excel_buffer.getvalue(),
        "invoice_data.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Download PDF
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer)
    table_data = [final_df.columns.to_list()] + final_df.values.tolist()
    table = Table(table_data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))
    doc.build([table])
    st.download_button("⬇ Download PDF", pdf_buffer.getvalue(), "invoice_data.pdf", "application/pdf")
