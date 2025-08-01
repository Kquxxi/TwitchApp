import sys
import os
import subprocess
import json
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
            [sys.executable, script],
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
    report_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'raport.html'))
    ready = os.path.exists(report_path)
    return jsonify({'ready': ready})

@app.route('/raport-fragment')
def raport_fragment():
    # wczytujemy JSON z bazy gotowych danych:
    with open(os.path.join(os.path.dirname(__file__),'..','raport_data.json'), encoding='utf-8') as f:
        data = json.load(f)
    clips = data['clips']
    stats = data['stats']
    return render_template('raport_fragment.html', clips=clips, stats=stats)

# --- KICK REPORT ENDPOINTS --------------------------------

@app.route('/api/generate-raport-kick')
def api_generate_raport_kick():
    script = os.path.join(os.path.dirname(__file__),
                          '..','kick','generate_raport_kick.py')
    out_html = os.path.join(os.path.dirname(__file__),
                            '..','kick','raport_kick.html')
    if os.path.exists(out_html):
        os.remove(out_html)
    subprocess.Popen([sys.executable, script])
    return jsonify({'message': 'Generowanie kick-raportu uruchomione'}), 202

@app.route('/raport-kick')
def raport_kick():
    return send_file(os.path.abspath(
        os.path.join('kick','raport_kick.html')
    ))

@app.route('/api/report-kick-ready')
def api_report_kick_ready():
    ready = os.path.exists(os.path.join('kick','raport_kick.html'))
    return jsonify({'ready': ready})

@app.route('/raport-kick-fragment')
def raport_kick_fragment():
    with open(os.path.join('kick','raport_kick_data.json'),
              encoding='utf-8') as f:
        data = json.load(f)
    return render_template('raport_kick_fragment.html',
                           clips=data['clips'], stats=data['stats'])


if __name__ == '__main__':
    app.run(debug=True)
