import os
import time
import threading
import subprocess
import re
import signal
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'videos')
HLS_DIR = os.path.join(BASE_DIR, 'static', 'hls')
HLS_PLAYLIST = os.path.join(HLS_DIR, 'stream.m3u8')
IDLE_SOURCE_PATH = os.path.join(BASE_DIR, 'idle.mp4')

# *** CRITICAL: Set your absolute FFmpeg path here ***
FFMPEG_PATH = r"C:\Users\unall\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe"

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['HLS_DIR'] = HLS_DIR

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(HLS_DIR, exist_ok=True)

# --- Global State ---
playlist_queue = []       # List of filenames
is_broadcasting = False   # Master switch
is_live_camera_mode = False # Source switch (False=Queue/Idle, True=Camera)

current_process = None
current_source_type = None # 'QUEUE', 'IDLE', 'LIVE', None
current_playing_file = None # For UI display

stop_event = threading.Event()

# --- Helper Functions ---

def start_ffmpeg(source, source_type):
    global current_process, current_source_type, current_playing_file
    
    print(f"Starting FFmpeg. Type: {source_type}, Source: {source}")
    
    cmd = [FFMPEG_PATH, '-y']

    # Input Options
    if source_type == 'LIVE':
        # Webcam Input (Windows dshow)
        # cmd.extend(['-f', 'dshow', '-i', 'video=Integrated Camera'])
        
        # Fallback to Test Source if no camera configured or for testing
        cmd.extend([
            '-f', 'lavfi', '-i', 'testsrc=size=1280x720:rate=30',
            '-f', 'lavfi', '-i', 'sine=frequency=1000'
        ])
    elif source_type == 'IDLE':
        if os.path.exists(source):
            # Loop the idle file indefinitely - NO -re for faster startup
            cmd.extend(['-stream_loop', '-1', '-i', source])
        else:
            # Fallback generated idle source (SMPTE bars)
            print("Idle file not found, using generated SMPTE bars.")
            cmd.extend([
                '-f', 'lavfi', '-i', 'smptebars=size=1280x720:rate=30',
                '-f', 'lavfi', '-i', 'sine=frequency=440'
            ])
    else:
        # QUEUE (Standard File) - NO -re for faster startup
        cmd.extend(['-i', source])

    # Output Options (HLS) - Optimized for continuous streaming
    # Key changes:
    # - hls_start_number_source: use sequence number for better tracking
    # - program_date_time: add timestamps for better sync
    # - append_list: smooth transitions between sources
    # - delete_segments: auto cleanup old segments
    # - Shorter segments (2s) for faster startup and better buffering
    cmd.extend([
        '-c:v', 'libx264', '-preset', 'ultrafast', '-tune', 'zerolatency',
        '-b:v', '2500k', '-maxrate', '3000k', '-bufsize', '6000k',
        '-g', '30', '-keyint_min', '30', '-sc_threshold', '0',
        '-c:a', 'aac', '-b:a', '128k', '-ar', '44100', '-ac', '2',
        '-f', 'hls',
        '-hls_time', '2',
        '-hls_list_size', '10',
        '-hls_flags', 'delete_segments+append_list+program_date_time',
        '-hls_segment_type', 'mpegts',
        '-hls_segment_filename', os.path.join(HLS_DIR, 'segment%05d.ts'),
        '-start_number', '0',
        HLS_PLAYLIST
    ])

    # Windows: Hide console window (but show errors for debugging)
    creation_flags = 0
    if os.name == 'nt':
        creation_flags = subprocess.CREATE_NO_WINDOW

    # Temporarily enable stderr to see FFmpeg errors
    current_process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=creation_flags
    )
    current_source_type = source_type
    current_playing_file = source if source_type == 'QUEUE' else source_type
    
    # Print FFmpeg command for debugging
    print(f"FFmpeg command: {' '.join(cmd)}")
    
    # Read stderr in a thread to capture errors
    def read_stderr():
        for line in current_process.stderr:
            try:
                print(f"FFmpeg: {line.decode('utf-8', errors='ignore').strip()}")
            except:
                pass
    
    import threading
    stderr_thread = threading.Thread(target=read_stderr, daemon=True)
    stderr_thread.start()

def stop_ffmpeg():
    global current_process, current_source_type, current_playing_file
    if current_process:
        print("Stopping FFmpeg process...")
        current_process.terminate()
        try:
            current_process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            current_process.kill()
        current_process = None
        current_source_type = None
        current_playing_file = None
        
        # Clean up old HLS segments after stopping
        print("Cleaning up HLS segments...")
        try:
            for file in os.listdir(HLS_DIR):
                if file.endswith('.ts') or file.endswith('.m3u8'):
                    file_path = os.path.join(HLS_DIR, file)
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        pass
        except Exception as e:
            print(f"Cleanup error: {e}")

# --- Background Manager ---

def stream_manager_loop():
    global is_broadcasting, is_live_camera_mode, current_process, current_source_type, playlist_queue

    while not stop_event.is_set():
        # 1. Check Broadcast State
        if not is_broadcasting:
            if current_process:
                stop_ffmpeg()
            time.sleep(1)
            continue

        # 2. Check Live Camera Mode
        if is_live_camera_mode:
            if current_source_type != 'LIVE':
                stop_ffmpeg()
                start_ffmpeg(None, 'LIVE')
            
            # Restart if crashed
            if current_process and current_process.poll() is not None:
                print("Live process died, restarting...")
                start_ffmpeg(None, 'LIVE')
            
            time.sleep(1)
            continue

        # 3. Queue / Idle Mode (is_live_camera_mode == False)
        
        # Check if current process finished
        if current_process and current_process.poll() is not None:
            print(f"Process finished (Type: {current_source_type}).")
            current_process = None
            current_source_type = None

        # If something is running, just wait (unless it's IDLE and we have a queue item)
        if current_process:
            if current_source_type == 'IDLE' and len(playlist_queue) > 0:
                print("New item in queue, stopping IDLE...")
                stop_ffmpeg() # Stop IDLE to play the new video
            else:
                # Normal playback
                time.sleep(1)
                continue

        # Nothing running. Decide what to play.
        if len(playlist_queue) > 0:
            # Play next in queue
            next_file = playlist_queue.pop(0)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], next_file)
            if os.path.exists(file_path):
                start_ffmpeg(file_path, 'QUEUE')
            else:
                print(f"File missing: {next_file}")
        else:
            # Queue empty -> Play IDLE
            # Only start if not already playing IDLE (handled by 'Nothing running' check)
            start_ffmpeg(IDLE_SOURCE_PATH, 'IDLE')
        
        time.sleep(1)

# Start Thread
bg_thread = threading.Thread(target=stream_manager_loop, daemon=True)
bg_thread.start()

# --- Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        playlist_queue.append(filename)
        return jsonify({'success': True, 'filename': filename})

@app.route('/status')
def status():
    return jsonify({
        'queue': playlist_queue,
        'is_broadcasting': is_broadcasting,
        'is_live_camera_mode': is_live_camera_mode,
        'current_source': current_source_type,
        'playing_file': current_playing_file
    })

# --- Control Endpoints ---

@app.route('/start_broadcast', methods=['POST'])
def start_broadcast():
    global is_broadcasting, is_live_camera_mode
    is_broadcasting = True
    is_live_camera_mode = False
    return jsonify({'success': True})

@app.route('/stop_broadcast', methods=['POST'])
def stop_broadcast():
    global is_broadcasting
    is_broadcasting = False
    return jsonify({'success': True})

@app.route('/go_live_stream', methods=['POST'])
def go_live_stream():
    global is_broadcasting, is_live_camera_mode
    is_broadcasting = True
    is_live_camera_mode = True
    return jsonify({'success': True})

@app.route('/end_live_stream', methods=['POST'])
def end_live_stream():
    global is_broadcasting, is_live_camera_mode
    is_broadcasting = True
    is_live_camera_mode = False
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
