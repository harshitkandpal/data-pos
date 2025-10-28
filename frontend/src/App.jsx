// import React, { useState, useMemo } from "react";
// import {
//   Zap,
//   Database,
//   Loader2,
//   BarChart3,
//   AlertTriangle,
//   CheckCircle,
//   Upload,
//   FileScan,
//   TestTube,
//   ChevronRight,
//   ChevronLeft,
//   XCircle,
//   FileText,
//   FlaskConical, // Added icon for simple demos
//   Flower, // Added icon for Iris
//   Film, // <-- Added icon for IMDB
// } from "lucide-react";

// // --- API Configuration ---
// const FLASK_API_URL = "http://127.0.0.1:5000/api"; // Corrected IP
// const PAGE_SIZE = 20; // For results table pagination

// // --- Reusable UI Components ---

// const Card = ({ title, icon, children, className = "" }) => (
//   <div
//     className={`bg-zinc-800 p-6 rounded-2xl shadow-xl border border-zinc-700 ${className}`}
//   >
//     {title && (
//       <h2 className="text-xl font-bold mb-4 text-zinc-100 border-b border-zinc-700 pb-2 flex items-center">
//         {icon}
//         {title}
//       </h2>
//     )}
//     {children}
//   </div>
// );

// const Button = ({
//   onClick,
//   children,
//   disabled = false,
//   variant = "primary",
//   className = "",
// }) => {
//   const baseStyle =
//     "w-full flex justify-center items-center py-3 px-4 rounded-xl shadow-lg text-sm font-medium transition-all";
//   const variants = {
//     primary: (isLoading) =>
//       isLoading
//         ? "bg-zinc-600 cursor-not-allowed"
//         : "bg-sky-600 hover:bg-sky-700 focus:ring-4 focus:ring-sky-500/50 text-white",
//     secondary: (isLoading) =>
//       isLoading
//         ? "bg-zinc-600 cursor-not-allowed"
//         : "bg-zinc-600 hover:bg-zinc-500 focus:ring-4 focus:ring-zinc-500/50 text-white",
//     tertiary: (isLoading) =>
//       isLoading
//         ? "bg-zinc-700 cursor-not-allowed"
//         : "bg-zinc-700 hover:bg-zinc-600 focus:ring-4 focus:ring-zinc-600/50 text-sky-300 border border-zinc-600 hover:border-zinc-500", // New style for simple demos
//   };
//   return (
//     <button
//       onClick={onClick}
//       disabled={disabled}
//       className={`${baseStyle} ${variants[variant](disabled)} ${className}`}
//     >
//       {disabled ? <Loader2 className="animate-spin mr-2" /> : children}
//     </button>
//   );
// };

// const ColumnConfig = ({ col, config, onConfigChange }) => {
//   // Use local state only for display values if needed, but config prop drives the logic
//   const [minValDisplay, setMinValDisplay] = useState(
//     config.min_val != null ? String(config.min_val) : ""
//   );
//   const [maxValDisplay, setMaxValDisplay] = useState(
//     config.max_val != null ? String(config.max_val) : ""
//   );

//   const handleConfigChange = (key, value) => {
//     onConfigChange(col.name, { ...config, [key]: value });
//   };

//   const handleMinMaxChange = (e, key) => {
//     const value = e.target.value;
//     // Update display immediately
//     if (key === "min_val") setMinValDisplay(value);
//     else setMaxValDisplay(value);
//     // Update parent config state (convert empty string to null, others to number)
//     onConfigChange(col.name, {
//       ...config,
//       [key]: value === "" ? null : Number(value),
//     });
//   };

//   return (
//     <div className="bg-zinc-700 p-4 rounded-lg border border-zinc-600 space-y-3">
//       <div className="flex justify-between items-center">
//         <span className="font-bold text-sky-400">{col.name}</span>
//         <select
//           value={config.data_type}
//           onChange={(e) => handleConfigChange("data_type", e.target.value)}
//           className="p-1 border border-zinc-500 bg-zinc-600 text-zinc-100 rounded-md text-xs"
//         >
//           <option value="Numerical">Numerical</option>
//           <option value="Categorical">Categorical</option>
//           <option value="Text">Text</option>
//         </select>
//       </div>

//       <div className="flex items-center space-x-2 text-sm">
//         <input
//           type="checkbox"
//           id={`feature-${col.name}`}
//           checked={config.is_feature}
//           onChange={(e) => handleConfigChange("is_feature", e.target.checked)}
//           className="h-4 w-4 rounded bg-zinc-600 border-zinc-500 text-sky-600 focus:ring-sky-500"
//         />
//         <label htmlFor={`feature-${col.name}`}>Use as Feature</label>
//       </div>

//       {config.data_type === "Numerical" && (
//         <div className="grid grid-cols-2 gap-2">
//           <input
//             type="number"
//             placeholder="Min Value"
//             value={minValDisplay} // Use display state
//             onChange={(e) => handleMinMaxChange(e, "min_val")} // Use display state setter
//             className="w-full text-sm p-2 border border-zinc-500 bg-zinc-600 text-zinc-100 rounded-lg focus:ring-sky-500 focus:border-sky-500"
//           />
//           <input
//             type="number"
//             placeholder="Max Value"
//             value={maxValDisplay} // Use display state
//             onChange={(e) => handleMinMaxChange(e, "max_val")} // Use display state setter
//             className="w-full text-sm p-2 border border-zinc-500 bg-zinc-600 text-zinc-100 rounded-lg focus:ring-sky-500 focus:border-sky-500"
//           />
//         </div>
//       )}

//       {config.data_type === "Categorical" && col.unique_values.length > 0 && (
//         <div className="text-xs text-zinc-400">
//           Detected values: {col.unique_values.slice(0, 3).join(", ")}
//           {col.unique_values.length > 3 ? "..." : ""}
//           {/* Add ability to view/edit valid categories if needed */}
//         </div>
//       )}
//     </div>
//   );
// };

// // --- Helper Functions ---

// const calculatePerformance = (flaggedRows, groundTruth, totalRows) => {
//   // Use string keys for flaggedRows, number indices for groundTruth
//   const predicted_indices = new Set(Object.keys(flaggedRows).map(Number));
//   // Ensure groundTruth and true_poison_indices exist
//   const true_indices = new Set(
//     groundTruth?.true_poison_indices?.map(Number) || []
//   );

//   let tp = 0,
//     fp = 0,
//     fn = 0,
//     tn = 0;

//   for (let i = 0; i < totalRows; i++) {
//     const isPredicted = predicted_indices.has(i);
//     const isTrue = true_indices.has(i);

//     if (isPredicted && isTrue) tp++;
//     else if (isPredicted && !isTrue) fp++;
//     else if (!isPredicted && isTrue) fn++;
//     else if (!isPredicted && !isTrue) tn++;
//   }

//   const precision = tp + fp > 0 ? tp / (tp + fp) : 0;
//   const recall = tp + fn > 0 ? tp / (tp + fn) : 0;
//   const f1 =
//     precision + recall > 0
//       ? (2 * (precision * recall)) / (precision + recall)
//       : 0;

//   // Note: Accuracy calculation was (tp + tn) / totalRows.
//   const accuracy = totalRows > 0 ? (tp + tn) / totalRows : 0; // Avoid division by zero

//   return {
//     "Total Rows": totalRows,
//     "True Poison": true_indices.size,
//     "Predicted Poison": predicted_indices.size,
//     "True Positives (TP)": tp,
//     "False Positives (FP)": fp,
//     "False Negatives (FN)": fn,
//     "True Negatives (TN)": tn,
//     Accuracy: (accuracy * 100).toFixed(2), // Convert to percentage
//     Precision: precision.toFixed(3),
//     Recall: recall.toFixed(3),
//     "F1-Score": f1.toFixed(3),
//   };
// };

// // --- Child Components ---

// // *** UPDATED WelcomeScreen Component ***
// const WelcomeScreen = ({
//   isLoading,
//   handleDemoLoad,
//   handleFileUpload,
//   datasetType,
//   setDatasetType,
//   error,
// }) => (
//   <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-6">
//     {/* Upload Card */}
//     <Card
//       title="Upload Your Data"
//       icon={<Upload className="w-5 h-5 mr-2 text-sky-400" />}
//       className="md:col-span-1"
//     >
//       <p className="text-sm text-zinc-400 mb-4">
//         Analyze your own CSV or Excel file.
//       </p>
//       <div className="mb-4">
//         <label className="block text-sm mb-2 text-zinc-300">Dataset Type</label>
//         <select
//           value={datasetType}
//           onChange={(e) => setDatasetType(e.target.value)}
//           className="w-full p-2 border border-zinc-600 bg-zinc-700 text-zinc-100 rounded-lg focus:ring-sky-500 focus:border-sky-500"
//         >
//           <option value="tabular">Tabular (Regression/Classification)</option>
//           <option value="text">Text (Classification)</option>
//         </select>
//       </div>
//       <input
//         type="file"
//         id="file-upload"
//         className="hidden"
//         accept=".csv, .xlsx"
//         onChange={(e) =>
//           e.target.files[0] && handleFileUpload(e.target.files[0])
//         }
//       />
//       <Button
//         onClick={() => document.getElementById("file-upload").click()}
//         disabled={isLoading}
//       >
//         <Upload className="mr-2" /> Upload File
//       </Button>
//     </Card>

//     {/* Demo Card - Now Organized */}
//     <Card
//       title="Load a Demo"
//       icon={<TestTube className="w-5 h-5 mr-2 text-sky-400" />}
//       className="md:col-span-1"
//     >
//       <p className="text-sm text-zinc-400 mb-4">
//         See how the tool works with pre-built, poisoned datasets.
//       </p>

//       {/* Tabular Demos Section */}
//       <div className="mb-6">
//         {" "}
//         {/* Added margin-bottom */}
//         <h3 className="text-md font-semibold text-zinc-300 mb-3 border-b border-zinc-700 pb-1 flex items-center">
//           <Database className="w-4 h-4 mr-2 text-sky-500" /> Tabular Demos
//         </h3>
//         <div className="space-y-3">
//           <Button
//             onClick={() => handleDemoLoad("tabular-classification-simple")}
//             disabled={isLoading}
//             variant="tertiary"
//             className="text-xs justify-start pl-4" // Align left
//           >
//             <Flower className="w-4 h-4 mr-2 flex-shrink-0" /> Iris
//             Classification (Simple)
//           </Button>
//           <Button
//             onClick={() => handleDemoLoad("tabular-regression-simple")}
//             disabled={isLoading}
//             variant="tertiary"
//             className="text-xs justify-start pl-4" // Align left
//           >
//             <FlaskConical className="w-4 h-4 mr-2 flex-shrink-0" /> Simple
//             Regression
//           </Button>
//           <Button
//             onClick={() => handleDemoLoad("tabular-regression")}
//             disabled={isLoading}
//             variant="secondary"
//             className="text-xs justify-start pl-4" // Align left
//           >
//             <Database className="w-4 h-4 mr-2 flex-shrink-0" /> California
//             Housing Regression
//           </Button>
//         </div>
//       </div>

//       {/* Text Demos Section */}
//       <div>
//         <h3 className="text-md font-semibold text-zinc-300 mb-3 border-b border-zinc-700 pb-1 flex items-center">
//           <FileText className="w-4 h-4 mr-2 text-sky-500" /> Text Demos
//         </h3>
//         <div className="space-y-3">
//           {/* --- NEW IMDB Button --- */}
//           <Button
//             onClick={() => handleDemoLoad("text-classification-imdb")}
//             disabled={isLoading}
//             variant="secondary"
//             className="text-xs justify-start pl-4" // Align left
//           >
//             <Film className="w-4 h-4 mr-2 flex-shrink-0" /> IMDB Movie Reviews
//           </Button>
//           {/* --- END NEW --- */}
//           <Button
//             onClick={() => handleDemoLoad("text-classification")}
//             disabled={isLoading}
//             variant="secondary"
//             className="text-xs justify-start pl-4" // Align left
//           >
//             <FileText className="w-4 h-4 mr-2 flex-shrink-0" /> 20 Newsgroups
//             Classification
//           </Button>
//         </div>
//       </div>
//     </Card>

//     {/* Error Message */}
//     {error && (
//       <div className="md:col-span-2 mt-4 p-3 bg-red-900/50 border border-red-700 text-red-300 rounded-xl text-sm">
//         {error}
//       </div>
//     )}
//   </div>
// );
// // *** END UPDATED WelcomeScreen ***

// const ConfigScreen = ({
//   fileInfo,
//   columnInfo,
//   config,
//   onColumnConfigChange,
//   isLoading,
//   error,
//   handleRunSanitize,
//   datasetType,
//   targetVar,
//   setTargetVar,
//   mlTask,
//   setMlTask,
//   textCol,
//   setTextCol,
// }) => {
//   const onRunSanitizeClick = () => {
//     let finalConfig = {};

//     // Update config with final feature/target settings
//     const finalColumnConfigs = Object.entries(config).map(
//       ([colName, colConfig]) => ({
//         ...colConfig, // Spread existing config for the column
//         col_name: colName, // <-- Ensure col_name is included
//         // Ensure target is not a feature
//         is_feature:
//           datasetType === "tabular"
//             ? colName !== targetVar && colConfig.is_feature
//             : colName !== textCol &&
//               colName !== targetVar &&
//               colConfig.is_feature,
//       })
//     );

//     if (datasetType === "tabular") {
//       finalConfig = {
//         ml_task: mlTask,
//         target_variable: targetVar,
//         columns: finalColumnConfigs, // Now contains objects with 'col_name'
//       };
//     } else {
//       // datasetType === 'text'
//       finalConfig = {
//         text_column: textCol,
//         target_column: targetVar,
//         phase_1_settings: {
//           // Add default phase 1 settings for text if not configured elsewhere
//           min_length: 10,
//           max_length: 5000,
//           flag_urls: true,
//           flag_html: true,
//         },
//         // Pass column configs for any *other* potential features
//         columns: finalColumnConfigs.filter(
//           (c) => c.col_name !== textCol && c.col_name !== targetVar
//         ),
//       };
//     }
//     // Call the actual sanitize handler passed down as a prop
//     handleRunSanitize(finalConfig);
//   };

//   return (
//     <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
//       <Card
//         title="1. Configure Pipeline"
//         icon={<FileScan className="w-5 h-5 mr-2 text-sky-400" />}
//         className="lg:col-span-1"
//       >
//         <div className="mb-4 p-3 bg-zinc-700 rounded-lg border border-zinc-600">
//           <p className="text-sm text-zinc-300">
//             File:{" "}
//             <span className="font-medium text-sky-400">
//               {fileInfo.filename}
//             </span>
//           </p>
//           <p className="text-sm text-zinc-300">
//             Rows:{" "}
//             <span className="font-medium text-zinc-100">
//               {fileInfo.rowCount}
//             </span>
//           </p>
//         </div>
//         <div className="space-y-4">
//           {datasetType === "tabular" ? (
//             <>
//               <div className="mb-4">
//                 <label className="block text-sm mb-2 text-zinc-300">
//                   ML Task
//                 </label>
//                 <select
//                   value={mlTask}
//                   onChange={(e) => setMlTask(e.target.value)}
//                   className="w-full p-2 border border-zinc-600 bg-zinc-700 text-zinc-100 rounded-lg focus:ring-sky-500 focus:border-sky-500"
//                 >
//                   <option value="regression">Regression</option>
//                   <option value="classification">Classification</option>
//                 </select>
//               </div>
//               <div className="mb-4">
//                 <label className="block text-sm mb-2 text-zinc-300">
//                   Target Variable (y)
//                 </label>
//                 <select
//                   value={targetVar}
//                   onChange={(e) => setTargetVar(e.target.value)}
//                   className="w-full p-2 border border-zinc-600 bg-zinc-700 text-zinc-100 rounded-lg focus:ring-sky-500 focus:border-sky-500"
//                 >
//                   <option value="">-- Select Target --</option>
//                   {/* Filter out potential non-string column names if necessary */}
//                   {columnInfo
//                     .filter((c) => typeof c.name === "string")
//                     .map((c) => (
//                       <option key={c.name} value={c.name}>
//                         {c.name}
//                       </option>
//                     ))}
//                 </select>
//               </div>
//             </>
//           ) : (
//             <>
//               <div className="mb-4">
//                 <label className="block text-sm mb-2 text-zinc-300">
//                   Text Column (X)
//                 </label>
//                 <select
//                   value={textCol}
//                   onChange={(e) => setTextCol(e.target.value)}
//                   className="w-full p-2 border border-zinc-600 bg-zinc-700 text-zinc-100 rounded-lg focus:ring-sky-500 focus:border-sky-500"
//                 >
//                   <option value="">-- Select Text Column --</option>
//                   {columnInfo
//                     .filter((c) => typeof c.name === "string")
//                     .map((c) => (
//                       <option key={c.name} value={c.name}>
//                         {c.name}
//                       </option>
//                     ))}
//                 </select>
//               </div>
//               <div className="mb-4">
//                 <label className="block text-sm mb-2 text-zinc-300">
//                   Target Column (y)
//                 </label>
//                 <select
//                   value={targetVar}
//                   onChange={(e) => setTargetVar(e.target.value)}
//                   className="w-full p-2 border border-zinc-600 bg-zinc-700 text-zinc-100 rounded-lg focus:ring-sky-500 focus:border-sky-500"
//                 >
//                   <option value="">-- Select Target --</option>
//                   {columnInfo
//                     .filter((c) => typeof c.name === "string")
//                     .map((c) => (
//                       <option key={c.name} value={c.name}>
//                         {c.name}
//                       </option>
//                     ))}
//                 </select>
//               </div>
//             </>
//           )}

//           <Button
//             onClick={onRunSanitizeClick}
//             disabled={
//               isLoading || !targetVar || (datasetType === "text" && !textCol)
//             }
//           >
//             <Zap className="mr-2" /> Run Sanitization
//           </Button>
//           {error && (
//             <div className="mt-4 p-3 bg-red-900/50 border border-red-700 text-red-300 rounded-xl text-sm">
//               {error}
//             </div>
//           )}
//         </div>
//       </Card>

//       <Card
//         title="2. Review Columns"
//         icon={<Database className="w-5 h-5 mr-2 text-sky-400" />}
//         className="lg:col-span-2"
//       >
//         <p className="text-sm text-zinc-400 mb-4">
//           Review the auto-detected column types and set constraints for Phase 1.
//         </p>
//         <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-[60vh] overflow-y-auto pr-2">
//           {/* Ensure config exists for the column before rendering */}
//           {columnInfo
//             .filter((c) => typeof c.name === "string")
//             .map((col) => (
//               <ColumnConfig
//                 key={col.name}
//                 col={col}
//                 config={
//                   config[col.name] || {
//                     data_type: col.auto_type,
//                     is_feature: true,
//                     min_val: null,
//                     max_val: null,
//                     unique_values: col.unique_values || [],
//                   }
//                 } // Provide default config
//                 onConfigChange={onColumnConfigChange}
//               />
//             ))}
//         </div>
//       </Card>
//     </div>
//   );
// };

// // --- MODIFIED ResultsScreen ---
// const ResultsScreen = ({
//   metrics,
//   fullData,
//   flaggedRows,
//   groundTruth,
//   datasetType,
//   textCol, // The actual text column name from config
//   targetCol, // The actual target column name from config (needed for display)
//   resetApp,
// }) => {
//   const [page, setPage] = useState(1);

//   const tableData = useMemo(() => {
//     // Ensure fullData is an array before mapping
//     if (!Array.isArray(fullData)) return [];

//     return fullData.map((row, index) => {
//       // Use safe prototype-safe check
//       const isFlagged = Object.prototype.hasOwnProperty.call(
//         flaggedRows,
//         String(index)
//       ); // Ensure index is string for check
//       // Ensure groundTruth and its property exist before accessing
//       const isTruePoison = groundTruth?.true_poison_indices?.includes(index);

//       let status = "clean";
//       // Only determine status if groundTruth exists
//       if (groundTruth) {
//         if (isFlagged && isTruePoison) status = "tp"; // True Positive
//         else if (isFlagged && !isTruePoison) status = "fp"; // False Positive
//         else if (!isFlagged && isTruePoison) status = "fn"; // False Negative
//       }

//       return {
//         ...row,
//         index,
//         is_flagged: isFlagged,
//         reason: isFlagged ? flaggedRows[String(index)] : "---", // Use string index
//         is_actual_poisoned: groundTruth ? isTruePoison : null, // Can be null if not demo
//         status: status,
//       };
//     });
//   }, [fullData, flaggedRows, groundTruth]);

//   // Filter flagged rows *after* mapping
//   const flaggedTableData = tableData.filter((row) => row.is_flagged);
//   const totalFlagged = flaggedTableData.length;

//   const paginatedData = flaggedTableData.slice(
//     (page - 1) * PAGE_SIZE,
//     page * PAGE_SIZE
//   );

//   // --- REFINED METRICS DISPLAY LOGIC ---
//   // Check if metrics object exists and is not empty
//   const hasMetrics =
//     metrics && typeof metrics === "object" && Object.keys(metrics).length > 0;

//   // Determine which metrics to display based on whether it's a demo run (presence of groundTruth implies detailed metrics)
//   const isDemoRun = !!groundTruth;
//   let metricsToDisplay = {};
//   if (hasMetrics) {
//     // If it's a demo run, expect the detailed metrics from the backend
//     if (isDemoRun) {
//       metricsToDisplay = metrics;
//     } else {
//       // If it's a user upload, display only the basic counts from the metrics object
//       metricsToDisplay = {
//         "Total Rows": metrics["Total Rows"],
//         "Flagged Rows": metrics["Flagged Rows"],
//       };
//     }
//   }
//   const metricGridCols = isDemoRun ? "lg:grid-cols-5" : "lg:grid-cols-2"; // Adjust grid columns
//   // --- END REFINED LOGIC ---

//   // --- Helper to display tabular data row ---
//   const renderTabularRowData = (row) => {
//     return Object.entries(row)
//       .filter(
//         ([key]) =>
//           key !== "index" &&
//           key !== "is_flagged" &&
//           key !== "reason" &&
//           key !== "is_actual_poisoned" &&
//           key !== "status"
//       )
//       .map(([key, val]) => {
//         // Highlight the target column
//         const isTarget = key === targetCol;
//         const displayVal =
//           String(val).slice(0, 20) + (String(val).length > 20 ? "..." : ""); // Truncate long values
//         return (
//           <span
//             key={key}
//             className={`mr-2 ${isTarget ? "font-bold text-sky-300" : ""}`}
//           >
//             {key}:{" "}
//             <span className={isTarget ? "" : "text-zinc-400"}>
//               {displayVal}
//             </span>
//           </span>
//         );
//       });
//   };
//   // --- End Helper ---

//   return (
//     <div className="space-y-8">
//       {/* Metrics Card */}
//       <Card
//         title="3. Performance Report"
//         icon={<BarChart3 className="w-5 h-5 mr-2 text-sky-400" />}
//       >
//         {/* Use the refined check: hasMetrics */}
//         {hasMetrics ? (
//           <div
//             className={`grid grid-cols-2 md:grid-cols-3 ${metricGridCols} gap-4 text-center`}
//           >
//             {Object.entries(metricsToDisplay).map(
//               ([key, value]) =>
//                 // Ensure value is not undefined/null before rendering the block
//                 value !== undefined &&
//                 value !== null && (
//                   <div
//                     key={key}
//                     className="bg-zinc-700 rounded-lg p-3 border border-zinc-600"
//                   >
//                     <p className="text-sm text-sky-400 font-semibold">
//                       {key.replace(/_/g, " ").toUpperCase()}
//                     </p>
//                     <p className="text-2xl font-bold">
//                       {/* Display numbers or string representation */}
//                       {typeof value === "number" ? value : String(value)}
//                     </p>
//                   </div>
//                 )
//             )}
//           </div>
//         ) : (
//           <p className="text-center text-zinc-400">
//             Run analysis to see metrics.
//           </p>
//         )}
//       </Card>

//       {/* Results Table Card */}
//       <Card
//         title={`4. Flagged Rows (${totalFlagged} found)`}
//         icon={<AlertTriangle className="w-5 h-5 mr-2 text-sky-400" />}
//       >
//         {totalFlagged > 0 ? (
//           <>
//             <div className="overflow-x-auto mt-4 rounded-xl border border-zinc-700">
//               <table className="min-w-full divide-y divide-zinc-700">
//                 <thead className="bg-zinc-700">
//                   <tr>
//                     <th className="px-4 py-3 text-left text-xs font-medium text-zinc-300 uppercase">
//                       Index
//                     </th>
//                     <th className="px-4 py-3 text-left text-xs font-medium text-zinc-300 uppercase">
//                       {datasetType === "text"
//                         ? textCol || "Text"
//                         : "Sample Data"}
//                     </th>
//                     <th className="px-4 py-3 text-left text-xs font-medium text-zinc-300 uppercase">
//                       Reason Flagged
//                     </th>
//                     {groundTruth && (
//                       <th className="px-4 py-3 text-left text-xs font-medium text-zinc-300 uppercase">
//                         Ground Truth
//                       </th>
//                     )}
//                   </tr>
//                 </thead>
//                 <tbody className="bg-zinc-800 divide-y divide-zinc-700 text-sm">
//                   {paginatedData.map((row) => (
//                     <tr
//                       key={row.index}
//                       className={`
//                         ${
//                           groundTruth && row.status === "tp"
//                             ? "bg-green-900/30 text-green-300"
//                             : ""
//                         }
//                         ${
//                           groundTruth && row.status === "fp"
//                             ? "bg-yellow-900/30 text-yellow-300"
//                             : ""
//                         }
//                          ${
//                            // Added FN highlighting
//                            groundTruth && row.status === "fn"
//                              ? "bg-red-900/30 text-red-300"
//                              : ""
//                          }
//                         ${
//                           !groundTruth && row.is_flagged
//                             ? "bg-red-900/30 text-red-300" // Keep red for user uploads
//                             : ""
//                         }
//                         hover:bg-zinc-700/50
//                       `}
//                     >
//                       <td className="px-4 py-3 font-mono">{row.index}</td>
//                       <td className="px-4 py-3 max-w-xl">
//                         {" "}
//                         {/* Increased max-width */}
//                         {/* Display relevant data based on type */}
//                         {
//                           datasetType === "text" && textCol && row[textCol] ? ( // Check if textCol and row[textCol] exist
//                             <span className="block truncate">
//                               {row[textCol]}
//                             </span> // Use truncate for text
//                           ) : datasetType === "tabular" ? (
//                             renderTabularRowData(row) // Use helper function
//                           ) : (
//                             "N/A"
//                           ) // Fallback
//                         }
//                       </td>
//                       <td className="px-4 py-3 text-red-300">{row.reason}</td>
//                       {groundTruth && (
//                         <td className="px-4 py-3">
//                           {row.is_actual_poisoned ? (
//                             <span className="flex items-center text-red-400">
//                               <AlertTriangle className="w-4 h-4 mr-1" /> Poison
//                             </span>
//                           ) : (
//                             <span className="flex items-center text-green-400">
//                               <CheckCircle className="w-4 h-4 mr-1" /> Clean
//                             </span>
//                           )}
//                         </td>
//                       )}
//                     </tr>
//                   ))}
//                 </tbody>
//               </table>
//             </div>

//             {/* Pagination Controls */}
//             {totalFlagged > PAGE_SIZE && (
//               <div className="flex justify-between items-center mt-4 text-sm text-zinc-300">
//                 <button
//                   onClick={() => setPage((p) => Math.max(p - 1, 1))}
//                   disabled={page === 1}
//                   className="px-3 py-1 bg-zinc-700 rounded hover:bg-zinc-600 disabled:opacity-50 flex items-center"
//                 >
//                   <ChevronLeft className="w-4 h-4 mr-1" /> Previous
//                 </button>
//                 <span>
//                   Page {page} / {Math.ceil(totalFlagged / PAGE_SIZE)}
//                 </span>
//                 <button
//                   onClick={() =>
//                     setPage((p) =>
//                       Math.min(p + 1, Math.ceil(totalFlagged / PAGE_SIZE))
//                     )
//                   }
//                   disabled={page === Math.ceil(totalFlagged / PAGE_SIZE)}
//                   className="px-3 py-1 bg-zinc-700 rounded hover:bg-zinc-600 disabled:opacity-50 flex items-center"
//                 >
//                   Next <ChevronRight className="w-4 h-4 ml-1" />
//                 </button>
//               </div>
//             )}
//           </>
//         ) : (
//           <p className="text-center text-zinc-400 py-4">
//             No rows were flagged by the pipeline.
//           </p>
//         )}
//       </Card>

//       <div className="flex space-x-4">
//         <Button onClick={resetApp} variant="secondary">
//           <ChevronLeft className="mr-2" /> Start Over
//         </Button>
//         <Button
//           onClick={() => alert("Export logic not implemented")}
//           variant="primary"
//         >
//           <FileText className="mr-2" /> Export Cleaned Data
//         </Button>
//       </div>
//     </div>
//   );
// };
// // --- END MODIFIED ResultsScreen ---

// const ProcessingScreen = ({ stage }) => (
//   <div className="flex flex-col items-center justify-center h-64">
//     <Loader2 className="animate-spin h-12 w-12 text-sky-400" />
//     <p className="mt-4 text-zinc-300">
//       {stage === "processing"
//         ? "Running analysis... this may take a moment."
//         : "Loading data..."}
//     </p>
//     {stage === "processing" && (
//       <p className="text-sm text-zinc-500">
//         (Embeddings and canary models are being processed)
//       </p>
//     )}
//   </div>
// );

// // --- Main App Component ---

// const App = () => {
//   const [stage, setStage] = useState("idle"); // 'idle', 'configuring', 'processing', 'results'
//   const [isLoading, setIsLoading] = useState(false);
//   const [error, setError] = useState(null);

//   // Data state
//   const [fileInfo, setFileInfo] = useState(null); // { filename, rowCount }
//   const [columnInfo, setColumnInfo] = useState([]); // [ { name, auto_type, unique_values } ]
//   const [fullData, setFullData] = useState([]); // [ { col1: val, ... }, ... ]
//   const [groundTruth, setGroundTruth] = useState(null); // { true_poison_indices: [...] }
//   const [datasetType, setDatasetType] = useState("tabular"); // 'tabular' or 'text'

//   // Config state - holds the configuration for *each* column by name
//   const [config, setConfig] = useState({}); // e.g., { 'colA': {data_type: 'Num', is_feature: true}, 'colB': {...} }
//   const [targetVar, setTargetVar] = useState(""); // Name of the target variable column
//   const [mlTask, setMlTask] = useState("regression"); // Only for tabular
//   const [textCol, setTextCol] = useState(""); // Only for text

//   // Results state
//   const [flaggedRows, setFlaggedRows] = useState({}); // { "10": "Reason...", "42": "Reason..." }
//   const [metrics, setMetrics] = useState(null); // <-- Start as null

//   // --- API Handlers ---

//   const handleApiCall = async (apiCall) => {
//     setIsLoading(true);
//     setError(null);
//     try {
//       await apiCall();
//     } catch (err) {
//       console.error("API Call Error:", err);
//       setError(err.message || "An unknown error occurred.");
//       // Optionally reset stage on error if needed
//       // setStage('idle');
//     } finally {
//       setIsLoading(false);
//     }
//   };

//   const handleDemoLoad = (demoType) =>
//     handleApiCall(async () => {
//       const response = await fetch(`${FLASK_API_URL}/load-demo`, {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({ type: demoType }),
//       });
//       const data = await response.json();
//       if (data.error) throw new Error(data.error);

//       // Check if data loaded successfully before proceeding
//       if (!data.columnInfo || !data.fullData) {
//         throw new Error(
//           "Demo data loading failed: Missing columnInfo or fullData."
//         );
//       }

//       // Initialize config from columnInfo
//       const initialConfig = {};
//       // Ensure columnInfo is an array
//       const cols = Array.isArray(data.columnInfo) ? data.columnInfo : [];
//       cols.forEach((col) => {
//         if (col && typeof col.name === "string") {
//           // Add checks
//           initialConfig[col.name] = {
//             data_type:
//               col.auto_type ||
//               (demoType.startsWith("tabular") ? "Categorical" : "Text"),
//             // Basic heuristic for default feature selection
//             // Assume feature unless it's clearly a target/ID/text
//             is_feature:
//               !col.name.toLowerCase().includes("target") &&
//               !col.name.toLowerCase().includes("price") &&
//               !col.name.toLowerCase().includes("species") &&
//               !col.name.toLowerCase().includes("sentiment") && // Added sentiment
//               !col.name.toLowerCase().includes("review") && // Added review
//               !col.name.toLowerCase().includes("text") &&
//               !col.name.toLowerCase().includes("id"), // Assume ID cols are not features
//             min_val: null,
//             max_val: null,
//             // Include unique values if provided (for Categorical display)
//             unique_values: col.unique_values || [],
//           };
//         }
//       });

//       const newDatasetType = demoType.startsWith("tabular")
//         ? "tabular"
//         : "text";
//       setDatasetType(newDatasetType);

//       // Set initial target/text cols based on common names
//       const safeColumnInfo = Array.isArray(data.columnInfo)
//         ? data.columnInfo
//         : []; // Ensure array

//       let foundTarget = "";
//       let foundText = "";

//       if (newDatasetType === "tabular") {
//         foundTarget = safeColumnInfo.find(
//           (c) =>
//             c &&
//             (c.name.toLowerCase().includes("price") ||
//               c.name.toLowerCase().includes("target") ||
//               c.name.toLowerCase().includes("species"))
//         )?.name;
//         setTargetVar(
//           foundTarget || safeColumnInfo[safeColumnInfo.length - 1]?.name || ""
//         );
//         setMlTask(
//           demoType.includes("regression") ? "regression" : "classification"
//         ); // Set task based on demo type
//       } else {
//         // Text
//         foundTarget = safeColumnInfo.find(
//           (c) =>
//             c &&
//             (c.name.toLowerCase().includes("target") ||
//               c.name.toLowerCase().includes("label") ||
//               c.name.toLowerCase().includes("sentiment")) // Added sentiment
//         )?.name;
//         foundText = safeColumnInfo.find(
//           (c) =>
//             c &&
//             (c.name.toLowerCase().includes("text") ||
//               c.name.toLowerCase().includes("review") || // Added review
//               c.name.toLowerCase().includes("comment"))
//         )?.name;

//         setTargetVar(
//           foundTarget || safeColumnInfo[safeColumnInfo.length - 1]?.name || ""
//         );
//         setTextCol(foundText || safeColumnInfo[0]?.name || "");
//       }

//       setConfig(initialConfig);
//       // Ensure fullData is an array
//       setFullData(Array.isArray(data.fullData) ? data.fullData : []);
//       setColumnInfo(safeColumnInfo); // Use safeColumnInfo
//       setGroundTruth(data.groundTruth);
//       setFileInfo({ filename: data.filename, rowCount: data.rowCount });
//       setStage("configuring");
//     });

//   const handleFileUpload = (file) =>
//     handleApiCall(async () => {
//       const formData = new FormData();
//       formData.append("file", file);
//       formData.append("dataset_type", datasetType);

//       const response = await fetch(`${FLASK_API_URL}/upload`, {
//         method: "POST",
//         body: formData,
//       });

//       const data = await response.json();
//       if (data.error) throw new Error(data.error);

//       // Check if data loaded successfully
//       if (!data.columnInfo || !data.fullData) {
//         throw new Error(
//           "File upload processing failed: Missing columnInfo or fullData."
//         );
//       }

//       // Initialize config from columnInfo
//       const initialConfig = {};
//       const cols = Array.isArray(data.columnInfo) ? data.columnInfo : [];
//       cols.forEach((col) => {
//         if (col && typeof col.name === "string") {
//           initialConfig[col.name] = {
//             data_type:
//               col.auto_type ||
//               (datasetType === "tabular" ? "Categorical" : "Text"),
//             // Default feature unless clearly target/text/id
//             is_feature:
//               !col.name.toLowerCase().includes("target") &&
//               !col.name.toLowerCase().includes("price") &&
//               !col.name.toLowerCase().includes("species") &&
//               !col.name.toLowerCase().includes("sentiment") &&
//               !col.name.toLowerCase().includes("review") &&
//               !col.name.toLowerCase().includes("text") &&
//               !col.name.toLowerCase().includes("id"),
//             min_val: null,
//             max_val: null,
//             unique_values: col.unique_values || [],
//           };
//         }
//       });

//       // Set initial target/text cols
//       const safeColumnInfo = Array.isArray(data.columnInfo)
//         ? data.columnInfo
//         : [];
//       let foundTarget = "";
//       let foundText = "";

//       if (datasetType === "tabular") {
//         foundTarget = safeColumnInfo.find(
//           (c) =>
//             c &&
//             (c.name.toLowerCase().includes("target") ||
//               c.name.toLowerCase().includes("price"))
//         )?.name;
//         setTargetVar(
//           foundTarget || safeColumnInfo[safeColumnInfo.length - 1]?.name || ""
//         );
//       } else {
//         // Text
//         foundTarget = safeColumnInfo.find(
//           (c) =>
//             c &&
//             (c.name.toLowerCase().includes("target") ||
//               c.name.toLowerCase().includes("label") ||
//               c.name.toLowerCase().includes("sentiment"))
//         )?.name;
//         foundText = safeColumnInfo.find(
//           (c) =>
//             c &&
//             (c.name.toLowerCase().includes("text") ||
//               c.name.toLowerCase().includes("review") ||
//               c.name.toLowerCase().includes("comment"))
//         )?.name;

//         setTargetVar(
//           foundTarget || safeColumnInfo[safeColumnInfo.length - 1]?.name || ""
//         );
//         setTextCol(foundText || safeColumnInfo[0]?.name || "");
//       }

//       setConfig(initialConfig);
//       setFullData(Array.isArray(data.fullData) ? data.fullData : []);
//       setColumnInfo(safeColumnInfo);
//       setGroundTruth(null); // No ground truth for user-uploaded files
//       setFileInfo({ filename: file.name, rowCount: data.rowCount });
//       setStage("configuring");
//     });

//   const handleRunSanitize = (finalConfig) =>
//     handleApiCall(async () => {
//       setStage("processing");

//       const payload = {
//         data: fullData,
//         config: finalConfig,
//         // Send groundTruth back if it exists
//         ...(groundTruth && { groundTruth: groundTruth }),
//       };

//       const response = await fetch(`${FLASK_API_URL}/sanitize`, {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify(payload),
//       });

//       const data = await response.json();

//       if (data.error) throw new Error(data.error);

//       const receivedFlaggedRows = data.flagged_rows || {};

//       setFlaggedRows(receivedFlaggedRows);

//       // Calculate metrics on the frontend
//       if (groundTruth) {
//         // Demo mode: Calculate full performance
//         const perf = calculatePerformance(
//           receivedFlaggedRows,
//           groundTruth,
//           fullData.length // Use length of original full data for total
//         );
//         setMetrics(perf);
//       } else {
//         // User upload mode: Calculate basic stats
//         const basicMetrics = {
//           "Total Rows": fullData.length, // Use length of original full data
//           "Flagged Rows": Object.keys(receivedFlaggedRows).length,
//         };
//         setMetrics(basicMetrics);
//       }

//       setStage("results");
//     });

//   const resetApp = () => {
//     setStage("idle");
//     setIsLoading(false);
//     setError(null);
//     setFileInfo(null);
//     setColumnInfo([]);
//     setFullData([]);
//     setGroundTruth(null);
//     setConfig({});
//     setFlaggedRows({});
//     setMetrics(null); // <-- Reset to null
//     setTargetVar("");
//     setMlTask("regression");
//     setTextCol("");
//   };

//   const handleColumnConfigChange = (colName, newColConfig) => {
//     setConfig((prev) => ({ ...prev, [colName]: newColConfig }));
//   };

//   // --- Main Render Logic ---

//   const renderCurrentStage = () => {
//     // Show loading overlay during API calls for upload/demo load
//     if (isLoading && (stage === "idle" || stage === "configuring")) {
//       return <ProcessingScreen stage="loading" />;
//     }
//     // Show processing screen during sanitize call
//     if (stage === "processing") {
//       return <ProcessingScreen stage="processing" />;
//     }

//     switch (stage) {
//       case "idle":
//         return (
//           <WelcomeScreen
//             isLoading={isLoading}
//             handleDemoLoad={handleDemoLoad}
//             handleFileUpload={handleFileUpload}
//             datasetType={datasetType}
//             setDatasetType={setDatasetType}
//             error={error}
//           />
//         );
//       case "configuring":
//         // Ensure necessary props are valid before rendering ConfigScreen
//         if (!fileInfo || !columnInfo || !config) {
//           // Optionally show a specific loading or error state, or reset
//           console.error("ConfigScreen: Missing required props", {
//             fileInfo,
//             columnInfo,
//             config,
//           });
//           resetApp(); // Reset if state is inconsistent
//           return <ProcessingScreen stage="loading" />; // Or show loading
//         }
//         return (
//           <ConfigScreen
//             fileInfo={fileInfo}
//             columnInfo={columnInfo}
//             config={config}
//             onColumnConfigChange={handleColumnConfigChange}
//             isLoading={isLoading}
//             error={error}
//             handleRunSanitize={handleRunSanitize}
//             datasetType={datasetType}
//             targetVar={targetVar}
//             setTargetVar={setTargetVar}
//             mlTask={mlTask}
//             setMlTask={setMlTask}
//             textCol={textCol}
//             setTextCol={setTextCol}
//           />
//         );
//       case "results":
//         // Ensure necessary props are valid before rendering ResultsScreen
//         // MODIFIED CHECK: metrics and flaggedRows can be {} but not null.
//         if (
//           metrics === null ||
//           !Array.isArray(fullData) ||
//           flaggedRows === null
//         ) {
//           console.error(
//             "ResultsScreen: Missing or invalid required props. State is likely inconsistent. Resetting.",
//             {
//               metrics,
//               fullData,
//               flaggedRows,
//             }
//           );
//           resetApp();
//           return <ProcessingScreen stage="loading" />;
//         }
//         return (
//           <ResultsScreen
//             metrics={metrics}
//             fullData={fullData}
//             flaggedRows={flaggedRows}
//             groundTruth={groundTruth}
//             datasetType={datasetType}
//             textCol={textCol} // Pass the name of the text column
//             targetCol={targetVar} // Pass the name of the target column
//             resetApp={resetApp}
//           />
//         );
//       default:
//         // Fallback to welcome screen if stage is invalid
//         return (
//           <WelcomeScreen
//             isLoading={isLoading}
//             handleDemoLoad={handleDemoLoad}
//             handleFileUpload={handleFileUpload}
//             datasetType={datasetType}
//             setDatasetType={setDatasetType}
//             error={error}
//           />
//         );
//     }
//   };

//   return (
//     <div className="min-h-screen bg-zinc-900 p-6 md:p-10 font-sans text-zinc-100">
//       <div className="max-w-7xl mx-auto">
//         <header className="flex justify-between items-center mb-10">
//           <h1 className="text-4xl font-extrabold text-sky-400 flex items-center">
//             <Database className="inline w-8 h-8 mr-3" /> PoisonGuard
//           </h1>
//           {stage !== "idle" && (
//             <button
//               onClick={resetApp}
//               className="flex items-center text-sm text-zinc-400 hover:text-red-400 transition-colors"
//               title="Reset application state"
//             >
//               <XCircle className="w-4 h-4 mr-1" /> Reset
//             </button>
//           )}
//         </header>

//         {renderCurrentStage()}
//       </div>
//     </div>
//   );
// };

// export default App;

import React, { useState, useMemo } from "react";
import {
  Zap,
  Database,
  Loader2,
  BarChart3,
  AlertTriangle,
  CheckCircle,
  Upload,
  FileScan,
  TestTube,
  ChevronRight,
  ChevronLeft,
  XCircle,
  FileText,
  FlaskConical, // Added icon for simple demos
  Flower, // Added icon for Iris
  Film, // Added icon for IMDB
  Download, // <-- Added Download icon
} from "lucide-react";

// --- API Configuration ---
const FLASK_API_URL = "http://127.0.0.1:5000/api"; // Corrected IP
const PAGE_SIZE = 20; // For results table pagination

// --- Reusable UI Components ---

const Card = ({ title, icon, children, className = "" }) => (
  <div
    className={`bg-zinc-800 p-6 rounded-2xl shadow-xl border border-zinc-700 ${className}`}
  >
    {title && (
      <h2 className="text-xl font-bold mb-4 text-zinc-100 border-b border-zinc-700 pb-2 flex items-center">
        {icon}
        {title}
      </h2>
    )}
    {children}
  </div>
);

const Button = ({
  onClick,
  children,
  disabled = false,
  variant = "primary",
  className = "",
}) => {
  const baseStyle =
    "w-full flex justify-center items-center py-3 px-4 rounded-xl shadow-lg text-sm font-medium transition-all";
  const variants = {
    primary: (isLoading) =>
      isLoading
        ? "bg-zinc-600 cursor-not-allowed text-zinc-400" // Adjusted disabled style
        : "bg-sky-600 hover:bg-sky-700 focus:ring-4 focus:ring-sky-500/50 text-white",
    secondary: (isLoading) =>
      isLoading
        ? "bg-zinc-600 cursor-not-allowed text-zinc-400"
        : "bg-zinc-600 hover:bg-zinc-500 focus:ring-4 focus:ring-zinc-500/50 text-white",
    tertiary: (isLoading) =>
      isLoading
        ? "bg-zinc-700 cursor-not-allowed text-zinc-500"
        : "bg-zinc-700 hover:bg-zinc-600 focus:ring-4 focus:ring-zinc-600/50 text-sky-300 border border-zinc-600 hover:border-zinc-500",
  };
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`${baseStyle} ${variants[variant](disabled)} ${className}`}
    >
      {disabled && variant === "primary" ? (
        <Loader2 className="animate-spin mr-2" />
      ) : (
        children
      )}{" "}
      {/* Show loader only on primary disabled */}
    </button>
  );
};

const ColumnConfig = ({ col, config, onConfigChange }) => {
  const [minValDisplay, setMinValDisplay] = useState(
    config.min_val != null ? String(config.min_val) : ""
  );
  const [maxValDisplay, setMaxValDisplay] = useState(
    config.max_val != null ? String(config.max_val) : ""
  );

  const handleConfigChange = (key, value) => {
    onConfigChange(col.name, { ...config, [key]: value });
  };

  const handleMinMaxChange = (e, key) => {
    const value = e.target.value;
    if (key === "min_val") setMinValDisplay(value);
    else setMaxValDisplay(value);
    onConfigChange(col.name, {
      ...config,
      [key]: value === "" ? null : Number(value),
    });
  };

  return (
    <div className="bg-zinc-700 p-4 rounded-lg border border-zinc-600 space-y-3">
      <div className="flex justify-between items-center">
        <span className="font-bold text-sky-400">{col.name}</span>
        <select
          value={config.data_type}
          onChange={(e) => handleConfigChange("data_type", e.target.value)}
          className="p-1 border border-zinc-500 bg-zinc-600 text-zinc-100 rounded-md text-xs"
        >
          <option value="Numerical">Numerical</option>
          <option value="Categorical">Categorical</option>
          <option value="Text">Text</option>
        </select>
      </div>
      <div className="flex items-center space-x-2 text-sm">
        <input
          type="checkbox"
          id={`feature-${col.name}`}
          checked={config.is_feature}
          onChange={(e) => handleConfigChange("is_feature", e.target.checked)}
          className="h-4 w-4 rounded bg-zinc-600 border-zinc-500 text-sky-600 focus:ring-sky-500"
        />
        <label htmlFor={`feature-${col.name}`}>Use as Feature</label>
      </div>
      {config.data_type === "Numerical" && (
        <div className="grid grid-cols-2 gap-2">
          <input
            type="number"
            placeholder="Min Value"
            value={minValDisplay}
            onChange={(e) => handleMinMaxChange(e, "min_val")}
            className="w-full text-sm p-2 border border-zinc-500 bg-zinc-600 text-zinc-100 rounded-lg focus:ring-sky-500 focus:border-sky-500"
          />
          <input
            type="number"
            placeholder="Max Value"
            value={maxValDisplay}
            onChange={(e) => handleMinMaxChange(e, "max_val")}
            className="w-full text-sm p-2 border border-zinc-500 bg-zinc-600 text-zinc-100 rounded-lg focus:ring-sky-500 focus:border-sky-500"
          />
        </div>
      )}
      {config.data_type === "Categorical" && col.unique_values?.length > 0 && (
        <div className="text-xs text-zinc-400">
          Detected values: {col.unique_values.slice(0, 3).join(", ")}
          {col.unique_values.length > 3 ? "..." : ""}
        </div>
      )}
    </div>
  );
};

// --- Helper Functions ---

const calculatePerformance = (flaggedRows, groundTruth, totalRows) => {
  const predicted_indices = new Set(Object.keys(flaggedRows || {}).map(Number)); // Handle null/undefined flaggedRows
  const true_indices = new Set(
    groundTruth?.true_poison_indices?.map(Number) || []
  );

  let tp = 0,
    fp = 0,
    fn = 0,
    tn = 0;

  for (let i = 0; i < totalRows; i++) {
    const isPredicted = predicted_indices.has(i);
    const isTrue = true_indices.has(i);
    if (isPredicted && isTrue) tp++;
    else if (isPredicted && !isTrue) fp++;
    else if (!isPredicted && isTrue) fn++;
    else if (!isPredicted && !isTrue) tn++;
  }

  const precision = tp + fp > 0 ? tp / (tp + fp) : 0;
  const recall = tp + fn > 0 ? tp / (tp + fn) : 0;
  const f1 =
    precision + recall > 0
      ? (2 * (precision * recall)) / (precision + recall)
      : 0;
  const accuracy = totalRows > 0 ? (tp + tn) / totalRows : 0;

  return {
    "Total Rows": totalRows,
    "True Poison": true_indices.size,
    "Predicted Poison": predicted_indices.size,
    "True Positives (TP)": tp,
    "False Positives (FP)": fp,
    "False Negatives (FN)": fn,
    "True Negatives (TN)": tn,
    Accuracy: (accuracy * 100).toFixed(2),
    Precision: precision.toFixed(3),
    Recall: recall.toFixed(3),
    "F1-Score": f1.toFixed(3),
  };
};

// *** NEW: CSV Conversion and Download Helper ***
const convertToCSV = (dataArray) => {
  if (!dataArray || dataArray.length === 0) {
    return "";
  }
  const headers = Object.keys(dataArray[0]);
  const csvRows = [];

  // Add header row
  csvRows.push(headers.map(escapeCsvValue).join(","));

  // Add data rows
  for (const row of dataArray) {
    const values = headers.map((header) => escapeCsvValue(row[header]));
    csvRows.push(values.join(","));
  }

  return csvRows.join("\n");
};

const escapeCsvValue = (value) => {
  if (value == null) {
    // Handles null and undefined
    return "";
  }
  const stringValue = String(value);
  // Check if value contains comma, newline, or double quote
  if (/[",\n]/.test(stringValue)) {
    // Escape double quotes by doubling them and wrap in double quotes
    return `"${stringValue.replace(/"/g, '""')}"`;
  }
  return stringValue;
};

const downloadCSV = (csvString, filename = "cleaned_data.csv") => {
  const blob = new Blob([csvString], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  if (link.download !== undefined) {
    // Feature detection
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", filename);
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url); // Clean up
  }
};
// *** END NEW HELPERS ***

// --- Child Components ---

const WelcomeScreen = ({
  isLoading,
  handleDemoLoad,
  handleFileUpload,
  datasetType,
  setDatasetType,
  error,
}) => (
  <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-6">
    {/* Upload Card */}
    <Card
      title="Upload Your Data"
      icon={<Upload className="w-5 h-5 mr-2 text-sky-400" />}
      className="md:col-span-1"
    >
      <p className="text-sm text-zinc-400 mb-4">
        Analyze your own CSV or Excel file.
      </p>
      <div className="mb-4">
        <label className="block text-sm mb-2 text-zinc-300">Dataset Type</label>
        <select
          value={datasetType}
          onChange={(e) => setDatasetType(e.target.value)}
          className="w-full p-2 border border-zinc-600 bg-zinc-700 text-zinc-100 rounded-lg focus:ring-sky-500 focus:border-sky-500"
        >
          <option value="tabular">Tabular (Regression/Classification)</option>
          <option value="text">Text (Classification)</option>
        </select>
      </div>
      <input
        type="file"
        id="file-upload"
        className="hidden"
        accept=".csv, .xlsx"
        onChange={(e) =>
          e.target.files[0] && handleFileUpload(e.target.files[0])
        }
      />
      <Button
        onClick={() => document.getElementById("file-upload").click()}
        disabled={isLoading}
      >
        <Upload className="mr-2" /> Upload File
      </Button>
    </Card>

    {/* Demo Card - Now Organized */}
    <Card
      title="Load a Demo"
      icon={<TestTube className="w-5 h-5 mr-2 text-sky-400" />}
      className="md:col-span-1"
    >
      <p className="text-sm text-zinc-400 mb-4">
        See how the tool works with pre-built, poisoned datasets.
      </p>

      {/* Tabular Demos Section */}
      <div className="mb-6">
        {" "}
        {/* Added margin-bottom */}
        <h3 className="text-md font-semibold text-zinc-300 mb-3 border-b border-zinc-700 pb-1 flex items-center">
          <Database className="w-4 h-4 mr-2 text-sky-500" /> Tabular Demos
        </h3>
        <div className="space-y-3">
          <Button
            onClick={() => handleDemoLoad("tabular-classification-simple")}
            disabled={isLoading}
            variant="tertiary"
            className="text-xs justify-start pl-4" // Align left
          >
            <Flower className="w-4 h-4 mr-2 flex-shrink-0" /> Iris
            Classification (Simple)
          </Button>
          <Button
            onClick={() => handleDemoLoad("tabular-regression-simple")}
            disabled={isLoading}
            variant="tertiary"
            className="text-xs justify-start pl-4" // Align left
          >
            <FlaskConical className="w-4 h-4 mr-2 flex-shrink-0" /> Simple
            Regression
          </Button>
          <Button
            onClick={() => handleDemoLoad("tabular-regression")}
            disabled={isLoading}
            variant="secondary"
            className="text-xs justify-start pl-4" // Align left
          >
            <Database className="w-4 h-4 mr-2 flex-shrink-0" /> California
            Housing Regression
          </Button>
        </div>
      </div>

      {/* Text Demos Section */}
      <div>
        <h3 className="text-md font-semibold text-zinc-300 mb-3 border-b border-zinc-700 pb-1 flex items-center">
          <FileText className="w-4 h-4 mr-2 text-sky-500" /> Text Demos
        </h3>
        <div className="space-y-3">
          <Button
            onClick={() => handleDemoLoad("text-classification-imdb")}
            disabled={isLoading}
            variant="secondary"
            className="text-xs justify-start pl-4" // Align left
          >
            <Film className="w-4 h-4 mr-2 flex-shrink-0" /> IMDB Movie Reviews
          </Button>
          <Button
            onClick={() => handleDemoLoad("text-classification")}
            disabled={isLoading}
            variant="secondary"
            className="text-xs justify-start pl-4" // Align left
          >
            <FileText className="w-4 h-4 mr-2 flex-shrink-0" /> 20 Newsgroups
            Classification
          </Button>
        </div>
      </div>
    </Card>

    {/* Error Message */}
    {error && (
      <div className="md:col-span-2 mt-4 p-3 bg-red-900/50 border border-red-700 text-red-300 rounded-xl text-sm">
        {error}
      </div>
    )}
  </div>
);

const ConfigScreen = ({
  fileInfo,
  columnInfo,
  config,
  onColumnConfigChange,
  isLoading,
  error,
  handleRunSanitize,
  datasetType,
  targetVar,
  setTargetVar,
  mlTask,
  setMlTask,
  textCol,
  setTextCol,
}) => {
  const onRunSanitizeClick = () => {
    let finalConfig = {};

    const finalColumnConfigs = Object.entries(config).map(
      ([colName, colConfig]) => ({
        ...colConfig,
        col_name: colName,
        is_feature:
          datasetType === "tabular"
            ? colName !== targetVar && colConfig.is_feature
            : colName !== textCol &&
              colName !== targetVar &&
              colConfig.is_feature,
      })
    );

    if (datasetType === "tabular") {
      finalConfig = {
        ml_task: mlTask,
        target_variable: targetVar,
        columns: finalColumnConfigs,
      };
    } else {
      finalConfig = {
        text_column: textCol,
        target_column: targetVar,
        phase_1_settings: {
          min_length: 10,
          max_length: 5000,
          flag_urls: true,
          flag_html: true,
        },
        columns: finalColumnConfigs.filter(
          (c) => c.col_name !== textCol && c.col_name !== targetVar
        ),
      };
    }
    handleRunSanitize(finalConfig);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <Card
        title="1. Configure Pipeline"
        icon={<FileScan className="w-5 h-5 mr-2 text-sky-400" />}
        className="lg:col-span-1"
      >
        <div className="mb-4 p-3 bg-zinc-700 rounded-lg border border-zinc-600">
          <p className="text-sm text-zinc-300">
            File:{" "}
            <span className="font-medium text-sky-400">
              {fileInfo?.filename || "N/A"}
            </span>
          </p>
          <p className="text-sm text-zinc-300">
            Rows:{" "}
            <span className="font-medium text-zinc-100">
              {fileInfo?.rowCount || "N/A"}
            </span>
          </p>
        </div>
        <div className="space-y-4">
          {datasetType === "tabular" ? (
            <>
              <div className="mb-4">
                <label className="block text-sm mb-2 text-zinc-300">
                  ML Task
                </label>
                <select
                  value={mlTask}
                  onChange={(e) => setMlTask(e.target.value)}
                  className="w-full p-2 border border-zinc-600 bg-zinc-700 text-zinc-100 rounded-lg focus:ring-sky-500 focus:border-sky-500"
                >
                  <option value="regression">Regression</option>
                  <option value="classification">Classification</option>
                </select>
              </div>
              <div className="mb-4">
                <label className="block text-sm mb-2 text-zinc-300">
                  Target Variable (y)
                </label>
                <select
                  value={targetVar}
                  onChange={(e) => setTargetVar(e.target.value)}
                  className="w-full p-2 border border-zinc-600 bg-zinc-700 text-zinc-100 rounded-lg focus:ring-sky-500 focus:border-sky-500"
                >
                  <option value="">-- Select Target --</option>
                  {(columnInfo || [])
                    .filter((c) => typeof c.name === "string")
                    .map((c) => (
                      <option key={c.name} value={c.name}>
                        {" "}
                        {c.name}{" "}
                      </option>
                    ))}
                </select>
              </div>
            </>
          ) : (
            <>
              <div className="mb-4">
                <label className="block text-sm mb-2 text-zinc-300">
                  Text Column (X)
                </label>
                <select
                  value={textCol}
                  onChange={(e) => setTextCol(e.target.value)}
                  className="w-full p-2 border border-zinc-600 bg-zinc-700 text-zinc-100 rounded-lg focus:ring-sky-500 focus:border-sky-500"
                >
                  <option value="">-- Select Text Column --</option>
                  {(columnInfo || [])
                    .filter((c) => typeof c.name === "string")
                    .map((c) => (
                      <option key={c.name} value={c.name}>
                        {" "}
                        {c.name}{" "}
                      </option>
                    ))}
                </select>
              </div>
              <div className="mb-4">
                <label className="block text-sm mb-2 text-zinc-300">
                  Target Column (y)
                </label>
                <select
                  value={targetVar}
                  onChange={(e) => setTargetVar(e.target.value)}
                  className="w-full p-2 border border-zinc-600 bg-zinc-700 text-zinc-100 rounded-lg focus:ring-sky-500 focus:border-sky-500"
                >
                  <option value="">-- Select Target --</option>
                  {(columnInfo || [])
                    .filter((c) => typeof c.name === "string")
                    .map((c) => (
                      <option key={c.name} value={c.name}>
                        {" "}
                        {c.name}{" "}
                      </option>
                    ))}
                </select>
              </div>
            </>
          )}
          <Button
            onClick={onRunSanitizeClick}
            disabled={
              isLoading || !targetVar || (datasetType === "text" && !textCol)
            }
          >
            <Zap className="mr-2" /> Run Sanitization
          </Button>
          {error && (
            <div className="mt-4 p-3 bg-red-900/50 border border-red-700 text-red-300 rounded-xl text-sm">
              {" "}
              {error}{" "}
            </div>
          )}
        </div>
      </Card>
      <Card
        title="2. Review Columns"
        icon={<Database className="w-5 h-5 mr-2 text-sky-400" />}
        className="lg:col-span-2"
      >
        <p className="text-sm text-zinc-400 mb-4">
          Review the auto-detected column types and set constraints for Phase 1.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-[60vh] overflow-y-auto pr-2">
          {(columnInfo || [])
            .filter((c) => typeof c.name === "string")
            .map((col) => (
              <ColumnConfig
                key={col.name}
                col={col}
                config={
                  config[col.name] || {
                    data_type: col.auto_type,
                    is_feature: true,
                    min_val: null,
                    max_val: null,
                    unique_values: col.unique_values || [],
                  }
                }
                onConfigChange={onColumnConfigChange}
              />
            ))}
        </div>
      </Card>
    </div>
  );
};

// *** UPDATED ResultsScreen with Export Button Handler ***
const ResultsScreen = ({
  metrics,
  fullData,
  flaggedRows,
  groundTruth,
  datasetType,
  textCol,
  targetCol,
  resetApp,
  handleExportCleanedData, // <-- Receive export handler
}) => {
  const [page, setPage] = useState(1);

  const tableData = useMemo(() => {
    if (!Array.isArray(fullData)) return [];
    return fullData.map((row, index) => {
      const isFlagged = Object.prototype.hasOwnProperty.call(
        flaggedRows || {},
        String(index)
      );
      const isTruePoison = groundTruth?.true_poison_indices?.includes(index);
      let status = "clean";
      if (groundTruth) {
        if (isFlagged && isTruePoison) status = "tp";
        else if (isFlagged && !isTruePoison) status = "fp";
        else if (!isFlagged && isTruePoison) status = "fn";
      }
      return {
        ...row,
        index,
        is_flagged: isFlagged,
        reason: isFlagged ? (flaggedRows || {})[String(index)] : "---",
        is_actual_poisoned: groundTruth ? isTruePoison : null,
        status: status,
      };
    });
  }, [fullData, flaggedRows, groundTruth]);

  const flaggedTableData = tableData.filter((row) => row.is_flagged);
  const totalFlagged = flaggedTableData.length;
  const paginatedData = flaggedTableData.slice(
    (page - 1) * PAGE_SIZE,
    page * PAGE_SIZE
  );
  const hasMetrics =
    metrics && typeof metrics === "object" && Object.keys(metrics).length > 0;
  const isDemoRun = !!groundTruth;
  let metricsToDisplay = {};
  if (hasMetrics) {
    metricsToDisplay = isDemoRun
      ? metrics
      : {
          "Total Rows": metrics["Total Rows"],
          "Flagged Rows": metrics["Flagged Rows"],
        };
  }
  const metricGridCols = isDemoRun ? "lg:grid-cols-5" : "lg:grid-cols-2";

  const renderTabularRowData = (row) => {
    return Object.entries(row)
      .filter(
        ([key]) =>
          ![
            "index",
            "is_flagged",
            "reason",
            "is_actual_poisoned",
            "status",
          ].includes(key)
      )
      .map(([key, val]) => {
        const isTarget = key === targetCol;
        const displayVal =
          String(val).slice(0, 20) + (String(val).length > 20 ? "..." : "");
        return (
          <span
            key={key}
            className={`mr-2 ${isTarget ? "font-bold text-sky-300" : ""}`}
          >
            {" "}
            {key}:{" "}
            <span className={isTarget ? "" : "text-zinc-400"}>
              {displayVal}
            </span>{" "}
          </span>
        );
      });
  };

  return (
    <div className="space-y-8">
      <Card
        title="3. Performance Report"
        icon={<BarChart3 className="w-5 h-5 mr-2 text-sky-400" />}
      >
        {hasMetrics ? (
          <div
            className={`grid grid-cols-2 md:grid-cols-3 ${metricGridCols} gap-4 text-center`}
          >
            {" "}
            {Object.entries(metricsToDisplay).map(
              ([key, value]) =>
                value !== undefined &&
                value !== null && (
                  <div
                    key={key}
                    className="bg-zinc-700 rounded-lg p-3 border border-zinc-600"
                  >
                    {" "}
                    <p className="text-sm text-sky-400 font-semibold">
                      {" "}
                      {key.replace(/_/g, " ").toUpperCase()}{" "}
                    </p>{" "}
                    <p className="text-2xl font-bold">
                      {" "}
                      {typeof value === "number" ? value : String(value)}{" "}
                    </p>{" "}
                  </div>
                )
            )}{" "}
          </div>
        ) : (
          <p className="text-center text-zinc-400">
            {" "}
            Run analysis to see metrics.{" "}
          </p>
        )}
      </Card>
      <Card
        title={`4. Flagged Rows (${totalFlagged} found)`}
        icon={<AlertTriangle className="w-5 h-5 mr-2 text-sky-400" />}
      >
        {totalFlagged > 0 ? (
          <>
            <div className="overflow-x-auto mt-4 rounded-xl border border-zinc-700">
              <table className="min-w-full divide-y divide-zinc-700">
                <thead className="bg-zinc-700">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-zinc-300 uppercase">
                      {" "}
                      Index{" "}
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-zinc-300 uppercase">
                      {" "}
                      {datasetType === "text"
                        ? textCol || "Text"
                        : "Sample Data"}{" "}
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-zinc-300 uppercase">
                      {" "}
                      Reason Flagged{" "}
                    </th>
                    {groundTruth && (
                      <th className="px-4 py-3 text-left text-xs font-medium text-zinc-300 uppercase">
                        {" "}
                        Ground Truth{" "}
                      </th>
                    )}
                  </tr>
                </thead>
                <tbody className="bg-zinc-800 divide-y divide-zinc-700 text-sm">
                  {paginatedData.map((row) => (
                    <tr
                      key={row.index}
                      className={` ${
                        groundTruth && row.status === "tp"
                          ? "bg-green-900/30 text-green-300"
                          : ""
                      } ${
                        groundTruth && row.status === "fp"
                          ? "bg-yellow-900/30 text-yellow-300"
                          : ""
                      } ${
                        groundTruth && row.status === "fn"
                          ? "bg-red-900/30 text-red-300"
                          : ""
                      } ${
                        !groundTruth && row.is_flagged
                          ? "bg-red-900/30 text-red-300"
                          : ""
                      } hover:bg-zinc-700/50 `}
                    >
                      <td className="px-4 py-3 font-mono">{row.index}</td>
                      <td className="px-4 py-3 max-w-xl">
                        {" "}
                        {datasetType === "text" && textCol && row[textCol] ? (
                          <span className="block truncate">
                            {" "}
                            {row[textCol]}{" "}
                          </span>
                        ) : datasetType === "tabular" ? (
                          renderTabularRowData(row)
                        ) : (
                          "N/A"
                        )}{" "}
                      </td>
                      <td className="px-4 py-3 text-red-300">{row.reason}</td>
                      {groundTruth && (
                        <td className="px-4 py-3">
                          {" "}
                          {row.is_actual_poisoned ? (
                            <span className="flex items-center text-red-400">
                              {" "}
                              <AlertTriangle className="w-4 h-4 mr-1" /> Poison{" "}
                            </span>
                          ) : (
                            <span className="flex items-center text-green-400">
                              {" "}
                              <CheckCircle className="w-4 h-4 mr-1" /> Clean{" "}
                            </span>
                          )}{" "}
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {totalFlagged > PAGE_SIZE && (
              <div className="flex justify-between items-center mt-4 text-sm text-zinc-300">
                {" "}
                <button
                  onClick={() => setPage((p) => Math.max(p - 1, 1))}
                  disabled={page === 1}
                  className="px-3 py-1 bg-zinc-700 rounded hover:bg-zinc-600 disabled:opacity-50 flex items-center"
                >
                  {" "}
                  <ChevronLeft className="w-4 h-4 mr-1" /> Previous{" "}
                </button>{" "}
                <span>
                  {" "}
                  Page {page} / {Math.ceil(totalFlagged / PAGE_SIZE)}{" "}
                </span>{" "}
                <button
                  onClick={() =>
                    setPage((p) =>
                      Math.min(p + 1, Math.ceil(totalFlagged / PAGE_SIZE))
                    )
                  }
                  disabled={page === Math.ceil(totalFlagged / PAGE_SIZE)}
                  className="px-3 py-1 bg-zinc-700 rounded hover:bg-zinc-600 disabled:opacity-50 flex items-center"
                >
                  {" "}
                  Next <ChevronRight className="w-4 h-4 ml-1" />{" "}
                </button>{" "}
              </div>
            )}
          </>
        ) : (
          <p className="text-center text-zinc-400 py-4">
            {" "}
            No rows were flagged by the pipeline.{" "}
          </p>
        )}
      </Card>
      <div className="flex space-x-4">
        <Button onClick={resetApp} variant="secondary">
          {" "}
          <ChevronLeft className="mr-2" /> Start Over{" "}
        </Button>
        {/* --- UPDATED EXPORT BUTTON --- */}
        <Button
          onClick={handleExportCleanedData}
          variant="primary"
          disabled={!fullData || fullData.length === 0}
        >
          <Download className="mr-2" /> Export Cleaned Data {/* Changed Icon */}
        </Button>
        {/* --- END UPDATE --- */}
      </div>
    </div>
  );
};
// *** END UPDATED ResultsScreen ***

const ProcessingScreen = ({ stage }) => (
  <div className="flex flex-col items-center justify-center h-64">
    <Loader2 className="animate-spin h-12 w-12 text-sky-400" />
    <p className="mt-4 text-zinc-300">
      {stage === "processing"
        ? "Running analysis... this may take a moment."
        : "Loading data..."}
    </p>
    {stage === "processing" && (
      <p className="text-sm text-zinc-500">
        (Embeddings and canary models are being processed)
      </p>
    )}
  </div>
);

// --- Main App Component ---

const App = () => {
  const [stage, setStage] = useState("idle");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [fileInfo, setFileInfo] = useState(null);
  const [columnInfo, setColumnInfo] = useState([]);
  const [fullData, setFullData] = useState([]);
  const [groundTruth, setGroundTruth] = useState(null);
  const [datasetType, setDatasetType] = useState("tabular");
  const [config, setConfig] = useState({});
  const [targetVar, setTargetVar] = useState("");
  const [mlTask, setMlTask] = useState("regression");
  const [textCol, setTextCol] = useState("");
  const [flaggedRows, setFlaggedRows] = useState({});
  const [metrics, setMetrics] = useState(null);

  const handleApiCall = async (apiCall) => {
    setIsLoading(true);
    setError(null);
    try {
      await apiCall();
    } catch (err) {
      console.error("API Call Error:", err);
      setError(err.message || "An unknown error occurred.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoLoad = (demoType) =>
    handleApiCall(async () => {
      const response = await fetch(`${FLASK_API_URL}/load-demo`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: demoType }),
      });
      const data = await response.json();
      if (data.error) throw new Error(data.error);
      if (!data.columnInfo || !data.fullData) {
        throw new Error(
          "Demo data loading failed: Missing columnInfo or fullData."
        );
      }
      const initialConfig = {};
      const cols = Array.isArray(data.columnInfo) ? data.columnInfo : [];
      cols.forEach((col) => {
        if (col && typeof col.name === "string") {
          initialConfig[col.name] = {
            data_type:
              col.auto_type ||
              (demoType.startsWith("tabular") ? "Categorical" : "Text"),
            is_feature:
              !col.name.toLowerCase().includes("target") &&
              !col.name.toLowerCase().includes("price") &&
              !col.name.toLowerCase().includes("species") &&
              !col.name.toLowerCase().includes("sentiment") &&
              !col.name.toLowerCase().includes("review") &&
              !col.name.toLowerCase().includes("text") &&
              !col.name.toLowerCase().includes("id"),
            min_val: null,
            max_val: null,
            unique_values: col.unique_values || [],
          };
        }
      });
      const newDatasetType = demoType.startsWith("tabular")
        ? "tabular"
        : "text";
      setDatasetType(newDatasetType);
      const safeColumnInfo = Array.isArray(data.columnInfo)
        ? data.columnInfo
        : [];
      let foundTarget = "";
      let foundText = "";
      if (newDatasetType === "tabular") {
        foundTarget = safeColumnInfo.find(
          (c) =>
            c &&
            (c.name.toLowerCase().includes("price") ||
              c.name.toLowerCase().includes("target") ||
              c.name.toLowerCase().includes("species"))
        )?.name;
        setTargetVar(
          foundTarget || safeColumnInfo[safeColumnInfo.length - 1]?.name || ""
        );
        setMlTask(
          demoType.includes("regression") ? "regression" : "classification"
        );
      } else {
        foundTarget = safeColumnInfo.find(
          (c) =>
            c &&
            (c.name.toLowerCase().includes("target") ||
              c.name.toLowerCase().includes("label") ||
              c.name.toLowerCase().includes("sentiment"))
        )?.name;
        foundText = safeColumnInfo.find(
          (c) =>
            c &&
            (c.name.toLowerCase().includes("text") ||
              c.name.toLowerCase().includes("review") ||
              c.name.toLowerCase().includes("comment"))
        )?.name;
        setTargetVar(
          foundTarget || safeColumnInfo[safeColumnInfo.length - 1]?.name || ""
        );
        setTextCol(foundText || safeColumnInfo[0]?.name || "");
      }
      setConfig(initialConfig);
      setFullData(Array.isArray(data.fullData) ? data.fullData : []);
      setColumnInfo(safeColumnInfo);
      setGroundTruth(data.groundTruth);
      setFileInfo({ filename: data.filename, rowCount: data.rowCount });
      setStage("configuring");
    });

  const handleFileUpload = (file) =>
    handleApiCall(async () => {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("dataset_type", datasetType);
      const response = await fetch(`${FLASK_API_URL}/upload`, {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      if (data.error) throw new Error(data.error);
      if (!data.columnInfo || !data.fullData) {
        throw new Error(
          "File upload processing failed: Missing columnInfo or fullData."
        );
      }
      const initialConfig = {};
      const cols = Array.isArray(data.columnInfo) ? data.columnInfo : [];
      cols.forEach((col) => {
        if (col && typeof col.name === "string") {
          initialConfig[col.name] = {
            data_type:
              col.auto_type ||
              (datasetType === "tabular" ? "Categorical" : "Text"),
            is_feature:
              !col.name.toLowerCase().includes("target") &&
              !col.name.toLowerCase().includes("price") &&
              !col.name.toLowerCase().includes("species") &&
              !col.name.toLowerCase().includes("sentiment") &&
              !col.name.toLowerCase().includes("review") &&
              !col.name.toLowerCase().includes("text") &&
              !col.name.toLowerCase().includes("id"),
            min_val: null,
            max_val: null,
            unique_values: col.unique_values || [],
          };
        }
      });
      const safeColumnInfo = Array.isArray(data.columnInfo)
        ? data.columnInfo
        : [];
      let foundTarget = "";
      let foundText = "";
      if (datasetType === "tabular") {
        foundTarget = safeColumnInfo.find(
          (c) =>
            c &&
            (c.name.toLowerCase().includes("target") ||
              c.name.toLowerCase().includes("price"))
        )?.name;
        setTargetVar(
          foundTarget || safeColumnInfo[safeColumnInfo.length - 1]?.name || ""
        );
      } else {
        foundTarget = safeColumnInfo.find(
          (c) =>
            c &&
            (c.name.toLowerCase().includes("target") ||
              c.name.toLowerCase().includes("label") ||
              c.name.toLowerCase().includes("sentiment"))
        )?.name;
        foundText = safeColumnInfo.find(
          (c) =>
            c &&
            (c.name.toLowerCase().includes("text") ||
              c.name.toLowerCase().includes("review") ||
              c.name.toLowerCase().includes("comment"))
        )?.name;
        setTargetVar(
          foundTarget || safeColumnInfo[safeColumnInfo.length - 1]?.name || ""
        );
        setTextCol(foundText || safeColumnInfo[0]?.name || "");
      }
      setConfig(initialConfig);
      setFullData(Array.isArray(data.fullData) ? data.fullData : []);
      setColumnInfo(safeColumnInfo);
      setGroundTruth(null);
      setFileInfo({ filename: file.name, rowCount: data.rowCount });
      setStage("configuring");
    });

  const handleRunSanitize = (finalConfig) =>
    handleApiCall(async () => {
      setStage("processing");
      const payload = {
        data: fullData,
        config: finalConfig,
        ...(groundTruth && { groundTruth: groundTruth }),
      };
      const response = await fetch(`${FLASK_API_URL}/sanitize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (data.error) throw new Error(data.error);
      const receivedFlaggedRows = data.flagged_rows || {};
      setFlaggedRows(receivedFlaggedRows);
      if (groundTruth) {
        const perf = calculatePerformance(
          receivedFlaggedRows,
          groundTruth,
          fullData.length
        );
        setMetrics(perf);
      } else {
        const basicMetrics = {
          "Total Rows": fullData.length,
          "Flagged Rows": Object.keys(receivedFlaggedRows).length,
        };
        setMetrics(basicMetrics);
      }
      setStage("results");
    });

  // *** NEW: Export Handler ***
  const handleExportCleanedData = () => {
    console.log("Export button clicked"); // Debug log
    if (!fullData || fullData.length === 0 || flaggedRows === null) {
      console.error("Cannot export: Data not available.");
      // Optionally show a user message here
      return;
    }
    try {
      // Filter out flagged rows
      const flaggedIndicesSet = new Set(Object.keys(flaggedRows || {}));
      const cleanedData = fullData.filter(
        (_, index) => !flaggedIndicesSet.has(String(index))
      );
      console.log(
        `Exporting ${cleanedData.length} cleaned rows out of ${fullData.length} total.`
      ); // Debug log

      if (cleanedData.length === 0) {
        console.warn("No data left after cleaning. Exporting empty file.");
        // Optionally show a user message
      }

      const csvString = convertToCSV(cleanedData);

      // Generate filename
      const originalFilename = fileInfo?.filename || "data.csv";
      const filenameWithoutExt = originalFilename
        .split(".")
        .slice(0, -1)
        .join(".");
      const downloadFilename = `cleaned_${filenameWithoutExt || "data"}.csv`;

      downloadCSV(csvString, downloadFilename);
      console.log(`Triggered download for ${downloadFilename}`); // Debug log
    } catch (error) {
      console.error("Error during export:", error);
      setError("Failed to generate or download the cleaned data CSV."); // Show error to user
    }
  };
  // *** END NEW HANDLER ***

  const resetApp = () => {
    setStage("idle");
    setIsLoading(false);
    setError(null);
    setFileInfo(null);
    setColumnInfo([]);
    setFullData([]);
    setGroundTruth(null);
    setConfig({});
    setFlaggedRows({});
    setMetrics(null);
    setTargetVar("");
    setMlTask("regression");
    setTextCol("");
  };
  const handleColumnConfigChange = (colName, newColConfig) => {
    setConfig((prev) => ({ ...prev, [colName]: newColConfig }));
  };

  const renderCurrentStage = () => {
    if (isLoading && (stage === "idle" || stage === "configuring")) {
      return <ProcessingScreen stage="loading" />;
    }
    if (stage === "processing") {
      return <ProcessingScreen stage="processing" />;
    }
    switch (stage) {
      case "idle":
        return (
          <WelcomeScreen
            isLoading={isLoading}
            handleDemoLoad={handleDemoLoad}
            handleFileUpload={handleFileUpload}
            datasetType={datasetType}
            setDatasetType={setDatasetType}
            error={error}
          />
        );
      case "configuring":
        if (!fileInfo || !columnInfo || !config) {
          console.error("ConfigScreen: Missing required props", {
            fileInfo,
            columnInfo,
            config,
          });
          resetApp();
          return <ProcessingScreen stage="loading" />;
        }
        return (
          <ConfigScreen
            fileInfo={fileInfo}
            columnInfo={columnInfo}
            config={config}
            onColumnConfigChange={handleColumnConfigChange}
            isLoading={isLoading}
            error={error}
            handleRunSanitize={handleRunSanitize}
            datasetType={datasetType}
            targetVar={targetVar}
            setTargetVar={setTargetVar}
            mlTask={mlTask}
            setMlTask={setMlTask}
            textCol={textCol}
            setTextCol={setTextCol}
          />
        );
      case "results":
        if (
          metrics === null ||
          !Array.isArray(fullData) ||
          flaggedRows === null
        ) {
          console.error(
            "ResultsScreen: Missing or invalid required props. Resetting.",
            { metrics, fullData, flaggedRows }
          );
          resetApp();
          return <ProcessingScreen stage="loading" />;
        }
        return (
          <ResultsScreen
            metrics={metrics}
            fullData={fullData}
            flaggedRows={flaggedRows}
            groundTruth={groundTruth}
            datasetType={datasetType}
            textCol={textCol}
            targetCol={targetVar}
            resetApp={resetApp}
            handleExportCleanedData={
              handleExportCleanedData
            } /* <-- Pass handler down */
          />
        );
      default:
        return (
          <WelcomeScreen
            isLoading={isLoading}
            handleDemoLoad={handleDemoLoad}
            handleFileUpload={handleFileUpload}
            datasetType={datasetType}
            setDatasetType={setDatasetType}
            error={error}
          />
        );
    }
  };

  return (
    <div className="min-h-screen bg-zinc-900 p-6 md:p-10 font-sans text-zinc-100">
      <div className="max-w-7xl mx-auto">
        <header className="flex justify-between items-center mb-10">
          <h1 className="text-4xl font-extrabold text-sky-400 flex items-center">
            {" "}
            <Database className="inline w-8 h-8 mr-3" /> PoisonGuard{" "}
          </h1>
          {stage !== "idle" && (
            <button
              onClick={resetApp}
              className="flex items-center text-sm text-zinc-400 hover:text-red-400 transition-colors"
              title="Reset application state"
            >
              {" "}
              <XCircle className="w-4 h-4 mr-1" /> Reset{" "}
            </button>
          )}
        </header>
        {renderCurrentStage()}
      </div>
    </div>
  );
};

export default App;
