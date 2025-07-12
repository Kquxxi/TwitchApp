import os
import subprocess
from flask import Flask, render_template, jsonify, send_file
from subprocess import CalledProcessError


app = Flask(
    __name__,
    static_folder='../static',
    template_folder='../templates'
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/update-streamers')
def api_update_streamers():
    script = os.path.abspath(os.path.join(os.path.dirname(__file__),'..','update_streamers.py'))
    try:
        res = subprocess.run(
            ['python', script],
            capture_output=True, text=True, check=True
        )
        return jsonify({'message': res.stdout})
    except CalledProcessError as e:
        # zwracamy stderr i code, by łatwiej debugować
        return jsonify({'error': e.stderr or str(e), 'code': e.returncode}), 500

@app.route('/api/generate-raport')
def api_generate_raport():
    report_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'raport.html'))
    # jeśli jest stary raport, to go usuwamy
    if os.path.exists(report_path):
        os.remove(report_path)
    # uruchamiamy w tle
    script = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'generate_raport.py'))
    subprocess.Popen(['python', script])
    return jsonify({'message': 'Generowanie raportu uruchomione'}), 202

@app.route('/raport')
def raport():
    return send_file(os.path.abspath('raport.html'))

@app.route('/api/report-ready')
def api_report_ready():
    # ścieżka do raport.html w rootzie
    report_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'raport.html'))
    ready = os.path.exists(report_path)
    return jsonify({'ready': ready})

if __name__ == '__main__':
    app.run(debug=True)
