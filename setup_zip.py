import os
import zipfile

# 1. Project file structure & clean code
project_files = {
    "requirements.txt": """flask>=3.0.0
flask-cors>=4.0.0
yt-dlp>=2024.0.0
""",

    "downloader.py": '''import os
import uuid
import yt_dlp

DOWNLOADS_DIR = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

class YouTubeEngine:
    @staticmethod
    def _base_opts(output_path):
        return {
            'outtmpl': output_path,
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web']
                }
            }
        }

    @staticmethod
    def get_video_info(url: str):
        opts = {
            'quiet': True,
            'skip_download': True,
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}}
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            meta = ydl.extract_info(url, download=False)
            return {
                "id": meta.get("id"),
                "title": meta.get("title", "YouTube Video"),
                "duration": meta.get("duration", 0),
                "thumbnail": meta.get("thumbnail"),
                "author": meta.get("uploader", "Unknown Channel")
            }

    @classmethod
    def download_media(cls, url: str, format_type: str, resolution: str):
        job_id = str(uuid.uuid4())[:8]
        output_template = os.path.join(DOWNLOADS_DIR, f"{job_id}_%(title)s.%(ext)s")
        opts = cls._base_opts(output_template)

        if format_type == 'mp3':
            opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:
            opts.update({
                'format': f'bestvideo[height<={resolution}]+bestaudio/best[height<={resolution}]/best',
                'merge_output_format': 'mp4',
            })

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = ydl.prepare_filename(info)
            if format_type == 'mp3':
                filepath = os.path.splitext(filepath)[0] + '.mp3'

            safe_title = "".join(c for c in info.get("title", "download") if c.isalnum() or c in (' ', '_', '-')).rstrip()
            download_name = f"{safe_title}.mp3" if format_type == 'mp3' else f"{safe_title}_{resolution}p.mp4"

            return os.path.abspath(filepath), download_name
''',

    "app.py": '''import os
from flask import Flask, render_template, request, jsonify, send_file, after_this_request
from flask_cors import CORS
from downloader import YouTubeEngine

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/info', methods=['POST'])
def video_info():
    data = request.get_json(silent=True) or {}
    url = data.get('url', '').strip()
    if not url:
        return jsonify({'error': 'URL missing hai'}), 400

    try:
        info = YouTubeEngine.get_video_info(url)
        return jsonify(info), 200
    except Exception as e:
        return jsonify({'error': f'Video verify nahi hui: {str(e)}'}), 400

@app.route('/api/download', methods=['POST'])
def process_download():
    data = request.get_json(silent=True) or {}
    url = data.get('url', '').strip()
    format_type = data.get('format', 'mp4')
    resolution = data.get('resolution', '720')

    if not url:
        return jsonify({'error': 'URL missing hai'}), 400

    try:
        file_path, download_filename = YouTubeEngine.download_media(url, format_type, resolution)

        @after_this_request
        def cleanup(response):
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                pass
            return response

        return send_file(
            file_path,
            as_attachment=True,
            download_name=download_filename,
            mimetype="audio/mpeg" if format_type == 'mp3' else "video/mp4"
        )
    except Exception as e:
        return jsonify({'error': f'Download fail hua: {str(e)}'}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("StreamFetch Server running at: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)
''',

    "templates/index.html": '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>StreamFetch - Media Hub</title>
  <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
  <main class="container">
    <div class="card">
      <header class="header">
        <h1>StreamFetch <span>Pro</span></h1>
        <p>Paste any YouTube link to preview and download in your desired quality</p>
      </header>

      <form id="urlForm" class="search-box">
        <input 
          type="url" 
          id="urlInput" 
          placeholder="https://www.youtube.com/watch?v=..." 
          required 
          autocomplete="off"
        >
        <button type="submit" id="inspectBtn">Inspect</button>
      </form>

      <section id="previewSection" class="preview-section hidden">
        <div class="player-wrapper">
          <iframe id="videoIframe" allowfullscreen></iframe>
        </div>
        <div class="video-meta">
          <h3 id="videoTitle"></h3>
          <p id="videoAuthor"></p>
        </div>

        <div class="control-grid">
          <div class="field">
            <label for="formatSelect">Format</label>
            <select id="formatSelect">
              <option value="mp4">Video (MP4)</option>
              <option value="mp3">Audio Only (MP3)</option>
            </select>
          </div>

          <div class="field" id="qualityField">
            <label for="qualitySelect">Resolution</label>
            <select id="qualitySelect">
              <option value="1080">1080p (Full HD)</option>
              <option value="720" selected>720p (HD)</option>
              <option value="480">480p</option>
              <option value="360">360p</option>
            </select>
          </div>
        </div>

        <button id="downloadBtn" class="download-btn">Start Download</button>
      </section>

      <div id="statusBox" class="status-box hidden"></div>
    </div>
  </main>

  <script src="/static/js/app.js"></script>
</body>
</html>
''',

    "static/css/style.css": ''':root {
  --bg: #090d16;
  --surface: #131b2e;
  --surface-border: #1e293b;
  --primary: #38bdf8;
  --primary-hover: #0284c7;
  --text-main: #f8fafc;
  --text-muted: #94a3b8;
  --success: #22c55e;
  --error: #ef4444;
}

* { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }

body {
  background-color: var(--bg);
  color: var(--text-main);
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px 16px;
}

.container { width: 100%; max-width: 680px; }

.card {
  background: var(--surface);
  border: 1px solid var(--surface-border);
  border-radius: 18px;
  padding: 32px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
}

.header { text-align: center; margin-bottom: 24px; }
.header h1 { font-size: 28px; margin-bottom: 6px; }
.header h1 span { color: var(--primary); }
.header p { color: var(--text-muted); font-size: 14px; }

.search-box {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

input[type="url"] {
  flex: 1;
  background: #0b1120;
  border: 1px solid var(--surface-border);
  border-radius: 10px;
  padding: 12px 16px;
  color: #fff;
  font-size: 15px;
  outline: none;
}
input[type="url"]:focus { border-color: var(--primary); }

#inspectBtn {
  background: var(--primary);
  color: #0b1120;
  border: none;
  font-weight: 700;
  padding: 0 22px;
  border-radius: 10px;
  cursor: pointer;
  transition: opacity 0.2s;
}
#inspectBtn:hover { opacity: 0.9; }

.hidden { display: none !important; }

.preview-section {
  margin-top: 24px;
  border-top: 1px solid var(--surface-border);
  padding-top: 24px;
}

.player-wrapper {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  border-radius: 12px;
  overflow: hidden;
  background: #000;
  margin-bottom: 16px;
}
.player-wrapper iframe { width: 100%; height: 100%; border: none; }

.video-meta { margin-bottom: 20px; }
.video-meta h3 { font-size: 16px; margin-bottom: 4px; color: var(--text-main); }
.video-meta p { font-size: 13px; color: var(--text-muted); }

.control-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin-bottom: 18px;
}

.field label {
  display: block;
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 6px;
  font-weight: 600;
}

select {
  width: 100%;
  background: #0b1120;
  border: 1px solid var(--surface-border);
  border-radius: 8px;
  padding: 10px 12px;
  color: #fff;
  outline: none;
  font-size: 14px;
}

.download-btn {
  width: 100%;
  background: #0284c7;
  color: #fff;
  border: none;
  padding: 14px;
  font-size: 15px;
  font-weight: 700;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.2s;
}
.download-btn:hover { background: var(--primary-hover); }
.download-btn:disabled { background: #334155; cursor: not-allowed; }

.status-box {
  margin-top: 18px;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  text-align: center;
}
.status-box.info { background: rgba(56, 189, 248, 0.1); color: var(--primary); }
.status-box.success { background: rgba(34, 197, 94, 0.1); color: var(--success); }
.status-box.error { background: rgba(239, 68, 68, 0.1); color: var(--error); }
''',

    "static/js/app.js": '''const urlForm = document.getElementById('urlForm');
const urlInput = document.getElementById('urlInput');
const inspectBtn = document.getElementById('inspectBtn');
const previewSection = document.getElementById('previewSection');
const videoIframe = document.getElementById('videoIframe');
const videoTitle = document.getElementById('videoTitle');
const videoAuthor = document.getElementById('videoAuthor');
const formatSelect = document.getElementById('formatSelect');
const qualityField = document.getElementById('qualityField');
const qualitySelect = document.getElementById('qualitySelect');
const downloadBtn = document.getElementById('downloadBtn');
const statusBox = document.getElementById('statusBox');

function setStatus(msg, type = 'info') {
  if (!msg) {
    statusBox.className = 'status-box hidden';
    return;
  }
  statusBox.className = `status-box ${type}`;
  statusBox.textContent = msg;
}

formatSelect.addEventListener('change', () => {
  if (formatSelect.value === 'mp3') {
    qualityField.style.opacity = '0.4';
    qualitySelect.disabled = true;
  } else {
    qualityField.style.opacity = '1';
    qualitySelect.disabled = false;
  }
});

urlForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const url = urlInput.value.trim();
  if (!url) return;

  inspectBtn.disabled = true;
  inspectBtn.textContent = 'Checking...';
  setStatus('Validating video with server...', 'info');

  try {
    const res = await fetch('/api/info', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Invalid video link');

    videoTitle.textContent = data.title;
    videoAuthor.textContent = data.author;
    videoIframe.src = `https://www.youtube.com/embed/${data.id}?autoplay=0`;

    previewSection.classList.remove('hidden');
    setStatus('');
  } catch (err) {
    setStatus(err.message, 'error');
    previewSection.classList.add('hidden');
  } finally {
    inspectBtn.disabled = false;
    inspectBtn.textContent = 'Inspect';
  }
});

downloadBtn.addEventListener('click', async () => {
  const url = urlInput.value.trim();
  const format = formatSelect.value;
  const resolution = qualitySelect.value;

  downloadBtn.disabled = true;
  downloadBtn.textContent = 'Processing media...';
  setStatus('Downloading & merging stream via FFmpeg on server...', 'info');

  try {
    const res = await fetch('/api/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, format, resolution })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || 'Server processing error');
    }

    const disposition = res.headers.get('Content-Disposition');
    let filename = format === 'mp3' ? 'audio.mp3' : `video_${resolution}p.mp4`;
    if (disposition && disposition.includes('filename=')) {
      filename = disposition.split('filename=')[1].replace(/["']/g, '');
    }

    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(downloadUrl);

    setStatus('Download completed successfully!', 'success');
  } catch (err) {
    setStatus(err.message, 'error');
  } finally {
    downloadBtn.disabled = false;
    downloadBtn.textContent = 'Start Download';
  }
});
'''
}

zip_filename = "yt-stream-downloader.zip"

print("Packaging project...")
with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
    for filepath, content in project_files.items():
        # Directory create karein
        parent_dir = os.path.dirname(filepath)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
            
        # File write karein
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
            
        # Zip me add karein
        zipf.write(filepath)
        print(f"Added: {filepath}")

print(f"\nZIP FILE CREATED: {zip_filename}")