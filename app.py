import os
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
