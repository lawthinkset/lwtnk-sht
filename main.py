import os
import re
import datetime
import subprocess
import random
from pathlib import Path
from urllib.parse import quote
import requests
import time

# ---------------- CONFIG ----------------

NUM_IMAGES = 8  # 8 unique scenes (faster generation)
IMAGE_WIDTH = 1080
IMAGE_HEIGHT = 1920
IMAGE_MODEL = "flux"

STORY_MAX_WORDS = 130

TOPICS_FILE = "topics.txt"

IMAGES_DIR = Path("images")
OUTPUT_DIR = Path("output")
AUDIO_DIR = Path("audio")

MUSIC_FILE = AUDIO_DIR / "music.mp3"

NARRATION_FILE = OUTPUT_DIR / "narration.mp3"
STORY_FILE = OUTPUT_DIR / "story.txt"
SCENES_FILE = OUTPUT_DIR / "scenes.txt"
SUBS_FILE = OUTPUT_DIR / "subtitles.ass"
ANIMATED_VIDEO = OUTPUT_DIR / "animated.mp4"
VIDEO_WITH_SUBS = OUTPUT_DIR / "video_with_subs.mp4"
FINAL_VIDEO = OUTPUT_DIR / "final_video.mp4"

WHISPER_MODEL_NAME = "small"

# ----------------------------------------

def ensure_dirs():
    IMAGES_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    AUDIO_DIR.mkdir(exist_ok=True)
    # Clean old images
    for f in IMAGES_DIR.glob("*.jpg"):
        f.unlink()

def choose_topic_for_today():
    """Choose today's topic and mark it as used."""
    topics_file = Path(TOPICS_FILE)
    used_topics_file = Path("used_topics.txt")
    
    # Read available topics
    with open(topics_file, "r", encoding="utf-8") as f:
        topics = [line.strip() for line in f if line.strip()]
    
    if not topics:
        raise Exception("No topics available! Run generate_topics.py first.")
    
    # Choose topic based on date (deterministic)
    today = datetime.date.today()
    selected_topic = topics[today.toordinal() % len(topics)]
    
    # Mark topic as used
    with open(used_topics_file, "a", encoding="utf-8") as f:
        f.write(f"{selected_topic}\n")
    
    # Remove used topic from topics.txt
    remaining_topics = [t for t in topics if t != selected_topic]
    with open(topics_file, "w", encoding="utf-8") as f:
        for topic in remaining_topics:
            f.write(f"{topic}\n")
    
    print(f"[topics] Selected: {selected_topic}")
    print(f"[topics] Remaining topics: {len(remaining_topics)}")
    
    return selected_topic

def generate_story_with_pollinations(topic: str) -> str:
    """Generate a short English law explanation."""
    base_url = "https://text.pollinations.ai/"
    
    # Determine the era of law
    is_ancient = topic.startswith("[ANCIENT]")
    is_medieval = topic.startswith("[MEDIEVAL]")
    is_modern = topic.startswith("[MODERN]")
    clean_topic = topic.replace("[ANCIENT] ", "").replace("[MEDIEVAL] ", "").replace("[MODERN] ", "")
    
    if is_ancient:
        system = (
            "You are a legal historian specializing in ancient laws. "
            "Write a fascinating explanation in 30 seconds (80-130 words) in English. "
            "Explain the ancient law clearly with historical context and interesting facts. "
            "Use engaging storytelling and vivid descriptions. No headings or titles."
        )
        prompt = f"Topic: {clean_topic}. Explain this ancient law with historical context."
    elif is_medieval:
        system = (
            "You are a legal historian specializing in medieval laws. "
            "Write an intriguing explanation in 30 seconds (80-130 words) in English. "
            "Explain the medieval law with historical context and fascinating details. "
            "Use engaging storytelling and vivid descriptions. No headings or titles."
        )
        prompt = f"Topic: {clean_topic}. Explain this medieval law with historical context."
    else:  # Modern
        system = (
            "You are a legal expert specializing in modern laws worldwide. "
            "Write a clear explanation in 30 seconds (80-130 words) in English. "
            "Explain the modern law with current context and practical implications. "
            "Use accessible language and real-world examples. No headings or titles."
        )
        prompt = f"Topic: {clean_topic}. Explain this modern law with current context."

    url = base_url + quote(prompt)
    params = {"model": "openai", "temperature": 1.0, "system": system}

    print(f"[story] Generating English law content for: {clean_topic}")
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    text = r.text.strip()

    words = text.split()
    if len(words) > STORY_MAX_WORDS:
        text = " ".join(words[:STORY_MAX_WORDS])

    with open(STORY_FILE, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"[story] Law content generated ({len(text.split())} words)")
    return text

def generate_scene_descriptions(story: str) -> list:
    """Extract distinct scene descriptions from the story sentences."""
    print(f"[scenes] Extracting {NUM_IMAGES} unique scene descriptions...")
    
    # Split story into sentences
    sentences = re.split(r'[.!?]+\s*', story.strip())
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
    
    # Create unique scenes from sentences
    scenes = []
    for i in range(NUM_IMAGES):
        if i < len(sentences):
            scene = sentences[i]
        else:
            # Cycle through sentences if we need more
            scene = sentences[i % len(sentences)]
        
        # Make each scene description more visual
        if i not in [j % len(sentences) for j in range(len(scenes))]:
            scenes.append(scene)
        else:
            # Add variation for repeated scenes
            variations = ["close-up view of", "wide shot of", "dramatic scene of", "peaceful moment of"]
            scenes.append(f"{variations[i % len(variations)]} {scene}")
    
    # Ensure uniqueness by adding index
    unique_scenes = []
    for i, scene in enumerate(scenes[:NUM_IMAGES]):
        unique_scenes.append(f"{scene}")
    
    # Save scenes
    with open(SCENES_FILE, "w", encoding="utf-8") as f:
        for i, scene in enumerate(unique_scenes):
            f.write(f"{i+1}. {scene}\n")
    
    print(f"[scenes] Created {len(unique_scenes)} unique scenes")
    return unique_scenes

def generate_image(scene: str, idx: int) -> Path:
    """Generate a unique law-themed image for each scene using Pollinations AI with Flux model."""
    # Create unique seed for each image based on scene content + index
    seed = hash(scene + str(idx)) % 1000000
    
    # Determine visual style based on the current topic's era
    topic_era = getattr(generate_image, 'topic_era', 'MODERN')
    
    # IMPROVED PROMPTS: Focus on scenes, architecture, and objects rather than people
    # This avoids deformed faces/bodies while creating stunning visuals
    
    if topic_era == 'ANCIENT':
        # Focus on ancient architecture, artifacts, and environments
        style_prompt = (
            f"stunning ancient civilization scene: {scene}, "
            # Architecture & Environment
            f"majestic ancient temples with towering stone columns, "
            f"intricate hieroglyphics carved in golden sandstone walls, "
            f"grand Egyptian pyramids under dramatic desert sky, "
            f"Roman forum with marble statues and classical architecture, "
            f"ancient Greek acropolis with Doric columns, "
            # Artifacts & Details
            f"ancient scrolls with detailed cuneiform writing, "
            f"clay tablets with legal inscriptions, "
            f"bronze scales of justice, ancient ceremonial objects, "
            f"ornate stone carvings depicting historical scenes, "
            # Lighting & Atmosphere
            f"warm golden hour lighting, dramatic shadows, "
            f"cinematic rays of sunlight through ancient structures, "
            f"atmospheric dust particles in air, "
            # Quality Controls
            f"photorealistic, ultra detailed, 8k resolution, "
            f"professional photography, National Geographic style, "
            f"historically accurate, museum quality, "
            f"epic composition, wide angle view, "
            f"sharp focus, perfect clarity, masterpiece"
        )
    elif topic_era == 'MEDIEVAL':
        # Focus on medieval architecture, manuscripts, and settings
        style_prompt = (
            f"breathtaking medieval scene: {scene}, "
            # Architecture & Environment
            f"grand medieval castle with gothic architecture, "
            f"stone courtroom with vaulted ceilings and arched windows, "
            f"magnificent cathedral interior with stained glass, "
            f"medieval great hall with wooden beams and tapestries, "
            f"candlelit chamber with stone walls, "
            # Artifacts & Details
            f"illuminated manuscripts with gold leaf decoration, "
            f"ancient parchment scrolls with wax seals, "
            f"ornate royal throne and crown, "
            f"medieval weapons and armor displays, "
            f"heraldic banners and coat of arms, "
            # Lighting & Atmosphere
            f"warm candlelight glow, dramatic torch lighting, "
            f"atmospheric medieval ambiance, "
            f"soft natural light through stained glass windows, "
            # Quality Controls
            f"photorealistic, ultra detailed, 8k resolution, "
            f"cinematic composition, historical accuracy, "
            f"professional photography, museum quality, "
            f"rich colors, perfect clarity, sharp focus, masterpiece"
        )
    else:  # MODERN
        # Focus on modern architecture, courtrooms, and legal symbols
        style_prompt = (
            f"impressive modern legal scene: {scene}, "
            # Architecture & Environment
            f"contemporary courthouse with marble columns and glass, "
            f"modern courtroom with wooden paneling and flags, "
            f"sleek government building with neoclassical design, "
            f"professional law library with floor-to-ceiling bookshelves, "
            f"elegant judicial chamber with modern furnishings, "
            # Symbols & Details
            f"golden scales of justice prominently displayed, "
            f"wooden gavel on polished desk, "
            f"leather-bound legal books and documents, "
            f"national flags and judicial symbols, "
            f"modern technology and displays, "
            # Lighting & Atmosphere
            f"professional studio lighting, clean bright atmosphere, "
            f"natural daylight through large windows, "
            f"sophisticated modern ambiance, "
            # Quality Controls
            f"photorealistic, ultra detailed, 8k resolution, "
            f"architectural photography, professional composition, "
            f"sharp focus, perfect clarity, pristine quality, "
            f"contemporary design, polished aesthetic, masterpiece"
        )
    
    # Add negative prompt to avoid common issues
    negative_prompt = (
        "deformed, distorted, disfigured, bad anatomy, "
        "ugly faces, bad faces, deformed bodies, "
        "extra limbs, missing limbs, blurry, low quality, "
        "watermark, text, signature, amateur"
    )
    
    # Encode prompts
    safe_prompt = quote(style_prompt)
    safe_negative = quote(negative_prompt)
    
    # Build URL with enhanced parameters for Flux model
    url = (
        f"https://image.pollinations.ai/prompt/{safe_prompt}"
        f"?width={IMAGE_WIDTH}&height={IMAGE_HEIGHT}"
        f"&model={IMAGE_MODEL}"
        f"&seed={seed}"
        f"&nologo=true"
        f"&enhance=true"
        f"&negative={safe_negative}"
    )

    out = IMAGES_DIR / f"scene_{idx:02d}.jpg"
    print(f"[image] Generating stunning {topic_era.lower()} image {idx+1}/{NUM_IMAGES}...")
    print(f"[image] Scene: {scene[:60]}...")
    
    # Retry logic with exponential backoff (longer waits for rate limits)
    max_retries = 5
    for attempt in range(max_retries):
        try:
            r = requests.get(url, timeout=180)
            r.raise_for_status()
            out.write_bytes(r.content)
            print(f"[image] ✅ Image {idx+1} generated successfully!")
            time.sleep(3)  # Slightly longer delay to ensure quality processing
            return out
        except requests.exceptions.HTTPError as e:
            # Handle 429 rate limits with much longer waits
            if e.response.status_code == 429:
                wait_time = (attempt + 1) * 20  # 20, 40, 60, 80, 100 seconds
                if attempt < max_retries - 1:
                    print(f"[image] ⏳ Rate limited! Retry {attempt+1}/{max_retries} (waiting {wait_time}s)")
                    time.sleep(wait_time)
                else:
                    print(f"[image] ❌ Failed to generate image {idx+1}: Rate limit exceeded")
                    raise e
            else:
                wait_time = (attempt + 1) * 5
                if attempt < max_retries - 1:
                    print(f"[image] ⚠️  HTTP {e.response.status_code}. Retry {attempt+1}/{max_retries} (waiting {wait_time}s)")
                    time.sleep(wait_time)
                else:
                    print(f"[image] ❌ Failed to generate image {idx+1}: {e}")
                    raise e
        except Exception as e:
            wait_time = (attempt + 1) * 5
            if attempt < max_retries - 1:
                print(f"[image] 🔄 Retry {attempt+1}/{max_retries} (waiting {wait_time}s)")
                time.sleep(wait_time)
            else:
                print(f"[image] ❌ Failed to generate image {idx+1}: {e}")
                raise e
    return out

def generate_images(scenes: list):
    """Generate unique images for each scene SEQUENTIALLY (avoids rate limits)"""
    print(f"[image] Generating {NUM_IMAGES} images sequentially (avoiding rate limits)...")
    return [generate_image(scene, i) for i, scene in enumerate(scenes)]

def generate_tts(story: str):
    """Generate narration using edge-tts (free Microsoft TTS)."""
    import asyncio
    try:
        import edge_tts
    except ImportError:
        subprocess.run(["pip", "install", "edge-tts"], check=True)
        import edge_tts
    
    print("[tts] Generating English narration with edge-tts...")
    
    VOICE = "en-US-GuyNeural"  # English male voice (or use "en-US-JennyNeural" for female)
    
    async def generate():
        communicate = edge_tts.Communicate(story, VOICE)
        await communicate.save(str(NARRATION_FILE))
    
    asyncio.run(generate())
    print(f"[tts] Narration saved to {NARRATION_FILE}")

def generate_word_subtitles():
    """Generate WORD-BY-WORD subtitles using Vosk (lightweight!)."""
    print("[subs] Generating word-level English subtitles with Vosk...")
    
    import json
    import wave
    from vosk import Model, KaldiRecognizer
    import os
    
    # Download Vosk model if not exists
    model_path = "vosk-model-small-en-us-0.15"
    if not os.path.exists(model_path):
        print("[subs] Downloading Vosk English model (~40 MB)...")
        import urllib.request
        import zipfile
        
        url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
        zip_path = "vosk-model.zip"
        
        urllib.request.urlretrieve(url, zip_path)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(".")
        
        os.remove(zip_path)
        print("[subs] Model downloaded!")
    
    # Convert MP3 to WAV for Vosk
    wav_file = "output/narration.wav"
    os.system(f'ffmpeg -y -i {NARRATION_FILE} -ar 16000 -ac 1 {wav_file}')
    
    # Load Vosk model
    model = Model(model_path)
    
    # Open WAV file
    wf = wave.open(wav_file, "rb")
    rec = KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(True)  # Enable word-level timestamps
    
    # Process audio
    words = []
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            if 'result' in result:
                for word_info in result['result']:
                    words.append({
                        'word': word_info['word'].upper(),
                        'start': word_info['start'],
                        'end': word_info['end']
                    })
    
    # Final result
    final_result = json.loads(rec.FinalResult())
    if 'result' in final_result:
        for word_info in final_result['result']:
            words.append({
                'word': word_info['word'].upper(),
                'start': word_info['start'],
                'end': word_info['end']
            })
    
    # Create ASS subtitle file
    ass_content = """[Script Info]
Title: Law Story
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Black,16,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,1,5,10,10,50,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    for word in words:
        start = word['start']
        end = word['end']
        text = word['word']
        
        start_time = f"{int(start//3600)}:{int((start%3600)//60):02d}:{start%60:.2f}"
        end_time = f"{int(end//3600)}:{int((end%3600)//60):02d}:{end%60:.2f}"
        
        ass_content += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}\n"
    
    # Save ASS file
    with open(SUBS_FILE, "w", encoding="utf-8") as f:
        f.write(ass_content)
    
    print(f"[subs] WORD-BY-WORD subtitles saved ({len(words)} words)")

def get_audio_duration(audio_file):
    """Get duration of audio file using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(audio_file)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())

def create_animated_slideshow(image_paths):
    """Create animated slideshow with Ken Burns zoom effect."""
    print("[video] Creating animated slideshow with Ken Burns effect...")
    
    # Get audio duration to match video length
    duration = get_audio_duration(NARRATION_FILE)
    per_image = duration / len(image_paths)
    
    # Create individual animated clips with zoom effect
    clips = []
    for i, img_path in enumerate(image_paths):
        clip_file = OUTPUT_DIR / f"clip_{i:02d}.mp4"
        clips.append(clip_file)
        
        # Calculate frames (30 fps)
        frames = max(int(per_image * 30), 60)
        
        # Alternate between zoom in and zoom out for variety
        if i % 2 == 0:
            # Zoom in effect
            zoom_start = 1.0
            zoom_end = 1.3
        else:
            # Zoom out effect  
            zoom_start = 1.3
            zoom_end = 1.0
        
        # Simple zoom with scale filter (more reliable on Windows)
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-vf", (
                f"scale=8000:-1,"
                f"zoompan=z='if(lte(on,1),{zoom_start},{zoom_start}+(({zoom_end}-{zoom_start})/{frames})*on)':"
                f"d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={IMAGE_WIDTH}x{IMAGE_HEIGHT}:fps=30"
            ),
            "-t", str(per_image),
            "-c:v", "libx264",
            "-preset", "slow",  # Better quality
            "-crf", "18",  # High quality (lower = better, 18-23 is good)
            "-pix_fmt", "yuv420p",
            str(clip_file)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[video] Zoom failed for clip {i+1}, using fallback...")
            # Fallback: simple static with slight movement
            cmd_fallback = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", str(img_path),
                "-vf", f"scale={IMAGE_WIDTH}:{IMAGE_HEIGHT}:force_original_aspect_ratio=increase,crop={IMAGE_WIDTH}:{IMAGE_HEIGHT},fps=30",
                "-t", str(per_image),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                str(clip_file)
            ]
            subprocess.run(cmd_fallback, check=True, capture_output=True)
        
        print(f"[video] Animated clip {i+1}/{len(image_paths)}")
    
    # Create concat list
    concat_file = OUTPUT_DIR / "concat.txt"
    with open(concat_file, "w") as f:
        for clip in clips:
            f.write(f"file '{clip.resolve()}'\n")
    
    # Concatenate all clips
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        str(ANIMATED_VIDEO)
    ]
    subprocess.run(cmd, check=True)
    print(f"[video] Animated slideshow saved to {ANIMATED_VIDEO}")
    
    # Cleanup individual clips
    for clip in clips:
        if clip.exists():
            clip.unlink()

def add_subtitles():
    """Overlay ASS subtitles on video."""
    print("[video] Adding UPPERCASE subtitles...")
    
    # Windows path needs special handling for FFmpeg filter
    subs_path = str(SUBS_FILE.resolve()).replace("\\", "/").replace(":", "\\:")
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(ANIMATED_VIDEO),
        "-vf", f"ass='{subs_path}'",
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(VIDEO_WITH_SUBS)
    ]
    subprocess.run(cmd, check=True)
    print(f"[video] Video with subtitles saved to {VIDEO_WITH_SUBS}")

def merge_audio():
    """Merge video with narration and background music."""
    print("[merge] Merging audio with background music...")
    
    if MUSIC_FILE.exists():
        # Merge narration + background music (music at lower volume)
        cmd = [
            "ffmpeg", "-y",
            "-i", str(VIDEO_WITH_SUBS),
            "-i", str(NARRATION_FILE),
            "-i", str(MUSIC_FILE),
            "-filter_complex", "[2:a]volume=0.25[bg];[1:a][bg]amix=inputs=2:duration=first[a]",
            "-map", "0:v",
            "-map", "[a]",
            "-shortest",
            "-c:v", "copy",
            str(FINAL_VIDEO)
        ]
    else:
        print("[merge] No music.mp3 found, using narration only")
        cmd = [
            "ffmpeg", "-y",
            "-i", str(VIDEO_WITH_SUBS),
            "-i", str(NARRATION_FILE),
            "-map", "0:v",
            "-map", "1:a",
            "-shortest",
            "-c:v", "copy",
            str(FINAL_VIDEO)
        ]
    
    subprocess.run(cmd, check=True)
    print(f"[merge] Final video saved to {FINAL_VIDEO}")

def main():
    ensure_dirs()

    topic = choose_topic_for_today()
    print("=" * 60)
    print(f"=== Topic: {topic}")
    print("=" * 60)
    
    # Extract era from topic for image styling
    if topic.startswith("[ANCIENT]"):
        topic_era = "ANCIENT"
    elif topic.startswith("[MEDIEVAL]"):
        topic_era = "MEDIEVAL"
    else:
        topic_era = "MODERN"
    
    # Store era as function attribute for image generation
    generate_image.topic_era = topic_era
    print(f"[main] Era: {topic_era}")

    # 1. Generate story with Pollinations AI
    story = generate_story_with_pollinations(topic)
    
    # 2. Generate unique scene descriptions from the story
    scenes = generate_scene_descriptions(story)
    
    # 3. Generate unique images for each scene
    images = generate_images(scenes)

    # 4. Generate narration with TTS
    generate_tts(story)
    
    # 5. Generate word-level UPPERCASE subtitles with Whisper
    generate_word_subtitles()
    
    # 6. Create animated slideshow with Ken Burns effect
    create_animated_slideshow(images)
    
    # 7. Add subtitles overlay
    add_subtitles()
    
    # 8. Merge audio (narration + background music)
    merge_audio()

    print("=" * 60)
    print(f"✅ DONE. Video ready: {FINAL_VIDEO}")
    print("=" * 60)

if __name__ == "__main__":
    main()
