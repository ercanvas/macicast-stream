"""
Script to add Program Name controls to index.html
"""

# Read the file
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# HTML to insert
program_html = '''
                <!-- Program Info -->
                <div class="control-section">
                    <div class="section-title">📺 Program Info</div>
                    <div style="margin-bottom: 15px;">
                        <div style="font-size: 11px; color: #6c757d; margin-bottom: 8px;">
                            Program Name (Top-Right Overlay)
                        </div>
                        <div style="display: flex; gap: 8px;">
                            <input type="text" id="programNameInput" placeholder="Enter program name..." 
                                   style="flex: 1; padding: 8px; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; color: #fff; font-size: 12px;">
                            <button onclick="updateProgramName()" class="upload-btn" style="padding: 8px 16px; width: auto;">UPDATE</button>
                        </div>
                        <div id="program-status" style="font-size: 11px; margin-top: 5px; height: 15px;"></div>
                    </div>
                </div>
'''

# JavaScript to insert
program_js = '''
        // Program Name Handling
        function updateProgramName() {
            const name = document.getElementById('programNameInput').value;
            const statusDiv = document.getElementById('program-status');
            
            statusDiv.textContent = "Updating...";
            statusDiv.style.color = "#ffc107";
            
            fetch('/set_program_name', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ program_name: name })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    statusDiv.textContent = "✓ Updated (Restart stream to apply)";
                    statusDiv.style.color = "#28a745";
                    setTimeout(() => statusDiv.textContent = '', 5000);
                } else {
                    statusDiv.textContent = "✗ Failed";
                    statusDiv.style.color = "#dc3545";
                }
            })
            .catch(err => {
                statusDiv.textContent = "✗ Error";
                statusDiv.style.color = "#dc3545";
            });
        }
'''

# Insert HTML before Overlay Controls
overlay_marker = '<!-- Overlay Controls -->'
if overlay_marker in content:
    content = content.replace(overlay_marker, program_html + '\n\n' + overlay_marker)
    print("✓ Inserted Program Info HTML")
else:
    print("✗ Could not find Overlay Controls marker")

# Insert JavaScript before </script>
script_end_marker = '    </script>'
if script_end_marker in content:
    content = content.replace(script_end_marker, program_js + script_end_marker)
    print("✓ Inserted Program Info JavaScript")
else:
    print("✗ Could not find script end marker")

# Write back
with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
