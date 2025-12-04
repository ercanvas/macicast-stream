"""Quick test to verify yt-dlp detection works"""
from content_provider import ContentProvider

provider = ContentProvider()
print(f"Detected yt-dlp path: {provider.ytdlp_path}")
print(f"Type: {type(provider.ytdlp_path)}")

# Verify it's a valid path
import os
if isinstance(provider.ytdlp_path, str):
    print(f"File exists: {os.path.isfile(provider.ytdlp_path)}")
elif isinstance(provider.ytdlp_path, list):
    print(f"Using Python module invocation")
