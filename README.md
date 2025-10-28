# PoisonGuard: The Data Sanitization Toolkit

An interactive web-based tool to detect and mitigate data poisoning in your datasets before you train your model.

## Table of Contents

- [Vision & Mission](#vision--mission)
- [Core Features](#core-features)
- [How It Works: The Sanitization Pipeline](#how-it-works-the-sanitization-pipeline)
- [In-Depth Module: Tabular Data](#in-depth-module-tabular-data)
- [Future Modules (Roadmap)](#future-modules-roadmap)
- [Proposed Technology Stack](#proposed-technology-stack)
- [Getting Started (Local Development)](#getting-started-local-development)
- [Project Plan](#project-plan)

---

## Vision & Mission

**Vision:** To build the first line of defense for machine learning models, ensuring that data quality issues and malicious attacks are identified and handled before they can corrupt the training process.

**Mission:** To provide an intuitive, powerful, and educational web tool that allows data scientists, analysts, and developers to easily upload their data, identify potential poison, and clean their datasets with confidence.

---

## Core Features

* **Multi-Modal Data Support:** Separate, specialized modules for Tabular, Text, and Image data.
* **Interactive UI:** A user-friendly interface to upload, configure, analyze, and review data.
* **Multi-Phase Detection:** A robust, layered pipeline that catches different types of poisoning attacks, from simple errors to sophisticated label flips.
* **Task-Aware Analysis:** The tool's algorithms adapt based on the user-defined ML task (e.g., Regression vs. Classification).
* **Rich Visualizations:** Interactive plots and tables to help users understand why a data point was flagged.
* **Exportable Results:** Download the cleaned dataset and a report of the findings.

---

## How It Works: The Sanitization Pipeline

PoisonGuard uses a three-phase pipeline to systematically clean data. This layered approach ensures that we catch a wide variety of issues.

### Phase 1: The Gatekeeper (Initial Validation)

* **Goal:** Catch blatantly invalid, malformed, or out-of-bounds data.
* **Methods:** Schema enforcement, data type checking, and user-defined range constraints.

### Phase 2: The Detective (Statistical Anomaly Detection)

* **Goal:** Find data points that are statistically improbable outliers, even if they are technically valid. These are prime candidates for feature manipulation attacks.
* **Methods:** Isolation Forest, Interquartile Range (IQR), Z-Score, and rare category detection.

### Phase 3: The Interrogator (Model-Based Label Auditing)

* **Goal:** Find the most subtle poison: data points with normal-looking features but an intentionally incorrect label (label flips).
* **Methods:** Training "canary" models to identify high-loss data points and instances where an ensemble of models disagrees on the prediction.

---

## In-Depth Module: Tabular Data

This is the core module of the initial version of PoisonGuard. It provides a full-featured workflow for cleaning CSV and Excel files.

### User Workflow & Required Inputs

This is what the user must provide at each step to enable the pipeline:

**Step 1: Upload & Initial Configuration**

* **Input:** Upload a CSV or Excel file.
* **UI:** The tool displays a preview of the first 50 rows.
* **Required User Action:**
    * **Select Columns:** The user checks the boxes for the columns they want to include in the analysis.
    * **Define Target Variable:** The user must select one column as the "Target" or "Label" (the `y` variable).
    * **Define ML Task:** The user must select the modeling task. This is the most critical input for the backend logic.
        * `()` Regression (e.g., predicting a house price)
        * `()` Classification (e.g., predicting if it will rain)

**Step 2: Define Constraints (For Pipeline Phase 1)**

* **UI:** The tool lists each selected column, its auto-detected data type, and input fields.
* **Required User Action:**
    * **Confirm Data Types:** The user confirms or corrects the data type (Numerical or Categorical).
    * **Set Numerical Constraints (Optional but Recommended):** For numerical columns, the user can enter a valid `Minimum` and `Maximum` value.
    * **Set Categorical Constraints (Optional but Recommended):** For categorical columns, the tool shows a list of all unique values. The user can uncheck any values they consider invalid.

**Step 3: Run Analysis**

* **Required User Action:** Click the "Sanitize My Data" button.
* **Backend Process:** The tool runs the full 3-phase pipeline based on the user's configuration.

**Step 4: Review Results & Mitigate**

* **UI:** A dashboard summarizing the findings.
* **Information Presented:**
    * A summary card: "Analyzed 50,000 rows. Flagged 312 (0.6%) for review."
    * **Constraint Violations:** A table of rows that failed Phase 1 checks.
    * **Statistical Outliers:** An interactive 2D scatter plot (using PCA/UMAP) highlighting the outliers from Phase 2. Users can hover over points to see their values.
    * **Suspicious Labels:** A table of the top N rows with the highest model loss from Phase 3. It will show the features, the original label, and the label predicted by the canary model.
* **Required User Action:** For each flagged row or group of rows, the user can choose to "Keep" or "Remove".

**Step 5: Export**

* **Required User Action:** Click "Download Cleaned Data".
* **Output:** A new CSV file containing only the "kept" data, ready for model training.

### Poison Detection Techniques Used

* **For Regression:** The pipeline will focus heavily on Phase 2, using Isolation Forest to detect high-leverage points that can skew the regression line.
* **For Classification:** The pipeline will give more weight to Phase 3, using canary models (like Logistic Regression or LightGBM) to find high-loss points indicative of label flips.

---

### In-Depth Module: Text Data

This module is designed for cleaning text classification datasets (e.g., sentiment analysis, spam detection, topic classification) in `CSV` or `JSONL` format.

#### User Workflow & Required Inputs

**Step 1: Upload & Initial Configuration**

* **Input:** Upload a `CSV` or `JSONL` file.
* **UI:** The tool displays a preview of the data.
* **Required User Action:**
    * **Select Text Column:** The user must select the column containing the raw text (the `X` variable).
    * **Select Target Column:** The user must select the column containing the label (the `y` variable).
    * **Define ML Task:** The user selects `Classification` (e.g., Sentiment, Spam, Topic).
    * **(Optional) Select Language:** User can select the primary language (e.g., "English") to flag outliers.

**Step 2: Define Constraints (For Pipeline Phase 1)**

* **UI:** The tool lists several "Gatekeeper" checks.
* **Required User Action:**
    * **Set Length Constraints:** Set a `Minimum` and `Maximum` character length (e.g., flag text shorter than 10 or longer than 5000 chars).
    * **Set Regex Filters:** Check boxes to flag common malicious patterns:
        * `()` Flag Malicious URLs
        * `()` Flag HTML/JavaScript tags
        * `()` Flag PII (experimental)
    * **Set Quality Filters:**
        * `()` Flag non-English text (if language was selected).
        * `()` Flag high-perplexity gibberish.

**Step 3: Run Analysis**

* **Required User Action:** Click the "Sanitize My Data" button.
* **Backend Process:** The tool runs the full 3-phase text pipeline. This may take longer than tabular data due to model loading and embedding generation.

**Step 4: Review Results & Mitigate**

* **UI:** A dashboard summarizing the findings.
* **Information Presented:**
    * A summary card: "Analyzed 10,000 rows. Flagged 150 (1.5%) for review."
    * **Constraint Violations (Phase 1):** A table of rows that failed Phase 1 (e.g., "Flagged: Contains URL").
    * **Statistical Outliers (Phase 2):** An interactive 2D `t-SNE` plot showing the text embeddings. Outliers will be clearly visible outside the main class clusters.
    * **Suspicious Labels (Phase 3):** A table of the top N rows with the highest model loss, showing the text, its original label, and the label predicted by the canary model.

**Step 5: Export**

* **Required User Action:** Click "Download Cleaned Data".
* **Output:** A new `CSV` file containing only the "kept" data.

#### Poison Detection Techniques Used (Text)

* **Phase 1 (Gatekeeper):** Catches malformed data.
    * **Length & Language Filters:** Simple validation of text length and language.
    * **Regex Filtering:** Uses regular expressions to find and flag text containing URLs, HTML/JS tags, or other user-defined patterns.
    * **Gibberish Detection:** Uses a perplexity score from a lightweight language model to flag nonsensical text (e.g., "asdlkjfh asdflkjh").

* **Phase 2 (Detective):** Catches semantic outliers.
    * **Outlier Embeddings:** This is the core of Phase 2.
        1.  A pre-trained **Sentence Transformer (e.g., Sentence-BERT)** converts all text into numerical vector embeddings.
        2.  An **Isolation Forest** or **Local Outlier Factor (LOF)** model is trained on these embeddings (grouped by class).
        3.  Any text whose embedding is "far away" from its class cluster is flagged as a statistical outlier. This is highly effective at catching text that is semantically out-of-place.

* **Phase 3 (Interrogator):** Catches classic label flips.
    * **Canary Model:** A `TfidfVectorizer` + `LogisticRegression` pipeline. This is a fast, robust, and interpretable baseline model.
    * **High-Loss Detection:** The canary model is trained using cross-validation. We use `cross_val_predict_proba` to get out-of-fold probabilities for every sample and then calculate its `log_loss`. A sample with an intentionally flipped label (e.g., a "brilliant" review labeled `Negative`) will have a very high loss and will be flagged.


### Image Data Module

* **User Input:** Upload a folder of images. Provide a metadata file mapping image filenames to labels.
* **Poison Techniques:**
    * **Metadata Validation:** Check for corrupted files or incorrect formats (Phase 1).
    * **Pixel Distribution Analysis:** Detect outliers based on brightness, contrast, or color histograms (Phase 2).
    * **Clean Label Detection:** Train a simple image classifier (e.g., MobileNetV2) and flag images where the model's prediction has very high confidence but the label is different (Phase 3).

---

## Proposed Technology Stack

* **Frontend:** React / Vue.js (for a dynamic, component-based UI).
* **Visualization:** Plotly.js or Chart.js for interactive plots.
* **Backend API:** **Flask** (A lightweight and powerful Python web framework for serving the API and processing data).
* **Data Science Libraries:** Pandas, NumPy, Scikit-learn, LightGBM.
* **Deployment:** Docker for containerization, hosted on a cloud provider (AWS, Google Cloud, Azure).

---

## Getting Started (Local Development)

This guide assumes you are running the Flask backend and a separate frontend (e.g., React) locally.

### 1. Backend (Flask)

**Prerequisites:**
* Python 3.8+
* pip (Python package installer)

**Setup:**

1.  Clone the repository:
    ```bash
    git clone [https://github.com/your-username/PoisonGuard.git](https://github.com/your-username/PoisonGuard.git)
    cd PoisonGuard/backend
    ```

2.  Create and activate a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  Install dependencies from `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: `requirements.txt` should contain `flask`, `flask-cors`, `pandas`, `scikit-learn`, `lightgbm`, `numpy`, `openpyxl`)*

4.  Run the Flask server:
    ```bash
    # Set the main application file (e.g., app.py)
    export FLASK_APP=app.py
    # Enable development mode for auto-reloading
    export FLASK_ENV=development
    # Run the app
    flask run
    ```
    *The backend will now be running on `http://127.0.0.1:5000`.*

### 2. Frontend (React/Vue)

1.  Navigate to the `frontend` directory:
    ```bash
    cd ../frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Run the development server:
    ```bash
    npm start
    ```
    *The frontend will open on `http://localhost:3000` and will make API calls to your Flask server.*

---

## Project Plan

### Phase I (Q1-Q2 2026): Minimum Viable Product (MVP)

* [x] Develop the full, end-to-end Tabular Data Module.
* [x] Implement all 5 steps of the user workflow.
* [x] Implement core detection algorithms for Phase 1, 2, and 3.
* [x] Allow CSV and Excel upload and cleaned CSV download.
* [ ] Basic user authentication and project saving.

### Phase II (Q3 2026): Advanced Features & UX

* [ ] Add more advanced statistical detection methods.
* [ ] Improve visualizations and add more exploratory data analysis tools.
* [ ] Generate a detailed PDF report of the sanitization process.
* [ ] Enhance performance for very large datasets.

### Phase III (Q4 2026 - Q1 2027): Expansion to New Data Types

* [ ] Begin development of the Text Data Module.
* [ ] Research and prototype the Image Data Module.
* [ ] Full release of the Text module and beta release of the Image module.