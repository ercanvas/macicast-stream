# Logo & Banner Overlay System - Usage Guide

## Overview

The TV Playout system now supports logo watermark and banner overlays that appear on top of the stream at all times.

## Features

- **Logo Watermark**: Positioned at top-left corner (10px padding)
- **Banner**: Positioned at bottom of screen (10px padding)
- **Automatic Resizing & Cropping**: Images are automatically resized to fit target dimensions
  - Logo: 10% of screen size (128x72px for HD)
  - Banner: Full width (1280x150px)
- **Automatic Conversion**: JPG images are automatically converted to PNG with transparency support
- **Validation**: File size and format validation
- **Dynamic Control**: Enable/disable overlays without restarting stream

## Image Requirements

### Logo Watermark
- **Target Size**: 10% of screen (e.g., 128x72px for 720p)
- **Automatic Handling**: Larger images will be automatically resized/cropped to fit
- **Maximum File Size**: 5MB
- **Formats**: PNG, JPG, JPEG
- **Best Practice**: Use PNG with transparent background

### Banner
- **Target Size**: 1280x150 pixels
- **Automatic Handling**: Larger images will be automatically resized/cropped to fit
- **Maximum File Size**: 10MB
- **Formats**: PNG, JPG, JPEG
- **Best Practice**: Use PNG with transparent background

## API Endpoints

### Upload Logo
```bash
curl -F "file=@logo.png" http://localhost:5000/upload_logo
```

**Response:**
```json
{
  "success": true,
  "message": "Logo uploaded successfully",
  "info": {
    "width": 200,
    "height": 100,
    "format": "PNG",
    "size_mb": 0.15,
    "recommended_width": 200,
    "recommended_height": 100
  }
}
```

### Upload Banner
```bash
curl -F "file=@banner.png" http://localhost:5000/upload_banner
```

**Response:**
```json
{
  "success": true,
  "message": "Banner uploaded successfully",
  "info": {
    "width": 1280,
    "height": 150,
    "format": "PNG",
    "size_mb": 0.45,
    "recommended_width": 1280,
    "recommended_height": 150
  }
}
```

### Get Overlay Status
```bash
curl http://localhost:5000/overlay_status
```

**Response:**
```json
{
  "overlay_enabled": true,
  "logo": {
    "exists": true,
    "width": 200,
    "height": 100,
    "size_mb": 0.15,
    "enabled": true
  },
  "banner": {
    "exists": true,
    "width": 1280,
    "height": 150,
    "size_mb": 0.45,
    "enabled": true
  },
  "recommendations": {
    "logo": {
      "width": 200,
      "height": 100,
      "max_size_mb": 5,
      "formats": ["png", "jpg", "jpeg"]
    },
    "banner": {
      "width": 1280,
      "height": 150,
      "max_size_mb": 10,
      "formats": ["png", "jpg", "jpeg"]
    }
  }
}
```

### Delete Logo
```bash
curl -X POST http://localhost:5000/delete_logo
```

### Delete Banner
```bash
curl -X POST http://localhost:5000/delete_banner
```

### Toggle Overlays
```bash
# Disable logo
curl -X POST http://localhost:5000/toggle_overlay \
  -H "Content-Type: application/json" \
  -d '{"type": "logo", "enabled": false}'

# Disable banner
curl -X POST http://localhost:5000/toggle_overlay \
  -H "Content-Type: application/json" \
  -d '{"type": "banner", "enabled": false}'

# Disable all overlays
curl -X POST http://localhost:5000/toggle_overlay \
  -H "Content-Type: application/json" \
  -d '{"type": "all", "enabled": false}'
```

## How It Works

### FFmpeg Integration

The overlay system uses FFmpeg's `filter_complex` to composite images over the video stream:

**With Both Logo and Banner:**
```bash
-filter_complex "[0:v][1:v]overlay=10:10[tmp];[tmp][2:v]overlay=0:H-h-10[out]" -map "[out]" -map "0:a"
```

**With Logo Only:**
```bash
-filter_complex "[0:v][1:v]overlay=10:10[out]" -map "[out]" -map "0:a"
```

**With Banner Only:**
```bash
-filter_complex "[0:v][1:v]overlay=0:H-h-10[out]" -map "[out]" -map "0:a"
```

### Overlay Inputs

- `[0:v]` - Main video stream (queue video, idle, or live camera)
- `[1:v]` - Logo image (if enabled)
- `[2:v]` - Banner image (if enabled and logo also enabled)

### Positioning

- **Logo**: `overlay=10:10` (10px from top-left)
- **Banner**: `overlay=0:H-h-10` (centered horizontally, 10px from bottom)
  - `H` = output height
  - `h` = banner height

## Usage Workflow

### 1. Prepare Your Images

Create or obtain:
- Logo image (PNG recommended, ~200x100px)
- Banner image (PNG recommended, ~1280x150px)

**Tip**: Use transparent backgrounds for professional look.

### 2. Upload Images

Using curl:
```bash
curl -F "file=@my_logo.png" http://localhost:5000/upload_logo
curl -F "file=@my_banner.png" http://localhost:5000/upload_banner
```

Or using Python:
```python
import requests

# Upload logo
with open('my_logo.png', 'rb') as f:
    response = requests.post('http://localhost:5000/upload_logo', files={'file': f})
    print(response.json())

# Upload banner
with open('my_banner.png', 'rb') as f:
    response = requests.post('http://localhost:5000/upload_banner', files={'file': f})
    print(response.json())
```

### 3. Start/Restart Broadcast

The overlays will automatically appear on the stream when you start broadcasting:

```bash
curl -X POST http://localhost:5000/start_broadcast
```

**Important**: If broadcast is already running, you need to restart it for new overlays to appear:
```bash
curl -X POST http://localhost:5000/stop_broadcast
# Wait 2 seconds
curl -X POST http://localhost:5000/start_broadcast
```

### 4. Verify Overlays

Check the video player - you should see:
- Logo in top-left corner
- Banner at bottom of screen

### 5. Manage Overlays

Toggle overlays on/off:
```bash
# Temporarily disable logo
curl -X POST http://localhost:5000/toggle_overlay \
  -H "Content-Type: application/json" \
  -d '{"type": "logo", "enabled": false}'
```

Delete and replace:
```bash
# Delete old logo
curl -X POST http://localhost:5000/delete_logo

# Upload new logo
curl -F "file=@new_logo.png" http://localhost:5000/upload_logo

# Restart broadcast to apply
curl -X POST http://localhost:5000/stop_broadcast
curl -X POST http://localhost:5000/start_broadcast
```

## Configuration

Edit `config.py` to customize overlay settings:

```python
# Overlay Positions
LOGO_POSITION_X = 10  # pixels from left
LOGO_POSITION_Y = 10  # pixels from top

BANNER_POSITION_X = 0  # pixels from left (0 = centered)
BANNER_POSITION_Y_OFFSET = 10  # pixels from bottom

# Overlay Settings
OVERLAY_ENABLED = True  # Master switch
LOGO_ENABLED = True
BANNER_ENABLED = True

# Size Limits
MAX_LOGO_SIZE_MB = 5
MAX_BANNER_SIZE_MB = 10
```

## Performance Impact

- **CPU Usage**: +5-10% (overlay rendering)
- **Memory**: +10-20MB (image loading)
- **Encoding Speed**: Minimal impact with optimized settings

## Troubleshooting

### Overlays Not Appearing

1. **Check overlay status**:
   ```bash
   curl http://localhost:5000/overlay_status
   ```
   Verify `exists: true` and `enabled: true`

2. **Restart broadcast**:
   ```bash
   curl -X POST http://localhost:5000/stop_broadcast
   curl -X POST http://localhost:5000/start_broadcast
   ```

3. **Check FFmpeg logs**:
   Look for overlay filter in console output

### Image Quality Issues

- Use PNG format for best quality
- Ensure image dimensions match recommendations
- Use transparent backgrounds for clean overlay

### File Upload Errors

- Check file size (logo <5MB, banner <10MB)
- Verify file format (PNG, JPG, JPEG only)
- Ensure file is not corrupted

## Example Images

### Creating Logo with Transparency (ImageMagick)
```bash
convert -size 200x100 xc:none \
  -fill white -font Arial -pointsize 40 \
  -gravity center -annotate +0+0 "MY TV" \
  logo.png
```

### Creating Banner with Gradient (ImageMagick)
```bash
convert -size 1280x150 gradient:blue-black \
  -fill white -font Arial -pointsize 30 \
  -gravity center -annotate +0+0 "Breaking News: Live Coverage" \
  banner.png
```

## Files Created

- `overlays/logo.png` - Current logo image
- `overlays/banner.png` - Current banner image

These files persist across restarts and can be manually replaced if needed.
