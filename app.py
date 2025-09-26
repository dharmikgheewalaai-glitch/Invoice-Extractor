from flask import Flask, request, render_template, send_file
import os
import pandas as pd
from extractor import extract_table_from_pdf, auto_calculate_missing

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/", methods=["GET", "POST"])
def upload_files():
    if request.method == "POST":
        uploaded_files = request.files.getlist("file[]")
        all_dataframes = []

        for file in uploaded_files:
            if file.filename.endswith(".pdf"):
                filepath = os.path.join(UPLOAD_FOLDER, file.filename)
                file.save(filepath)

                df = extract_table_from_pdf(filepath)

                if not df.empty:
                    # ✅ Add source file column
                    df["Source File"] = file.filename

                    # ✅ Auto calculate missing values
                    df = auto_calculate_missing(df)

                    all_dataframes.append(df)

        if all_dataframes:
            final_df = pd.concat(all_dataframes, ignore_index=True)
            output_file = os.path.join(UPLOAD_FOLDER, "merged_output.xlsx")
            final_df.to_excel(output_file, index=False)

            return send_file(output_file, as_attachment=True)

        return "❌ No valid tables found in uploaded PDFs."

    return render_template("upload.html")
