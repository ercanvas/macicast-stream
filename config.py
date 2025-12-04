"""
Configuration file for TV Playout System
Centralized settings for segment management, FFmpeg parameters, and system resources
"""

import os

# --- Directory Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'videos')
HLS_DIR = os.path.join(BASE_DIR, 'static', 'hls')
TRASH_DIR = os.path.join(HLS_DIR, 'trash')
HLS_PLAYLIST = os.path.join(HLS_DIR, 'stream.m3u8')
SEGMENT_METADATA_FILE = os.path.join(HLS_DIR, 'segments_metadata.json')
IDLE_SOURCE_PATH = os.path.join(BASE_DIR, 'idle.mp4')

# *** CRITICAL: Set your absolute FFmpeg path here ***
FFMPEG_PATH = r"C:\Users\unall\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe"

# --- Segment Management Configuration ---
# Maximum number of segments to keep in active directory (older ones moved to trash)
MAX_ACTIVE_SEGMENTS = 50

# Time in seconds before permanently deleting segments from trash
TRASH_RETENTION_TIME = 3600  # 1 hour

# HLS segment duration in seconds
HLS_SEGMENT_DURATION = 2

# Number of segments to keep in playlist
HLS_PLAYLIST_SIZE = 10

# --- FFmpeg Encoding Configuration ---
# Video encoding preset (ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow)
# veryfast provides good balance between CPU usage and quality
VIDEO_PRESET = 'veryfast'

# Video bitrate settings
VIDEO_BITRATE = '2500k'
VIDEO_MAXRATE = '3000k'
VIDEO_BUFSIZE = '6000k'

# GOP (Group of Pictures) size - keyframe interval
# Lower value = more keyframes = better seeking but higher bitrate
GOP_SIZE = 60  # 2 seconds at 30fps

# Audio settings
AUDIO_BITRATE = '128k'
AUDIO_SAMPLE_RATE = '44100'
AUDIO_CHANNELS = 2

# --- System Monitoring Configuration ---
# Interval in seconds for updating system stats
STATS_UPDATE_INTERVAL = 2

# Interval in seconds for segment cleanup check
CLEANUP_CHECK_INTERVAL = 10

# --- Resource Limits ---
# Maximum CPU percentage threshold for warnings
MAX_CPU_THRESHOLD = 80

# Maximum memory usage in MB for warnings
MAX_MEMORY_THRESHOLD = 1024

# --- Logging Configuration ---
# Enable detailed FFmpeg logging (set to False for production)
VERBOSE_FFMPEG_LOGGING = False

# Enable segment tracking debug logs
DEBUG_SEGMENT_TRACKING = True

# --- Overlay Configuration ---
# Directory for overlay images (logo, banner)
OVERLAYS_DIR = os.path.join(BASE_DIR, 'overlays')
LOGO_PATH = os.path.join(OVERLAYS_DIR, 'logo.png')
BANNER_PATH = os.path.join(OVERLAYS_DIR, 'banner.png')

# Overlay Positions
# Logo: top-left corner with padding
LOGO_POSITION_X = 10
LOGO_POSITION_Y = 10

# Banner: bottom of screen with padding
BANNER_POSITION_X = 0
BANNER_POSITION_Y_OFFSET = 10  # pixels from bottom

# Overlay Settings
OVERLAY_ENABLED = True
LOGO_ENABLED = True
BANNER_ENABLED = True

# Recommended sizes (will be auto-scaled if different)
LOGO_RECOMMENDED_WIDTH = 200
LOGO_RECOMMENDED_HEIGHT = 100
BANNER_RECOMMENDED_WIDTH = 1280
BANNER_RECOMMENDED_HEIGHT = 150

# Maximum file sizes (in MB)
MAX_LOGO_SIZE_MB = 5
MAX_BANNER_SIZE_MB = 10

# Allowed image formats
ALLOWED_OVERLAY_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# --- Stream Resolution ---
# Used for calculating overlay sizes
STREAM_WIDTH = 1280
STREAM_HEIGHT = 720

# --- Program Name Overlay ---
PROGRAM_NAME_ENABLED = True
FONT_PATH = "arial.ttf"  # FFmpeg usually finds this on Windows, or provide full path C:/Windows/Fonts/arial.ttf
FONT_SIZE = 24
FONT_COLOR = "white"
BOX_COLOR = "black@0.0"
BOX_BORDER_WIDTH = 5
PROGRAM_NAME_X = "w-tw-10"  # Top-right (w = width, tw = text width)
PROGRAM_NAME_Y = "10"       # 10px from top

# --- TikTok Automation Configuration ---
AUTO_MODE_ENABLED = False
TIKTOK_HASHTAGS = ["funny", "dance", "comedy", "trending"]

