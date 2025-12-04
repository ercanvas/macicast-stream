"""Quick test to verify YouTube search works"""
from content_provider import ContentProvider

provider = ContentProvider()
print(f"Detected yt-dlp path: {provider.ytdlp_path}")

# Test YouTube search
print("\n--- Testing YouTube search ---")
url, title = provider.get_random_video("funny")

if url and title:
    print(f"✅ Success!")
    print(f"Title: {title}")
    print(f"URL: {url[:100]}...")  # Print first 100 chars
else:
    print("❌ Failed to fetch video")
