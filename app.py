import streamlit as st
import requests
import random
import os
import time
from datetime import datetime
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import io
import google.generativeai as genai

# Page config - MUST be first Streamlit command
st.set_page_config(
    page_title="AI Shorts Forge",
    page_icon="🔥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for mobile optimization
st.markdown("""
<style>
    .stButton > button {
        width: 100%;
        background-color: #ff4b4b;
        color: white;
        font-size: 18px;
        font-weight: bold;
        padding: 14px;
        border-radius: 30px;
        margin: 10px 0;
    }
    .stVideo {
        border-radius: 15px;
        margin: 10px 0;
    }
    @media (max-width: 768px) {
        .stMarkdown h1 {
            font-size: 28px;
        }
        .stMarkdown h2 {
            font-size: 22px;
        }
    }
    .upload-time {
        background-color: #2c2c2c;
        border-radius: 10px;
        padding: 10px;
        text-align: center;
        margin: 5px;
    }
    .ai-badge {
        background-color: #ff4b4b;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        display: inline-block;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("🔥 AI Shorts Forge")
st.markdown('<span class="ai-badge">⚡ Powered by Gemini AI</span>', unsafe_allow_html=True)
st.caption("Generate motivational shorts • Fresh content every batch • USA-optimized")

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

# Free stock footage URLs (Mixkit - completely free)
FOOTAGE_URLS = [
    "https://assets.mixkit.co/videos/preview/mixkit-mountains-at-sunset-3885-large.mp4",
    "https://assets.mixkit.co/videos/preview/mixkit-waves-crashing-on-the-shore-2765-large.mp4",
    "https://assets.mixkit.co/videos/preview/mixkit-time-lapse-of-nyc-skyline-3860-large.mp4",
    "https://assets.mixkit.co/videos/preview/mixkit-forest-trees-3297-large.mp4",
    "https://assets.mixkit.co/videos/preview/mixkit-young-woman-running-in-nature-3280-large.mp4",
    "https://assets.mixkit.co/videos/preview/mixkit-man-reaching-mountain-peak-4056-large.mp4",
]

# USA peak upload times (Pakistan Time)
UPLOAD_SCHEDULE = [
    {"pkt": "4:00 PM", "us": "6:00 AM EST", "type": "Morning Motivation", "views": "⭐⭐⭐⭐⭐"},
    {"pkt": "6:00 PM", "us": "8:00 AM EST", "type": "Commute Time", "views": "⭐⭐⭐⭐⭐"},
    {"pkt": "8:00 PM", "us": "10:00 AM EST", "type": "Mid-Morning Break", "views": "⭐⭐⭐⭐"},
    {"pkt": "10:00 PM", "us": "12:00 PM EST", "type": "Lunch Break", "views": "⭐⭐⭐⭐"},
    {"pkt": "12:00 AM", "us": "2:00 PM EST", "type": "Afternoon Slump", "views": "⭐⭐⭐"},
    {"pkt": "2:00 AM", "us": "4:00 PM EST", "type": "End of Work Day", "views": "⭐⭐⭐⭐"},
    {"pkt": "4:00 AM", "us": "6:00 PM EST", "type": "Evening Peak", "views": "⭐⭐⭐⭐⭐"},
    {"pkt": "6:00 AM", "us": "8:00 PM EST", "type": "Prime Time", "views": "⭐⭐⭐⭐⭐"},
    {"pkt": "8:00 AM", "us": "10:00 PM EST", "type": "Late Night", "views": "⭐⭐⭐"},
    {"pkt": "10:00 AM", "us": "12:00 AM EST", "type": "Midnight Scroll", "views": "⭐⭐"}
]

# Fallback topics (if API fails)
FALLBACK_TOPICS = [
    {"title": "Why Everyone Quits Right Before Success", "hook": "You're closer than you think. Don't stop now.", "keywords": "success persistence never give up"},
    {"title": "The 5 AM Secret That Changed My Life", "hook": "What you do before 6am determines everything.", "keywords": "morning routine discipline success"},
]

def generate_ai_topic():
    """Generate a fresh motivational topic using Gemini AI"""
    
    if not st.session_state.api_available:
        return random.choice(FALLBACK_TOPICS)
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = """Generate ONE unique, powerful motivational topic for a 60-second YouTube Short.

Make it fresh and USA-focused. Never repeat common clichés.

Format EXACTLY as:
TITLE: [catchy title under 60 characters]
HOOK: [attention-grabbing first sentence]
KEYWORDS: [3-5 keywords, comma separated]"""
        
        response = model.generate_content(prompt)
        lines = response.text.strip().split('\n')
        
        title = ""
        hook = ""
        keywords = ""
        
        for line in lines:
            if line.startswith('TITLE:'):
                title = line.replace('TITLE:', '').strip()
            elif line.startswith('HOOK:'):
                hook = line.replace('HOOK:', '').strip()
            elif line.startswith('KEYWORDS:'):
                keywords = line.replace('KEYWORDS:', '').strip()
        
        if title and hook and keywords:
            return {"title": title, "hook": hook, "keywords": keywords}
        return random.choice(FALLBACK_TOPICS)
    except:
        return random.choice(FALLBACK_TOPICS)

def generate_ai_script(title, hook):
    """Generate the full script using Gemini"""
    
    if not st.session_state.api_available:
        return f"{hook}\n\nYou are capable of amazing things.\n\nSubscribe for daily motivation."
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""Write a powerful 50-60 second motivational script.
Title: {title}
Hook: {hook}

Requirements: 100-120 words, 6-8 short sentences, emotional tone.
Script:"""
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return f"{hook}\n\nSubscribe for daily motivation."

def generate_ai_seo(title, hook, keywords, short_num):
    """Generate SEO metadata using Gemini"""
    
    if not st.session_state.api_available:
        schedule = UPLOAD_SCHEDULE[short_num % len(UPLOAD_SCHEDULE)]
        return {
            "title": f"{title} 🔥 | Motivational Short"[:70],
            "description": f"{hook}\n\n💪 {title}\n\nSubscribe for daily motivation.\n\n#motivation",
            "hashtags": f"#motivation #{keywords.replace(' ', ' #')}",
            "best_time_pkt": schedule['pkt'],
            "best_time_us": schedule['us'],
            "best_type": schedule['type'],
            "expected_views": schedule['views']
        }
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        schedule = UPLOAD_SCHEDULE[short_num % len(UPLOAD_SCHEDULE)]
        
        prompt = f"""Create SEO metadata for a motivational YouTube Short.
Title: {title}
Hook: {hook}
Keywords: {keywords}

Generate:
TITLE: (under 70 chars)
DESCRIPTION: (200-250 chars with hashtags)
HASHTAGS: (10-12 hashtags)"""
        
        response = model.generate_content(prompt)
        lines = response.text.strip().split('\n')
        
        seo_title = f"{title} 🔥"[:70]
        description = ""
        hashtags = ""
        
        for line in lines:
            if line.startswith('TITLE:'):
                seo_title = line.replace('TITLE:', '').strip()
            elif line.startswith('DESCRIPTION:'):
                description = line.replace('DESCRIPTION:', '').strip()
            elif line.startswith('HASHTAGS:'):
                hashtags = line.replace('HASHTAGS:', '').strip()
        
        return {
            "title": seo_title[:70],
            "description": description[:500],
            "hashtags": hashtags,
            "best_time_pkt": schedule['pkt'],
            "best_time_us": schedule['us'],
            "best_type": schedule['type'],
            "expected_views": schedule['views']
        }
    except:
        schedule = UPLOAD_SCHEDULE[short_num % len(UPLOAD_SCHEDULE)]
        return {
            "title": f"{title} 🔥"[:70],
            "description": f"{hook}\n\nSubscribe for daily motivation.\n\n#motivation",
            "hashtags": "#motivation #success",
            "best_time_pkt": schedule['pkt'],
            "best_time_us": schedule['us'],
            "best_type": schedule['type'],
            "expected_views": schedule['views']
        }

def create_text_image(text, size, color, bg_color=(0,0,0)):
    """Create text overlay using PIL (no ImageMagick needed)"""
    try:
        img = Image.new('RGBA', (1080, 200), bg_color + (0,))  # Transparent background
        draw = ImageDraw.Draw(img)
        
        # Try to use a default font
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
        except:
            font = ImageFont.load_default()
        
        # Calculate text position
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (1080 - text_width) // 2
        y = (200 - text_height) // 2
        
        draw.text((x, y), text, fill=color, font=font)
        
        # Convert to numpy array for MoviePy
        img_array = np.array(img)
        return img_array
    except:
        return None

def create_motivational_short(title, hook, short_num, test_mode=False):
    """Create a single motivational short video"""
    
    os.makedirs("shorts", exist_ok=True)
    output_path = f"shorts/short_{short_num:03d}.mp4"
    temp_video = f"temp_{short_num}.mp4"
    
    duration = 30 if test_mode else 55  # Shorter for testing
    
    try:
        footage_url = random.choice(FOOTAGE_URLS)
        response = requests.get(footage_url, stream=True, timeout=30)
        
        if response.status_code == 200:
            with open(temp_video, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            clip = VideoFileClip(temp_video)
            
            # Crop to vertical 9:16
            if clip.w / clip.h > 9/16:
                clip = clip.resize(height=1920)
                clip = clip.crop(x_center=clip.w/2, y_center=clip.h/2, width=1080, height=1920)
            else:
                clip = clip.resize(width=1080)
                clip = clip.crop(x_center=clip.w/2, y_center=clip.h/2, width=1080, height=1920)
            
            clip = clip.subclip(0, min(duration, clip.duration))
        else:
            clip = ColorClip(size=(1080, 1920), color=(0, 0, 20), duration=duration)
    except:
        clip = ColorClip(size=(1080, 1920), color=(0, 0, 20), duration=duration)
    
    # Create text clips using CompositeVideoClip with PIL images
    # For simplicity, we'll use a cleaner approach - just background with text
    
    # Create text as image clips to avoid ImageMagick
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create title image
        title_img = Image.new('RGBA', (1080, 300), (0, 0, 0, 0))
        draw = ImageDraw.Draw(title_img)
        font_size = 60
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        # Draw title text
        bbox = draw.textbbox((0, 0), title, font=font)
        text_width = bbox[2] - bbox[0]
        x = (1080 - text_width) // 2
        draw.text((x, 100), title, fill=(255, 255, 255), font=font)
        
        # Convert to clip
        title_array = np.array(title_img)
        title_clip = ImageClip(title_array, transparent=True, duration=duration).set_position(('center', 200))
        
        # Create hook image
        hook_img = Image.new('RGBA', (1080, 200), (0, 0, 0, 0))
        draw = ImageDraw.Draw(hook_img)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 42)
        except:
            font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), hook, font=font)
        text_width = bbox[2] - bbox[0]
        x = (1080 - text_width) // 2
        draw.text((x, 50), hook, fill=(255, 75, 75), font=font)
        
        hook_array = np.array(hook_img)
        hook_clip = ImageClip(hook_array, transparent=True, duration=duration).set_position(('center', 450))
        
        # Create CTA image
        cta_img = Image.new('RGBA', (1080, 150), (0, 0, 0, 0))
        draw = ImageDraw.Draw(cta_img)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 38)
        except:
            font = ImageFont.load_default()
        
        cta_text = "Subscribe 🔔 Daily Motivation"
        bbox = draw.textbbox((0, 0), cta_text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (1080 - text_width) // 2
        draw.text((x, 50), cta_text, fill=(255, 255, 255), font=font)
        
        cta_array = np.array(cta_img)
        cta_clip = ImageClip(cta_array, transparent=True, duration=duration).set_position(('center', 1650))
        
        # Combine all clips
        final = CompositeVideoClip([clip, title_clip, hook_clip, cta_clip])
        
    except Exception as e:
        # Ultra simple fallback: just the background
        final = clip
    
    # Export video
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
    
    # Cleanup
    if os.path.exists(temp_video):
        os.remove(temp_video)
    
    return output_path

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Test mode toggle
    test_mode = st.checkbox("🧪 Test Mode (1 short only)", value=False)
    
    if not test_mode:
        num_shorts = st.slider("Number of Shorts", 5, 10, 10)
    else:
        num_shorts = 1
        st.info("Test mode: Only 1 short will be generated (faster)")
    
    st.divider()
    
    if st.session_state.api_available:
        st.success("✅ Gemini AI Connected")
    else:
        st.warning("⚠️ Add Gemini API Key to Secrets")
        st.caption("Get key from aistudio.google.com")
    
    st.divider()
    st.header("🌍 Upload Times (PKT)")
    for s in UPLOAD_SCHEDULE[:3]:
        st.markdown(f"**{s['pkt']}** → {s['us']}")
    
    st.divider()
    st.caption("Made with 🔥 | Pakistan → World")

# Main content
if not st.session_state.shorts_generated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        btn_label = "🧪 TEST GENERATE (1 SHORT)" if test_mode else "🔥 GENERATE SHORTS"
        if st.button(btn_label, type="primary"):
            with st.spinner("Creating your shorts... 1-2 minutes"):
                
                if os.path.exists("shorts"):
                    import shutil
                    shutil.rmtree("shorts")
                os.makedirs("shorts", exist_ok=True)
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                shorts_data = []
                
                for i in range(num_shorts):
                    status_text.text(f"Generating Short {i+1}/{num_shorts}...")
                    
                    topic = generate_ai_topic()
                    seo = generate_ai_seo(topic['title'], topic['hook'], topic['keywords'], i)
                    video_path = create_motivational_short(topic['title'], topic['hook'], i+1, test_mode)
                    
                    with open(video_path, 'rb') as f:
                        video_bytes = f.read()
                    
                    shorts_data.append({
                        "num": i+1,
                        "topic": topic,
                        "video_bytes": video_bytes,
                        "seo": seo
                    })
                    
                    progress_bar.progress((i + 1) / num_shorts)
                
                status_text.text("✅ All shorts created!")
                st.session_state.shorts_list = shorts_data
                st.session_state.shorts_generated = True
                time.sleep(1)
                st.rerun()

# Display results
if st.session_state.shorts_generated:
    st.success(f"✅ {len(st.session_state.shorts_list)} short(s) ready!")
    
    for short in st.session_state.shorts_list:
        with st.expander(f"🎬 Short #{short['num']}: {short['topic']['title'][:50]}...", expanded=True):
            st.video(short['video_bytes'])
            
            st.download_button(
                label=f"📥 Download Short #{short['num']}",
                data=short['video_bytes'],
                file_name=f"motivation_short_{short['num']:03d}.mp4",
                mime="video/mp4",
                key=f"download_{short['num']}"
            )
            
            st.markdown("---")
            st.markdown("### 📋 Copy-Paste SEO")
            
            st.markdown("**🎯 Title:**")
            st.code(short['seo']['title'], language='text')
            
            st.markdown("**📝 Description:**")
            st.code(short['seo']['description'], language='text')
            
            st.markdown("**#️⃣ Hashtags:**")
            st.code(short['seo']['hashtags'], language='text')
            
            st.info(f"⏰ Best upload time: {short['seo']['best_time_pkt']} PKT ({short['seo']['best_time_us']})")
    
    st.divider()
    if st.button("🔄 GENERATE NEW BATCH"):
        st.session_state.shorts_generated = False
        st.session_state.shorts_list = []
        st.rerun()

# Footer
st.divider()
st.markdown("""
---
### 🚀 Quick Start

1. **Test Mode** (checkbox in sidebar) - generates 1 short in 1-2 minutes
2. **Full Mode** - generates 10 shorts in 3-4 minutes
3. **Download** each video to your phone
4. **Copy SEO** (title, description, hashtags)
5. **Upload to YouTube Shorts** at suggested Pakistan times

**Get Gemini API key:** [aistudio.google.com](https://aistudio.google.com/)
""")
