import os
import threading
import subprocess
import time
import shutil
import atexit

from flask import Flask, render_template, request, jsonify, Response, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

import config
import psutil

from state_manager import StateManager, SegmentTracker
from trash_manager import TrashBinManager
from trash_manager import TrashBinManager
from overlay_manager import OverlayManager
from content_provider import ContentProvider


app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# --- Configuration ---
app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
app.config['HLS_DIR'] = config.HLS_DIR

# Ensure directories exist
os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(config.HLS_DIR, exist_ok=True)
os.makedirs(config.TRASH_DIR, exist_ok=True)
os.makedirs(config.OVERLAYS_DIR, exist_ok=True)

# --- Initialize State Management ---
state_manager = StateManager()
segment_tracker = SegmentTracker(config.SEGMENT_METADATA_FILE)
trash_manager = TrashBinManager(config.HLS_DIR, config.TRASH_DIR, segment_tracker)
trash_manager = TrashBinManager(config.HLS_DIR, config.TRASH_DIR, segment_tracker)
overlay_manager = OverlayManager()
content_provider = ContentProvider()


# --- Global Variables ---
stop_event = threading.Event()
segment_monitor_thread = None

# --- Helper Functions ---

def get_video_duration(file_path):
    """Get video duration using ffprobe"""
    try:
        cmd = [
            config.FFMPEG_PATH.replace('ffmpeg', 'ffprobe'),
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        return float(result.stdout.strip())
    except:
        return None

def start_ffmpeg(source, source_type):
    """Start FFmpeg process with optimized settings"""
    print(f"Starting FFmpeg. Type: {source_type}, Source: {source}")
    
    cmd = [config.FFMPEG_PATH, '-y']

    # Get video duration for tracking
    video_duration = None
    if source_type == 'QUEUE' and os.path.exists(source):
        video_duration = get_video_duration(source)

    # Input Options
    if source_type == 'LIVE':
        # Webcam Input (Windows dshow) or test source
        cmd.extend([
            '-f', 'lavfi', '-i', 'testsrc=size=1280x720:rate=30',
            '-f', 'lavfi', '-i', 'sine=frequency=1000'
        ])
    elif source_type == 'IDLE':
        if os.path.exists(source):
            cmd.extend(['-stream_loop', '-1', '-i', source])
        else:
            print("Idle file not found, using generated SMPTE bars.")
            cmd.extend([
                '-f', 'lavfi', '-i', 'smptebars=size=1280x720:rate=30',
                '-f', 'lavfi', '-i', 'sine=frequency=440'
            ])
    elif source_type == 'URL':
        # Remote URL (YouTube stream, etc.)
        # Add reconnect flags for stability
        cmd.extend([
            '-reconnect', '1',
            '-reconnect_streamed', '1',
            '-reconnect_delay_max', '5',
            '-i', source
        ])
    else:
        # QUEUE (Standard File)
        cmd.extend(['-i', source])

    # Add overlay inputs if available
    overlay_inputs = overlay_manager.get_overlay_inputs()
    for overlay_path in overlay_inputs:
        cmd.extend(['-i', overlay_path])
    
    # Get overlay filter
    overlay_filter = overlay_manager.get_ffmpeg_overlay_filter()
    
    # Program Name Overlay
    program_name = state_manager.get_program_name()
    final_output_label = "[out]"
    
    if config.PROGRAM_NAME_ENABLED and program_name and os.path.exists(config.FONT_PATH):
        # Only add text overlay if font file exists
        # Escape special characters for FFmpeg
        safe_program_name = program_name.replace(":", "\\:").replace("'", "'\\\\''")
        
        drawtext_filter = (
            f"drawtext=text='{safe_program_name}':fontfile={config.FONT_PATH}:"
            f"fontsize={config.FONT_SIZE}:fontcolor={config.FONT_COLOR}:"
            f"x={config.PROGRAM_NAME_X}:y={config.PROGRAM_NAME_Y}:"
            f"box=1:boxcolor={config.BOX_COLOR}:boxborderw={config.BOX_BORDER_WIDTH}"
        )
        
        if overlay_filter:
            # Chain it: [out] -> drawtext -> [out_final]
            overlay_filter += f";{final_output_label}{drawtext_filter}[out_final]"
            final_output_label = "[out_final]"
        else:
            # Apply directly to input: [0:v] -> drawtext -> [out]
            overlay_filter = f"[0:v]{drawtext_filter}{final_output_label}"
    elif config.PROGRAM_NAME_ENABLED and program_name and not os.path.exists(config.FONT_PATH):
        print(f"Warning: Font file not found at {config.FONT_PATH}, skipping program name overlay")
    
    # Output Options (HLS) - Optimized for CPU usage
    cmd.extend([
        '-c:v', 'libx264', '-preset', config.VIDEO_PRESET, '-tune', 'zerolatency',
        '-b:v', config.VIDEO_BITRATE, '-maxrate', config.VIDEO_MAXRATE, '-bufsize', config.VIDEO_BUFSIZE,
        '-g', str(config.GOP_SIZE), '-keyint_min', str(config.GOP_SIZE), '-sc_threshold', '0',
        '-c:a', 'aac', '-b:a', config.AUDIO_BITRATE, '-ar', str(config.AUDIO_SAMPLE_RATE), '-ac', str(config.AUDIO_CHANNELS)
    ])
    
    # Add overlay filter if available
    if overlay_filter:
        cmd.extend(['-filter_complex', overlay_filter, '-map', final_output_label, '-map', '0:a'])
    
    # HLS output settings
    cmd.extend([
        '-f', 'hls',
        '-hls_time', str(config.HLS_SEGMENT_DURATION),
        '-hls_list_size', str(config.HLS_PLAYLIST_SIZE),
        '-hls_flags', 'delete_segments+append_list+program_date_time',
        '-hls_segment_type', 'mpegts',
        '-hls_segment_filename', os.path.join(config.HLS_DIR, 'segment%05d.ts'),
        '-start_number', '0',
        config.HLS_PLAYLIST
    ])

    # Start process (Windows-specific flags for hiding console window)
    if os.name == 'nt':
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE if config.VERBOSE_FFMPEG_LOGGING else subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
    else:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE if config.VERBOSE_FFMPEG_LOGGING else subprocess.DEVNULL
        )
    
    state_manager.set_current_process(process)
    
    # Update playback state
    playing_file = os.path.basename(source) if source_type == 'QUEUE' else source_type
    state_manager.set_current_playback(source_type, playing_file, video_duration)
    
    print(f"FFmpeg started. PID: {process.pid}")
    
    # Read stderr in a thread if verbose logging enabled
    if config.VERBOSE_FFMPEG_LOGGING:
        def read_stderr():
            for line in process.stderr:
                try:
                    print(f"FFmpeg: {line.decode('utf-8', errors='ignore').strip()}")
                except:
                    pass
        
        stderr_thread = threading.Thread(target=read_stderr, daemon=True)
        stderr_thread.start()

def stop_ffmpeg():
    """Stop FFmpeg process"""
    process = state_manager.get_current_process()
    if process:
        print("Stopping FFmpeg process...")
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
        
        state_manager.clear_current_process()
        state_manager.clear_current_playback()
        
        print("FFmpeg stopped")

def monitor_segments():
    """Monitor HLS directory for new segments and track them"""
    last_segments = set()
    
    while not stop_event.is_set():
        try:
            # Get current segments
            current_segments = set(trash_manager.get_active_segments())
            
            # Find new segments
            new_segments = current_segments - last_segments
            
            for segment in new_segments:
                # Get current playback info
                playback = state_manager.get_current_playback()
                
                if playback['source_type']:
                    # Track this segment
                    segment_tracker.add_segment(
                        segment_name=segment,
                        source_video=playback['playing_file'],
                        source_type=playback['source_type'],
                        start_time=playback['elapsed_time'],
                        duration=config.HLS_SEGMENT_DURATION
                    )
                    
                    state_manager.increment_segment_count()
            
            last_segments = current_segments
            
        except Exception as e:
            print(f"Error in segment monitor: {e}")
        
        time.sleep(1)

# --- Background Manager ---

def stream_manager_loop():
    """Main stream management loop"""
    while not stop_event.is_set():
        # 1. Check Broadcast State
        if not state_manager.is_broadcasting():
            if state_manager.get_current_process():
                stop_ffmpeg()
            time.sleep(1)
            continue

        # 2. Check Live Camera Mode
        if state_manager.is_live_camera_mode():
            playback = state_manager.get_current_playback()
            if playback['source_type'] != 'LIVE':
                stop_ffmpeg()
                start_ffmpeg(None, 'LIVE')
            
            # Restart if crashed
            process = state_manager.get_current_process()
            if process and process.poll() is not None:
                print("Live process died, restarting...")
                start_ffmpeg(None, 'LIVE')
            
            time.sleep(1)
            continue

        # 3. Queue / Idle Mode
        process = state_manager.get_current_process()
        playback = state_manager.get_current_playback()
        
        # Check if current process finished
        if process and process.poll() is not None:
            print(f"Process finished (Type: {playback['source_type']}).")
            state_manager.clear_current_process()
            state_manager.clear_current_playback()
            process = None

        # If something is running, just wait (unless it's IDLE and we have a queue item)
        if process:
            if playback['source_type'] == 'IDLE' and state_manager.queue_length() > 0:
                print("New item in queue, stopping IDLE...")
                stop_ffmpeg()
            else:
                time.sleep(1)
                continue

        # Nothing running. Decide what to play.
        if state_manager.queue_length() > 0:
            # Play next in queue
            next_file = state_manager.pop_from_queue()
            file_path = os.path.join(config.UPLOAD_FOLDER, next_file)
            if os.path.exists(file_path):
                # If coming from auto mode, we might want to reset program name or keep it?
                # Usually queue items have their own logic, but for now let's reset if needed.
                # Or just let the user set it manually for queue items.
                start_ffmpeg(file_path, 'QUEUE')
            else:
                print(f"File missing: {next_file}")
        
        elif state_manager.is_auto_mode():
            # Auto Mode: Fetch from YouTube
            hashtag = state_manager.get_current_hashtag()
            print(f"[AUTO MODE] Fetching video for hashtag: '{hashtag}'...")
            
            url, title = content_provider.get_random_video(hashtag)
            
            if url:
                print(f"[AUTO MODE] Starting video: {title}")
                print(f"[AUTO MODE] Stream URL: {url[:100]}...")  # Print first 100 chars
                # Update program name to video title
                state_manager.set_program_name(title)
                start_ffmpeg(url, 'URL')
            else:
                print("[AUTO MODE] Failed to fetch video, falling back to IDLE...")
                start_ffmpeg(config.IDLE_SOURCE_PATH, 'IDLE')
                # Sleep a bit longer to avoid rapid retry loops if API is down
                time.sleep(5)
                
        else:
            # Queue empty -> Play IDLE
            start_ffmpeg(config.IDLE_SOURCE_PATH, 'IDLE')
        
        time.sleep(1)

# Start Background Threads
bg_thread = threading.Thread(target=stream_manager_loop, daemon=True)
bg_thread.start()

segment_monitor_thread = threading.Thread(target=monitor_segments, daemon=True)
segment_monitor_thread.start()

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
        file.save(os.path.join(config.UPLOAD_FOLDER, filename))
        state_manager.add_to_queue(filename)
        return jsonify({'success': True, 'filename': filename})

@app.route('/status')
def status():
    """Legacy status endpoint"""
    state = state_manager.get_full_state()
    return jsonify({
        'queue': state['queue'],
        'is_broadcasting': state['is_broadcasting'],
        'is_live_camera_mode': state['is_live_camera_mode'],
        'current_source': state['current_playback']['source_type'],
        'playing_file': state['current_playback']['playing_file']
    })

# --- New API Endpoints ---

@app.route('/api/state')
def api_state():
    """Get full application state"""
    return jsonify(state_manager.get_full_state())

@app.route('/api/segments/current')
def api_current_segment():
    """Get current playing segment details"""
    current = segment_tracker.get_current_segment()
    if current:
        return jsonify(current)
    return jsonify({'error': 'No active segment'}), 404

@app.route('/api/segments/history')
def api_segment_history():
    """Get segment history"""
    limit = request.args.get('limit', 20, type=int)
    history = segment_tracker.get_segment_history(limit)
    return jsonify(history)

@app.route('/api/segments/stats')
def api_segment_stats():
    """Get segment statistics"""
    return jsonify(segment_tracker.get_stats())

@app.route('/api/trash/stats')
def api_trash_stats():
    """Get trash bin statistics"""
    return jsonify(trash_manager.get_stats())

@app.route('/api/system/stats')
def api_system_stats():
    """Get system resource usage"""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        # Get FFmpeg process stats if running
        ffmpeg_stats = None
        process = state_manager.get_current_process()
        if process:
            try:
                p = psutil.Process(process.pid)
                ffmpeg_stats = {
                    'cpu_percent': p.cpu_percent(interval=0.1),
                    'memory_mb': p.memory_info().rss / (1024 * 1024)
                }
            except:
                pass
        
        return jsonify({
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_used_mb': memory.used / (1024 * 1024),
            'memory_total_mb': memory.total / (1024 * 1024),
            'ffmpeg': ffmpeg_stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Virtual Stream Routes (Username Support) ---

@app.route('/live/<username>/stream.m3u8')
def user_stream_playlist(username):
    """Serve the main playlist under a user-specific URL"""
    # We ignore the username for now and serve the same stream
    # This creates the illusion of a unique link
    return send_from_directory(config.HLS_DIR, 'stream.m3u8')

@app.route('/live/<username>/playlist.m3u')
def user_stream_playlist_m3u(username):
    """Serve a Master Playlist (M3U) for IPTV players"""
    host = request.host_url.rstrip('/')
    stream_url = f"{host}/live/{username}/stream.m3u8"
    logo_url = "https://seeklogo.com/images/T/tv-logo-F7231DA292-seeklogo.com.png"
    
    # M3U content with logo
    content = f"""#EXTM3U
#EXTINF:-1 tvg-id="sinlive" tvg-name="SinLive" tvg-logo="{logo_url}" group-title="Live",SinLive Stream
{stream_url}"""

    return Response(content, mimetype='text/plain')

@app.route('/live/<username>/<path:filename>')
def user_stream_segment(username, filename):
    """Serve HLS segments under a user-specific URL"""
    return send_from_directory(config.HLS_DIR, filename)

# --- Control Endpoints ---

@app.route('/start_broadcast', methods=['POST'])
def start_broadcast():
    state_manager.set_broadcasting(True)
    state_manager.set_live_camera_mode(False)
    return jsonify({'success': True})

@app.route('/stop_broadcast', methods=['POST'])
def stop_broadcast():
    state_manager.set_broadcasting(False)
    return jsonify({'success': True})

@app.route('/go_live_stream', methods=['POST'])
def go_live_stream():
    state_manager.set_broadcasting(True)
    state_manager.set_live_camera_mode(True)
    return jsonify({'success': True})

@app.route('/end_live_stream', methods=['POST'])
def end_live_stream():
    state_manager.set_broadcasting(True)
    state_manager.set_live_camera_mode(False)
    return jsonify({'success': True})

# --- Overlay Endpoints ---

@app.route('/set_program_name', methods=['POST'])
def set_program_name():
    """Update the program name overlay text"""
    data = request.json
    name = data.get('program_name', '')
    state_manager.set_program_name(name)
    return jsonify({'success': True, 'program_name': name})

@app.route('/upload_logo', methods=['POST'])
def upload_logo():
    """Upload logo image for watermark"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        # Save temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join(config.UPLOAD_FOLDER, f'temp_logo_{filename}')
        file.save(temp_path)
        
        # Process with overlay manager
        success, message, info = overlay_manager.save_logo(temp_path)
        
        # Remove temp file
        try:
            os.remove(temp_path)
        except:
            pass
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'info': info
            })
        else:
            return jsonify({'error': message}), 400

@app.route('/upload_banner', methods=['POST'])
def upload_banner():
    """Upload banner image"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        # Save temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join(config.UPLOAD_FOLDER, f'temp_banner_{filename}')
        file.save(temp_path)
        
        # Process with overlay manager
        success, message, info = overlay_manager.save_banner(temp_path)
        
        # Remove temp file
        try:
            os.remove(temp_path)
        except:
            pass
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'info': info
            })
        else:
            return jsonify({'error': message}), 400

@app.route('/delete_logo', methods=['POST'])
def delete_logo():
    """Delete logo overlay"""
    success = overlay_manager.delete_logo()
    if success:
        return jsonify({'success': True, 'message': 'Logo deleted'})
    return jsonify({'error': 'Failed to delete logo'}), 500

@app.route('/delete_banner', methods=['POST'])
def delete_banner():
    """Delete banner overlay"""
    success = overlay_manager.delete_banner()
    if success:
        return jsonify({'success': True, 'message': 'Banner deleted'})
    return jsonify({'error': 'Failed to delete banner'}), 500

@app.route('/overlay_status')
def overlay_status():
    """Get current overlay status and recommendations"""
    return jsonify(overlay_manager.get_status())

@app.route('/toggle_overlay', methods=['POST'])
def toggle_overlay():
    """Toggle overlay system on/off"""
    data = request.get_json() or {}
    overlay_type = data.get('type')  # 'logo', 'banner', or 'all'
    enabled = data.get('enabled', True)
    
    if overlay_type == 'logo':
        config.LOGO_ENABLED = enabled
    elif overlay_type == 'banner':
        config.BANNER_ENABLED = enabled
    elif overlay_type == 'all':
        config.OVERLAY_ENABLED = enabled
    else:
        return jsonify({'error': 'Invalid overlay type'}), 400
    
    return jsonify({
        'success': True,
        'overlay_enabled': config.OVERLAY_ENABLED,
        'logo_enabled': config.LOGO_ENABLED,
        'banner_enabled': config.BANNER_ENABLED
    })

# --- Auto Mode Endpoints ---

@app.route('/api/automode/start', methods=['POST'])
def start_auto_mode():
    data = request.json or {}
    hashtag = data.get('hashtag')
    
    if hashtag:
        state_manager.set_current_hashtag(hashtag)
    
    state_manager.set_auto_mode(True)
    
    # If currently IDLE, we can stop it to trigger auto mode immediately
    playback = state_manager.get_current_playback()
    if playback['source_type'] == 'IDLE':
        stop_ffmpeg()
        
    return jsonify({'success': True, 'hashtag': state_manager.get_current_hashtag()})

@app.route('/api/automode/stop', methods=['POST'])
def stop_auto_mode():
    state_manager.set_auto_mode(False)
    return jsonify({'success': True})

@app.route('/api/automode/set_hashtag', methods=['POST'])
def set_auto_hashtag():
    data = request.json
    hashtag = data.get('hashtag')
    if hashtag:
        state_manager.set_current_hashtag(hashtag)
        return jsonify({'success': True, 'hashtag': hashtag})
    return jsonify({'error': 'No hashtag provided'}), 400

# --- Cleanup on Exit ---

def cleanup():
    """Cleanup resources on application exit"""
    print("Cleaning up...")
    stop_event.set()
    stop_ffmpeg()
    trash_manager.stop()

def cleanup_on_startup():
    """
    Perform cleanup on application startup:
    1. Delete all files in static/hls EXCEPT stream.m3u8
    2. Delete all files in overlays directory
    """
    print("Performing startup cleanup...")
    
    # 1. Clean HLS directory
    if os.path.exists(config.HLS_DIR):
        print(f"Cleaning HLS directory: {config.HLS_DIR}")
        for filename in os.listdir(config.HLS_DIR):
            file_path = os.path.join(config.HLS_DIR, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    # Keep stream.m3u8, delete everything else
                    if filename != 'stream.m3u8':
                        os.unlink(file_path)
                        print(f"Deleted: {filename}")
                elif os.path.isdir(file_path) and filename != 'trash':
                    # Optional: delete subdirectories if any (except trash)
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")
    
    # 2. Clean Overlays directory
    if os.path.exists(config.OVERLAYS_DIR):
        print(f"Cleaning Overlays directory: {config.OVERLAYS_DIR}")
        for filename in os.listdir(config.OVERLAYS_DIR):
            file_path = os.path.join(config.OVERLAYS_DIR, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                    print(f"Deleted overlay: {filename}")
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")

atexit.register(cleanup)

if __name__ == '__main__':
    cleanup_on_startup()
    app.run(host='0.0.0.0', port=5000, debug=False)
