# server/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from data_poisoning_service import TextBasedPoisonDetection, TableBasedPoisonDetection

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})


@app.route("/api/detect-poisoning", methods=["POST"])
def detect_poisoning():
    dataset_type = request.form.get("dataset_type", "text").lower()

    if dataset_type == "text":
        service = TextBasedPoisonDetection()
    elif dataset_type == "table":
        service = TableBasedPoisonDetection()
    else:
        return jsonify({"error": "Invalid dataset_type, choose 'text' or 'table'"}), 400

    try:
        df = service.load_data(n_samples=5000, poison_fraction=0.05)
        results = service.process_data(df)
        return jsonify(
            {
                "message": "Detection successful",
                "results": results["data"],
                "metrics": results["metrics"],
                "actual_poisoned": results.get("actual_poisoned", []),
                "predicted_poisoned": results.get("predicted_poisoned", []),
            }
        )
    except Exception as e:
        app.logger.error(f"Error in /api/detect-poisoning: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)


# from flask import Flask, request, jsonify
# from flask_cors import CORS
# import pandas as pd
# import io


# # import the service classes we just defined
# from services.tabular_service import TabularDataService
# from services.textual_service import TextDataService
# from services.poisonInjector import PoisonInjector
# from services.poisonInjector import load_demo_dataset

# # application initialization.
# app = Flask(__name__)

# # cors implementation allowing the requrests to come from origin mentioned and that starts with /api/
# CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})


# @app.route("/api/upload", methods=["POST"])
# def upload_and_preview():
#     """
#     handles file uploads, returning a preview and column analysis.
#     this is the first step in the user workflow.
#     """

#     if "file" not in request.files:
#         return jsonify({"error": "No file part in the request"}), 400

#     file = request.files["file"]
#     dataset_type = request.form.get("dataset_type", "tabular").lower()

#     if file.filename == "":
#         return jsonify({"error": "No selected file"}), 400

#     try:
#         contents = file.read()
#         if file.filename.endswith(".csv"):
#             df = pd.read_csv(io.BytesIO(contents))
#         elif file.filename.endswith(".xlsx"):
#             df = pd.read_excel(io.BytesIO(contents))
#         else:
#             return jsonify({"error": "Unsupported file format"}), 400

#         # generate column info for the frontend config ui
#         column_info = []
#         for col in df.columns:
#             # for tabular data, we auto-detect type
#             if dataset_type == "tabular":
#                 dtype = (
#                     "Numeric"
#                     if pd.api.types.is_numeric_dtype(df[col])
#                     else "Categorical"
#                 )
#                 unique_vals = []
#                 if dtype == "Categorical":
#                     # send up to 50 unique values for user to validate
#                     unique_vals = df[col].unique().tolist()[:50]
#                 column_info.append(
#                     {"name": col, "auto_type": dtype, "unique_values": unique_vals}
#                 )
#             else:  # For text, we just need the names
#                 column_info.append({"name": col, "auto_type": "Text"})

#         # Return everything the frontend needs to proceed
#         return jsonify(
#             {
#                 "filename": file.filename,
#                 "rowCount": len(df),
#                 "columnInfo": column_info,
#                 "previewData": df.head(50).to_dict(orient="records"),
#                 "fullData": df.to_dict(orient="records"),  # Send data to frontend state
#             }
#         )

#     except Exception as e:
#         app.logger.error(f"Error in /api/upload: {e}")
#         return jsonify({"error": f"Failed to process file: {str(e)}"}), 500


# @app.route("/api/sanitize", methods=["POST"])
# def sanitize_data():
#     """
#     Receives the full dataset and user config, runs the appropriate
#     pipeline, and returns the flagged rows.
#     """
#     payload = request.get_json()
#     if not payload or "data" not in payload or "config" not in payload:
#         return jsonify(
#             {"error": "Invalid payload. 'data' and 'config' keys are required."}
#         ), 400

#     config = payload["config"]

#     try:
#         # Recreate the DataFrame from the JSON sent by the frontend
#         df = pd.DataFrame(payload["data"])

#         # Determine which service to use based on the config structure
#         if "ml_task" in config:  # This indicates a tabular configuration
#             service = TabularDataService(df, config)
#         elif "text_column" in config:  # This indicates a text configuration
#             service = TextDataService(df, config)
#         else:
#             return jsonify(
#                 {"error": "Invalid configuration. Could not determine dataset type."}
#             ), 400

#         # Run the pipeline and get the results
#         flagged_rows = service.run_pipeline()

#         # Convert integer keys to string for JSON compatibility
#         results = {str(k): v for k, v in flagged_rows.items()}

#         return jsonify({"message": "Sanitization successful", "flagged_rows": results})

#     except Exception as e:
#         app.logger.error(f"Error in /api/sanitize: {e}")
#         return jsonify({"error": str(e)}), 500


# @app.route("/api/load-demo", methods=["POST"])
# def load_demo():
#     """
#     Loads a clean dataset, poisons it, and returns it in the
#     same format as the /upload endpoint, PLUS ground truth.

#     Expects a JSON payload: {"type": "tabular-regression"}
#     """
#     payload = request.get_json()
#     dataset_type = payload.get("type", "tabular-regression")
#     app.logger.info(f"Received request for demo: {dataset_type}")

#     try:
#         # 1. Load and poison the data using our new service
#         poisoned_df, true_poison_indices = load_demo_dataset(dataset_type)

#         # 2. Analyze columns for the UI (same logic as /upload)
#         column_info = []
#         for col in poisoned_df.columns:
#             if "tabular" in dataset_type:
#                 dtype = (
#                     "Numerical"
#                     if pd.api.types.is_numeric_dtype(poisoned_df[col])
#                     else "Categorical"
#                 )
#                 unique_vals = []
#                 if dtype == "Categorical":
#                     unique_vals = poisoned_df[col].astype(str).unique().tolist()[:50]
#                 column_info.append(
#                     {"name": col, "auto_type": dtype, "unique_values": unique_vals}
#                 )
#             else:  # text
#                 column_info.append({"name": col, "auto_type": "Text"})

#         # 3. Return the full response
#         return jsonify(
#             {
#                 "filename": f"demo_{dataset_type}.csv",
#                 "rowCount": len(poisoned_df),
#                 "columnInfo": column_info,
#                 "previewData": poisoned_df.head(50).to_dict(orient="records"),
#                 "fullData": poisoned_df.to_dict(orient="records"),
#                 # The CRITICAL new field for the frontend:
#                 "groundTruth": {"true_poison_indices": true_poison_indices},
#             }
#         )
#     except Exception as e:
#         app.logger.error(f"Error in /api/load-demo: {e}", exc_info=True)
#         return jsonify({"error": f"Failed to load demo: {str(e)}"}), 500


# if __name__ == "__main__":
#     app.run(debug=True, port=5000)
