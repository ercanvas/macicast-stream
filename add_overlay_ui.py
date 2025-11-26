"""
Script to add overlay controls to index.html
Run this to properly insert the overlay UI
"""

# Read the original file
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# HTML to insert (overlay controls section)
overlay_html = '''
                <!-- Overlay Controls -->
                <div class="control-section">
                    <div class="section-title">🎨 Logo & Banner Overlays</div>
                    
                    <!-- Logo Upload -->
                    <div style="margin-bottom: 15px;">
                        <div style="font-size: 12px; font-weight: 600; margin-bottom: 8px; color: #a0a0a0;">
                            📍 LOGO (Top-Left)
                        </div>
                        <div style="font-size: 11px; color: #6c757d; margin-bottom: 8px;">
                            Recommended: 200x100px | Max: 5MB | PNG/JPG
                        </div>
                        <form id="logo-upload-form" style="display: flex; gap: 8px; margin-bottom: 8px;">
                            <input type="file" id="logoInput" accept=".png,.jpg,.jpeg" 
                                   style="flex: 1; font-size: 11px; padding: 8px; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; color: #fff;">
                            <button type="submit" class="upload-btn" style="padding: 8px 16px; font-size: 11px; width: auto;">UPLOAD</button>
                        </form>
                        <div id="logo-status" style="font-size: 11px; margin-top: 5px;"></div>
                    </div>

                    <!-- Banner Upload -->
                    <div style="margin-bottom: 15px;">
                        <div style="font-size: 12px; font-weight: 600; margin-bottom: 8px; color: #a0a0a0;">
                            📊 BANNER (Bottom)
                        </div>
                        <div style="font-size: 11px; color: #6c757d; margin-bottom: 8px;">
                            Recommended: 1280x150px | Max: 10MB | PNG/JPG
                        </div>
                        <form id="banner-upload-form" style="display: flex; gap: 8px; margin-bottom: 8px;">
                            <input type="file" id="bannerInput" accept=".png,.jpg,.jpeg" 
                                   style="flex: 1; font-size: 11px; padding: 8px; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; color: #fff;">
                            <button type="submit" class="upload-btn" style="padding: 8px 16px; font-size: 11px; width: auto;">UPLOAD</button>
                        </form>
                        <div id="banner-status" style="font-size: 11px; margin-top: 5px;"></div>
                    </div>

                    <!-- Overlay Status -->
                    <div id="overlay-info" style="background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 10px; font-size: 11px;">
                        <div style="color: #a0a0a0;">Loading overlay status...</div>
                    </div>
                </div>

'''

# JavaScript to insert (overlay upload handlers)
overlay_js = '''
        // Overlay Upload Handling
        document.getElementById('logo-upload-form').addEventListener('submit', function (e) {
            e.preventDefault();
            const fileInput = document.getElementById('logoInput');
            const file = fileInput.files[0];
            if (!file) return;
            
            const formData = new FormData();
            formData.append('file', file);
            const statusDiv = document.getElementById('logo-status');
            
            statusDiv.textContent = "Uploading logo...";
            statusDiv.style.color = "#ffc107";
            
            fetch('/upload_logo', { method: 'POST', body: formData })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        statusDiv.textContent = `✓ ${data.message} (${data.info.width}x${data.info.height})`;
                        statusDiv.style.color = "#28a745";
                        fileInput.value = '';
                        updateOverlayStatus();
                        setTimeout(() => statusDiv.textContent = '', 5000);
                    } else {
                        statusDiv.textContent = `✗ ${data.error}`;
                        statusDiv.style.color = "#dc3545";
                    }
                })
                .catch(err => {
                    statusDiv.textContent = "✗ Upload Failed";
                    statusDiv.style.color = "#dc3545";
                });
        });

        document.getElementById('banner-upload-form').addEventListener('submit', function (e) {
            e.preventDefault();
            const fileInput = document.getElementById('bannerInput');
            const file = fileInput.files[0];
            if (!file) return;
            
            const formData = new FormData();
            formData.append('file', file);
            const statusDiv = document.getElementById('banner-status');
            
            statusDiv.textContent = "Uploading banner...";
            statusDiv.style.color = "#ffc107";
            
            fetch('/upload_banner', { method: 'POST', body: formData })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        statusDiv.textContent = `✓ ${data.message} (${data.info.width}x${data.info.height})`;
                        statusDiv.style.color = "#28a745";
                        fileInput.value = '';
                        updateOverlayStatus();
                        setTimeout(() => statusDiv.textContent = '', 5000);
                    } else {
                        statusDiv.textContent = `✗ ${data.error}`;
                        statusDiv.style.color = "#dc3545";
                    }
                })
                .catch(err => {
                    statusDiv.textContent = "✗ Upload Failed";
                    statusDiv.style.color = "#dc3545";
                });
        });

        // Update Overlay Status
        function updateOverlayStatus() {
            fetch('/overlay_status')
                .then(response => response.json())
                .then(data => {
                    const infoDiv = document.getElementById('overlay-info');
                    let html = '';
                    
                    if (data.logo.exists) {
                        html += `<div style="margin-bottom: 8px;">
                            <span style="color: #28a745;">✓</span> Logo: ${data.logo.width}x${data.logo.height} (${data.logo.size_mb}MB)
                        </div>`;
                    } else {
                        html += `<div style="margin-bottom: 8px; color: #6c757d;">○ Logo: Not uploaded</div>`;
                    }
                    
                    if (data.banner.exists) {
                        html += `<div>
                            <span style="color: #28a745;">✓</span> Banner: ${data.banner.width}x${data.banner.height} (${data.banner.size_mb}MB)
                        </div>`;
                    } else {
                        html += `<div style="color: #6c757d;">○ Banner: Not uploaded</div>`;
                    }
                    
                    infoDiv.innerHTML = html;
                })
                .catch(err => {
                    console.error('Error fetching overlay status:', err);
                });
        }

        // Update overlay status periodically
        setInterval(updateOverlayStatus, 5000);
        updateOverlayStatus();

'''

# Find insertion points
queue_marker = '                <!-- Queue -->'
script_end_marker = '    </script>'

# Insert HTML before Queue section
if queue_marker in content:
    content = content.replace(queue_marker, overlay_html + queue_marker)
    print("✓ Inserted overlay HTML controls")
else:
    print("✗ Could not find Queue marker")

# Insert JavaScript before </script>
if script_end_marker in content:
    content = content.replace(script_end_marker, overlay_js + script_end_marker)
    print("✓ Inserted overlay JavaScript")
else:
    print("✗ Could not find script end marker")

# Write back
with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✅ Done! Overlay controls added to index.html")
print("Restart the Flask server and refresh your browser.")
