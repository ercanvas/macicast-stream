import subprocess
import json
import random
import shutil
import sys
import os

class ContentProvider:
    def __init__(self):
        # Detect yt-dlp path, especially when running in a virtual environment
        ytdlp_path = None
        
        # First, check if we're in a venv and look for yt-dlp there
        if hasattr(sys, 'prefix') and sys.prefix != sys.base_prefix:
            # We're in a virtual environment
            if sys.platform == 'win32':
                venv_ytdlp = os.path.join(sys.prefix, 'Scripts', 'yt-dlp.exe')
            else:
                venv_ytdlp = os.path.join(sys.prefix, 'bin', 'yt-dlp')
            
            if os.path.isfile(venv_ytdlp):
                ytdlp_path = venv_ytdlp
        
        # Fallback to system PATH
        if not ytdlp_path:
            ytdlp_path = shutil.which('yt-dlp')
        
        # Final fallback: use python -m yt_dlp
        if not ytdlp_path:
            ytdlp_path = [sys.executable, '-m', 'yt_dlp']
        
        self.ytdlp_path = ytdlp_path

    def get_random_video(self, hashtag):
        """
        Fetches a random video URL and title from YouTube for a given hashtag/keyword.
        Returns a tuple (url, title) or (None, None) if failed.
        """
        if not hashtag:
            return None, None

        # Clean hashtag
        search_term = hashtag.replace('#', '')
        
        print(f"Searching YouTube for: {search_term}...")

        # Use YouTube search which is much more reliable with yt-dlp
        # ytsearch10: means "search YouTube and get 10 results"
        
        try:
            # Get top 10 search results from YouTube
            search_query = f"ytsearch10:{search_term}"
            
            # Handle both string path and list (for python -m invocation)
            if isinstance(self.ytdlp_path, list):
                cmd = self.ytdlp_path + [
                    '--dump-json',
                    '--flat-playlist',
                    '--playlist-end', '10',
                    search_query
                ]
            else:
                cmd = [
                    self.ytdlp_path,
                    '--dump-json',
                    '--flat-playlist',
                    '--playlist-end', '10',
                    search_query
                ]
            
            # Run command with timeout
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=30)
            
            if result.returncode != 0:
                print(f"❌ yt-dlp search failed with return code {result.returncode}")
                print(f"   Error: {result.stderr[:500]}")  # Print first 500 chars of error
                return None, None

            videos = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        data = json.loads(line)
                        videos.append(data)
                    except:
                        pass
            
            if not videos:
                print("❌ No videos found in search results")
                return None, None

            # Pick a random video
            print(f"✓ Found {len(videos)} videos, selecting random one...")
            selected = random.choice(videos)
            video_url = selected.get('url')
            if not video_url:
                # Sometimes the url is in id field for YouTube
                video_id = selected.get('id')
                if video_id:
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                else:
                    print("❌ Could not extract video URL or ID")
                    return None, None
            
            title = selected.get('title', 'YouTube Video')
            
            # Now resolve the direct stream URL for this video
            # Request a format that has both video and audio combined
            print(f"✓ Resolving stream for: {title}")
            
            # Use format selection to get a stream with both video and audio
            # 'best' gives us the best quality with audio+video combined
            if isinstance(self.ytdlp_path, list):
                cmd_resolve = self.ytdlp_path + [
                    '-f', 'best[ext=mp4]/best',  # Prefer mp4 format with audio+video
                    '-g', 
                    video_url
                ]
            else:
                cmd_resolve = [
                    self.ytdlp_path,
                    '-f', 'best[ext=mp4]/best',  # Prefer mp4 format with audio+video
                    '-g',
                    video_url
                ]
            
            result_resolve = subprocess.run(cmd_resolve, capture_output=True, text=True, encoding='utf-8', timeout=30)
            
            if result_resolve.returncode != 0:
                print(f"❌ Failed to resolve stream with return code {result_resolve.returncode}")
                print(f"   Error: {result_resolve.stderr[:500]}")
                return None, None
                
            stream_url = result_resolve.stdout.strip()
            
            # Take the first URL (should be a combined stream now)
            stream_url = stream_url.split('\n')[0]
            
            print(f"✓ Successfully resolved stream URL (length: {len(stream_url)} chars)")
            return stream_url, title

        except subprocess.TimeoutExpired:
            print("❌ yt-dlp command timed out after 30 seconds")
            return None, None
        except Exception as e:
            print(f"❌ Error fetching YouTube video: {type(e).__name__}: {str(e)}")
            return None, None
