import streamlit as st
import pandas as pd
import pdfplumber
from extractor import parse_invoice
import io

st.set_page_config(page_title="Invoice Extractor", layout="wide")
st.title("Invoice Extractor")

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

    # Combine all invoices
    final_df = pd.concat(all_data, ignore_index=True)

    st.subheader("Extracted Invoice Data")
    st.dataframe(final_df, use_container_width=True)

    # Downloads
    csv_buffer = io.BytesIO()
    final_df.to_csv(csv_buffer, index=False)
    st.download_button(
        "⬇ Download CSV",
        data=csv_buffer.getvalue(),
        file_name="invoice_data.csv",
        mime="text/csv"
    )

    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        final_df.to_excel(writer, index=False, sheet_name="Invoices")
    st.download_button(
        "⬇ Download Excel",
        data=excel_buffer.getvalue(),
        file_name="invoice_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
    from reportlab.lib import colors

    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer)
    table_data = [final_df.columns.to_list()] + final_df.astype(str).values.tolist()
    table = Table(table_data)
    style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ])
    table.setStyle(style)
    doc.build([table])
    st.download_button(
        "⬇ Download PDF",
        data=pdf_buffer.getvalue(),
        file_name="invoice_data.pdf",
        mime="application/pdf"
    )
