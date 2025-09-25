import streamlit as st
import tempfile
import os
import pandas as pd
from extractor import parse_invoice

st.set_page_config(page_title="Invoice Extractor", layout="wide")
st.title("📄 Invoice Extractor")

uploaded_file = st.file_uploader("Upload Invoice PDF", type=["pdf"])

if uploaded_file:
    # ---- Save uploaded PDF to a temporary file ----
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_path = tmp_file.name

    # ---- Extract invoice data ----
    try:
        df = parse_invoice(tmp_path, uploaded_file.name)

        st.subheader("Extracted Invoice Data")
        st.dataframe(df)

        # ---- Download options ----
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇ Download CSV", csv, "invoice_data.csv", "text/csv")

        excel = df.to_excel("invoice_data.xlsx", index=False)
        with open("invoice_data.xlsx", "rb") as f:
            st.download_button("⬇ Download Excel", f, "invoice_data.xlsx")

        pdf_out = df.to_string(index=False)
        st.download_button("⬇ Download TXT", pdf_out, "invoice_data.txt")

    except Exception as e:
        st.error(f"Error parsing invoice: {e}")

    finally:
        # ---- Clean up temporary file ----
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
