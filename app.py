import streamlit as st
import pandas as pd
from extractor import process_file

st.set_page_config(page_title="GST Invoice Extractor", layout="wide")
st.title("GST Invoice Extractor")

uploaded_files = st.file_uploader(
    "Upload invoice files (PDF/Image)", 
    type=["pdf", "png", "jpg", "jpeg"], 
    accept_multiple_files=True
)

if uploaded_files:
    all_data = []
    for file in uploaded_files:
        with open(file.name, "wb") as f:
            f.write(file.getbuffer())
        extracted_data = process_file(file.name)
        for row in extracted_data:
            row["Source File"] = file.name
            all_data.append(row)

    if all_data:
        df = pd.DataFrame(all_data)
        st.subheader("📊 Extracted Invoice Data")
        st.dataframe(df, use_container_width=True)

        # Download buttons
        st.subheader("📥 Download Extracted Data")
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "invoices.csv", "text/csv")

        excel = df.to_excel("invoices.xlsx", index=False)
        with open("invoices.xlsx", "rb") as f:
            st.download_button("Download Excel", f, "invoices.xlsx")

        pdf = df.to_markdown(index=False).encode("utf-8")
        st.download_button("Download PDF (table as text)", pdf, "invoices.pdf")
