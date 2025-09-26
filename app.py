import os
import sys
import pandas as pd
from extractor import extract_table_from_pdf, auto_calculate_missing

def process_pdfs(input_folder, output_file="merged_output.xlsx"):
    """
    Process all PDFs in the given folder and export a merged Excel file.
    """
    all_dataframes = []

    for file in os.listdir(input_folder):
        if file.lower().endswith(".pdf"):
            filepath = os.path.join(input_folder, file)
            print(f"📄 Processing {file}...")

            df = extract_table_from_pdf(filepath)

            if not df.empty:
                df["Source File"] = file
                df = auto_calculate_missing(df)
                all_dataframes.append(df)

    if all_dataframes:
        final_df = pd.concat(all_dataframes, ignore_index=True)
        final_df.to_excel(output_file, index=False)
        print(f"✅ Extraction complete! Saved to {output_file}")
    else:
        print("❌ No valid tables found in any PDFs.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python app.py <folder_with_pdfs>")
    else:
        input_folder = sys.argv[1]
        process_pdfs(input_folder)
