"""
State Management Module
Provides thread-safe state management for the TV Playout system
"""

import threading
import json
import os
import time
from datetime import datetime
from typing import Optional, Dict, List, Any
import config


class StateManager:
    """
    Centralized, thread-safe state management for the application
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        
        # Broadcast state
        self._is_broadcasting = False
        self._is_live_camera_mode = False
        
        # Playlist queue
        self._playlist_queue = []
        
        # Current playback info
        self._current_source_type = None  # 'QUEUE', 'IDLE', 'LIVE', None
        self._current_playing_file = None
        self._current_video_start_time = None  # When current video started playing
        self._current_video_duration = None  # Duration of current video
        
        # Process management
        self._current_process = None
        
        # Statistics
        self._total_videos_played = 0
        self._total_segments_created = 0
        self._stream_start_time = None
        
        # Program Name
        self._program_name = ""
        
        # Auto Mode
        self._auto_mode_enabled = config.AUTO_MODE_ENABLED
        self._current_hashtag = config.TIKTOK_HASHTAGS[0] if config.TIKTOK_HASHTAGS else "trending"


    def set_program_name(self, name: str):
        with self._lock:
            self._program_name = name
            
    def get_program_name(self) -> str:
        with self._lock:
            return self._program_name

    # --- Auto Mode State ---

    def set_auto_mode(self, enabled: bool):
        with self._lock:
            self._auto_mode_enabled = enabled
            
    def is_auto_mode(self) -> bool:
        with self._lock:
            return self._auto_mode_enabled
            
    def set_current_hashtag(self, hashtag: str):
        with self._lock:
            self._current_hashtag = hashtag
            
    def get_current_hashtag(self) -> str:
        with self._lock:
            return self._current_hashtag

    
    # --- Broadcasting State ---
    
    def set_broadcasting(self, is_broadcasting: bool):
        with self._lock:
            self._is_broadcasting = is_broadcasting
            if is_broadcasting and self._stream_start_time is None:
                self._stream_start_time = time.time()
    
    def is_broadcasting(self) -> bool:
        with self._lock:
            return self._is_broadcasting
    
    def set_live_camera_mode(self, is_live: bool):
        with self._lock:
            self._is_live_camera_mode = is_live
    
    def is_live_camera_mode(self) -> bool:
        with self._lock:
            return self._is_live_camera_mode
    
    # --- Playlist Queue ---
    
    def add_to_queue(self, filename: str):
        with self._lock:
            self._playlist_queue.append(filename)
    
    def pop_from_queue(self) -> Optional[str]:
        with self._lock:
            if len(self._playlist_queue) > 0:
                return self._playlist_queue.pop(0)
            return None
    
    def get_queue(self) -> List[str]:
        with self._lock:
            return self._playlist_queue.copy()
    
    def queue_length(self) -> int:
        with self._lock:
            return len(self._playlist_queue)
    
    # --- Current Playback ---
    
    def set_current_playback(self, source_type: str, playing_file: str, duration: float = None):
        with self._lock:
            self._current_source_type = source_type
            self._current_playing_file = playing_file
            self._current_video_start_time = time.time()
            self._current_video_duration = duration
            
            if source_type == 'QUEUE':
                self._total_videos_played += 1
    
    def clear_current_playback(self):
        with self._lock:
            self._current_source_type = None
            self._current_playing_file = None
            self._current_video_start_time = None
            self._current_video_duration = None
    
    def get_current_playback(self) -> Dict[str, Any]:
        with self._lock:
            elapsed_time = 0
            if self._current_video_start_time:
                elapsed_time = time.time() - self._current_video_start_time
            
            return {
                'source_type': self._current_source_type,
                'playing_file': self._current_playing_file,
                'elapsed_time': elapsed_time,
                'duration': self._current_video_duration,
                'start_time': self._current_video_start_time
            }
    
    def get_current_timestamp(self) -> float:
        """Get current timestamp in the playing video"""
        with self._lock:
            if self._current_video_start_time:
                return time.time() - self._current_video_start_time
            return 0.0
    
    # --- Process Management ---
    
    def set_current_process(self, process):
        with self._lock:
            self._current_process = process
    
    def get_current_process(self):
        with self._lock:
            return self._current_process
    
    def clear_current_process(self):
        with self._lock:
            self._current_process = None
    
    # --- Statistics ---
    
    def increment_segment_count(self):
        with self._lock:
            self._total_segments_created += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        with self._lock:
            uptime = 0
            if self._stream_start_time:
                uptime = time.time() - self._stream_start_time
            
            return {
                'total_videos_played': self._total_videos_played,
                'total_segments_created': self._total_segments_created,
                'queue_length': len(self._playlist_queue)
            }
    
    # --- Full State Export ---
    
    def get_full_state(self) -> Dict[str, Any]:
        """Get complete state for API responses"""
        with self._lock:
            playback = self.get_current_playback()
            stats = self.get_statistics()
            
            return {
                'is_broadcasting': self._is_broadcasting,
                'is_live_camera_mode': self._is_live_camera_mode,
                'queue': self._playlist_queue.copy(),
                'current_playback': playback,
                'statistics': stats,
                'statistics': stats,
                'program_name': self._program_name,
                'auto_mode_enabled': self._auto_mode_enabled,
                'current_hashtag': self._current_hashtag
            }


class SegmentTracker:
    """
    Tracks HLS segments and their metadata
    Maps segments to source videos and timestamps
    """
    
    def __init__(self, metadata_file: str):
        self._lock = threading.RLock()
        self._metadata_file = metadata_file
        self._segments = {}  # segment_name -> metadata
        self._load_metadata()
    
    def _load_metadata(self):
        """Load existing metadata from file"""
        if os.path.exists(self._metadata_file):
            try:
                with open(self._metadata_file, 'r', encoding='utf-8') as f:
                    self._segments = json.load(f)
            except Exception as e:
                print(f"Error loading segment metadata: {e}")
                self._segments = {}
    
    def _save_metadata(self):
        """Save metadata to file"""
        try:
            with open(self._metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self._segments, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving segment metadata: {e}")
    
    def add_segment(self, segment_name: str, source_video: str, source_type: str, 
                   start_time: float, duration: float):
        """Add a new segment with metadata"""
        with self._lock:
            self._segments[segment_name] = {
                'source_video': source_video,
                'source_type': source_type,
                'start_time': start_time,
                'duration': duration,
                'created_at': datetime.now().isoformat(),
                'status': 'active'
            }
            self._save_metadata()
            
            if config.DEBUG_SEGMENT_TRACKING:
                print(f"Tracked segment: {segment_name} from {source_video} at {start_time:.2f}s")
    
    def update_segment_status(self, segment_name: str, status: str):
        """Update segment status (active, archived, deleted)"""
        with self._lock:
            if segment_name in self._segments:
                self._segments[segment_name]['status'] = status
                self._save_metadata()
    
    def get_segment_info(self, segment_name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific segment"""
        with self._lock:
            return self._segments.get(segment_name)
    
    def get_current_segment(self) -> Optional[Dict[str, Any]]:
        """Get the most recently created active segment"""
        with self._lock:
            active_segments = [
                (name, meta) for name, meta in self._segments.items()
                if meta['status'] == 'active'
            ]
            
            if active_segments:
                # Sort by creation time and get the latest
                active_segments.sort(key=lambda x: x[1]['created_at'], reverse=True)
                name, meta = active_segments[0]
                return {'segment_name': name, **meta}
            
            return None
    
    def get_segment_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent segment history"""
        with self._lock:
            segments = [
                {'segment_name': name, **meta}
                for name, meta in self._segments.items()
            ]
            
            # Sort by creation time (newest first)
            segments.sort(key=lambda x: x['created_at'], reverse=True)
            
            return segments[:limit]
    
    def cleanup_deleted_segments(self):
        """Remove metadata for deleted segments"""
        with self._lock:
            deleted = [
                name for name, meta in self._segments.items()
                if meta['status'] == 'deleted'
            ]
            
            for name in deleted:
                del self._segments[name]
            
            if deleted:
                self._save_metadata()
                print(f"Cleaned up metadata for {len(deleted)} deleted segments")
    
    def get_stats(self) -> Dict[str, int]:
        """Get segment statistics"""
        with self._lock:
            stats = {
                'total': len(self._segments),
                'active': 0,
                'archived': 0,
                'deleted': 0
            }
            
            for meta in self._segments.values():
                status = meta.get('status', 'active')
                if status in stats:
                    stats[status] += 1
            
            return stats
