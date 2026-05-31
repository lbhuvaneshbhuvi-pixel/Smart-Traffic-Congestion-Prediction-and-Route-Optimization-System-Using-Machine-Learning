import os
import subprocess
import sys

def verify_and_run():
    print("=" * 60)
    print("  AI-Powered Smart Traffic Congestion Prediction System  ")
    print("=" * 60)
    
    # Step 1: Check dataset
    if not os.path.exists("traffic_data.csv"):
        print("\n[*] Step 1: Historical dataset 'traffic_data.csv' not found.")
        print("[*] Generating high-fidelity traffic simulation data...")
        try:
            subprocess.run([sys.executable, "data_generator.py"], check=True)
            print("[+] Dataset generated successfully.")
        except subprocess.CalledProcessError as e:
            print(f"[-] Error generating dataset: {e}")
            sys.exit(1)
    else:
        print("[+] Step 1: Historical dataset 'traffic_data.csv' is present.")

    # Step 2: Check ML artifacts
    required_artifacts = ["best_model.pkl", "preprocessor.pkl", "model_comparison.json"]
    missing_artifacts = [a for a in required_artifacts if not os.path.exists(a)]
    
    if missing_artifacts:
        print(f"\n[*] Step 2: Missing ML model artifacts: {missing_artifacts}")
        print("[*] Launching machine learning ensemble training pipeline...")
        try:
            subprocess.run([sys.executable, "train_model.py"], check=True)
            print("[+] Machine learning ensemble models trained and saved.")
        except subprocess.CalledProcessError as e:
            print(f"[-] Error training models: {e}")
            sys.exit(1)
    else:
        print("[+] Step 2: Pre-trained machine learning model artifacts are present.")

    # Step 3: Run Flask application
    print("\n[*] Step 3: Initializing database and starting web server...")
    print("[*] Dashboard will be available at: http://127.0.0.1:5000/")
    print("-" * 60)
    
    try:
        from app import app
        app.run(debug=True, host='127.0.0.1', port=5000)
    except ImportError as e:
        print(f"[-] Failed to import backend components: {e}")
        print("[-] Please ensure all dependencies in requirements.txt are installed.")
        sys.exit(1)

if __name__ == "__main__":
    verify_and_run()
