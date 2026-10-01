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

    if not url.strip():
        st.error("Please enter a YouTube URL.")
        st.stop()

    temp_dir = tempfile.mkdtemp(
        prefix="yt_download_"
    )

    output_template = os.path.join(
        temp_dir,
        "%(title).180s.%(ext)s"
    )

    try:

        progress = st.progress(0)
        status = st.empty()

        # ====================================================
        # VIDEO
        # ====================================================

        if media_type == "Video":

            if quality == "Best available":

                if output_format == "MP4":

                    format_selector = (
                        "bestvideo[ext=mp4]+bestaudio[ext=m4a]/"
                        "best[ext=mp4]/"
                        "bestvideo+bestaudio/best"
                    )

                elif output_format == "WEBM":

                    format_selector = (
                        "bestvideo[ext=webm]+bestaudio[ext=webm]/"
                        "best[ext=webm]/"
                        "bestvideo+bestaudio/best"
                    )

                else:

                    format_selector = (
                        "bestvideo+bestaudio/best"
                    )

            else:

                height = int(
                    quality.replace("p", "")
                )

                if output_format == "MP4":

                    format_selector = (
                        f"bestvideo[height<={height}][ext=mp4]+"
                        f"bestaudio[ext=m4a]/"
                        f"best[height<={height}][ext=mp4]/"
                        f"bestvideo[height<={height}]+"
                        f"bestaudio/"
                        f"best[height<={height}]"
                    )

                elif output_format == "WEBM":

                    format_selector = (
                        f"bestvideo[height<={height}][ext=webm]+"
                        f"bestaudio[ext=webm]/"
                        f"best[height<={height}][ext=webm]/"
                        f"bestvideo[height<={height}]+"
                        f"bestaudio/"
                        f"best[height<={height}]"
                    )

                else:

                    format_selector = (
                        f"bestvideo[height<={height}]+"
                        f"bestaudio/"
                        f"best[height<={height}]"
                    )

            ydl_opts = {
                "format": format_selector,

                "merge_output_format":
                    output_format.lower(),

                "outtmpl":
                    output_template,

                "noplaylist": True,

                "quiet": True,

                "no_warnings": True,

                "restrictfilenames": False,

                # Avoid leaving incomplete files
                "continuedl": True,

                # Don't keep temporary partial output
                "keepvideo": False,
            }

        # ====================================================
        # AUDIO
        # ====================================================

        else:

            ydl_opts = {

                "format":
                    "bestaudio/best",

                "outtmpl":
                    output_template,

                "noplaylist": True,

                "quiet": True,

                "no_warnings": True,

                "restrictfilenames": False,

                "postprocessors": [
                    {
                        "key":
                            "FFmpegExtractAudio",

                        "preferredcodec":
                            audio_format.lower(),

                        "preferredquality":
                            "192",
                    }
                ],
            }

        # ====================================================
        # DOWNLOAD
        # ====================================================

        status.info(
            "Fetching media information..."
        )

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(
                url,
                download=True,
            )

        progress.progress(90)

        status.info(
            "Checking downloaded file..."
        )

        # ====================================================
        # FIND FINAL FILE
        # ====================================================

        files = []

        for p in Path(temp_dir).iterdir():

            if not p.is_file():
                continue

            # Ignore temporary yt-dlp files
            if p.name.endswith(
                (".part", ".ytdl", ".temp")
            ):
                continue

            files.append(p)

        if not files:

            raise RuntimeError(
                "yt-dlp finished, but no final output file "
                "was found."
            )

        # ====================================================
        # FIND VALID FILE
        # ====================================================

        valid_files = [
            p for p in files
            if p.stat().st_size > 0
        ]

        if not valid_files:

            raise RuntimeError(
                "The output file was created but is 0 bytes."
            )

        # Select largest valid file.
        # This is safer than using modification time.
        downloaded = max(
            valid_files,
            key=lambda p: p.stat().st_size
        )

        file_size = downloaded.stat().st_size

        # ====================================================
        # FINAL VALIDATION
        # ====================================================

        if file_size < 1024:

            raise RuntimeError(
                f"The downloaded file is only "
                f"{file_size} bytes."
            )

        progress.progress(100)

        status.success(
            "Download completed."
        )

        # ====================================================
        # MIME TYPE
        # ====================================================

        mime_types = {

            ".mp4":
                "video/mp4",

            ".mkv":
                "video/x-matroska",

            ".webm":
                "video/webm",

            ".mp3":
                "audio/mpeg",

            ".m4a":
                "audio/mp4",

            ".wav":
                "audio/wav",
        }

        mime = mime_types.get(
            downloaded.suffix.lower(),
            "application/octet-stream",
        )

        # ====================================================
        # READ COMPLETE FILE
        # ====================================================

        with open(
            downloaded,
            "rb",
        ) as f:

            data = f.read()

        if not data:

            raise RuntimeError(
                "The output file could not be read."
            )

        if len(data) != file_size:

            raise RuntimeError(
                "The file changed while being read."
            )

        # ====================================================
        # STREAMLIT DOWNLOAD
        # ====================================================

        st.download_button(

            label=f"⬇ Save {downloaded.name}",

            data=data,

            file_name=downloaded.name,

            mime=mime,

            use_container_width=True,
        )

        st.caption(
            f"File size: "
            f"{file_size / (1024 * 1024):.2f} MB"
        )

    except Exception as exc:

        st.error(
            "Download failed."
        )

        st.code(
            str(exc)
        )

    finally:

        # Streamlit has already received the bytes
        # through st.download_button.
        shutil.rmtree(
            temp_dir,
            ignore_errors=True,
        )
