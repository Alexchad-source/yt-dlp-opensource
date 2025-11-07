from flask import Flask, request, jsonify
import yt_dlp
import tempfile
import os
import boto3
from botocore.exceptions import BotoCoreError, NoCredentialsError

app = Flask(__name__)

# ----------------------------
# Configure S3
# ----------------------------
S3_BUCKET = os.environ.get("S3_BUCKET")
S3_REGION = os.environ.get("S3_REGION", "us-east-1")
S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY")
S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY")

if not all([S3_BUCKET, S3_ACCESS_KEY, S3_SECRET_KEY]):
    print("⚠️  Missing S3 credentials! Set S3_BUCKET, S3_ACCESS_KEY, and S3_SECRET_KEY in Render environment.")

s3 = boto3.client(
    "s3",
    region_name=S3_REGION,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY
)

# ----------------------------
# Route
# ----------------------------
@app.route("/download", methods=["POST"])
def download_video():
    data = request.json or {}
    url = data.get("url")

    if not url:
        return jsonify({"error": "Missing 'url'"}), 400

    try:
        # Create temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            ydl_opts = {
                "format": "bestvideo+bestaudio/best",
                "merge_output_format": "mp4",
                "outtmpl": os.path.join(tmpdir, "%(title)s.%(ext)s"),
                "quiet": True,
                "no_warnings": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

            # Determine the downloaded file
            filename = f"{info.get('title', 'video')}.mp4"
            local_path = os.path.join(tmpdir, filename)

            if not os.path.exists(local_path):
                # yt_dlp might save differently; find first .mp4 in tmpdir
                for f in os.listdir(tmpdir):
                    if f.endswith(".mp4"):
                        local_path = os.path.join(tmpdir, f)
                        break

            # Upload to S3
            s3_key = f"videos/{os.path.basename(local_path)}"

            s3.upload_file(
                local_path,
                S3_BUCKET,
                s3_key,
                ExtraArgs={"ACL": "public-read", "ContentType": "video/mp4"}
            )

            public_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{s3_key}"

            return jsonify({
                "title": info.get("title", "Untitled"),
                "description": info.get("description", ""),
                "duration": info.get("duration", 0),
                "thumbnail": info.get("thumbnail"),
                "publicUrl": public_url
            })

    except (BotoCoreError, NoCredentialsError) as e:
        return jsonify({"error": f"S3 upload failed: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Video Downloader API running!"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
