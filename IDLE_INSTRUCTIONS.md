# Idle Stream Instructions

To ensure the "Idle Mode" works perfectly (looping indefinitely without gaps), you should provide a custom video file.

## 1. Create or Download `idle.mp4`

You need a video file named `idle.mp4` in the root directory of the project (`c:\Users\unall\sinlive\`).

### Option A: Generate one using FFmpeg (Recommended)
Open a terminal in the project folder and run this command to create a 10-second looping test pattern:

```powershell
ffmpeg -f lavfi -i testsrc=duration=10:size=1280x720:rate=30 -f lavfi -i sine=frequency=1000:duration=10 -c:v libx264 -c:a aac -b:a 128k idle.mp4
```

### Option B: Use your own video
1.  Find any `.mp4` video you want to loop (e.g., a "Stream Starting Soon" animation or a station logo).
2.  Rename it to `idle.mp4`.
3.  Place it in `c:\Users\unall\sinlive\`.

## 2. How it works
*   When the **Queue is empty** and **Broadcast is ON**, the system looks for `idle.mp4`.
*   If found, it plays it in an infinite loop (`-stream_loop -1`).
*   If NOT found, the system falls back to a generated SMPTE color bar pattern.
