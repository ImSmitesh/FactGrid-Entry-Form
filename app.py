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
    script_path = os.path.join('update data', 'fetch_data.py')
    try:
        result = subprocess.run(
            ['python', script_path],
            capture_output=True, text=True, check=True
        )
        return jsonify({'stdout': result.stdout, 'stderr': result.stderr})
    except subprocess.CalledProcessError as e:
        return jsonify({'stdout': e.stdout, 'stderr': e.stderr, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
