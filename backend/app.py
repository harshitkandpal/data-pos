from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import io
import logging
import torch
import tempfile
import os

from services.tabular_service import TabularDataService
from services.text_service import TextDataService
from services.poisonInjector import load_demo_dataset

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(message)s")

CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})


# =========================
# FILE UPLOAD
# =========================
@app.route("/api/upload", methods=["POST"])
def upload_and_preview():

    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]
    dataset_type = request.form.get("dataset_type", "tabular").lower()

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    try:

        contents = file.read()

        # =========================
        # CSV FILE
        # =========================
        if file.filename.endswith(".csv"):

            try:
                df = pd.read_csv(
                    io.BytesIO(contents),
                    encoding="utf-8",
                    engine="python"
                )
            except UnicodeDecodeError:
                df = pd.read_csv(
                    io.BytesIO(contents),
                    encoding="latin1",
                    engine="python"
                )

        # =========================
        # EXCEL FILE
        # =========================
        elif file.filename.endswith(".xlsx"):

            df = pd.read_excel(io.BytesIO(contents))

        # =========================
        # NEURAL NETWORK FILE
        # =========================
        elif file.filename.endswith((".pt", ".pth", ".h5")):

            temp_path = os.path.join(tempfile.gettempdir(), file.filename)

            with open(temp_path, "wb") as f:
                f.write(contents)

            total_params = 0
            risk_level = "LOW"

            try:

                model = torch.load(temp_path, map_location="cpu")

                if hasattr(model, "parameters"):
                    for p in model.parameters():
                        total_params += p.numel()

            except Exception:
                risk_level = "UNKNOWN"

            return jsonify({
                "filename": file.filename,
                "rowCount": 1,
                "columnInfo": [],
                "previewData": [{
                    "model_file": file.filename,
                    "parameters": total_params,
                    "risk": risk_level
                }],
                "fullData": [{
                    "model_file": file.filename,
                    "parameters": total_params,
                    "risk": risk_level
                }]
            })

        else:
            return jsonify({"error": "Unsupported file format"}), 400


        # =========================
        # DATASET PROCESSING
        # =========================
        df = df.where(pd.notnull(df), None)

        column_info = []

        for col in df.columns:

            if dataset_type == "tabular":

                if pd.api.types.is_numeric_dtype(df[col]):
                    dtype = "Numerical"
                    unique_vals = []

                else:

                    col_to_convert = df[col]

                    if df[col].dtype == "object":
                        try:
                            col_to_convert = df[col].astype(str).str.strip()
                        except Exception:
                            pass

                    converted_col = pd.to_numeric(col_to_convert, errors="coerce")

                    if not converted_col.isnull().all():
                        dtype = "Numerical"
                        unique_vals = []
                    else:
                        dtype = "Categorical"
                        unique_vals = df[col].astype(str).unique().tolist()[:50]

                column_info.append({
                    "name": col,
                    "auto_type": dtype,
                    "unique_values": unique_vals,
                })

            else:

                column_info.append({
                    "name": col,
                    "auto_type": "Text",
                    "unique_values": [],
                })


        return jsonify({
            "filename": file.filename,
            "rowCount": len(df),
            "columnInfo": column_info,
            "previewData": df.head(50).to_dict(orient="records"),
            "fullData": df.to_dict(orient="records"),
        })

    except Exception as e:
        app.logger.error(f"Error in /api/upload: {e}", exc_info=True)
        return jsonify({"error": f"Failed to process file: {str(e)}"}), 500


# =========================
# SANITIZE PIPELINE
# =========================
@app.route("/api/sanitize", methods=["POST"])
def sanitize_data():

    payload = request.get_json()

    if not payload or "data" not in payload or "config" not in payload:
        return jsonify({"error": "Invalid payload"}), 400

    config = payload["config"]

    try:

        df = pd.DataFrame(payload["data"])

        if "ml_task" in config:
            service = TabularDataService(df, config)

        elif "text_column" in config:
            service = TextDataService(df, config)

        else:
            return jsonify({"error": "Invalid configuration"}), 400

        flagged_rows = service.run_pipeline()

        results = (
            {str(k): v for k, v in flagged_rows.items()}
            if isinstance(flagged_rows, dict)
            else {}
        )

        return jsonify({
            "message": "Sanitization successful",
            "flagged_rows": results
        })

    except Exception as e:
        app.logger.error(f"Error in sanitize: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# =========================
# DEMO DATA
# =========================
@app.route("/api/load-demo", methods=["POST"])
def load_demo():

    payload = request.get_json()
    dataset_type = payload.get("type", "tabular-regression")

    try:

        poisoned_df, true_poison_indices = load_demo_dataset(dataset_type)

        poisoned_df = poisoned_df.where(pd.notnull(poisoned_df), None)

        column_info = []

        for col in poisoned_df.columns:

            if col == "__original_index__":
                continue

            if pd.api.types.is_numeric_dtype(poisoned_df[col]):
                dtype = "Numerical"
                unique_vals = []
            else:
                dtype = "Categorical"
                unique_vals = poisoned_df[col].astype(str).unique().tolist()[:50]

            column_info.append({
                "name": col,
                "auto_type": dtype,
                "unique_values": unique_vals,
            })


        return jsonify({
            "filename": f"demo_{dataset_type}.csv",
            "rowCount": len(poisoned_df),
            "columnInfo": column_info,
            "previewData": poisoned_df.head(50).to_dict(orient="records"),
            "fullData": poisoned_df.to_dict(orient="records"),
            "groundTruth": {"true_poison_indices": true_poison_indices},
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================
# RUN SERVER
# =========================
if __name__ == "__main__":
    app.run(debug=True, port=5000)