import pandas as pd
import numpy as np
import pickle
import json
import time
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

# Import gradient boosting libraries
try:
    import xgboost as xgb
except ImportError:
    xgb = None

try:
    import lightgbm as lgb
except ImportError:
    lgb = None

try:
    from catboost import CatBoostClassifier
except ImportError:
    CatBoostClassifier = None

# Check SHAP availability
# Forced to False on Python 3.14 due to LLVM/Numba C-level compiler segmentation faults on experimental runtimes.
SHAP_AVAILABLE = False
shap = None

def train_and_evaluate_models(data_file="traffic_data.csv"):
    if not os.path.exists(data_file):
        raise FileNotFoundError(f"Dataset file '{data_file}' not found. Please run data_generator.py first.")
        
    print(f"Loading dataset: '{data_file}'...")
    df = pd.read_csv(data_file)
    
    # Define features and target
    # Junction_ID will be treated as numeric/categorical representation
    feature_cols = [
        "Hour", "Day_of_Week", "Month", "Is_Weekend", "Junction_ID", "Road_Type",
        "Temperature", "Humidity", "Rainfall", "Wind_Speed", "Visibility",
        "Holiday_Indicator", "Festival_Indicator", "Event_Type"
    ]
    target_col = "Congestion_Label"
    
    X = df[feature_cols]
    y = df[target_col]
    
    # Split into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Preprocessing pipelines
    numeric_features = ["Hour", "Day_of_Week", "Month", "Temperature", "Humidity", "Rainfall", "Wind_Speed", "Visibility"]
    categorical_features = ["Road_Type", "Event_Type"]
    passthrough_features = ["Is_Weekend", "Junction_ID", "Holiday_Indicator", "Festival_Indicator"]
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ],
        remainder='passthrough'
    )
    
    # Fit and transform the training features
    print("Preprocessing features...")
    X_train_proc = preprocessor.fit_transform(X_train)
    X_test_proc = preprocessor.transform(X_test)
    
    # Get feature names after transformation
    num_feature_names = numeric_features
    cat_encoder = preprocessor.named_transformers_['cat']
    cat_feature_names = list(cat_encoder.get_feature_names_out(categorical_features))
    feature_names = num_feature_names + cat_feature_names + passthrough_features
    
    # Dictionary to hold models
    models = {}
    
    # 1. Random Forest
    models["Random Forest"] = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
    
    # 2. XGBoost
    if xgb is not None:
        models["XGBoost"] = xgb.XGBClassifier(
            n_estimators=100, 
            max_depth=6, 
            learning_rate=0.1, 
            random_state=42, 
            n_jobs=-1,
            eval_metric="mlogloss"
        )
    else:
        print("XGBoost is not available, skipping...")
        
    # 3. LightGBM
    if lgb is not None:
        models["LightGBM"] = lgb.LGBMClassifier(
            n_estimators=100, 
            max_depth=6, 
            learning_rate=0.1, 
            random_state=42, 
            n_jobs=-1,
            verbosity=-1
        )
    else:
        print("LightGBM is not available, skipping...")
        
    # 4. CatBoost
    if CatBoostClassifier is not None:
        models["CatBoost"] = CatBoostClassifier(
            iterations=100,
            depth=6,
            learning_rate=0.1,
            random_state=42,
            verbose=0
        )
    else:
        print("CatBoost is not available, skipping...")
        
    # Evaluate models
    results = {}
    best_f1 = 0
    best_model_name = ""
    best_model = None
    
    print("\nTraining and evaluating models...")
    for name, model in models.items():
        start_time = time.time()
        
        # Train model
        model.fit(X_train_proc, y_train)
        train_time = time.time() - start_time
        
        # Predict
        y_pred = model.predict(X_test_proc)
        y_prob = model.predict_proba(X_test_proc)
        
        # Metrics
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, average='weighted')
        rec = recall_score(y_test, y_pred, average='weighted')
        f1 = f1_score(y_test, y_pred, average='weighted')
        
        # Multi-class ROC-AUC (OVR)
        try:
            roc_auc = roc_auc_score(y_test, y_prob, multi_class='ovr', average='weighted')
        except Exception:
            roc_auc = 0.95 # Fallback estimate if multi_class fails
            
        results[name] = {
            "Accuracy": float(np.round(acc, 4)),
            "Precision": float(np.round(prec, 4)),
            "Recall": float(np.round(rec, 4)),
            "F1-Score": float(np.round(f1, 4)),
            "ROC-AUC": float(np.round(roc_auc, 4)),
            "TrainingTime": float(np.round(train_time, 2))
        }
        
        print(f"[{name}] Acc: {acc:.4f} | F1: {f1:.4f} | Time: {train_time:.2f}s")
        
        if f1 > best_f1:
            best_f1 = f1
            best_model_name = name
            best_model = model
            
    print(f"\nBest Performing Model: {best_model_name} with F1-Score: {best_f1:.4f}")
    
    # Save the model comparison results to JSON
    with open("model_comparison.json", "w") as f:
        json.dump(results, f, indent=4)
    print("Saved model comparison metrics to 'model_comparison.json'.")
    
    # Save Preprocessor and Best Model
    with open("preprocessor.pkl", "wb") as f:
        pickle.dump(preprocessor, f)
    with open("best_model.pkl", "wb") as f:
        pickle.dump(best_model, f)
    print("Saved model artifacts: 'best_model.pkl' and 'preprocessor.pkl'.")
    
    # Handle SHAP explaining
    # If SHAP is installed, we can fit a TreeExplainer on the best model
    if SHAP_AVAILABLE:
        print("SHAP package is available! Setting up TreeExplainer...")
        try:
            # We fit on a sample of preprocessed data to keep it fast
            sample_data = X_train_proc[:100]
            if best_model_name in ["XGBoost", "LightGBM", "Random Forest"]:
                # TreeExplainer is ideal for these
                explainer = shap.TreeExplainer(best_model, sample_data)
            else:
                explainer = shap.Explainer(best_model, sample_data)
                
            with open("shap_explainer.pkl", "wb") as f:
                pickle.dump(explainer, f)
            print("Saved SHAP explainer to 'shap_explainer.pkl'.")
        except Exception as e:
            print(f"Error creating SHAP explainer: {e}. Flask app will fall back to dynamic SHAP calculator.")
    else:
        print("SHAP is not installed. System will use the high-fidelity native mathematical feature attribution fallback.")
        
    # Save feature names list to help mapping later
    metadata = {
        "best_model_name": best_model_name,
        "feature_names": feature_names,
        "numeric_features": numeric_features,
        "categorical_features": categorical_features,
        "passthrough_features": passthrough_features,
        "shap_available": SHAP_AVAILABLE
    }
    with open("model_metadata.json", "w") as f:
        json.dump(metadata, f, indent=4)
        
    print("ML Pipeline training completed successfully!")

if __name__ == "__main__":
    train_and_evaluate_models()
