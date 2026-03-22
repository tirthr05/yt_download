import yt_dlp
import gradio as gr
import os
import base64

def download_video(url, format_choice):
    if not url.strip():
        return """<p style='color:rgba(239,68,68,0.7);font-family:Outfit,sans-serif;font-size:13px;font-weight:400;margin:0;'>⚠ Please enter a YouTube URL</p>""", None

    output_dir = "/tmp/downloads"
    os.makedirs(output_dir, exist_ok=True)
    for old in os.listdir(output_dir):
        try: os.remove(os.path.join(output_dir, old))
        except: pass

    format_map = {
        "1080p  MP4":  "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]",
        "4K  MP4":     "bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/best[height<=2160]",
        "2K  MP4":     "bestvideo[height<=1440][ext=mp4]+bestaudio[ext=m4a]/best[height<=1440]",
        "720p  MP4":   "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]",
        "480p  MP4":   "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]",
        "MP3  Audio":  "bestaudio/best",
    }

    selected_format = format_map.get(format_choice, "best")
    is_audio = "MP3" in format_choice

    ydl_opts = {
        "format": selected_format,
        "outtmpl": f"{output_dir}/%(title)s.%(ext)s",
        "merge_output_format": "mp4" if not is_audio else None,
        "noplaylist": True,
        "concurrent_fragment_downloads": 4,
        "buffersize": 1024 * 16,
        "retries": 3,
        "fragment_retries": 3,
        "http_chunk_size": 10485760,
    }

    if is_audio:
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "320",
        }]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)

        files = [os.path.join(output_dir, f) for f in os.listdir(output_dir)
                 if os.path.isfile(os.path.join(output_dir, f))]
        if not files:
            return "<p style='color:rgba(239,68,68,0.7);font-size:13px;margin:0;'>⚠ File not found after download.</p>", None

        filepath = max(files, key=os.path.getmtime)
        filename = os.path.basename(filepath)
        file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
        mime_type = "audio/mpeg" if is_audio else "video/mp4"

        with open(filepath, "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode()

        html = f"""
        <div style='display:flex;align-items:center;gap:10px;font-family:Outfit,sans-serif;margin-bottom:14px;'>
            <div style='width:24px;height:24px;background:linear-gradient(135deg,#22c55e,#16a34a);border-radius:50%;
                        display:flex;align-items:center;justify-content:center;font-size:12px;color:#fff;
                        box-shadow:0 0 14px rgba(34,197,94,0.55);flex-shrink:0;'>✓</div>
            <div>
                <div style='color:rgba(255,255,255,0.55);font-size:13px;line-height:1.3;'>
                    Ready — <strong style='color:#fbbf24;'>{filename[:55]}</strong>
                </div>
                <div style='color:rgba(255,255,255,0.22);font-size:11px;margin-top:2px;'>{file_size_mb:.1f} MB</div>
            </div>
        </div>
        <a id='dl-link' href='data:{mime_type};base64,{b64}' download='{filename}'
           style='display:flex;align-items:center;justify-content:center;gap:10px;width:100%;
                  padding:14px 20px;background:linear-gradient(135deg,#22c55e 0%,#16a34a 100%);
                  border-radius:13px;text-decoration:none;color:#fff;font-family:Outfit,sans-serif;
                  font-size:15px;font-weight:700;box-shadow:0 6px 24px rgba(34,197,94,0.35);cursor:pointer;'>
            ⬇ Save File &nbsp;·&nbsp; {file_size_mb:.1f} MB
        </a>
        <script>setTimeout(function(){{var a=document.getElementById('dl-link');if(a)a.click();}},400);</script>
        """
        return html, filepath

    except Exception as e:
        return f"<p style='color:rgba(239,68,68,0.8);font-size:13px;margin:0;'>❌ {str(e)}</p>", None


css = """
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&display=swap');
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
html,body{background:#080b14!important;font-family:'Outfit',sans-serif!important;min-height:100vh;}
.gradio-container{background:#080b14!important;max-width:100%!important;width:100%!important;min-height:100vh!important;padding:0!important;margin:0!important;font-family:'Outfit',sans-serif!important;}
.gradio-container>.main{background:transparent!important;padding:0!important;}
.gradio-container>.main>.wrap{padding:0!important;background:transparent!important;}
footer{display:none!important;}
.block,.panel,.form{background:transparent!important;border:none!important;box-shadow:none!important;padding:0!important;}
.gap{gap:14px!important;}

/* Background */
#page-bg{position:fixed;inset:0;z-index:0;pointer-events:none;
  background:radial-gradient(ellipse 80% 60% at 50% 0%,rgba(99,102,241,0.15) 0%,transparent 60%),
             radial-gradient(ellipse 50% 40% at 85% 85%,rgba(245,158,11,0.08) 0%,transparent 55%),
             linear-gradient(160deg,#080b14 0%,#0c1020 60%,#080b14 100%);}
#page-bg::before{content:'';position:absolute;width:700px;height:700px;border-radius:50%;
  background:radial-gradient(circle,rgba(99,102,241,0.05) 0%,transparent 70%);
  top:-200px;left:-150px;animation:floatOrb 20s ease-in-out infinite;}
#page-bg::after{content:'';position:absolute;width:500px;height:500px;border-radius:50%;
  background:radial-gradient(circle,rgba(245,158,11,0.05) 0%,transparent 70%);
  bottom:-150px;right:-100px;animation:floatOrb 25s ease-in-out infinite reverse;}
@keyframes floatOrb{0%,100%{transform:translate(0,0) scale(1);}33%{transform:translate(40px,-30px) scale(1.06);}66%{transform:translate(-20px,20px) scale(0.96);}}
.pt{position:fixed;border-radius:50%;pointer-events:none;animation:drift linear infinite;opacity:0;z-index:1;}
@keyframes drift{0%{transform:translateY(105vh);opacity:0;}8%{opacity:1;}92%{opacity:0.5;}100%{transform:translateY(-60px) translateX(50px);opacity:0;}}

/* Layout */
#app-center{position:relative;z-index:2;max-width:680px!important;width:100%!important;margin:0 auto!important;padding:52px 24px 72px!important;display:flex!important;flex-direction:column!important;align-items:center!important;}

/* Badge */
#yt-badge{display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:100px;padding:5px 16px 5px 8px;margin-bottom:22px;backdrop-filter:blur(10px);}
#yt-badge .ldot{width:7px;height:7px;background:#22c55e;border-radius:50%;box-shadow:0 0 8px #22c55e;animation:pdot 2s ease-in-out infinite;}
@keyframes pdot{0%,100%{box-shadow:0 0 6px #22c55e;}50%{box-shadow:0 0 14px #22c55e;}}
#yt-badge span{font-size:11px;font-weight:500;color:rgba(255,255,255,0.35);letter-spacing:0.5px;}

/* Headline */
#yt-headline{text-align:center;margin-bottom:6px;}
#yt-headline h1{font-family:'Outfit',sans-serif;font-size:clamp(48px,7vw,80px);font-weight:900;color:#f8fafc;letter-spacing:-2px;margin:0;line-height:1.05;}
#yt-headline h1 .gw{background:linear-gradient(135deg,#f59e0b 0%,#f97316 45%,#a78bfa 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
#yt-sub{font-size:13px;color:rgba(255,255,255,0.18);font-weight:400;letter-spacing:0.8px;margin-bottom:32px;text-align:center;}

/* Card */
#yt-card{width:100%!important;background:rgba(14,17,30,0.80)!important;border:1px solid rgba(255,255,255,0.08)!important;border-radius:24px!important;padding:28px 28px 26px!important;backdrop-filter:blur(24px)!important;box-shadow:0 0 0 1px rgba(255,255,255,0.03) inset,0 24px 60px rgba(0,0,0,0.5)!important;position:relative!important;}
#yt-card::before{content:'';position:absolute;top:0;left:12%;right:12%;height:1px;background:linear-gradient(to right,transparent,rgba(255,255,255,0.1),transparent);}

/* URL input */
.block>label>span,.label-wrap>span{font-family:'Outfit',sans-serif!important;font-size:10px!important;font-weight:600!important;color:rgba(255,255,255,0.22)!important;letter-spacing:1.5px!important;text-transform:uppercase!important;display:block!important;margin-bottom:8px!important;}
#url-input textarea,#url-input input{background:rgba(255,255,255,0.04)!important;border:1px solid rgba(255,255,255,0.09)!important;border-radius:14px!important;color:rgba(255,255,255,0.82)!important;font-family:'Outfit',sans-serif!important;font-size:14px!important;font-weight:300!important;padding:15px 20px!important;height:52px!important;transition:all 0.25s ease!important;outline:none!important;caret-color:#a78bfa!important;box-shadow:none!important;resize:none!important;}
#url-input textarea:focus,#url-input input:focus{border-color:rgba(99,102,241,0.5)!important;background:rgba(255,255,255,0.06)!important;box-shadow:0 0 0 3px rgba(99,102,241,0.08)!important;}
#url-input textarea::placeholder,#url-input input::placeholder{color:rgba(255,255,255,0.14)!important;}

/* ── FORMAT RADIO — styled as grid buttons ── */
#format-radio{width:100%;}
#format-radio .wrap{display:grid!important;grid-template-columns:repeat(3,1fr)!important;gap:8px!important;padding:0!important;}
#format-radio label{
  background:rgba(255,255,255,0.04)!important;
  border:1px solid rgba(255,255,255,0.09)!important;
  border-radius:12px!important;
  padding:12px 8px 11px!important;
  cursor:pointer!important;
  display:flex!important;
  flex-direction:column!important;
  align-items:center!important;
  justify-content:center!important;
  gap:3px!important;
  transition:all 0.2s ease!important;
  text-align:center!important;
  min-height:64px!important;
}
#format-radio label:hover{border-color:rgba(255,255,255,0.2)!important;background:rgba(255,255,255,0.07)!important;transform:translateY(-1px)!important;}
/* Hide the actual radio dot */
#format-radio input[type=radio]{display:none!important;}
/* Selected state */
#format-radio label:has(input:checked){
  border-color:rgba(245,158,11,0.65)!important;
  background:rgba(245,158,11,0.09)!important;
  box-shadow:0 0 0 1px rgba(245,158,11,0.2) inset,0 4px 16px rgba(245,158,11,0.12)!important;
}
/* Label text */
#format-radio .svelte-s1r2yt,
#format-radio span{
  font-family:'Outfit',sans-serif!important;
  font-size:13px!important;
  font-weight:600!important;
  color:rgba(255,255,255,0.75)!important;
  letter-spacing:0!important;
  text-transform:none!important;
  margin:0!important;
  line-height:1.2!important;
}
#format-radio label:has(input:checked) span{color:#fbbf24!important;}

/* Download button */
#dl-button button{background:linear-gradient(135deg,#f59e0b 0%,#f97316 50%,#a855f7 100%)!important;background-size:200% 200%!important;border:none!important;border-radius:14px!important;color:#fff!important;font-family:'Outfit',sans-serif!important;font-size:15px!important;font-weight:700!important;height:54px!important;width:100%!important;padding:0!important;cursor:pointer!important;animation:gshift 4s ease infinite!important;box-shadow:0 6px 28px rgba(249,115,22,0.28)!important;transition:box-shadow 0.25s,transform 0.15s!important;}
@keyframes gshift{0%,100%{background-position:0% 50%;}50%{background-position:100% 50%;}}
#dl-button button:hover{box-shadow:0 10px 40px rgba(249,115,22,0.42)!important;transform:translateY(-2px) scale(1.005)!important;}
#dl-button button:active{transform:translateY(0) scale(0.998)!important;}

/* Result area */
#result-area{background:rgba(255,255,255,0.02)!important;border:1px solid rgba(255,255,255,0.06)!important;border-radius:14px!important;min-height:52px!important;padding:14px 18px!important;width:100%!important;}
.dvd{height:1px;background:linear-gradient(to right,transparent,rgba(255,255,255,0.05),transparent);margin:6px 0 16px;width:100%;}

/* Format section label */
#fmt-section-label{font-size:10px;font-weight:600;color:rgba(255,255,255,0.22);letter-spacing:1.5px;text-transform:uppercase;display:block;margin-bottom:10px;font-family:'Outfit',sans-serif;width:100%;}

@media(max-width:520px){#app-center{padding:32px 16px 48px!important;}#yt-card{padding:20px 14px 18px!important;}#format-radio .wrap{gap:6px!important;}}
@media(max-width:360px){#format-radio .wrap{grid-template-columns:repeat(2,1fr)!important;}}
"""

FORMAT_CHOICES = [
    "1080p  MP4",
    "4K  MP4",
    "2K  MP4",
    "720p  MP4",
    "480p  MP4",
    "MP3  Audio",
]

with gr.Blocks(css=css, title="YT Downloader") as app:

    gr.HTML("""
    <div id="page-bg"></div>
    <div class="pt" style="width:3px;height:3px;background:#a78bfa;left:14%;animation-duration:13s;animation-delay:0s;"></div>
    <div class="pt" style="width:2px;height:2px;background:#f59e0b;left:32%;animation-duration:17s;animation-delay:2s;"></div>
    <div class="pt" style="width:3px;height:3px;background:#6366f1;left:58%;animation-duration:11s;animation-delay:5s;"></div>
    <div class="pt" style="width:2px;height:2px;background:#fbbf24;left:74%;animation-duration:15s;animation-delay:1s;"></div>
    <div class="pt" style="width:3px;height:3px;background:#8b5cf6;left:90%;animation-duration:19s;animation-delay:3s;"></div>
    """)

    with gr.Column(elem_id="app-center"):

        gr.HTML("""
            <div id="yt-badge"><div class="ldot"></div>
            <span>Free &nbsp;·&nbsp; No limits &nbsp;·&nbsp; Up to 4K &nbsp;·&nbsp; Instant</span></div>
            <div id="yt-headline"><h1>Download <span class="gw">anything.</span></h1></div>
            <p id="yt-sub">Paste · Choose · Done</p>
        """)

        with gr.Column(elem_id="yt-card"):

            url_input = gr.Textbox(
                placeholder="Paste YouTube URL here…",
                label="Video URL",
                elem_id="url-input",
                lines=1,
                max_lines=1,
            )

            gr.HTML('<div class="dvd"></div>')
            gr.HTML('<span id="fmt-section-label">Format &amp; Quality</span>')

            # ✅ Real Gradio Radio — value is reliably sent to Python
            format_choice = gr.Radio(
                choices=FORMAT_CHOICES,
                value="1080p  MP4",
                label="",
                elem_id="format-radio",
            )

            gr.HTML('<div class="dvd"></div>')

            download_btn = gr.Button(
                "⬇  Download Now",
                elem_id="dl-button",
                variant="primary",
                size="lg",
            )

            gr.HTML('<div class="dvd"></div>')

            result_html = gr.HTML(
                value="<p style='color:rgba(255,255,255,0.13);font-family:Outfit,sans-serif;font-size:13px;font-weight:300;margin:0;'>Your file will appear here…</p>",
                elem_id="result-area",
            )

            file_output = gr.File(visible=False)

    download_btn.click(
        fn=download_video,
        inputs=[url_input, format_choice],
        outputs=[result_html, file_output],
    )

app.launch()
