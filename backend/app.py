from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import io
import logging  # <-- Import logging


# import the service classes we just defined
from services.tabular_service import TabularDataService
from services.text_service import TextDataService

# from services.poisonInjector import PoisonInjector
from services.poisonInjector import load_demo_dataset

# application initialization.
app = Flask(__name__)

# Configure logging if not already done elsewhere
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(message)s")


# cors implementation allowing the requrests to come from origin mentioned and that starts with /api/
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})


@app.route("/api/upload", methods=["POST"])
def upload_and_preview():
    """
    handles file uploads, returning a preview and column analysis.
    this is the first step in the user workflow.
    """

    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]
    dataset_type = request.form.get("dataset_type", "tabular").lower()

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    try:
        contents = file.read()
        if file.filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
        elif file.filename.endswith(".xlsx"):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            return jsonify({"error": "Unsupported file format"}), 400

        # generate column info for the frontend config ui
        column_info = []
        for col in df.columns:
            if dataset_type == "tabular":
                # First, check if it's already numeric
                if pd.api.types.is_numeric_dtype(df[col]):
                    dtype = "Numerical"
                    unique_vals = []
                else:
                    # It's not numeric. It's likely 'object' type.

                    col_to_convert = df[col]  # Start with the original column

                    # --- NEW, MORE ROBUST LOGIC ---
                    # If the column type is 'object' (likely strings),
                    # it might have whitespace. Let's strip it.
                    if df[col].dtype == "object":
                        try:
                            # Convert to string (to be safe), strip whitespace
                            col_to_convert = df[col].astype(str).str.strip()
                        except Exception as e:
                            # If stripping fails for some reason, log it and use original
                            app.logger.warning(f"Could not strip column {col}: {e}")
                            pass

                    # Attempt coercion to numeric on the (potentially) cleaned column
                    converted_col = pd.to_numeric(col_to_convert, errors="coerce")
                    # --- END NEW LOGIC ---

                    # Now, check the result of the coercion.
                    # If it's NOT all NaN (i.e., at least one value converted successfully)
                    if not converted_col.isnull().all():
                        # If we have *some* valid numbers, treat it as Numerical.
                        dtype = "Numerical"
                        unique_vals = []
                    else:
                        # If coercion resulted in ALL NaNs, it's definitely Categorical.
                        dtype = "Categorical"
                        unique_vals = df[col].astype(str).unique().tolist()[:50]

                column_info.append(
                    {"name": col, "auto_type": dtype, "unique_values": unique_vals}
                )

            else:  # For text, we just need the names
                # Make sure to add unique_values here too for consistency
                column_info.append(
                    {"name": col, "auto_type": "Text", "unique_values": []}
                )

        # Return everything the frontend needs to proceed
        return jsonify(
            {
                "filename": file.filename,
                "rowCount": len(df),
                "columnInfo": column_info,
                "previewData": df.head(50).to_dict(orient="records"),
                "fullData": df.to_dict(orient="records"),  # Send data to frontend state
            }
        )

    except Exception as e:
        app.logger.error(f"Error in /api/upload: {e}", exc_info=True)  # Added exc_info
        return jsonify({"error": f"Failed to process file: {str(e)}"}), 500


@app.route("/api/sanitize", methods=["POST"])
def sanitize_data():
    """
    Receives the full dataset and user config, runs the appropriate
    pipeline, and returns the flagged rows.
    """
    payload = request.get_json()
    if not payload or "data" not in payload or "config" not in payload:
        return jsonify(
            {"error": "Invalid payload. 'data' and 'config' keys are required."}
        ), 400

    config = payload["config"]

    try:
        # Recreate the DataFrame from the JSON sent by the frontend
        df = pd.DataFrame(payload["data"])

        # --- ADDED LOGGING ---
        app.logger.info(
            f"DataFrame columns received in /sanitize: {df.columns.tolist()}"
        )
        app.logger.info(f"Config received in /sanitize: {config}")
        # --- END LOGGING ---

        # Determine which service to use based on the config structure
        if "ml_task" in config:  # This indicates a tabular configuration
            app.logger.info("Initializing TabularDataService...")
            service = TabularDataService(df, config)
        elif "text_column" in config:  # This indicates a text configuration
            app.logger.info("Initializing TextDataService...")
            service = TextDataService(df, config)
        else:
            app.logger.error(f"Invalid config received: {config}")
            return jsonify(
                {"error": "Invalid configuration. Could not determine dataset type."}
            ), 400

        # Run the pipeline and get the results
        flagged_rows = service.run_pipeline()

        # Convert integer keys to string for JSON compatibility
        # Ensure flagged_rows is a dict before conversion
        results = (
            {str(k): v for k, v in flagged_rows.items()}
            if isinstance(flagged_rows, dict)
            else {}
        )

        return jsonify({"message": "Sanitization successful", "flagged_rows": results})

    except KeyError as ke:  # Catch specific KeyError
        app.logger.error(
            f"KeyError in /api/sanitize: {ke}. Check DataFrame columns and config.",
            exc_info=True,
        )
        return jsonify(
            {"error": f"Configuration Error: Column '{ke}' not found in the data."}
        ), 500
    except Exception as e:
        app.logger.error(
            f"Error in /api/sanitize: {e}", exc_info=True
        )  # Added exc_info
        return jsonify({"error": str(e)}), 500


@app.route("/api/load-demo", methods=["POST"])
def load_demo():
    """
    Loads a clean dataset, poisons it, and returns it in the
    same format as the /upload endpoint, PLUS ground truth.

    Expects a JSON payload: {"type": "tabular-regression"}
    """
    payload = request.get_json()
    dataset_type = payload.get("type", "tabular-regression")
    app.logger.info(f"Received request for demo: {dataset_type}")

    try:
        # 1. Load and poison the data using our new service
        poisoned_df, true_poison_indices = load_demo_dataset(dataset_type)

        # Check if loading failed (returned empty DataFrame)
        if poisoned_df.empty:
            app.logger.error(
                f"load_demo_dataset returned an empty DataFrame for type: {dataset_type}"
            )
            # Return an error or a response indicating failure
            return jsonify(
                {"error": f"Failed to load or process demo data '{dataset_type}'."}
            ), 500

        # 2. Analyze columns for the UI (Robust logic copied from /upload)
        column_info = []
        for col in poisoned_df.columns:
            # Skip the internal tracking column
            if col == "__original_index__":
                continue

            if "tabular" in dataset_type:
                # --- START ROBUST FIX ---
                # First, check if it's already numeric
                if pd.api.types.is_numeric_dtype(poisoned_df[col]):
                    dtype = "Numerical"
                    unique_vals = []
                else:
                    # It's not numeric. It's likely 'object' type (e.g., from poisoning)

                    col_to_convert = poisoned_df[col]  # Start with the original column

                    # If the column type is 'object', it might have whitespace
                    # (less likely here, but good to keep for consistency)
                    if poisoned_df[col].dtype == "object":
                        try:
                            # Convert to string, strip whitespace
                            col_to_convert = poisoned_df[col].astype(str).str.strip()
                        except Exception as e:
                            app.logger.warning(f"Could not strip column {col}: {e}")
                            pass

                    # Attempt coercion to numeric on the (potentially) cleaned column
                    # This will turn "TYPE_ERROR" and other strings into NaN
                    converted_col = pd.to_numeric(col_to_convert, errors="coerce")

                    # Now, check the result of the coercion.
                    # If it's NOT all NaN (i.e., at least one *number* exists)
                    if not converted_col.isnull().all():
                        # If we have *some* valid numbers, treat it as Numerical.
                        dtype = "Numerical"
                        unique_vals = []
                    else:
                        # If coercion resulted in ALL NaNs, it's definitely Categorical.
                        dtype = "Categorical"
                        # Make sure to handle potential NaNs before getting unique values
                        unique_vals = (
                            poisoned_df[col].astype(str).unique().tolist()[:50]
                        )

                column_info.append(
                    {"name": col, "auto_type": dtype, "unique_values": unique_vals}
                )
                # --- END ROBUST FIX ---

            else:  # text
                # Make sure to add unique_values here too for consistency
                column_info.append(
                    {"name": col, "auto_type": "Text", "unique_values": []}
                )

        # 3. Return the full response
        return jsonify(
            {
                "filename": f"demo_{dataset_type}.csv",
                "rowCount": len(poisoned_df),
                "columnInfo": column_info,
                "previewData": poisoned_df.head(50).to_dict(orient="records"),
                "fullData": poisoned_df.to_dict(orient="records"),
                # The CRITICAL new field for the frontend:
                "groundTruth": {"true_poison_indices": true_poison_indices},
            }
        )
    except Exception as e:
        app.logger.error(
            f"Error in /api/load-demo: {e}", exc_info=True
        )  # Added exc_info
        return jsonify({"error": f"Failed to load demo: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
