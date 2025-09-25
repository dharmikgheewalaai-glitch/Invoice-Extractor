import streamlit as st
import tempfile
import os
import traceback
from extractor import parse_invoice

st.set_page_config(page_title="Invoice Extractor", layout="wide")
st.title("📄 Invoice Extractor")

uploaded_file = st.file_uploader("Upload Invoice PDF", type=["pdf"])

if uploaded_file:
    # ---- Save uploaded file to a temporary file ----
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    try:
        # ---- Call extractor with file path ----
        df = parse_invoice(tmp_path, uploaded_file.name, text="")

        st.subheader("Extracted Invoice Data")
        st.dataframe(df, use_container_width=True)

        # ---- Download buttons ----
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"{os.path.splitext(uploaded_file.name)[0]}.csv",
            mime="text/csv",
        )

        from io import BytesIO
        excel_buffer = BytesIO()
        df.to_excel(excel_buffer, index=False, engine="openpyxl")
        st.download_button(
            label="Download Excel",
            data=excel_buffer.getvalue(),
            file_name=f"{os.path.splitext(uploaded_file.name)[0]}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    except Exception as e:
        st.error(f"❌ Error parsing invoice: {e}")
        st.text(traceback.format_exc())
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
