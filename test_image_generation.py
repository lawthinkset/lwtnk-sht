import os
import requests
import time
from pathlib import Path
from urllib.parse import quote
from PIL import Image
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "")
IMAGE_WIDTH = 720
IMAGE_HEIGHT = 1280
IMAGE_MODEL = "zimage"  # Z-Image Turbo with improved prompts
FINAL_WIDTH = 1080
FINAL_HEIGHT = 1920

# Create test directory
TEST_DIR = Path("test_images")
TEST_DIR.mkdir(exist_ok=True)

# Clean old test images
for f in TEST_DIR.glob("*.jpg"):
    f.unlink()

def generate_test_image(scene: str, era: str, idx: int):
    """Generate a test image with the new zimage model."""
    
    if not POLLINATIONS_API_KEY:
        raise ValueError("POLLINATIONS_API_KEY not set! Check your .env file")
    
    seed = hash(scene + str(idx)) % 1000000
    
    # Create era-specific prompts with CRITICAL SFW requirements
    if era == 'ANCIENT':
        style_prompt = (
            # CRITICAL: SFW AND CLOTHING FIRST - ABSOLUTE PRIORITY
            f"SAFE FOR WORK, FULLY CLOTHED PEOPLE, "
            f"everyone wearing complete period clothing, "
            f"full robes and togas covering entire body, "
            f"modest historical dress, NO NUDITY, "
            f"professional family-friendly content, "
            # Anatomy (with clothing)
            f"professional photograph, correct human anatomy, "
            f"beautiful faces with clear eyes nose mouth, "
            f"normal hands with 5 fingers, proper proportions, "
            f"realistic clothed people, "
            # Scene content
            f"{scene}, "
            f"ancient Roman or Greek legal setting, "
            f"judges and citizens in full traditional robes, "
            f"detailed expressive faces, dignified poses, "
            f"magnificent ancient architecture, marble columns, "
            f"stone temples, classical buildings, "
            f"golden hour lighting, warm sunlight, cinematic, "
            f"photorealistic, ultra detailed, sharp focus, "
            f"professional photography, 8k quality, "
            f"National Geographic documentary style"
        )
    elif era == 'MEDIEVAL':
        style_prompt = (
            # CRITICAL: SFW AND CLOTHING FIRST - ABSOLUTE PRIORITY
            f"SAFE FOR WORK, FULLY CLOTHED PEOPLE, "
            f"everyone wearing complete period clothing, "
            f"full armor and ceremonial robes covering entire body, "
            f"modest medieval dress, NO NUDITY, "
            f"professional family-friendly content, "
            # Anatomy (with clothing)
            f"professional photograph, correct human anatomy, "
            f"beautiful faces with clear eyes nose mouth, "
            f"normal hands with 5 fingers, proper proportions, "
            f"realistic clothed people, "
            # Scene content
            f"{scene}, "
            f"medieval European castle legal setting, "
            f"knights and nobles in full traditional dress, "
            f"detailed expressive faces, dignified poses, "
            f"gothic castle, stone halls, stained glass windows, "
            f"dramatic lighting, torch light, candlelight, atmospheric, "
            f"photorealistic, ultra detailed, sharp focus, "
            f"professional photography, 8k quality, "
            f"Game of Thrones TV show style"
        )
    else:  # MODERN
        style_prompt = (
            # CRITICAL: SFW AND CLOTHING FIRST - ABSOLUTE PRIORITY
            f"SAFE FOR WORK, FULLY CLOTHED PEOPLE, "
            f"everyone wearing complete business attire, "
            f"full suits and professional clothing covering entire body, "
            f"modest business dress, NO NUDITY, "
            f"professional family-friendly content, "
            # Anatomy (with clothing)
            f"professional photograph, correct human anatomy, "
            f"beautiful faces with clear eyes nose mouth, "
            f"normal hands with 5 fingers, proper proportions, "
            f"realistic clothed people, "
            # Scene content
            f"{scene}, "
            f"modern professional legal setting, "
            f"diverse lawyers and judges in full business suits, "
            f"detailed expressive faces, professional poses, "
            f"contemporary courthouse, glass and marble, modern architecture, "
            f"professional lighting, bright clean atmosphere, "
            f"photorealistic, ultra detailed, sharp focus, "
            f"professional photography, 8k quality, "
            f"corporate magazine style"
        )
    
    # COMPREHENSIVE negative prompt - block ALL deformities AND NSFW
    negative_prompt = (
        # CRITICAL: NSFW blocking
        "nude, nudity, naked, nsfw, exposed skin, bare chest, "
        "bare body, undressed, topless, revealing, "
        "inappropriate, adult content, sexual, "
        # Face deformities
        "deformed face, ugly face, distorted face, malformed face, "
        "disfigured face, bad eyes, crossed eyes, missing eyes, extra eyes, "
        "bad nose, missing nose, deformed mouth, bad teeth, "
        "asymmetrical face, mutated face, "
        # Body deformities
        "deformed body, bad anatomy, wrong anatomy, extra limbs, "
        "missing limbs, extra arms, extra legs, missing arms, missing legs, "
        "bad hands, deformed hands, extra fingers, missing fingers, "
        "fused fingers, mutated hands, poorly drawn hands, "
        "bad feet, deformed feet, extra toes, missing toes, "
        "malformed limbs, disfigured, mutation, mutated, "
        "extra body parts, duplicate body parts, "
        # Proportions
        "bad proportions, long neck, long body, elongated, "
        "stretched, distorted proportions, "
        # Quality issues
        "blurry, low quality, low resolution, pixelated, "
        "grainy, jpeg artifacts, compression artifacts, "
        # Style issues
        "cartoon, anime, drawing, painting, illustration, "
        "3d render, cgi, "
        # Other
        "watermark, text, signature, username, "
        "cropped, cut off, out of frame"
    )
    
    safe_prompt = quote(style_prompt)
    safe_negative = quote(negative_prompt)
    
    url = (
        f"https://gen.pollinations.ai/image/{safe_prompt}"
        f"?width={IMAGE_WIDTH}&height={IMAGE_HEIGHT}"
        f"&model={IMAGE_MODEL}"
        f"&seed={seed}"
        f"&nologo=true"
        f"&nofeed=true"
        f"&enhance=true"
        f"&negative={safe_negative}"
    )
    
    headers = {
        "Authorization": f"Bearer {POLLINATIONS_API_KEY}"
    }
    
    out = TEST_DIR / f"sfw_{era.lower()}_{idx}_original.jpg"
    out_upscaled = TEST_DIR / f"sfw_{era.lower()}_{idx}_hd.jpg"
    
    print(f"\n{'='*60}")
    print(f"🎬 Generating {era} image {idx+1}")
    print(f"📸 Scene: {scene}")
    print(f"{'='*60}")
    
    try:
        print(f"⏳ Downloading from Pollinations AI (zimage - SFW ONLY)...")
        r = requests.get(url, headers=headers, timeout=90)
        r.raise_for_status()
        
        if len(r.content) < 1000:
            raise ValueError("Image too small")
        
        out.write_bytes(r.content)
        print(f"✅ Downloaded: {out.name} ({len(r.content)//1024}KB)")
        
        # Upscale to HD
        print(f"🔍 Upscaling from {IMAGE_WIDTH}x{IMAGE_HEIGHT} to {FINAL_WIDTH}x{FINAL_HEIGHT}...")
        img = Image.open(out)
        img_upscaled = img.resize((FINAL_WIDTH, FINAL_HEIGHT), Image.Resampling.LANCZOS)
        img_upscaled.save(out_upscaled, quality=95, optimize=True)
        print(f"✅ Upscaled: {out_upscaled.name} ({out_upscaled.stat().st_size//1024}KB)")
        
        print(f"🎉 SUCCESS! Both versions saved to test_images/")
        return out_upscaled
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

# Test scenes for each era
test_scenes = [
    {
        "era": "ANCIENT",
        "scene": "Ancient Roman judge in toga presiding over a trial in the Forum, with marble columns and citizens watching"
    },
    {
        "era": "MEDIEVAL", 
        "scene": "Medieval knight standing trial before a king in a grand castle hall with stained glass windows"
    },
    {
        "era": "MODERN",
        "scene": "Modern lawyer presenting evidence in a contemporary glass courthouse with dramatic lighting"
    }
]

print("\n" + "="*60)
print("🎨 TESTING Z-IMAGE WITH SFW REQUIREMENTS")
print("="*60)
print(f"Model: {IMAGE_MODEL}")
print(f"Original Size: {IMAGE_WIDTH}x{IMAGE_HEIGHT}")
print(f"Upscaled Size: {FINAL_WIDTH}x{FINAL_HEIGHT}")
print("="*60)

# Generate test images
for idx, test in enumerate(test_scenes):
    try:
        generate_test_image(test["scene"], test["era"], idx)
        time.sleep(3)  # Rate limiting
    except Exception as e:
        print(f"⚠️ Failed to generate {test['era']} image: {e}")

print("\n" + "="*60)
print("✅ TEST COMPLETE!")
print(f"📁 Check the 'test_images' folder for results")
print("="*60)
