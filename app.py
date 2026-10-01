import os
import shutil
import tempfile
from pathlib import Path

import streamlit as st
import yt_dlp


st.set_page_config(
    page_title="YouTube Downloader",
    page_icon="▶",
    layout="centered",
)

# ---------- Clean light UI ----------
st.markdown(
    """
    <style>

    /* =====================================================
       MAIN PAGE
       ===================================================== */

    .stApp {
        background: #f7f8fa;
    }

    .block-container {
        max-width: 850px;
        padding-top: 3rem;
        padding-bottom: 4rem;
    }


    /* =====================================================
       TITLE
       ===================================================== */

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


    /* =====================================================
       LABELS
       ===================================================== */

    label,
    .stRadio label,
    .stSelectbox label,
    .stTextInput label {
        color: #252525 !important;
        font-weight: 600 !important;
    }


    /* =====================================================
       TEXT INPUT
       ===================================================== */

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


    /* =====================================================
       DROPDOWN
       ===================================================== */

    div[data-baseweb="select"] > div {
        background: #ffffff !important;
        border: 1px solid #d9dce1 !important;
        border-radius: 9px !important;
        color: #171717 !important;
    }

    div[data-baseweb="select"] span {
        color: #171717 !important;
    }


    /* =====================================================
       RADIO BUTTONS
       ===================================================== */

    .stRadio > div {
        gap: 1.5rem;
    }

    .stRadio label {
        color: #333333 !important;
    }


    /* =====================================================
       DOWNLOAD BUTTON
       ===================================================== */

    div.stButton > button {
        width: 100%;
        height: 3.2rem;

        background: #ff3b30 !important;
        color: #ffffff !important;

        border: none !important;
        border-radius: 9px !important;

        font-size: 1rem;
        font-weight: 650;

        transition: all 0.15s ease;
    }

    div.stButton > button:hover {
        background: #e92f25 !important;
        color: #ffffff !important;
        border: none !important;
    }

    div.stButton > button:active {
        transform: scale(0.99);
    }


    /* =====================================================
       INFORMATION BOX
       ===================================================== */

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


    /* =====================================================
       SUCCESS / ERROR / STATUS
       ===================================================== */

    div[data-testid="stAlert"] {
        border-radius: 9px !important;
    }


    /* =====================================================
       DOWNLOAD FILE BUTTON
       ===================================================== */

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


    /* =====================================================
       PROGRESS BAR
       ===================================================== */

    div[data-testid="stProgress"] > div > div {
        background-color: #ff3b30 !important;
    }


    /* =====================================================
       REMOVE EXCESS STREAMLIT DECORATION
       ===================================================== */

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

st.markdown('<div class="main-title">▶ YouTube Downloader</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Download a video or extract its audio with yt-dlp.</div>',
    unsafe_allow_html=True,
)

url = st.text_input(
    "YouTube URL",
    placeholder="https://www.youtube.com/watch?v=...",
)

media_type = st.radio(
    "Download type",
    ["Video", "Audio"],
    horizontal=True,
)

if media_type == "Video":
    quality = st.selectbox(
        "Video quality",
        ["Best available", "1080p", "720p", "480p", "360p"],
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

st.markdown(
    '<div class="info-box">Only download content you are authorized to download '
    'and use, and respect the applicable terms and copyright rules.</div>',
    unsafe_allow_html=True,
)

st.write("")

if st.button("Download", type="primary"):
    if not url.strip():
        st.error("Please enter a YouTube URL.")
        st.stop()

    # Temporary directory: files are removed after the user downloads them
    temp_dir = tempfile.mkdtemp(prefix="yt_download_")
    output_template = os.path.join(temp_dir, "%(title).180s.%(ext)s")

    try:
        progress = st.progress(0)
        status = st.empty()

        if media_type == "Video":
            if quality == "Best available":
                height_filter = None
            else:
                height_filter = int(quality.replace("p", ""))

            if height_filter:
                format_selector = (
                    f"bestvideo[height<={height_filter}]+bestaudio/"
                    f"best[height<={height_filter}]"
                )
            else:
                format_selector = "bestvideo+bestaudio/best"

            merge_format = output_format.lower()

            ydl_opts = {
                "format": format_selector,
                "merge_output_format": merge_format,
                "outtmpl": output_template,
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,
                "restrictfilenames": False,
            }

        else:
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": output_template,
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,
                "restrictfilenames": False,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": audio_format.lower(),
                        "preferredquality": "192",
                    }
                ],
            }

        status.info("Fetching media information...")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        files = [
            p for p in Path(temp_dir).iterdir()
            if p.is_file() and not p.name.endswith((".part", ".ytdl"))
        ]

        if not files:
            raise RuntimeError(
                "The download completed but no output file was found. "
                "The selected format may not be available."
            )

        downloaded = max(files, key=lambda p: p.stat().st_mtime)

        progress.progress(100)
        status.success("Download completed.")

        mime_types = {
            ".mp4": "video/mp4",
            ".mkv": "video/x-matroska",
            ".webm": "video/webm",
            ".mp3": "audio/mpeg",
            ".m4a": "audio/mp4",
            ".wav": "audio/wav",
        }

        mime = mime_types.get(downloaded.suffix.lower(), "application/octet-stream")

        with open(downloaded, "rb") as f:
            data = f.read()

        st.download_button(
            label=f"⬇ Save {downloaded.name}",
            data=data,
            file_name=downloaded.name,
            mime=mime,
            use_container_width=True,
        )

    except Exception as exc:
        st.error("Download failed.")
        st.code(str(exc))

    finally:
        # Remove temporary files after the Streamlit run finishes.
        # The download_button above has already received the file bytes.
        shutil.rmtree(temp_dir, ignore_errors=True)
