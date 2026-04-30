import streamlit as st
import requests
import random
import os
import time
import shutil
from datetime import datetime
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import google.generativeai as genai

# Page config
st.set_page_config(
    page_title="AI Shorts Forge",
    page_icon="🔥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.title("🔥 AI Shorts Forge")
st.caption("Generate motivational YouTube Shorts • 55 seconds each")

# Initialize session state
if 'shorts_data' not in st.session_state:
    st.session_state.shorts_data = []
if 'generation_complete' not in st.session_state:
    st.session_state.generation_complete = False
if 'generating' not in st.session_state:
    st.session_state.generating = False

# Initialize Gemini
try:
    GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        api_available = True
    else:
        api_available = False
except:
    api_available = False

# Stock footage URLs
FOOTAGE_URLS = [
    "https://assets.mixkit.co/videos/preview/mixkit-mountains-at-sunset-3885-large.mp4",
    "https://assets.mixkit.co/videos/preview/mixkit-waves-crashing-on-the-shore-2765-large.mp4",
    "https://assets.mixkit.co/videos/preview/mixkit-time-lapse-of-nyc-skyline-3860-large.mp4",
    "https://assets.mixkit.co/videos/preview/mixkit-forest-trees-3297-large.mp4",
    "https://assets.mixkit.co/videos/preview/mixkit-young-woman-running-in-nature-3280-large.mp4",
]

FALLBACK_TOPICS = [
    {"title": "Why Everyone Quits Right Before Success", "hook": "You're closer than you think. Don't stop now.", "keywords": "success persistence"},
    {"title": "The 5 AM Secret That Changed My Life", "hook": "What you do before 6am determines everything.", "keywords": "morning routine discipline"},
    {"title": "Discipline Over Motivation", "hook": "Motivation fades. Discipline stays.", "keywords": "discipline self control"},
]

UPLOAD_SCHEDULE = [
    {"pkt": "4:00 PM", "us": "6:00 AM EST", "type": "Morning Motivation"},
    {"pkt": "6:00 PM", "us": "8:00 AM EST", "type": "Commute Time"},
    {"pkt": "8:00 PM", "us": "10:00 AM EST", "type": "Mid-Morning Break"},
    {"pkt": "10:00 PM", "us": "12:00 PM EST", "type": "Lunch Break"},
    {"pkt": "12:00 AM", "us": "2:00 PM EST", "type": "Afternoon Slump"},
]

def generate_topic():
    if not api_available:
        return random.choice(FALLBACK_TOPICS)
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = """Generate ONE unique motivational topic.
Format:
TITLE: [title under 60 chars]
HOOK: [attention grabbing sentence]
KEYWORDS: [3 keywords]"""
        response = model.generate_content(prompt)
        lines = response.text.strip().split('\n')
        title = lines[0].replace('TITLE:', '').strip()
        hook = lines[1].replace('HOOK:', '').strip()
        keywords = lines[2].replace('KEYWORDS:', '').strip()
        return {"title": title[:60], "hook": hook[:100], "keywords": keywords}
    except:
        return random.choice(FALLBACK_TOPICS)

def get_seo(title, hook, keywords, idx):
    schedule = UPLOAD_SCHEDULE[idx % len(UPLOAD_SCHEDULE)]
    return {
        "title": f"{title} 🔥"[:70],
        "description": f"{hook}\n\n💪 {title}\n\nSubscribe for daily motivation!\n\n#motivation #{keywords.replace(' ', ' #')}",
        "hashtags": f"#motivation #{keywords.replace(' ', ' #')}",
        "best_time_pkt": schedule['pkt'],
        "best_time_us": schedule['us'],
    }

def download_footage(url, output_path):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, stream=True, timeout=30)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        return False
    except:
        return False

def create_text_image(text, font_size, color, width=1080, height=300):
    try:
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
        
        font = None
        for path in font_paths:
            if os.path.exists(path):
                try:
                    font = ImageFont.truetype(path, font_size)
                    break
                except:
                    continue
        
        if font is None:
            font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        y = (height - 100) // 2
        
        for offset in [(-2,-2), (-2,2), (2,-2), (2,2)]:
            draw.text((x+offset[0], y+offset[1]), text, fill=(0,0,0), font=font)
        draw.text((x, y), text, fill=color, font=font)
        
        return np.array(img)
    except:
        return np.zeros((height, width, 4), dtype=np.uint8)

def create_short(title, hook, short_num):
    os.makedirs("shorts", exist_ok=True)
    output_path = f"shorts/short_{short_num:03d}.mp4"
    temp_video = f"temp_{short_num}.mp4"
    duration = 55
    
    video_clip = None
    for footage_url in FOOTAGE_URLS:
        if download_footage(footage_url, temp_video):
            try:
                clip = VideoFileClip(temp_video)
                if clip.w / clip.h > 9/16:
                    clip = clip.resize(height=1920)
                    clip = clip.crop(x_center=clip.w/2, y_center=clip.h/2, width=1080, height=1920)
                else:
                    clip = clip.resize(width=1080)
                    clip = clip.crop(x_center=clip.w/2, y_center=clip.h/2, width=1080, height=1920)
                video_clip = clip.subclip(0, min(duration, clip.duration))
                if video_clip.duration < duration:
                    loops = int(duration / video_clip.duration) + 1
                    video_clip = concatenate_videoclips([video_clip] * loops).subclip(0, duration)
                break
            except:
                if os.path.exists(temp_video):
                    os.remove(temp_video)
                continue
    
    if video_clip is None:
        video_clip = ColorClip(size=(1080, 1920), color=(20, 20, 40), duration=duration)
    
    try:
        title_img = create_text_image(title, 65, (255, 255, 255))
        title_clip = ImageClip(title_img, transparent=True, duration=duration).set_position(('center', 200))
        
        hook_img = create_text_image(hook, 45, (255, 75, 75))
        hook_clip = ImageClip(hook_img, transparent=True, duration=duration).set_position(('center', 500))
        
        cta_img = create_text_image("Subscribe 🔔 Daily Motivation", 40, (255, 255, 255))
        cta_clip = ImageClip(cta_img, transparent=True, duration=duration).set_position(('center', 1700))
        
        final = CompositeVideoClip([video_clip, title_clip, hook_clip, cta_clip])
    except:
        final = video_clip
    
    final.write_videofile(output_path, fps=24, codec='libx264', threads=2, preset='fast', bitrate='1500k', logger=None, verbose=False)
    
    if os.path.exists(temp_video):
        os.remove(temp_video)
    
    return output_path

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    num_shorts = st.slider("Number of Shorts", 1, 10, 5)
    
    st.divider()
    if api_available:
        st.success("✅ Gemini AI Connected")
    else:
        st.warning("⚠️ Add Gemini API Key")
    
    st.divider()
    st.header("🌍 Best Upload Times (PKT)")
    for s in UPLOAD_SCHEDULE:
        st.markdown(f"**{s['pkt']}** → {s['us']}")
    
    st.divider()
    if st.button("🗑️ DELETE ALL VIDEOS", use_container_width=True):
        if os.path.exists("shorts"):
            shutil.rmtree("shorts")
            os.makedirs("shorts", exist_ok=True)
        st.session_state.shorts_data = []
        st.session_state.generation_complete = False
        st.rerun()
    
    if st.session_state.shorts_data:
        st.divider()
        st.caption(f"📁 {len(st.session_state.shorts_data)} video(s) saved")

# Main area
if not st.session_state.generation_complete and not st.session_state.generating:
    if st.button(f"🔥 GENERATE {num_shorts} SHORTS (55 sec each)", type="primary", use_container_width=True):
        st.session_state.generating = True
        st.rerun()

# Generation in progress
if st.session_state.generating:
    st.info(f"🎬 Generating {num_shorts} motivational shorts... This takes 30-60 seconds per video.")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Create a placeholder for videos to appear
    videos_placeholder = st.container()
    
    new_shorts = []
    
    for i in range(num_shorts):
        status_text.text(f"🎥 Creating Short {i+1}/{num_shorts}: Generating topic...")
        
        topic = generate_topic()
        
        status_text.text(f"🎥 Creating Short {i+1}/{num_shorts}: Making video (55 seconds)...")
        
        video_path = create_short(topic['title'], topic['hook'], i+1)
        seo = get_seo(topic['title'], topic['hook'], topic['keywords'], i)
        
        with open(video_path, 'rb') as f:
            video_bytes = f.read()
        
        short_data = {
            "num": i+1,
            "title": topic['title'],
            "hook": topic['hook'],
            "video_bytes": video_bytes,
            "seo_title": seo['title'],
            "seo_description": seo['description'],
            "seo_hashtags": seo['hashtags'],
            "best_time_pkt": seo['best_time_pkt'],
            "best_time_us": seo['best_time_us'],
            "path": video_path
        }
        new_shorts.append(short_data)
        
        # Show video immediately as it's created
        with videos_placeholder:
            with st.expander(f"✅ Short #{i+1}: {topic['title'][:40]}...", expanded=True):
                st.video(video_bytes)
                st.download_button(
                    label=f"📥 Download Short #{i+1}",
                    data=video_bytes,
                    file_name=f"motivation_short_{i+1:03d}.mp4",
                    mime="video/mp4",
                    key=f"download_{i}"
                )
        
        progress_bar.progress((i + 1) / num_shorts)
    
    status_text.text("✅ All shorts created successfully!")
    
    # Save to session state
    st.session_state.shorts_data = new_shorts
    st.session_state.generation_complete = True
    st.session_state.generating = False
    
    time.sleep(2)
    st.rerun()

# Display existing shorts (after generation)
if st.session_state.generation_complete and st.session_state.shorts_data:
    st.success(f"✅ {len(st.session_state.shorts_data)} shorts ready for upload!")
    
    for short in st.session_state.shorts_data:
        with st.expander(f"🎬 Short #{short['num']}: {short['title'][:40]}...", expanded=False):
            st.video(short['video_bytes'])
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.download_button(
                    label=f"📥 Download Video",
                    data=short['video_bytes'],
                    file_name=f"motivation_short_{short['num']:03d}.mp4",
                    mime="video/mp4",
                    key=f"download_main_{short['num']}"
                )
            with col2:
                if st.button(f"🗑️ Delete", key=f"delete_{short['num']}"):
                    if os.path.exists(short['path']):
                        os.remove(short['path'])
                    st.session_state.shorts_data = [s for s in st.session_state.shorts_data if s['num'] != short['num']]
                    if not st.session_state.shorts_data:
                        st.session_state.generation_complete = False
                    st.rerun()
            
            st.markdown("---")
            st.markdown("### 📋 Copy-Paste SEO")
            
            st.markdown("**🎯 Title:**")
            st.code(short['seo_title'], language='text')
            
            st.markdown("**📝 Description:**")
            st.code(short['seo_description'], language='text')
            
            st.markdown("**#️⃣ Hashtags:**")
            st.code(short['seo_hashtags'], language='text')
            
            st.info(f"⏰ Best upload time: {short['best_time_pkt']} PKT ({short['best_time_us']})")
    
    if st.button("🔄 GENERATE NEW BATCH", use_container_width=True):
        st.session_state.generation_complete = False
        st.session_state.shorts_data = []
        st.rerun()

# Footer
st.divider()
st.markdown("""
---
### 📱 How to Use

| Step | Action |
| :--- | :--- |
| 1 | Select number of shorts (1-10) in sidebar |
| 2 | Click "GENERATE" button |
| 3 | Watch videos appear AS they're created |
| 4 | Download each video to your phone |
| 5 | Copy SEO (title, description, hashtags) |
| 6 | Upload to YouTube Shorts at suggested times |

**Get Gemini API key:** [aistudio.google.com](https://aistudio.google.com/)
""")
