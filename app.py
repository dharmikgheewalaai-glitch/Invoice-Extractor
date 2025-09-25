import streamlit as st
import pandas as pd
import tempfile
import os
from extractor import parse_invoice

st.set_page_config(page_title="Invoice Extractor", layout="wide")

st.title("📑 Invoice Extractor")

uploaded_file = st.file_uploader("Upload Invoice PDF", type=["pdf"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    try:
        df = parse_invoice(tmp_path, "", uploaded_file.name)

        st.subheader("Extracted Invoice Data")
        st.dataframe(df, use_container_width=True)

        # Download as Excel
        out_path = tmp_path.replace(".pdf", ".xlsx")
        df.to_excel(out_path, index=False)

        with open(out_path, "rb") as f:
            st.download_button(
                "Download as Excel",
                f,
                file_name=f"{os.path.splitext(uploaded_file.name)[0]}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
    except Exception as e:
        st.error(f"❌ Error parsing invoice: {e}")
    finally:
        os.unlink(tmp_path)
