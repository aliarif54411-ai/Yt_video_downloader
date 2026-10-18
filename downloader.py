import os
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
