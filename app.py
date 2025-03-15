from flask import Flask, request, send_file, jsonify, render_template
import subprocess, json, time, os, zipfile, shutil, logging
from threading import Thread
from sys import platform
import uuid

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_key_123")  # For dev only

# Global dictionary to store download states
download_states = {}

def install_ffmpeg():
    """Install FFMPEG if needed"""
    try:
        binary = "python3.exe" if platform == "win32" else "python3"
        proc = subprocess.Popen(
            [binary, "-m", "spotdl", "--download-ffmpeg"],
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE
        )
        time.sleep(5)
        proc.stdin.write(b"y")
        proc.stdin.flush()
        logger.info("FFMPEG installation completed")
    except Exception as e:
        logger.error(f"FFMPEG installation failed: {str(e)}")

def read_stdout(process, session_id):
    """Read stdout and update progress for a specific session"""
    try:
        while True:
            line = process.stdout.readline()
            if not line:
                break
            
            if line.startswith(b"Found "):
                try:
                    download_states[session_id]["num"] = int(line.split(b" ")[1].decode())
                except ValueError:
                    logger.warning(f"Could not parse track count from line: {line}")
                    
            if line.startswith(b"Downloaded ") or line.startswith(b"Skipping "):
                download_states[session_id]["downloaded_size"] += 1
                
            download_states[session_id]["output"] += line
            time.sleep(0.05)
    except Exception as e:
        logger.error(f"Error reading stdout: {str(e)}")
        download_states[session_id]["error"] = str(e)

def cleanup_sessions():
    """Cleanup function to delete old sessions after 1 hour"""
    while True:
        current_time = time.time()
        for session_id, state in list(download_states.items()):
            try:
                folder_creation_time = os.path.getctime(state["folder"])
                if current_time - folder_creation_time > 3600:
                    shutil.rmtree(state["folder"])
                    del download_states[session_id]
                    logger.info(f"Cleaned up session: {session_id}")
            except Exception as e:
                logger.error(f"Failed to cleanup session {session_id}: {str(e)}")
        time.sleep(3600)

# Start cleanup thread
Thread(target=cleanup_sessions, daemon=True).start()

# Install FFMPEG on startup
install_ffmpeg()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def start_download():
    try:
        url = request.json.get("url")
        if not url:
            return jsonify({"error": "URL is required"}), 400
            
        if not url.startswith("https://open.spotify.com/"):
            return jsonify({"error": "Invalid Spotify URL"}), 400

        session_id = str(uuid.uuid4())
        download_folder = f"./downloads/{session_id}/"
        
        os.makedirs(download_folder, exist_ok=True)
        
        download_states[session_id] = {
            "output": b"",
            "n": 1,
            "num": 1,
            "download_size": 1,
            "downloaded_size": 0,
            "folder": download_folder,
            "timestamp": time.time(),
            "error": None,
            "process": None,
            "cancelled": False
        }

        process = subprocess.Popen(
            ["python3", '-m', 'spotdl', url, '--output', download_folder],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        download_states[session_id]["process"] = process
        Thread(target=read_stdout, args=(process, session_id), daemon=True).start()
        
        return jsonify({"session_id": session_id})
        
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Remaining routes from original implementation...
@app.route('/output')
def get_output():
    session_id = request.args.get('session_id')
    if not session_id or session_id not in download_states:
        return "No such session", 404
    return download_states[session_id]["output"]

@app.route('/download-progress')
def download_progress():
    session_id = request.args.get('session_id')
    if not session_id or session_id not in download_states:
        return jsonify({"error": "No such session"}), 404

    state = download_states[session_id]
    percentage = int((state["downloaded_size"] / state["num"]) * 100) if state["num"] > 0 else 0
    return jsonify({
        "percentage": percentage,
        "download_complete": state["downloaded_size"] == state["num"]
    })

@app.route('/download/<session_id>')
def download_zip(session_id):
    folder = f"./downloads/{session_id}/"
    if not os.path.exists(folder):
        return jsonify({"error": "No such session"}), 404

    zip_filename = f"./downloads/{session_id}.zip"
    with zipfile.ZipFile(zip_filename, 'w') as zf:
        for root, _, files in os.walk(folder):
            for file in files:
                file_path = os.path.join(root, file)
                zf.write(file_path, os.path.relpath(file_path, folder))

    return send_file(zip_filename, as_attachment=True)

@app.route('/tracks')
def get_tracks():
    session_id = request.args.get('session_id')
    if not session_id or session_id not in download_states:
        return jsonify({"error": "No such session"}), 404

    folder = f"./downloads/{session_id}/"
    tracks = [f for f in os.listdir(folder) if f.endswith('.mp3')]
    return jsonify(tracks)

@app.route('/download-track/<session_id>/<track_name>')
def download_track(session_id, track_name):
    track_path = f"./downloads/{session_id}/{track_name}"
    if not os.path.exists(track_path):
        return jsonify({"error": "Track not found"}), 404
    return send_file(track_path, as_attachment=True)

@app.route('/cancel-download')
def cancel_download():
    session_id = request.args.get('session_id')
    if not session_id or session_id not in download_states:
        return jsonify({"error": "No such session"}), 404

    state = download_states[session_id]
    if state["process"]:
        state["process"].terminate()
        state["cancelled"] = True
        
    try:
        shutil.rmtree(state["folder"])
        del download_states[session_id]
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Failed to cancel download: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
