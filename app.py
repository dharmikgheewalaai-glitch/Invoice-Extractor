import streamlit as st
import tempfile
import os
from extractor import parse_invoice

st.set_page_config(page_title="Invoice Extractor", layout="wide")
st.title("Invoice Extractor App")

uploaded_file = st.file_uploader("Upload Invoice PDF", type=["pdf"])

if uploaded_file:
    # Save uploaded file to a temp file (pdfplumber needs path or file-like object)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_path = tmp_file.name

    with open(tmp_path, "rb") as f:
        pdf_bytes = f.read()

    text = ""  # Optional: OCR / raw text if needed

    df = parse_invoice(tmp_path, text, uploaded_file.name)

    st.subheader("Extracted Invoice Data")
    st.dataframe(df)

    # Download option
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download as CSV",
        data=csv,
        file_name="invoice_data.csv",
        mime="text/csv",
    )

    # Clean up temp file
    os.remove(tmp_path)
