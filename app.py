import yt_dlp
import gradio as gr
import os
import base64

# ── Global progress state ──────────────────────────────────────
_progress = {"pct": 0, "speed": "", "eta": "", "phase": "idle"}

def _hook(d):
    if d["status"] == "downloading":
        raw = d.get("_percent_str", "0%").strip()
        for code in ["\x1b[0;94m", "\x1b[0m", "\x1b[0;32m", "\x1b[0;33m"]:
            raw = raw.replace(code, "")
        raw = raw.replace("%", "").strip()
        try:    pct = float(raw)
        except: pct = _progress["pct"]
        _progress.update({
            "pct":   min(pct, 98),
            "speed": d.get("_speed_str", "—").strip(),
            "eta":   d.get("_eta_str",   "—").strip(),
            "phase": "downloading",
        })
    elif d["status"] == "finished":
        _progress.update({"pct": 99, "phase": "merging", "speed": "", "eta": ""})


def _bar_html(pct, speed="", eta="", phase="idle"):
    if phase == "idle":
        return "<p style='color:rgba(255,255,255,0.13);font-family:Outfit,sans-serif;font-size:13px;font-weight:300;margin:0;'>Your file will appear here…</p>"

    color = (
        "linear-gradient(90deg,#6366f1,#818cf8)" if pct < 50 else
        "linear-gradient(90deg,#6366f1,#f59e0b)" if pct < 90 else
        "linear-gradient(90deg,#f59e0b,#22c55e)"
    )
    label = {
        "starting":    "Starting…",
        "downloading": f"Downloading  {speed}  ·  ETA {eta}",
        "merging":     "Merging video + audio…",
        "encoding":    "Preparing download link…",
    }.get(phase, "Processing…")

    return f"""
    <div style='font-family:Outfit,sans-serif;'>
        <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;'>
            <span style='font-size:12px;color:rgba(255,255,255,0.45);'>{label}</span>
            <span style='font-size:13px;font-weight:700;color:#fbbf24;'>{pct:.0f}%</span>
        </div>
        <div style='width:100%;height:8px;background:rgba(255,255,255,0.06);border-radius:99px;overflow:hidden;'>
            <div style='height:100%;width:{pct}%;background:{color};border-radius:99px;
                        transition:width 0.5s ease;box-shadow:0 0 10px rgba(99,102,241,0.4);'></div>
        </div>
        <p style='font-size:11px;color:rgba(255,255,255,0.18);margin-top:8px;'>Please keep this tab open…</p>
    </div>"""


def download_video(url, format_choice):
    global _progress

    if not url.strip():
        return _bar_html(0, phase="idle"), None

    _progress = {"pct": 0, "speed": "", "eta": "", "phase": "starting"}

    output_dir = "/tmp/yt_downloads"
    os.makedirs(output_dir, exist_ok=True)
    for old in os.listdir(output_dir):
        try: os.remove(os.path.join(output_dir, old))
        except: pass

    # ── Flexible format strings with multiple fallbacks ────────
    format_map = {
        "1080p  MP4":  "bestvideo[height<=1080]+bestaudio/bestvideo[height<=1080]/best[height<=1080]/best",
        "4K  MP4":     "bestvideo[height<=2160]+bestaudio/bestvideo[height<=2160]/best[height<=2160]/best",
        "2K  MP4":     "bestvideo[height<=1440]+bestaudio/bestvideo[height<=1440]/best[height<=1440]/best",
        "720p  MP4":   "bestvideo[height<=720]+bestaudio/bestvideo[height<=720]/best[height<=720]/best",
        "480p  MP4":   "bestvideo[height<=480]+bestaudio/bestvideo[height<=480]/best[height<=480]/best",
        "MP3  Audio":  "bestaudio/best",
    }

    is_audio = "MP3" in format_choice
    cookie_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookies.txt")

    ydl_opts = {
        "format": format_map.get(format_choice, "best"),
        "outtmpl": f"{output_dir}/%(title)s.%(ext)s",
        "merge_output_format": "mp4" if not is_audio else None,
        "noplaylist": True,
        "concurrent_fragment_downloads": 8,
        "buffersize": 1024 * 32,
        "http_chunk_size": 10 * 1024 * 1024,
        "retries": 5,
        "fragment_retries": 5,
        "progress_hooks": [_hook],
        "cookiefile": cookie_file,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web", "ios"],
            }
        },
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        },
        "socket_timeout": 30,
        "geo_bypass": True,
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
            _progress["phase"] = "idle"
            return "<p style='color:rgba(239,68,68,0.7);font-size:13px;margin:0;'>⚠ File not found.</p>", None

        filepath     = max(files, key=os.path.getmtime)
        filename     = os.path.basename(filepath)
        file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
        mime_type    = "audio/mpeg" if is_audio else "video/mp4"

        _progress.update({"pct": 99, "phase": "encoding"})

        with open(filepath, "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode()

        _progress["phase"] = "done"

        html = f"""
        <div style='font-family:Outfit,sans-serif;margin-bottom:16px;'>
            <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;'>
                <span style='font-size:12px;color:rgba(255,255,255,0.45);'>Complete ✓</span>
                <span style='font-size:13px;font-weight:700;color:#22c55e;'>100%</span>
            </div>
            <div style='width:100%;height:8px;background:rgba(255,255,255,0.06);border-radius:99px;overflow:hidden;'>
                <div style='height:100%;width:100%;background:linear-gradient(90deg,#22c55e,#16a34a);
                            border-radius:99px;box-shadow:0 0 12px rgba(34,197,94,0.5);'></div>
            </div>
        </div>
        <div style='display:flex;align-items:center;gap:10px;margin-bottom:14px;'>
            <div style='width:28px;height:28px;background:linear-gradient(135deg,#22c55e,#16a34a);border-radius:50%;
                        display:flex;align-items:center;justify-content:center;font-size:13px;color:#fff;
                        box-shadow:0 0 14px rgba(34,197,94,0.55);flex-shrink:0;'>✓</div>
            <div>
                <div style='color:rgba(255,255,255,0.6);font-size:13px;line-height:1.3;'>
                    <strong style='color:#fbbf24;'>{filename[:52]}</strong>
                </div>
                <div style='color:rgba(255,255,255,0.22);font-size:11px;margin-top:2px;'>
                    {file_size_mb:.1f} MB · {format_choice}
                </div>
            </div>
        </div>
        <a id='dl-link' href='data:{mime_type};base64,{b64}' download='{filename}'
           style='display:flex;align-items:center;justify-content:center;gap:10px;width:100%;
                  padding:15px 20px;background:linear-gradient(135deg,#22c55e 0%,#16a34a 100%);
                  border-radius:13px;text-decoration:none;color:#fff;
                  font-family:Outfit,sans-serif;font-size:15px;font-weight:700;
                  box-shadow:0 6px 24px rgba(34,197,94,0.4);cursor:pointer;transition:all 0.2s;'
           onmouseover="this.style.transform='translateY(-2px)';this.style.boxShadow='0 12px 32px rgba(34,197,94,0.55)';"
           onmouseout="this.style.transform='none';this.style.boxShadow='0 6px 24px rgba(34,197,94,0.4)';">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            ⬇ Save File &nbsp;·&nbsp; {file_size_mb:.1f} MB
        </a>
        <script>
        (function tryClick() {{
            var a = document.getElementById('dl-link');
            if (a) {{ a.click(); }}
            else   {{ setTimeout(tryClick, 150); }}
        }})();
        </script>"""

        return html, filepath

    except Exception as e:
        _progress["phase"] = "idle"
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
@keyframes drift{0%{transform:translateY(105vh);opacity:0;}8%{opacity:1;}92%{opacity:.5;}100%{transform:translateY(-60px) translateX(50px);opacity:0;}}
#app-center{position:relative;z-index:2;max-width:680px!important;width:100%!important;margin:0 auto!important;padding:52px 24px 72px!important;display:flex!important;flex-direction:column!important;align-items:center!important;}
#yt-badge{display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:100px;padding:5px 16px 5px 8px;margin-bottom:22px;backdrop-filter:blur(10px);}
#yt-badge .ldot{width:7px;height:7px;background:#22c55e;border-radius:50%;box-shadow:0 0 8px #22c55e;animation:pdot 2s ease-in-out infinite;}
@keyframes pdot{0%,100%{box-shadow:0 0 6px #22c55e;}50%{box-shadow:0 0 14px #22c55e;}}
#yt-badge span{font-size:11px;font-weight:500;color:rgba(255,255,255,0.35);letter-spacing:.5px;}
#yt-headline{text-align:center;margin-bottom:6px;}
#yt-headline h1{font-family:'Outfit',sans-serif;font-size:clamp(48px,7vw,80px);font-weight:900;color:#f8fafc;letter-spacing:-2px;margin:0;line-height:1.05;}
#yt-headline h1 .gw{background:linear-gradient(135deg,#f59e0b 0%,#f97316 45%,#a78bfa 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
#yt-sub{font-size:13px;color:rgba(255,255,255,0.18);font-weight:400;letter-spacing:.8px;margin-bottom:32px;text-align:center;}
#yt-card{width:100%!important;background:rgba(14,17,30,.80)!important;border:1px solid rgba(255,255,255,.08)!important;border-radius:24px!important;padding:28px 28px 26px!important;backdrop-filter:blur(24px)!important;box-shadow:0 0 0 1px rgba(255,255,255,.03) inset,0 24px 60px rgba(0,0,0,.5)!important;position:relative!important;}
#yt-card::before{content:'';position:absolute;top:0;left:12%;right:12%;height:1px;background:linear-gradient(to right,transparent,rgba(255,255,255,.1),transparent);}
.block>label>span,.label-wrap>span{font-family:'Outfit',sans-serif!important;font-size:10px!important;font-weight:600!important;color:rgba(255,255,255,.22)!important;letter-spacing:1.5px!important;text-transform:uppercase!important;display:block!important;margin-bottom:8px!important;}
#url-input textarea,#url-input input{background:rgba(255,255,255,.04)!important;border:1px solid rgba(255,255,255,.09)!important;border-radius:14px!important;color:rgba(255,255,255,.82)!important;font-family:'Outfit',sans-serif!important;font-size:14px!important;font-weight:300!important;padding:15px 20px!important;height:52px!important;transition:all .25s ease!important;outline:none!important;caret-color:#a78bfa!important;box-shadow:none!important;resize:none!important;}
#url-input textarea:focus,#url-input input:focus{border-color:rgba(99,102,241,.5)!important;background:rgba(255,255,255,.06)!important;box-shadow:0 0 0 3px rgba(99,102,241,.08)!important;}
#url-input textarea::placeholder,#url-input input::placeholder{color:rgba(255,255,255,.14)!important;}
#format-radio{width:100%;}
#format-radio .wrap{display:grid!important;grid-template-columns:repeat(3,1fr)!important;gap:8px!important;padding:0!important;}
#format-radio label{background:rgba(255,255,255,.04)!important;border:1px solid rgba(255,255,255,.09)!important;border-radius:12px!important;padding:14px 8px!important;cursor:pointer!important;display:flex!important;flex-direction:column!important;align-items:center!important;justify-content:center!important;transition:all .2s ease!important;text-align:center!important;min-height:52px!important;}
#format-radio label:hover{border-color:rgba(255,255,255,.2)!important;background:rgba(255,255,255,.07)!important;transform:translateY(-1px)!important;}
#format-radio input[type=radio]{display:none!important;}
#format-radio label:has(input:checked){border-color:rgba(245,158,11,.65)!important;background:rgba(245,158,11,.09)!important;box-shadow:0 0 0 1px rgba(245,158,11,.2) inset,0 4px 16px rgba(245,158,11,.12)!important;}
#format-radio span{font-family:'Outfit',sans-serif!important;font-size:13px!important;font-weight:600!important;color:rgba(255,255,255,.75)!important;letter-spacing:0!important;text-transform:none!important;margin:0!important;line-height:1.3!important;}
#format-radio label:has(input:checked) span{color:#fbbf24!important;}
#dl-button button{background:linear-gradient(135deg,#f59e0b 0%,#f97316 50%,#a855f7 100%)!important;background-size:200% 200%!important;border:none!important;border-radius:14px!important;color:#fff!important;font-family:'Outfit',sans-serif!important;font-size:15px!important;font-weight:700!important;height:54px!important;width:100%!important;padding:0!important;cursor:pointer!important;animation:gshift 4s ease infinite!important;box-shadow:0 6px 28px rgba(249,115,22,.28)!important;transition:box-shadow .25s,transform .15s!important;}
@keyframes gshift{0%,100%{background-position:0% 50%;}50%{background-position:100% 50%;}}
#dl-button button:hover{box-shadow:0 10px 40px rgba(249,115,22,.42)!important;transform:translateY(-2px) scale(1.005)!important;}
#dl-button button:active{transform:translateY(0) scale(.998)!important;}
#result-area{background:rgba(255,255,255,.02)!important;border:1px solid rgba(255,255,255,.06)!important;border-radius:14px!important;min-height:70px!important;padding:16px 18px!important;width:100%!important;}
.dvd{height:1px;background:linear-gradient(to right,transparent,rgba(255,255,255,.05),transparent);margin:6px 0 16px;width:100%;}
#fmt-section-label{font-size:10px;font-weight:600;color:rgba(255,255,255,.22);letter-spacing:1.5px;text-transform:uppercase;display:block;margin-bottom:10px;font-family:'Outfit',sans-serif;width:100%;}
@media(max-width:520px){#app-center{padding:32px 16px 48px!important;}#yt-card{padding:20px 14px 18px!important;}#format-radio .wrap{gap:6px!important;}}
@media(max-width:360px){#format-radio .wrap{grid-template-columns:repeat(2,1fr)!important;}}
"""

FORMAT_CHOICES = ["1080p  MP4", "4K  MP4", "2K  MP4", "720p  MP4", "480p  MP4", "MP3  Audio"]

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
                lines=1, max_lines=1,
            )

            gr.HTML('<div class="dvd"></div>')
            gr.HTML('<span id="fmt-section-label">Format &amp; Quality</span>')

            format_choice = gr.Radio(
                choices=FORMAT_CHOICES,
                value="1080p  MP4",
                label=None,
                elem_id="format-radio",
            )

            gr.HTML('<div class="dvd"></div>')
            download_btn = gr.Button("⬇  Download Now", elem_id="dl-button", variant="primary", size="lg")
            gr.HTML('<div class="dvd"></div>')

            result_html = gr.HTML(
                value="<p style='color:rgba(255,255,255,0.13);font-family:Outfit,sans-serif;font-size:13px;font-weight:300;margin:0;'>Your file will appear here…</p>",
                elem_id="result-area",
            )
            file_output = gr.File(visible=False)

    timer = gr.Timer(value=0.8, active=False)

    def tick():
        p = _progress
        if p["phase"] in ("idle", "done"):
            return gr.HTML()
        return gr.HTML(_bar_html(p["pct"], p["speed"], p["eta"], p["phase"]))

    download_btn.click(
        fn=lambda: (_bar_html(0, phase="starting"), gr.Timer(active=True)),
        inputs=[],
        outputs=[result_html, timer],
        queue=False,
    ).then(
        fn=download_video,
        inputs=[url_input, format_choice],
        outputs=[result_html, file_output],
    ).then(
        fn=lambda: gr.Timer(active=False),
        outputs=[timer],
    )

    timer.tick(fn=tick, outputs=[result_html])

port = int(os.environ.get("PORT", 7860))
app.launch(server_name="0.0.0.0", server_port=port)
