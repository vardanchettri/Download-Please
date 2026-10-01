import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import streamlit as st


st.set_page_config(
    page_title="YouTube Downloader",
    page_icon="▶",
    layout="centered",
)


# ============================================================
# LOAD THE NEWEST yt-dlp (nightly)
# YouTube breaks yt-dlp often (e.g. the Aug 2026 android_vr 403 wave).
# Fixes land in the nightly build first, so we install it once per
# server start into a temp folder and import from there.
# ============================================================

NIGHTLY_DIR = Path(tempfile.gettempdir()) / "ytdlp_nightly"


@st.cache_resource(show_spinner="Updating yt-dlp to the latest version...")
def load_latest_ytdlp():
    try:
        marker = NIGHTLY_DIR / ".installed"

        if not marker.exists():
            NIGHTLY_DIR.mkdir(parents=True, exist_ok=True)

            subprocess.run(
                [
                    sys.executable, "-m", "pip", "install",
                    "--upgrade", "--pre", "--quiet",
                    "--disable-pip-version-check",
                    "--target", str(NIGHTLY_DIR),
                    "yt-dlp[default]",
                ],
                check=True,
                timeout=240,
                capture_output=True,
            )

            marker.write_text("ok")

        if str(NIGHTLY_DIR) not in sys.path:
            sys.path.insert(0, str(NIGHTLY_DIR))

        return True

    except Exception:
        # Fall back to the yt-dlp from requirements.txt
        return False


NIGHTLY_OK = load_latest_ytdlp()

if NIGHTLY_OK and str(NIGHTLY_DIR) not in sys.path:
    sys.path.insert(0, str(NIGHTLY_DIR))

import yt_dlp  # noqa: E402

# ============================================================
# UI
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background: #f7f8fa;
    }

    .block-container {
        max-width: 850px;
        padding-top: 3rem;
        padding-bottom: 4rem;
    }

    .main-title {
        text-align: center;
        font-size: 2.6rem;
        font-weight: 750;
        color: #171717;
        letter-spacing: -0.8px;
        margin-bottom: 0.25rem;
    }

    .subtitle {
        text-align: center;
        color: #6b7280;
        font-size: 1rem;
        margin-bottom: 2.5rem;
    }

    label,
    .stRadio label,
    .stSelectbox label,
    .stTextInput label {
        color: #252525 !important;
        font-weight: 600 !important;
    }

    div[data-baseweb="input"] {
        background: #ffffff !important;
        border: 1px solid #d9dce1 !important;
        border-radius: 9px !important;
    }

    div[data-baseweb="input"]:focus-within {
        border-color: #ff3b30 !important;
        box-shadow: 0 0 0 1px #ff3b30 !important;
    }

    div[data-baseweb="input"] input {
        color: #171717 !important;
        background: #ffffff !important;
    }

    div[data-baseweb="input"] input::placeholder {
        color: #9ca3af !important;
    }

    div[data-baseweb="select"] > div {
        background: #ffffff !important;
        border: 1px solid #d9dce1 !important;
        border-radius: 9px !important;
        color: #171717 !important;
    }

    div[data-baseweb="select"] span {
        color: #171717 !important;
    }

    .stRadio > div {
        gap: 1.5rem;
    }

    .stRadio label {
        color: #333333 !important;
    }

    div.stButton > button {
        width: 100%;
        height: 3.2rem;
        background: #ff3b30 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 9px !important;
        font-size: 1rem;
        font-weight: 650;
    }

    div.stButton > button:hover {
        background: #e92f25 !important;
        color: #ffffff !important;
    }

    .info-box {
        padding: 1rem 1.1rem;
        background: #ffffff;
        border: 1px solid #e1e4e8;
        border-radius: 9px;
        color: #6b7280;
        font-size: 0.88rem;
        line-height: 1.5;
        margin-top: 0.5rem;
    }

    div[data-testid="stAlert"] {
        border-radius: 9px !important;
    }

    div[data-testid="stDownloadButton"] button {
        width: 100%;
        background: #171717 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 9px !important;
        height: 3rem;
        font-weight: 600;
    }

    div[data-testid="stDownloadButton"] button:hover {
        background: #333333 !important;
        color: #ffffff !important;
    }

    div[data-testid="stProgress"] > div > div {
        background-color: #ff3b30 !important;
    }

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        background: transparent !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPERS
# ============================================================

MIME_TYPES = {
    ".mp4": "video/mp4",
    ".mkv": "video/x-matroska",
    ".webm": "video/webm",
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
    ".wav": "audio/wav",
}

# YouTube returns 403 for some player clients depending on the server IP
# and the moment. We try several clients one after the other.
CLIENT_STRATEGIES = [
    None,                          # yt-dlp default (nightly picks the best)
    ["tv", "web_safari"],
    ["mweb"],
    ["web_safari"],
    ["ios"],
    ["android"],
]


@st.cache_resource(show_spinner=False)
def find_ffmpeg():
    """Return the path to an ffmpeg binary, or None."""
    path = shutil.which("ffmpeg")
    if path:
        return path

    # Fallback: ffmpeg bundled in the pip package "imageio-ffmpeg"
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def find_js_runtime():
    """yt-dlp needs a JS runtime (deno or node) to solve YouTube challenges."""
    runtimes = {}

    deno = shutil.which("deno")
    if deno:
        runtimes["deno"] = {"path": deno}

    node = shutil.which("node")
    if node:
        runtimes["node"] = {"path": node}

    return runtimes


def build_format_selector(media_type, quality, output_format):
    if media_type == "Audio":
        return "bestaudio/best"

    h = ""
    if quality != "Best available":
        h = f"[height<={int(quality.replace('p', ''))}]"

    if output_format == "MP4":
        return (
            f"bestvideo{h}[ext=mp4]+bestaudio[ext=m4a]/"
            f"bestvideo{h}+bestaudio/"
            f"best{h}[ext=mp4]/"
            f"best{h}/best"
        )

    if output_format == "WEBM":
        return (
            f"bestvideo{h}[ext=webm]+bestaudio[ext=webm]/"
            f"bestvideo{h}+bestaudio/"
            f"best{h}[ext=webm]/"
            f"best{h}/best"
        )

    return f"bestvideo{h}+bestaudio/best{h}/best"


def build_ydl_opts(
    *,
    media_type,
    quality,
    output_format,
    audio_format,
    temp_dir,
    ffmpeg_path,
    cookies_path,
    clients,
    progress_hook,
):
    opts = {
        "format": build_format_selector(media_type, quality, output_format),
        "outtmpl": os.path.join(temp_dir, "%(title).150B [%(id)s].%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "restrictfilenames": True,
        "windowsfilenames": True,
        "overwrites": True,
        "progress_hooks": [progress_hook],
        # Network robustness (helps against 403 / throttling)
        "retries": 10,
        "fragment_retries": 10,
        "file_access_retries": 5,
        "extractor_retries": 3,
        "socket_timeout": 30,
        "concurrent_fragment_downloads": 4,
        "http_chunk_size": 10 * 1024 * 1024,
        "geo_bypass": True,
        "nocheckcertificate": False,
        # Let yt-dlp fetch the YouTube challenge solver if it is missing
        "remote_components": ["ejs:github"],
    }

    js_runtimes = find_js_runtime()
    if js_runtimes:
        opts["js_runtimes"] = js_runtimes

    if ffmpeg_path:
        opts["ffmpeg_location"] = ffmpeg_path

    if cookies_path:
        opts["cookiefile"] = cookies_path

    if clients:
        opts["extractor_args"] = {"youtube": {"player_client": clients}}

    if media_type == "Video":
        opts["merge_output_format"] = output_format.lower()
    else:
        opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": audio_format.lower(),
                "preferredquality": "192",
            }
        ]

    return opts


def clear_dir(path):
    for p in Path(path).iterdir():
        try:
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
            else:
                p.unlink()
        except Exception:
            pass


def pick_output_file(temp_dir, wanted_ext):
    files = [
        p
        for p in Path(temp_dir).iterdir()
        if p.is_file()
        and not p.name.endswith((".part", ".ytdl", ".temp", ".txt"))
        and p.stat().st_size > 0
    ]

    if not files:
        return None

    preferred = [p for p in files if p.suffix.lower() == wanted_ext]
    pool = preferred or files
    return max(pool, key=lambda p: p.stat().st_size)


def friendly_error(message):
    low = message.lower()

    if "ffmpeg" in low or "ffprobe" in low:
        return (
            "ffmpeg is not available on the server.\n\n"
            "Make sure packages.txt contains the line 'ffmpeg' "
            "and requirements.txt contains 'imageio-ffmpeg', "
            "then reboot the app."
        )

    if "sign in to confirm" in low or "not a bot" in low:
        return (
            "YouTube is asking this server to prove it is not a bot "
            "(this happens a lot on cloud hosting IPs).\n\n"
            "Fix: upload a cookies.txt file in the 'Advanced' section "
            "above and try again."
        )

    if "403" in low or "forbidden" in low:
        return (
            "YouTube refused the download (HTTP 403) with every method "
            "that was tried.\n\n"
            "Fixes: reboot the app (it re-installs the newest yt-dlp "
            "on start), or upload a cookies.txt file in the 'Advanced' "
            "section."
        )

    if "private video" in low or "members-only" in low:
        return "This video is private or members-only."

    if "video unavailable" in low or "not available" in low:
        return "This video is unavailable (removed, private or region-locked)."

    if "unsupported url" in low:
        return "This URL is not supported. Please paste a valid YouTube link."

    return None


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">▶ YouTube Downloader</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    'Download a video or extract its audio with yt-dlp.'
    '</div>',
    unsafe_allow_html=True,
)


# ============================================================
# INPUT
# ============================================================

url = st.text_input(
    "YouTube URL",
    placeholder="https://www.youtube.com/watch?v=...",
)

media_type = st.radio(
    "Download type",
    ["Video", "Audio"],
    horizontal=True,
)


# ============================================================
# OPTIONS
# ============================================================

quality = "Best available"
output_format = "MP4"
audio_format = "MP3"

if media_type == "Video":

    quality = st.selectbox(
        "Video quality",
        [
            "Best available",
            "1080p",
            "720p",
            "480p",
            "360p",
        ],
    )

    output_format = st.selectbox(
        "Video format",
        ["MP4", "MKV", "WEBM"],
    )

else:

    audio_format = st.selectbox(
        "Audio format",
        ["MP3", "M4A", "WAV"],
    )

with st.expander("Advanced (optional)"):
    st.caption(
        f"yt-dlp version: {yt_dlp.version.__version__} "
        f"({'nightly' if NIGHTLY_OK else 'from requirements.txt'})"
    )
    cookies_file = st.file_uploader(
        "cookies.txt (Netscape format)",
        type=["txt"],
        help=(
            "Only needed if YouTube blocks the server with a 403 or "
            "'confirm you're not a bot' error."
        ),
    )


# ============================================================
# NOTICE
# ============================================================

st.markdown(
    '<div class="info-box">'
    'Only download content you are authorized to download and use, '
    'and respect the applicable terms and copyright rules.'
    '</div>',
    unsafe_allow_html=True,
)

st.write("")


# ============================================================
# DOWNLOAD
# ============================================================

if st.button("Download", type="primary"):

    st.session_state.pop("result", None)

    if not url.strip():
        st.error("Please enter a YouTube URL.")
        st.stop()

    ffmpeg_path = find_ffmpeg()

    needs_ffmpeg = media_type == "Audio" or True  # merging also needs it
    if needs_ffmpeg and not ffmpeg_path:
        st.error("ffmpeg was not found on the server.")
        st.code(
            "1) packages.txt  ->  ffmpeg\n"
            "2) requirements.txt  ->  imageio-ffmpeg\n"
            "Then reboot the app."
        )
        st.stop()

    temp_dir = tempfile.mkdtemp(prefix="yt_download_")

    try:
        progress = st.progress(0)
        status = st.empty()

        # Optional cookies
        cookies_path = None
        if cookies_file is not None:
            cookies_dir = tempfile.mkdtemp(prefix="yt_cookies_")
            cookies_path = os.path.join(cookies_dir, "cookies.txt")
            with open(cookies_path, "wb") as cf:
                cf.write(cookies_file.getvalue())
        else:
            cookies_dir = None

        def progress_hook(d):
            try:
                if d.get("status") == "downloading":
                    total = d.get("total_bytes") or d.get(
                        "total_bytes_estimate"
                    )
                    done = d.get("downloaded_bytes") or 0
                    if total:
                        progress.progress(
                            min(85, max(1, int(done / total * 85)))
                        )
                elif d.get("status") == "finished":
                    progress.progress(85)
            except Exception:
                pass

        status.info("Fetching media information...")

        wanted_ext = (
            "." + output_format.lower()
            if media_type == "Video"
            else "." + audio_format.lower()
        )

        downloaded = None
        last_error = None

        for attempt, clients in enumerate(CLIENT_STRATEGIES, start=1):

            clear_dir(temp_dir)

            if attempt > 1:
                status.info(
                    f"Retrying with another method "
                    f"({attempt}/{len(CLIENT_STRATEGIES)})..."
                )
                progress.progress(0)

            ydl_opts = build_ydl_opts(
                media_type=media_type,
                quality=quality,
                output_format=output_format,
                audio_format=audio_format,
                temp_dir=temp_dir,
                ffmpeg_path=ffmpeg_path,
                cookies_path=cookies_path,
                clients=clients,
                progress_hook=progress_hook,
            )

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.extract_info(url.strip(), download=True)

                candidate = pick_output_file(temp_dir, wanted_ext)

                if candidate is None:
                    raise RuntimeError(
                        "yt-dlp finished, but no output file was found."
                    )

                if candidate.stat().st_size < 1024:
                    raise RuntimeError(
                        f"The downloaded file is only "
                        f"{candidate.stat().st_size} bytes."
                    )

                downloaded = candidate
                break

            except Exception as exc:
                last_error = exc
                msg = str(exc).lower()

                # Errors that another client cannot fix
                if any(
                    s in msg
                    for s in (
                        "unsupported url",
                        "private video",
                        "members-only",
                        "video unavailable",
                        "this video has been removed",
                    )
                ):
                    break

        if downloaded is None:
            raise last_error or RuntimeError("Download failed.")

        progress.progress(95)
        status.info("Preparing file...")

        file_size = downloaded.stat().st_size

        with open(downloaded, "rb") as f:
            data = f.read()

        if len(data) != file_size:
            raise RuntimeError("The file changed while being read.")

        progress.progress(100)
        status.success("Download completed.")

        # Keep result in session state so the download button survives reruns
        st.session_state["result"] = {
            "name": downloaded.name,
            "data": data,
            "mime": MIME_TYPES.get(
                downloaded.suffix.lower(), "application/octet-stream"
            ),
            "size": file_size,
        }

    except Exception as exc:

        st.error("Download failed.")

        nice = friendly_error(str(exc))

        if nice:
            st.warning(nice)

        with st.expander("Technical details"):
            st.code(str(exc))

    finally:

        shutil.rmtree(temp_dir, ignore_errors=True)

        try:
            if cookies_dir:
                shutil.rmtree(cookies_dir, ignore_errors=True)
        except NameError:
            pass


# ============================================================
# RESULT (persists after reruns)
# ============================================================

result = st.session_state.get("result")

if result:

    st.download_button(
        label=f"⬇ Save {result['name']}",
        data=result["data"],
        file_name=result["name"],
        mime=result["mime"],
        use_container_width=True,
    )

    st.caption(f"File size: {result['size'] / (1024 * 1024):.2f} MB")
