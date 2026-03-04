from flask import Flask, render_template, jsonify, request
import subprocess
import os
import requests

app = Flask(__name__)

# ==========================================
# --- CONFIGURATION (FILL THESE IN) ---
# ==========================================

# 1. Credentials for QuickStatements (Adding data)
QS_USERNAME = "Smitesh Sorathiya"  # e.g., "SmiteshSorathiya"
QS_TOKEN = r"$2y$10$zPYhMHzTz07h20UCtRkpHOsG3.oxTTMRUmTtjOrJcUyuynL14TyeO"  # The long token from the QS page

# 2. Credentials for MediaWiki API (Creating the empty QID)
# If you don't have a Bot Password, use your normal FactGrid website password.
# Do NOT put your QS Token here.
MW_USERNAME = "Smitesh Sorathiya" # Same as above, unless using a Bot format like User@BotName
MW_PASSWORD = "#Grid_Fact_rocks@01" 

# URLs
QS_API_URL = "https://database.factgrid.de/quickstatements/api.php"
FACTGRID_MW_API = "https://database.factgrid.de/w/api.php"

HEADERS = {
    "User-Agent": "MonasteryEntryBot/1.0 (smitesh.sorathiya@adwgoe.de)"
}

# ==========================================
# --- ROUTES: FRONTEND ---
# ==========================================

@app.route('/')
def monasteries():
    return render_template('index.html')

@app.route('/complexes')
def complexes():
    return render_template('complexes.html')

# ==========================================
# --- ROUTE: CREATE EMPTY QID (MEDIAWIKI API) ---
# ==========================================

@app.route("/create-empty-item", methods=["POST"])
def create_empty_item():
    print("\n--- Attempting to create QID via Standard MediaWiki API ---")
    session = requests.Session()

    try:
        # 1. Get a login token
        login_token_res = session.get(FACTGRID_MW_API, params={
            "action": "query", "meta": "tokens", "type": "login", "format": "json"
        }).json()
        login_token = login_token_res.get('query', {}).get('tokens', {}).get('logintoken')

        if not login_token:
            return jsonify({"error": "Failed to fetch login token"}), 500

        # 2. Login
        login_res = session.post(FACTGRID_MW_API, data={
            "action": "login", 
            "lgname": MW_USERNAME, 
            "lgpassword": MW_PASSWORD,
            "lgtoken": login_token,
            "format": "json"
        }).json()
        
        login_result = login_res.get("login", {}).get("result")
        if login_result != "Success":
            error_reason = login_res.get("login", {}).get("reason", "Unknown error")
            print(f"--- LOGIN FAILED: {error_reason} ---")
            return jsonify({"error": f"Login Failed: {error_reason}"}), 401
        
        print("--- Login Successful! ---")

        # 3. Get a CSRF token
        csrf_res = session.get(FACTGRID_MW_API, params={
            "action": "query", "meta": "tokens", "format": "json"
        }).json()
        csrf_token = csrf_res.get('query', {}).get('tokens', {}).get('csrftoken')

        # 4. Create the item
        create_res = session.post(FACTGRID_MW_API, data={
            "action": "wbeditentity",
            "new": "item",
            "token": csrf_token,
            "data": '{"labels":{"en":{"language":"en","value":"New FactGrid Entry"}}}',
            "format": "json"
        }).json()

        new_qid = create_res.get("entity", {}).get("id")
        
        if new_qid:
            print(f"--- SUCCESS: Created {new_qid} ---")
            return jsonify({"id": new_qid})
        else:
            error_info = create_res.get("error", {}).get("info", str(create_res))
            print(f"--- Creation failed: {error_info} ---")
            return jsonify({"error": f"Creation failed: {error_info}"}), 500

    except Exception as e:
        print(f"--- Critical Error in QID Creation: {e} ---")
        return jsonify({"error": str(e)}), 500

# ==========================================
# --- ROUTE: SAVE MONASTERY DATA (QS API) ---
# ==========================================

@app.route("/save-data", methods=["POST"])
def save_data():
    raw_data = request.json
    v1_command = raw_data.get('command')
    
    if not v1_command:
        return jsonify({"error": "No V1 commands provided"}), 400

    payload = {
        "action": "import",
        "format": "v1",
        "data": v1_command,
        "submit": 1,
        "username": QS_USERNAME, # Make sure this is "Smitesh Sorathiya" (with the space!)
        "token": QS_TOKEN        # Make sure this is the token from the QuickStatements page
    }

    try:
        r = requests.post(QS_API_URL, data=payload, headers=HEADERS)
        
        # --- NEW DEBUGGING PRINTS ---
        print(f"\n--- QS RAW STATUS: {r.status_code} ---")
        print(f"--- QS RAW RESPONSE: {r.text} ---\n")
        # ----------------------------

        response_data = r.json()
        
        if response_data.get("status") == "OK":
            print(f"QS Batch Submitted successfully! Batch ID: {response_data.get('batch_id')}")
            return jsonify(response_data), 200
        else:
            print(f"QS Error: {response_data}")
            return jsonify(response_data), 500
            
    except Exception as e:
        print(f"QS Request Failed: {e}")
        return jsonify({"error": str(e)}), 500

# ==========================================
# --- ROUTE: SAVE COMPLEX DATA (QS API) ---
# ==========================================

@app.route("/save-complex-data", methods=["POST"])
def save_complex_data():
    raw_data = request.json
    v1_command = raw_data.get('v1') # Complexes form uses 'v1' instead of 'command'
    
    if not v1_command:
        return jsonify({"error": "No V1 commands provided"}), 400

    payload = {
        "action": "import",
        "format": "v1",
        "data": v1_command,
        "submit": 1,
        "username": QS_USERNAME,
        "token": QS_TOKEN
    }

    try:
        r = requests.post(QS_API_URL, data=payload, headers=HEADERS)
        response_data = r.json()
        
        if response_data.get("status") == "OK":
            print(f"QS Complex Batch Submitted! Batch ID: {response_data.get('batch_id')}")
            return jsonify(response_data), 200
        else:
            print(f"QS Error: {response_data}")
            return jsonify(response_data), 500
            
    except Exception as e:
        print(f"QS Complex Request Failed: {e}")
        return jsonify({"error": str(e)}), 500

# ==========================================
# --- ROUTE: FETCH SCRIPT ---
# ==========================================

@app.route('/run-fetch-script')
def run_fetch_script():
    try:
        result = subprocess.run(
            ['python3', 'fetch_data.py'],
            cwd=os.path.join(os.getcwd(), 'update data'),
            capture_output=True,
            text=True,
            check=True,
            stdin=subprocess.DEVNULL,
        )
        return jsonify({'stdout': result.stdout, 'stderr': result.stderr})
    except subprocess.CalledProcessError as e:
        return jsonify({'stdout': e.stdout, 'stderr': e.stderr, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)