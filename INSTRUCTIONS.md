# TV Playout Automation (PoC)

This is a Proof of Concept web application for a TV Playout system using Python (Flask) and FFmpeg.

## Prerequisites

1.  **Python 3.x**: Ensure Python is installed.
2.  **FFmpeg**: This is critical.
    *   **Download**: Go to [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) (Windows) or your OS package manager.
    *   **Install**: Extract the downloaded archive.
    *   **PATH**: Add the `bin` folder (where `ffmpeg.exe` is located) to your System Environment Variables (PATH).
    *   **Verify**: Open a new terminal and run `ffmpeg -version`. If it fails, the app will not work.

## Installation

1.  Open a terminal in this directory.
2.  Install Python dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

1.  Start the Flask server:
    ```bash
    python app.py
    ```
2.  Open your browser and navigate to:
    ```
    http://localhost:5000
    ```

## Usage

1.  **Dashboard**: You will see the "TV Playout Dashboard".
2.  **Idle State**: Initially, if the queue is empty, the player will show "SMPTE Color Bars" (Idle Stream).
3.  **Upload**: Use the form to upload `.mp4` video files. They will be added to the queue.
4.  **Auto-Play**: The system will automatically play videos from the queue sequentially.
5.  **Go Live**: Click the "GO LIVE" button.
    *   This stops the current video and switches to the "Live Source".
    *   **Default Live Source**: A test pattern (Visual Clock).
    *   **Real Webcam**: To use a real webcam, edit `app.py` (search for `LIVE MODE`) and uncomment the `dshow` command, replacing "Integrated Camera" with your webcam's name.

## Notes

*   **Latency**: HLS has inherent latency (usually 10-20 seconds).
*   **Continuity**: The system uses `append_list` to try and keep the stream continuous, but player glitches may occur when switching sources due to timestamp discontinuities.
*   **Files**: Uploaded videos are stored in the `videos/` folder.
*   **Stream**: The HLS stream is generated in `static/hls/`.
