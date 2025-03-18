import requests
import time

# Step 1: Define Twelve Labs API key
API_KEY = "your_twelve_labs_api_key"
VIDEO_URL = "your_video_file_url"  # or local file path


# Step 2: Upload Video to Twelve Labs
def upload_video(video_url):
    url = "https://api.twelvelabs.io/v1/videos"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    data = {"url": video_url}

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        video_id = response.json()["id"]
        print(f"✅ Video Uploaded! ID: {video_id}")
        return video_id
    else:
        print("❌ Upload Failed:", response.text)
        return None


# Step 3: Extract Key Moments from Video
def get_key_moments(video_id):
    url = f"https://api.twelvelabs.io/v1/videos/{video_id}/highlights"
    headers = {"Authorization": f"Bearer {API_KEY}"}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        moments = response.json()["highlights"]
        return moments
    else:
        print("❌ Failed to fetch highlights:", response.text)
        return None


# Step 4: Generate Ad Snippets
def generate_ad_snippets(moments):
    ad_snippets = []
    for moment in moments:
        start = moment["start_time"]
        end = moment["end_time"]
        confidence = moment["confidence"]

        if confidence > 0.8:  # Only select highly engaging moments
            ad_snippets.append((start, end))

    return ad_snippets


# Running the Pipeline
video_id = upload_video(VIDEO_URL)
if video_id:
    time.sleep(10)  # Give time for processing
    moments = get_key_moments(video_id)
    if moments:
        ad_snippets = generate_ad_snippets(moments)
        print("🎬 Best Ad Snippets:", ad_snippets)
