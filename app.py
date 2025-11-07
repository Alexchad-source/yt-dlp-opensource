from flask import Flask, request, jsonify
import yt_dlp
import base64

app = Flask(__name__)

@app.route('/download', methods=['POST'])
def download_video():
    data = request.json
    url = data.get('url')
    
    ydl_opts = {
        'format': 'best[ext=mp4]',
        'quiet': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        video_url = info['url']
        
        # Download video
        import requests
        video_data = requests.get(video_url).content
        
        # Get thumbnail
        thumbnail_url = info.get('thumbnail')
        thumbnail_data = None
        if thumbnail_url:
            thumbnail_data = requests.get(thumbnail_url).content
        
        return jsonify({
            'videoData': base64.b64encode(video_data).decode(),
            'thumbnailData': base64.b64encode(thumbnail_data).decode() if thumbnail_data else None,
            'title': info.get('title', 'Untitled'),
            'description': info.get('description', ''),
            'duration': info.get('duration', 0),
            'videoContentType': 'video/mp4',
            'thumbnailContentType': 'image/jpeg'
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
