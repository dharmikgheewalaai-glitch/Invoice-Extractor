import streamlit as st
import pandas as pd
import pdfplumber
from extractor import parse_invoice
from io import BytesIO

st.set_page_config(page_title="Invoice Extractor", layout="wide")
st.title("Invoice Extractor")

uploaded_files = st.file_uploader(
    "Upload Invoice PDFs", type=["pdf"], accept_multiple_files=True
)

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
    # Excel buffer
    excel_buffer = BytesIO()
    final_df.to_excel(excel_buffer, index=False, engine="openpyxl")

    # CSV data
    csv_data = final_df.to_csv(index=False).encode("utf-8")

    # TXT fallback (instead of PDF)
    txt_data = final_df.to_string(index=False).encode("utf-8")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button(
            "⬇ Excel",
            data=excel_buffer.getvalue(),
            file_name="invoices.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    with col2:
        st.download_button(
            "⬇ CSV",
            data=csv_data,
            file_name="invoices.csv",
            mime="text/csv",
        )

    with col3:
        st.download_button(
            "⬇ TXT",
            data=txt_data,
            file_name="invoices.txt",
            mime="text/plain",
        )
