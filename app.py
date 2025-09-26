import streamlit as st
import pandas as pd
from extractor import extract_table_from_pdf

st.set_page_config(page_title="Invoice Extractor", layout="wide")

st.title("📑 Invoice Extractor")
st.write("Upload your invoice PDF and extract tabular data into Excel/CSV.")

uploaded_file = st.file_uploader("Upload Invoice PDF", type=["pdf"])

if uploaded_file:
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.read())

    st.info("⏳ Extracting data...")
    df = extract_table_from_pdf("temp.pdf")

    if not df.empty:
        st.success("✅ Data extracted successfully!")
        st.dataframe(df)

        # Download buttons
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "invoice_data.csv", "text/csv")

        excel_file = "invoice_data.xlsx"
        df.to_excel(excel_file, index=False)
        with open(excel_file, "rb") as f:
            st.download_button("Download Excel", f, "invoice_data.xlsx")
    else:
        st.error("⚠️ No tables found in the invoice.")
