"""
Overlay Manager Module
Handles logo watermark and banner overlays for HLS stream
"""

import os
import shutil
from typing import Optional, Dict, Any, Tuple
from PIL import Image, ImageOps
import config


class OverlayManager:
    """
    Manages overlay images (logo and banner) for the stream
    Handles upload, validation, resizing, and FFmpeg filter generation
    """
    
    def __init__(self):
        # Ensure overlays directory exists
        os.makedirs(config.OVERLAYS_DIR, exist_ok=True)
        
        # Track overlay status
        self._logo_exists = os.path.exists(config.LOGO_PATH)
        self._banner_exists = os.path.exists(config.BANNER_PATH)
    
    def validate_image(self, file_path: str, max_size_mb: int) -> Tuple[bool, str]:
        """
        Validate uploaded image file
        Returns: (is_valid, error_message)
        """
        try:
            # Check file exists
            if not os.path.exists(file_path):
                return False, "File does not exist"
            
            # Check file size
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if file_size_mb > max_size_mb:
                return False, f"File too large ({file_size_mb:.1f}MB). Max: {max_size_mb}MB"
            
            # Check if valid image
            try:
                img = Image.open(file_path)
                img.verify()
            except Exception as e:
                return False, f"Invalid image file: {str(e)}"
            
            # Check format
            file_ext = os.path.splitext(file_path)[1].lower().replace('.', '')
            if file_ext not in config.ALLOWED_OVERLAY_EXTENSIONS:
                return False, f"Invalid format. Allowed: {', '.join(config.ALLOWED_OVERLAY_EXTENSIONS)}"
            
            return True, "Valid"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def save_logo(self, source_path: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Save uploaded logo image with automatic resizing/cropping
        Target: 10% of screen width/height
        Returns: (success, message, image_info)
        """
        # Validate
        is_valid, error_msg = self.validate_image(source_path, config.MAX_LOGO_SIZE_MB)
        if not is_valid:
            return False, error_msg, None
        
        try:
            # Calculate target dimensions (10% of screen)
            target_width = int(config.STREAM_WIDTH * 0.10)
            target_height = int(config.STREAM_HEIGHT * 0.10)
            
            # Process image
            img = Image.open(source_path)
            
            # Convert to RGBA for transparency
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Resize and crop to fit exactly 10% box
            # ImageOps.fit resizes and crops to center
            img = ImageOps.fit(img, (target_width, target_height), method=Image.Resampling.LANCZOS)
            
            # Save
            img.save(config.LOGO_PATH, 'PNG')
            
            self._logo_exists = True
            
            image_info = {
                'width': target_width,
                'height': target_height,
                'format': 'PNG',
                'size_mb': os.path.getsize(config.LOGO_PATH) / (1024 * 1024),
                'recommended_width': target_width,
                'recommended_height': target_height
            }
            
            return True, "Logo uploaded and resized successfully", image_info
            
        except Exception as e:
            return False, f"Error saving logo: {str(e)}", None
    
    def save_banner(self, source_path: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Save uploaded banner image with automatic resizing/cropping
        Target: Full width, recommended height
        Returns: (success, message, image_info)
        """
        # Validate
        is_valid, error_msg = self.validate_image(source_path, config.MAX_BANNER_SIZE_MB)
        if not is_valid:
            return False, error_msg, None
        
        try:
            # Calculate target dimensions
            target_width = config.STREAM_WIDTH
            target_height = config.BANNER_RECOMMENDED_HEIGHT
            
            # Process image
            img = Image.open(source_path)
            
            # Convert to RGBA
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Resize and crop
            img = ImageOps.fit(img, (target_width, target_height), method=Image.Resampling.LANCZOS)
            
            # Save
            img.save(config.BANNER_PATH, 'PNG')
            
            self._banner_exists = True
            
            image_info = {
                'width': target_width,
                'height': target_height,
                'format': 'PNG',
                'size_mb': os.path.getsize(config.BANNER_PATH) / (1024 * 1024),
                'recommended_width': target_width,
                'recommended_height': target_height
            }
            
            return True, "Banner uploaded and resized successfully", image_info
            
        except Exception as e:
            return False, f"Error saving banner: {str(e)}", None
    
    def delete_logo(self) -> bool:
        """Delete logo file"""
        try:
            if os.path.exists(config.LOGO_PATH):
                os.remove(config.LOGO_PATH)
            self._logo_exists = False
            return True
        except Exception as e:
            print(f"Error deleting logo: {e}")
            return False
    
    def delete_banner(self) -> bool:
        """Delete banner file"""
        try:
            if os.path.exists(config.BANNER_PATH):
                os.remove(config.BANNER_PATH)
            self._banner_exists = False
            return True
        except Exception as e:
            print(f"Error deleting banner: {e}")
            return False
    
    def get_ffmpeg_overlay_filter(self) -> Optional[str]:
        """
        Generate FFmpeg filter_complex for overlays
        Returns None if no overlays are enabled/available
        """
        if not config.OVERLAY_ENABLED:
            return None
        
        # Check which overlays are available and enabled
        logo_ready = config.LOGO_ENABLED and os.path.exists(config.LOGO_PATH)
        banner_ready = config.BANNER_ENABLED and os.path.exists(config.BANNER_PATH)
        
        if not logo_ready and not banner_ready:
            return None
        
        # Build filter complex
        # Input [0:v] is the main video stream
        # Input [1:v] is logo (if exists)
        # Input [2:v] is banner (if exists)
        
        if logo_ready and banner_ready:
            # Both logo and banner
            filter_complex = (
                f"[0:v][1:v]overlay={config.LOGO_POSITION_X}:{config.LOGO_POSITION_Y}[tmp];"
                f"[tmp][2:v]overlay={config.BANNER_POSITION_X}:H-h-{config.BANNER_POSITION_Y_OFFSET}[out]"
            )
            return filter_complex
        elif logo_ready:
            # Only logo
            filter_complex = (
                f"[0:v][1:v]overlay={config.LOGO_POSITION_X}:{config.LOGO_POSITION_Y}[out]"
            )
            return filter_complex
        elif banner_ready:
            # Only banner
            filter_complex = (
                f"[0:v][1:v]overlay={config.BANNER_POSITION_X}:H-h-{config.BANNER_POSITION_Y_OFFSET}[out]"
            )
            return filter_complex
        
        return None
    
    def get_overlay_inputs(self) -> list:
        """
        Get list of overlay input files for FFmpeg
        Returns list of file paths in order: [logo, banner]
        """
        inputs = []
        
        if config.LOGO_ENABLED and os.path.exists(config.LOGO_PATH):
            inputs.append(config.LOGO_PATH)
        
        if config.BANNER_ENABLED and os.path.exists(config.BANNER_PATH):
            inputs.append(config.BANNER_PATH)
        
        return inputs
    
    def get_status(self) -> Dict[str, Any]:
        """Get current overlay status"""
        logo_info = None
        banner_info = None
        
        # Get logo info
        if os.path.exists(config.LOGO_PATH):
            try:
                img = Image.open(config.LOGO_PATH)
                logo_info = {
                    'exists': True,
                    'width': img.size[0],
                    'height': img.size[1],
                    'size_mb': round(os.path.getsize(config.LOGO_PATH) / (1024 * 1024), 2),
                    'enabled': config.LOGO_ENABLED
                }
            except:
                logo_info = {'exists': False, 'enabled': config.LOGO_ENABLED}
        else:
            logo_info = {'exists': False, 'enabled': config.LOGO_ENABLED}
        
        # Get banner info
        if os.path.exists(config.BANNER_PATH):
            try:
                img = Image.open(config.BANNER_PATH)
                banner_info = {
                    'exists': True,
                    'width': img.size[0],
                    'height': img.size[1],
                    'size_mb': round(os.path.getsize(config.BANNER_PATH) / (1024 * 1024), 2),
                    'enabled': config.BANNER_ENABLED
                }
            except:
                banner_info = {'exists': False, 'enabled': config.BANNER_ENABLED}
        else:
            banner_info = {'exists': False, 'enabled': config.BANNER_ENABLED}
        
        return {
            'overlay_enabled': config.OVERLAY_ENABLED,
            'logo': logo_info,
            'banner': banner_info,
            'recommendations': {
                'logo': {
                    'width': config.LOGO_RECOMMENDED_WIDTH,
                    'height': config.LOGO_RECOMMENDED_HEIGHT,
                    'max_size_mb': config.MAX_LOGO_SIZE_MB,
                    'formats': list(config.ALLOWED_OVERLAY_EXTENSIONS)
                },
                'banner': {
                    'width': config.BANNER_RECOMMENDED_WIDTH,
                    'height': config.BANNER_RECOMMENDED_HEIGHT,
                    'max_size_mb': config.MAX_BANNER_SIZE_MB,
                    'formats': list(config.ALLOWED_OVERLAY_EXTENSIONS)
                }
            }
        }
