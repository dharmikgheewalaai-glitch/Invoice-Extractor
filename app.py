import streamlit as st
import pandas as pd
import pdfplumber
from extractor import parse_invoice

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

    # Downloads
    st.download_button(
        "⬇ Download as Excel",
        final_df.to_excel("invoices.xlsx", index=False),
        file_name="invoices.xlsx",
    )
    st.download_button(
        "⬇ Download as CSV",
        final_df.to_csv(index=False).encode("utf-8"),
        file_name="invoices.csv",
    )
    st.download_button(
        "⬇ Download as PDF",
        final_df.to_string(index=False).encode("utf-8"),
        file_name="invoices.txt",  # exporting as txt (simple), can replace with reportlab pdf
    )
