"""
Trash Bin Manager Module
Handles automatic cleanup of old HLS segments
"""

import os
import time
import threading
import shutil
from typing import List, Dict, Any
from datetime import datetime
import config


class TrashBinManager:
    """
    Manages segment lifecycle: active -> trash -> deleted
    Automatically moves old segments to trash and permanently deletes after retention period
    """
    
    def __init__(self, hls_dir: str, trash_dir: str, segment_tracker):
        self._hls_dir = hls_dir
        self._trash_dir = trash_dir
        self._segment_tracker = segment_tracker
        self._lock = threading.RLock()
        
        # Ensure trash directory exists
        os.makedirs(self._trash_dir, exist_ok=True)
        
        # Track when segments were moved to trash
        self._trash_timestamps = {}  # filename -> timestamp
        
        # Start cleanup thread
        self._stop_event = threading.Event()
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()
    
    def get_active_segments(self) -> List[str]:
        """Get list of active segment files in HLS directory"""
        try:
            files = [
                f for f in os.listdir(self._hls_dir)
                if f.endswith('.ts') and os.path.isfile(os.path.join(self._hls_dir, f))
            ]
            # Sort by modification time (oldest first)
            files.sort(key=lambda f: os.path.getmtime(os.path.join(self._hls_dir, f)))
            return files
        except Exception as e:
            print(f"Error getting active segments: {e}")
            return []
    
    def get_trash_segments(self) -> List[str]:
        """Get list of segments in trash directory"""
        try:
            if not os.path.exists(self._trash_dir):
                return []
            return [
                f for f in os.listdir(self._trash_dir)
                if f.endswith('.ts')
            ]
        except Exception as e:
            print(f"Error getting trash segments: {e}")
            return []
    
    def move_to_trash(self, segment_name: str) -> bool:
        """Move a segment from active directory to trash"""
        with self._lock:
            source_path = os.path.join(self._hls_dir, segment_name)
            dest_path = os.path.join(self._trash_dir, segment_name)
            
            try:
                if os.path.exists(source_path):
                    shutil.move(source_path, dest_path)
                    self._trash_timestamps[segment_name] = time.time()
                    
                    # Update segment tracker
                    self._segment_tracker.update_segment_status(segment_name, 'archived')
                    
                    print(f"Moved to trash: {segment_name}")
                    return True
            except Exception as e:
                print(f"Error moving {segment_name} to trash: {e}")
            
            return False
    
    def delete_permanently(self, segment_name: str) -> bool:
        """Permanently delete a segment from trash"""
        with self._lock:
            trash_path = os.path.join(self._trash_dir, segment_name)
            
            try:
                if os.path.exists(trash_path):
                    os.remove(trash_path)
                    
                    # Remove from trash timestamps
                    if segment_name in self._trash_timestamps:
                        del self._trash_timestamps[segment_name]
                    
                    # Update segment tracker
                    self._segment_tracker.update_segment_status(segment_name, 'deleted')
                    
                    print(f"Permanently deleted: {segment_name}")
                    return True
            except Exception as e:
                print(f"Error deleting {segment_name}: {e}")
            
            return False
    
    def cleanup_old_segments(self):
        """Move old active segments to trash if exceeding MAX_ACTIVE_SEGMENTS"""
        with self._lock:
            active_segments = self.get_active_segments()
            
            if len(active_segments) > config.MAX_ACTIVE_SEGMENTS:
                # Move oldest segments to trash
                segments_to_move = active_segments[:len(active_segments) - config.MAX_ACTIVE_SEGMENTS]
                
                for segment in segments_to_move:
                    self.move_to_trash(segment)
                
                if segments_to_move:
                    print(f"Moved {len(segments_to_move)} old segments to trash")
    
    def cleanup_trash(self):
        """Permanently delete segments from trash that exceeded retention time"""
        with self._lock:
            current_time = time.time()
            segments_to_delete = []
            
            for segment_name, trash_time in list(self._trash_timestamps.items()):
                if current_time - trash_time > config.TRASH_RETENTION_TIME:
                    segments_to_delete.append(segment_name)
            
            for segment in segments_to_delete:
                self.delete_permanently(segment)
            
            if segments_to_delete:
                print(f"Permanently deleted {len(segments_to_delete)} segments from trash")
                
                # Cleanup metadata for deleted segments
                self._segment_tracker.cleanup_deleted_segments()
    
    def _cleanup_loop(self):
        """Background thread for periodic cleanup"""
        while not self._stop_event.is_set():
            try:
                # Cleanup old active segments
                self.cleanup_old_segments()
                
                # Cleanup trash
                self.cleanup_trash()
                
            except Exception as e:
                print(f"Error in cleanup loop: {e}")
            
            # Wait before next cleanup check
            self._stop_event.wait(config.CLEANUP_CHECK_INTERVAL)
    
    def stop(self):
        """Stop the cleanup thread"""
        self._stop_event.set()
        if self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=2)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get trash bin statistics"""
        with self._lock:
            active_segments = self.get_active_segments()
            trash_segments = self.get_trash_segments()
            
            # Calculate trash size
            trash_size_bytes = 0
            for segment in trash_segments:
                try:
                    trash_path = os.path.join(self._trash_dir, segment)
                    trash_size_bytes += os.path.getsize(trash_path)
                except:
                    pass
            
            trash_size_mb = trash_size_bytes / (1024 * 1024)
            
            return {
                'active_segments': len(active_segments),
                'trash_segments': len(trash_segments),
                'trash_size_mb': round(trash_size_mb, 2),
                'max_active_segments': config.MAX_ACTIVE_SEGMENTS,
                'retention_time_hours': config.TRASH_RETENTION_TIME / 3600
            }
    
    def force_cleanup_all(self):
        """Force cleanup of all segments (for testing or manual cleanup)"""
        with self._lock:
            # Move all active segments to trash
            active_segments = self.get_active_segments()
            for segment in active_segments:
                self.move_to_trash(segment)
            
            # Delete all trash segments
            trash_segments = self.get_trash_segments()
            for segment in trash_segments:
                self.delete_permanently(segment)
            
            print(f"Force cleanup: moved {len(active_segments)} to trash, deleted {len(trash_segments)}")
