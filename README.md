# TV Playout Automation System

A Flask-based web application for TV playout automation with HLS streaming support. Upload videos, manage playlists, and stream content via HLS protocol.

## Features

- 📺 **HLS Streaming**: Real-time video streaming using HTTP Live Streaming (HLS)
- 🎬 **Video Queue Management**: Upload and queue multiple MP4 videos
- 🔴 **Live Camera Support**: Switch between video playback and live camera feed
- 💤 **Idle Loop**: Automatic idle screen when queue is empty
- 🎨 **Modern Web UI**: Beautiful, responsive dashboard with real-time status updates
- 🔄 **Automatic Transitions**: Seamless switching between videos, idle, and live modes

## Prerequisites

- Python 3.8+
- FFmpeg (must be installed and accessible)
- Modern web browser with HLS.js support

## Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/sinlive.git
cd sinlive
```

2. **Create virtual environment**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Linux/Mac
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Install FFmpeg**
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) or use `winget install ffmpeg`
   - **Linux**: `sudo apt install ffmpeg`
   - **Mac**: `brew install ffmpeg`

5. **Configure FFmpeg path** (if needed)
   
   Edit `app.py` and set the correct FFmpeg path:
   ```python
   FFMPEG_PATH = r"C:\path\to\ffmpeg.exe"  # Windows
   # or
   FFMPEG_PATH = "ffmpeg"  # Linux/Mac (if in PATH)
   ```

6. **Create idle video** (optional)
   
   Place an `idle.mp4` file in the project root, or the system will generate SMPTE color bars automatically.

## Usage

1. **Start the server**
```bash
python app.py
```

2. **Open the dashboard**
   
   Navigate to `http://localhost:5000` in your web browser

3. **Start broadcasting**
   - Click **"▶ Start"** to begin streaming
   - Upload videos using the **"Upload Video"** section
   - Videos will automatically play in queue order
   - When queue is empty, idle screen displays

4. **Live camera mode**
   - Click **"🔴 Go Live"** to switch to live camera feed
   - Click **"End Live"** to return to queue/idle mode

## Project Structure

```
sinlive/
├── app.py                 # Flask application & streaming logic
├── requirements.txt       # Python dependencies
├── idle.mp4              # Idle screen video (optional)
├── templates/
│   └── index.html        # Web dashboard UI
├── static/
│   └── hls/              # HLS output directory (auto-generated)
└── videos/               # Uploaded videos directory
```

## Configuration

### FFmpeg Settings

HLS streaming parameters can be adjusted in `app.py`:

```python
'-hls_time', '2',          # Segment duration (seconds)
'-hls_list_size', '10',    # Playlist size
'-b:v', '2500k',           # Video bitrate
'-preset', 'ultrafast',    # Encoding speed
```

### Camera Source

To use a real camera instead of test pattern, edit `app.py`:

```python
# Uncomment and configure your camera:
cmd.extend(['-f', 'dshow', '-i', 'video=Your Camera Name'])
```

## API Endpoints

- `GET /` - Dashboard UI
- `GET /status` - Get current system status
- `POST /upload` - Upload video file
- `POST /start_broadcast` - Start broadcasting
- `POST /stop_broadcast` - Stop broadcasting
- `POST /go_live_stream` - Switch to live camera
- `POST /end_live_stream` - Return to queue mode

## Troubleshooting

### Videos not playing
- Ensure FFmpeg is installed and path is correct
- Check browser console for HLS errors
- Verify video format is H.264/AAC MP4

### CORS errors
- Flask-CORS is enabled by default
- Check browser console for specific errors

### Segment errors
- HLS segments are auto-cleaned on stream transitions
- Check `static/hls/` directory permissions

## Technologies Used

- **Backend**: Flask, Python
- **Streaming**: FFmpeg, HLS protocol
- **Frontend**: HTML5, JavaScript, HLS.js
- **Styling**: Custom CSS with modern design

## License

MIT License - feel free to use and modify for your projects

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss proposed changes.

## Acknowledgments

- FFmpeg for video processing
- HLS.js for browser playback
- Flask for web framework
