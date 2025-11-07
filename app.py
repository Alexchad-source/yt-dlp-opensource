from flask import Flask, request, send_file, jsonify
import yt_dlp
import tempfile
import os

app = Flask(__name__)

@app.route("/download", methods=["POST"])
def download_video():
    data = request.json or {}
    url = data.get("url")

    if not url:
        return jsonify({"error": "Missing 'url'"}), 400

    try:
        # Create a temporary directory for the download
        with tempfile.TemporaryDirectory() as tmpdir:
            output_template = os.path.join(tmpdir, "%(title)s.%(ext)s")

            ydl_opts = {
                "format": "bestvideo+bestaudio/best",
                "merge_output_format": "mp4",
                "outtmpl": output_template,
                "quiet": True,
                "no_warnings": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

            # Find the downloaded file path
            filename = f"{info.get('title', 'video')}.mp4"
            filepath = os.path.join(tmpdir, filename)
            if not os.path.exists(filepath):
                # fallback in case yt_dlp renames it slightly
                for f in os.listdir(tmpdir):
                    if f.endswith(".mp4"):
                        filepath = os.path.join(tmpdir, f)
                        break

            # Stream the downloaded file as a response
            return send_file(
                filepath,
                mimetype="video/mp4",
                as_attachment=True,
                download_name=filename
            )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Video Downloader API running!"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
