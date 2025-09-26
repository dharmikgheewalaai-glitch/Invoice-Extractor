import streamlit as st
import pandas as pd
from extractor import extract_table_from_pdf, auto_calculate_missing

st.set_page_config(page_title="Invoice Extractor", layout="wide")

st.title("📄 Invoice Extractor")
st.write("Upload one or more invoice PDFs and download the extracted data as Excel.")

uploaded_files = st.file_uploader("Upload Invoice PDFs", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    all_dataframes = []
    for uploaded_file in uploaded_files:
        st.write(f"📑 Processing: {uploaded_file.name}")
        with open(uploaded_file.name, "wb") as f:
            f.write(uploaded_file.getbuffer())

        df = extract_table_from_pdf(uploaded_file.name)
        if not df.empty:
            df["Source File"] = uploaded_file.name
            df = auto_calculate_missing(df)
            all_dataframes.append(df)

    if all_dataframes:
        final_df = pd.concat(all_dataframes, ignore_index=True)
        st.dataframe(final_df)

        output_file = "merged_output.xlsx"
        final_df.to_excel(output_file, index=False)

        with open(output_file, "rb") as f:
            st.download_button(
                label="📥 Download Excel",
                data=f,
                file_name="merged_output.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.error("❌ No valid tables found in the uploaded PDFs.")
