from flask import Flask, render_template, jsonify
import subprocess
import os

app = Flask(__name__)

@app.route('/')
def monasteries():
    return render_template('index.html')

# Serve Complexes form
@app.route('/complexes')
def complexes():
    return render_template('complexes.html')

# Endpoint to run a Python script in fetch_data/
@app.route('/run-fetch-script')
def run_fetch_script():
    try:
        subprocess.Popen(
            ['python3', 'fetch_data.py'],
            cwd=os.path.join(os.getcwd(), 'update data'),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True
        )

        return jsonify({
            "status": "started",
            "message": "Fetch script is running in the background"
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
