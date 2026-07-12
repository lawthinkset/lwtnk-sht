"""
Instagram Reels Upload - Using tmpfiles.org for Public URL
Uploads video to tmpfiles.org, then uses URL for Instagram API
"""

import os
import requests
import time
from pathlib import Path

def upload_to_instagram(video_path, caption):
    """
    Upload video to Instagram Reels via temporary public URL.
    """
    
    print("\n" + "=" * 60)
    print("📸 INSTAGRAM UPLOAD STARTING")
    print("=" * 60)
    
    # Get credentials
    access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
    user_id = os.getenv('INSTAGRAM_ACCOUNT_ID')
    
    if not access_token:
        error_msg = "❌ INSTAGRAM_ACCESS_TOKEN not set"
        print(f"[instagram] {error_msg}")
        raise ValueError(error_msg)
    
    if not user_id:
        error_msg = "❌ INSTAGRAM_ACCOUNT_ID not set"
        print(f"[instagram] {error_msg}")
        raise ValueError(error_msg)
    
    print(f"[instagram] ✅ Credentials loaded")
    print(f"[instagram] User ID: {user_id}")
    
    # Check video file
    video_path_obj = Path(video_path)
    if not video_path_obj.exists():
        error_msg = f"❌ Video file not found: {video_path}"
        print(f"[instagram] {error_msg}")
        raise FileNotFoundError(error_msg)
    
    file_size_mb = video_path_obj.stat().st_size / (1024 * 1024)
    print(f"[instagram] ✅ Video file found: {video_path}")
    print(f"[instagram] Video size: {file_size_mb:.2f} MB")
    
    # Limit caption
    caption_limited = caption[:2200] if len(caption) > 2200 else caption
    print(f"[instagram] Caption length: {len(caption_limited)} characters")
    
    try:
        # Step 1: Upload to tmpfiles.org to get public URL
        print("[instagram] Step 1: Uploading to GitHub raw URL...")
        import subprocess as _sp, uuid as _uuid, os as _os
        _vid_name = "ig_" + _uuid.uuid4().hex[:8] + ".mp4"
        _os.system("cp " + str(upload_path) + " " + _vid_name)
        _os.system("git config --global user.email bot@bot.com")
        _os.system("git config --global user.name Bot")
        _os.system("git add -f " + _vid_name)
        _os.system("git commit -m \"add " + _vid_name + "\"")
        for _ in range(3):
            _ret = _os.system("git push origin main")
            if _ret == 0:
                break
            time.sleep(5)
        video_url = "https://raw.githubusercontent.com/" + thriveruswave + "/" + lawthinkset + "/main/" + _vid_name
        print("[instagram] GitHub raw URL: " + video_url)
        
        container_url = f"https://graph.facebook.com/v18.0/{user_id}/media"
        container_params = {
            'media_type': 'REELS',
            'video_url': video_url,
            'caption': caption_limited,
            'share_to_feed': 'false',
            'access_token': access_token
        }
        
        container_response = requests.post(container_url, params=container_params, timeout=60)
        
        if container_response.status_code != 200:
            error_data = container_response.json() if container_response.text else {}
            error_msg = error_data.get('error', {}).get('message', 'Unknown error')
            print(f"[instagram] ❌ Container creation failed: {error_msg}")
            print(f"[instagram] Full response: {container_response.text[:500]}")
            raise Exception(f"Instagram Container Error: {error_msg}")
        
        container_id = container_response.json().get('id')
        print(f"[instagram] ✅ Container created: {container_id}")
        
        # Step 3: Wait for processing
        print("[instagram] Step 3: Waiting 60 seconds for processing...")
        time.sleep(60)

        # Step 4: Publish
        print("[instagram] Step 4: Publishing...")
        publish_url = f"https://graph.facebook.com/v21.0/{user_id}/media_publish"
        publish_params = {
            "creation_id": container_id,
            "access_token": access_token
        }
        publish_response = requests.post(publish_url, params=publish_params, timeout=60)

        if publish_response.status_code != 200:
            print("[instagram] First publish failed, retrying after 30s...")
            time.sleep(30)
            publish_response = requests.post(publish_url, params=publish_params, timeout=60)

        if publish_response.status_code != 200:
            error_data = publish_response.json() if publish_response and publish_response.text else {}
            error_msg = error_data.get("error", {}).get("message", "Unknown error")
            print(f"[instagram] Publish failed: {error_msg}")
            raise Exception(f"Instagram Publish Error: {error_msg}")

        media_id = publish_response.json().get("id")
        
        print(f"[instagram] ✅ SUCCESS! Video published to Instagram!")
        print(f"[instagram] Media ID: {media_id}")
        print(f"[instagram] Check your Instagram profile to see the Reel!")
        print("=" * 60)
        
        return {
            'id': media_id,
            'platform': 'instagram',
            'status': 'success'
        }
        
    except Exception as e:
        print(f"[instagram] ❌ ERROR!")
        print(f"[instagram] {str(e)}")
        print("=" * 60)
        raise

if __name__ == '__main__':
    video_file = Path('output/final_video.mp4')
    if video_file.exists():
        try:
            result = upload_to_instagram(str(video_file), "Test upload")
            print(f"\n✅ Success! Result: {result}")
        except Exception as e:
            print(f"\n❌ Failed: {e}")
    else:
        print(f"❌ Video not found: {video_file}")
