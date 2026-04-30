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

# Session state
if 'shorts_generated' not in st.session_state:
    st.session_state.shorts_generated = False
if 'shorts_list' not in st.session_state:
    st.session_state.shorts_list = []
if 'api_available' not in st.session_state:
    st.session_state.api_available = False

# Initialize Gemini
try:
    GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        st.session_state.api_available = True
except:
    st.session_state.api_available = False

# Free stock footage URLs
FOOTAGE_URLS = [
    "https://assets.mixkit.co/videos/preview/mixkit-mountains-at-sunset-3885-large.mp4",
    "https://assets.mixkit.co/videos/preview/mixkit-waves-crashing-on-the-shore-2765-large.mp4",
    "https://assets.mixkit.co/videos/preview/mixkit-time-lapse-of-nyc-skyline-3860-large.mp4",
    "https://assets.mixkit.co/videos/preview/mixkit-forest-trees-3297-large.mp4",
    "https://assets.mixkit.co/videos/preview/mixkit-young-woman-running-in-nature-3280-large.mp4",
    "https://assets.mixkit.co/videos/preview/mixkit-man-reaching-mountain-peak-4056-large.mp4",
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

def generate_ai_topic():
    if not st.session_state.api_available:
        return random.choice(FALLBACK_TOPICS)
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = """Generate ONE unique motivational topic for a YouTube Short.
Format EXACTLY as:
TITLE: [title under 60 chars]
HOOK: [attention grabbing sentence]
KEYWORDS: [3 keywords]"""
        response = model.generate_content(prompt)
        lines = response.text.strip().split('\n')
        title = lines[0].replace('TITLE:', '').strip() if len(lines) > 0 else "Stay Strong"
        hook = lines[1].replace('HOOK:', '').strip() if len(lines) > 1 else "You can do this"
        keywords = lines[2].replace('KEYWORDS:', '').strip() if len(lines) > 2 else "motivation"
        return {"title": title[:60], "hook": hook[:100], "keywords": keywords}
    except:
        return random.choice(FALLBACK_TOPICS)

def generate_ai_seo(title, hook, keywords, short_num):
    schedule = UPLOAD_SCHEDULE[short_num % len(UPLOAD_SCHEDULE)]
    return {
        "title": f"{title} 🔥"[:70],
        "description": f"{hook}\n\n💪 {title}\n\nSubscribe for daily motivation!\n\n#motivation #{keywords.replace(' ', ' #')}",
        "hashtags": f"#motivation #{keywords.replace(' ', ' #')}",
        "best_time_pkt": schedule['pkt'],
        "best_time_us": schedule['us'],
        "best_type": schedule['type']
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
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
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
        text_height = bbox[3] - bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        for offset_x, offset_y in [(-2,-2), (-2,2), (2,-2), (2,2)]:
            draw.text((x+offset_x, y+offset_y), text, fill=(0,0,0), font=font)
        draw.text((x, y), text, fill=color, font=font)
        
        return np.array(img)
    except:
        return np.zeros((height, width, 4), dtype=np.uint8)

def create_motivational_short(title, hook, short_num):
    """Create a FULL 55-second YouTube Short"""
    
    os.makedirs("shorts", exist_ok=True)
    output_path = f"shorts/short_{short_num:03d}.mp4"
    temp_video = f"temp_{short_num}.mp4"
    
    # 55 seconds is the optimal Short length
    duration = 55
    
    video_clip = None
    for footage_url in random.sample(FOOTAGE_URLS, len(FOOTAGE_URLS)):
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
                
                # Loop if footage is shorter than 55 seconds
                if video_clip.duration < duration:
                    loops = int(duration / video_clip.duration) + 1
                    video_clip = concatenate_videoclips([video_clip] * loops).subclip(0, duration)
                break
            except:
                if os.path.exists(temp_video):
                    os.remove(temp_video)
                continue
    
    if video_clip is None:
        from moviepy.video.VideoClip import ColorClip
        video_clip = ColorClip(size=(1080, 1920), color=(20, 20, 40), duration=duration)
    
    try:
        title_img = create_text_image(title, 65, (255, 255, 255))
        title_clip = ImageClip(title_img, transparent=True, duration=duration).set_position(('center', 200))
        
        hook_img = create_text_image(hook, 45, (255, 75, 75))
        hook_clip = ImageClip(hook_img, transparent=True, duration=duration).set_position(('center', 500))
        
        cta_text = "Subscribe 🔔 Daily Motivation"
        cta_img = create_text_image(cta_text, 40, (255, 255, 255))
        cta_clip = ImageClip(cta_img, transparent=True, duration=duration).set_position(('center', 1700))
        
        final = CompositeVideoClip([video_clip, title_clip, hook_clip, cta_clip])
    except:
        final = video_clip
    
    final.write_videofile(
        output_path,
        fps=24,
        codec='libx264',
        threads=2,
        preset='fast',
        bitrate='1500k',
        logger=None,
        verbose=False
    )
    
    if os.path.exists(temp_video):
        os.remove(temp_video)
    
    return output_path

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    st.divider()
    if st.session_state.api_available:
        st.success("✅ Gemini AI Connected")
    else:
        st.warning("⚠️ Add Gemini API Key to Secrets")
    
    st.divider()
    st.header("🌍 Best Upload Times (PKT)")
    for s in UPLOAD_SCHEDULE[:5]:
        st.markdown(f"**{s['pkt']}** → {s['us']} ({s['type']})")
    
    st.divider()
    if st.button("🗑️ DELETE ALL VIDEOS"):
        if os.path.exists("shorts"):
            shutil.rmtree("shorts")
            os.makedirs("shorts", exist_ok=True)
        st.session_state.shorts_generated = False
        st.session_state.shorts_list = []
        st.rerun()

# Main content
if not st.session_state.shorts_generated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔥 GENERATE 5 SHORTS (55 sec each)", type="primary"):
            with st.spinner("Creating 5 motivational shorts... 4-5 minutes"):
                
                if os.path.exists("shorts"):
                    shutil.rmtree("shorts")
                os.makedirs("shorts", exist_ok=True)
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                shorts_data = []
                
                for i in range(5):
                    status_text.text(f"Generating Short {i+1}/5...")
                    
                    topic = generate_ai_topic()
                    seo = generate_ai_seo(topic['title'], topic['hook'], topic['keywords'], i)
                    video_path = create_motivational_short(topic['title'], topic['hook'], i+1)
                    
                    with open(video_path, 'rb') as f:
                        video_bytes = f.read()
                    
                    shorts_data.append({
                        "num": i+1,
                        "topic": topic,
                        "video_bytes": video_bytes,
                        "seo": seo,
                        "path": video_path
                    })
                    
                    progress_bar.progress((i + 1) / 5)
                
                status_text.text("✅ All 5 shorts created!")
                st.session_state.shorts_list = shorts_data
                st.session_state.shorts_generated = True
                st.rerun()

# Display generated shorts
if st.session_state.shorts_generated:
    st.success(f"✅ {len(st.session_state.shorts_list)} shorts ready! Each is 55 seconds.")
    
    for short in st.session_state.shorts_list:
        with st.expander(f"🎬 Short #{short['num']}: {short['topic']['title'][:40]}...", expanded=True):
            st.video(short['video_bytes'])
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.download_button(
                    label=f"📥 Download Video",
                    data=short['video_bytes'],
                    file_name=f"motivation_short_{short['num']:03d}.mp4",
                    mime="video/mp4",
                    key=f"download_{short['num']}"
                )
            with col2:
                if st.button(f"🗑️ Delete", key=f"delete_{short['num']}"):
                    if os.path.exists(short['path']):
                        os.remove(short['path'])
                    st.session_state.shorts_list = [s for s in st.session_state.shorts_list if s['num'] != short['num']]
                    st.rerun()
            
            st.markdown("---")
            st.markdown("### 📋 Copy-Paste SEO")
            
            st.markdown("**🎯 Title:**")
            st.code(short['seo']['title'], language='text')
            
            st.markdown("**📝 Description:**")
            st.code(short['seo']['description'], language='text')
            
            st.markdown("**#️⃣ Hashtags:**")
            st.code(short['seo']['hashtags'], language='text')
            
            st.info(f"⏰ Upload at: {short['seo']['best_time_pkt']} PKT ({short['seo']['best_time_us']}) for best reach")
    
    st.divider()
    if st.button("🔄 GENERATE NEW BATCH"):
        st.session_state.shorts_generated = False
        st.session_state.shorts_list = []
        st.rerun()

st.divider()
st.markdown("""
---
### 📱 YouTube Shorts Length Guide

| Duration | Type | Best For |
| :--- | :--- | :--- |
| **55 seconds** | ✅ Standard Short | Maximum engagement & reach |
| 15-60 seconds | ✅ Valid Short | YouTube Shorts feed |
| Over 60 seconds | ❌ Regular Video | Different algorithm |

**This app creates FULL 55-second YouTube Shorts - ready to upload!**

Get Gemini API key: [aistudio.google.com](https://aistudio.google.com/)
""")
