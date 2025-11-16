# Universal Downloader

Universal is a console-based bulk downloader built around `yt-dlp` with optional Discord integration.  
It is designed to reliably download videos or audio from a wide range of sites, with quality-of-life features like:

- Flexible input sources (single link, text file, Discord channel)
- Audio-only mode with optional MP3 cover embedding
- Global bandwidth limiting
- Multi-download (concurrent jobs) with per-fragment concurrency
- Lightweight daily statistics and smart cookie handling
  
---

## Features

- **Multi-source input**
  - Enter a single URL directly in the console
  - Load a list of URLs from a `.txt` file
  - Fetch URLs from a Discord channel via bot

- **Audio-only mode**
  - Toggle *Only audio* to extract and download audio tracks
  - Output as MP3 via `FFmpegExtractAudio`

- **MP3 cover embedding (v1.5.0)**
  - New setting: *MP3 cover embedding*
  - When enabled, thumbnails are downloaded and embedded as album covers in MP3 files (audio-only mode)
  - Uses `FFmpegThumbnailsConvertor` + `EmbedThumbnail`
  - Automatically cleans up temporary thumbnail image files after successful conversion

- **Global bandwidth limiting**
  - Configure a global rate limit in MB/s
  - Applies to all downloads via `yt-dlp`’s `ratelimit` option

- **Multi-download & concurrency**
  - Toggle *Multi download* to process multiple links concurrently
  - Configure *Max concurrent downloads*
  - Uses a semaphore and per-fragment concurrency with `concurrent_fragment_downloads`

- **Discord integration**
  - Connect a bot to a specific channel to read up to 1,000 recent messages
  - Extracts and normalizes HTTP/HTTPS links
  - Handles common permission and API errors gracefully

- **Smart cookie handling**
  - Reads `cookies.txt` from the script directory
  - Supports both Netscape-format and common JSON exports (e.g. from browsers/extensions)
  - Cleans and normalizes cookies into a temporary Netscape cookie file per run
  - Automatically wires the cookie file into `yt-dlp`

- **Robust error handling**
  - Friendly messages for common HTTP and network errors (403, 404, 429, 5xx, DNS issues, SSL errors, timeouts)
  - Clear feedback for disk space issues and file-system errors
  - Graceful handling of `yt-dlp` extractor and post-processing errors

- **Download statistics**
  - Tracks per-download size in a lightweight JSON file (`.universal_stats.json`)
  - Shows daily download count and total size in the header
  - Automatically prunes old events beyond a retention window

- **Cross-platform console UI**
  - Text-based interface, no GUI dependencies required
  - Windows console resizing (where supported) with safe fallbacks on other platforms
  - Colored status messages for better readability

---

## Requirements

- **Python**: 3.8 or newer is recommended
- **Dependencies**:
  - [`yt-dlp`](https://github.com/yt-dlp/yt-dlp)
  - [`discord.py`](https://github.com/Rapptz/discord.py)
  - [`aiohttp`](https://github.com/aio-libs/aiohttp)
- **FFmpeg**:
  - Required for video conversion, audio extraction, and MP3 cover embedding  
  - Must be available in your system `PATH` as `ffmpeg`

If any of the Python dependencies are missing, `universal.py` will attempt to install them via `pip` on first run and then exit, so you can restart it afterwards.

---

## Installation

1. **Download the script**

   Place `universal.py` in a directory of your choice.

2. **Install Python 3**

   Make sure `python` or `python3` is available in your shell.

3. **Install FFmpeg**

   - Windows: Use a static build from the FFmpeg website or a package manager (e.g. `chocolatey`, `scoop`)
   - Linux: Use your distribution’s package manager (e.g. `apt install ffmpeg`, `pacman -S ffmpeg`)
   - macOS: Use Homebrew (`brew install ffmpeg`)

4. **Run once to bootstrap**

   ```bash
   python universal.py
   ```

   The script will:
   - Install missing Python dependencies (if needed)
   - Create a default `config.json` if it does not exist
   - Ask you to provide a download path

---

## Configuration

Configuration is stored in `config.json` in the same directory as `universal.py`.

### Config keys

- `download_path`  
  Absolute or relative path where all downloaded files are stored.

- `discord_bot_token`  
  Discord bot token used to connect and read messages.

- `discord_channel_id`  
  Channel ID from which links will be read.

- `max_download_rate_bps`  
  Global download rate limit in bytes per second.
  - `0` means unlimited
  - Set via the *Global bandwidth limit* option in MB/s

- `audio_only`  
  when `true`, downloads audio-only and converts to MP3.

- `multi_download`  
  when `true`, enables concurrent downloads.

- `max_concurrent_downloads`  
  Integer (1–12); limits the number of concurrent downloads and influences fragment concurrency.

- `embed_mp3_cover`  
  when `true`, embeds the thumbnail as an MP3 cover in audio-only mode (v1.5.0).

You can either edit `config.json` manually or use the in-script **Settings** menu.

---

## Usage

### Starting the tool

```bash
python universal.py
```

On startup, the tool:

- Ensures console size (Windows)
- Checks for FFmpeg and prints a warning if not found
- Loads and validates `config.json`
- Ensures a valid, writable download path
- Displays a header with cumulative stats for the current day

### Main menu

You will see:

- `[1] Enter a link`  
- `[2] From a .txt file`  
- `[3] From a Discord channel`  
- `[S] Settings`  

#### 1. Enter a link

- Type a direct URL and press Enter
- After the first download, you can keep adding links or press Enter on an empty line to return to the main menu

#### 2. From a .txt file

- Select a `.txt` file (GUI file picker where available, otherwise enter the path manually)
- Each non-empty line is treated as a potential URL
- Invalid or empty lines are ignored
- If at least one URL is valid, you will be prompted:
  - Press Enter to start downloads
  - Or `B` to go back

#### 3. From a Discord channel

- Ensures `discord_bot_token` and `discord_channel_id` are set
- Connects a bot to the specified channel
- Reads recent messages and extracts HTTP/HTTPS links
- Normalizes and deduplicates all links
- Prompts you to start or go back before downloading

---

## Settings

Select `[S] Settings` from the main menu.

The settings menu shows the current configuration with colored values:

- `On` in green
- `Off` in yellow

### Options

1. **Change download path**  
   - Set or update the download directory
   - Path is validated and normalized

2. **Set/Change Discord bot token**  
   - Configure the bot token for Discord integration

3. **Set/Change Discord channel ID**  
   - Configure the numeric channel ID used to fetch links

4. **Global bandwidth limit**  
   - Configure the limit in MB/s (0 = unlimited)
   - Stored in `max_download_rate_bps` in bytes per second

5. **Toggle Only audio**  
   - Switch between full video downloads and audio-only MP3
   - Requires FFmpeg

6. **Toggle MP3 cover embedding**  
   - Controls `embed_mp3_cover`
   - When `On` and `Only audio` is also `On`, the thumbnail is downloaded and embedded as an MP3 cover

7. **Toggle Multi download**  
   - Enable or disable concurrent downloads

8. **Set Max concurrent downloads**  
   - Set an integer between 1 and 12
   - Controls how many downloads run in parallel

---

## MP3 Cover Embedding

In version 1.5.0, MP3 cover embedding has been turned into a dedicated setting.

### Behavior

- **Enabled** (`embed_mp3_cover = true`) and **Only audio** enabled:
  - Downloads the best audio stream
  - Downloads a thumbnail
  - Converts audio to MP3 via FFmpeg
  - Converts the thumbnail to JPEG
  - Embeds the cover image into the MP3
  - Cleans up temporary thumbnail files

- **Disabled** (`embed_mp3_cover = false`) or **Only audio** disabled:
  - No thumbnail download
  - No album cover embedding
  - Regular MP3 extraction only

This allows you to choose whether your audio-only downloads should include embedded cover art without affecting any other modes.

---

## Error Handling and Diagnostics

Universal surfaces common issues in a readable way:

- **Network/HTTP**
  - 403, 404, 429, 5xx, DNS failures, SSL errors, and timeouts map to concise, human-readable messages

- **File system**
  - No space left on device
  - Invalid or unwritable download paths

- **FFmpeg**
  - Clear message if FFmpeg is missing when audio-only or post-processing is required

- **Discord**
  - Invalid or missing token
  - Invalid channel ID (must be numeric)
  - Permission or visibility problems
  - API errors from `discord.py`

For unexpected exceptions, the script includes the Python error type and message to aid debugging.

---

## Stats and Privacy

- Stats are stored locally in `.universal_stats.json`
- Data points:
  - Timestamp (UTC)
  - Downloaded file size
- Used only to show:
  - Number of downloads today
  - Total size of downloads today
- Old entries are pruned after a retention period; there is no network transmission of these stats

If you prefer, you can delete `.universal_stats.json` at any time; it will be recreated automatically.

---

## Updating

Universal can notify you when `universal.py` in the configured GitHub repository has changed:

- On startup, it queries the latest commit affecting `universal.py`
- If a new commit exists compared to your last seen version, a small update box is displayed
- You can:
  - Press Enter to continue
  - Press `O` to open the commit in your browser

This mechanism is purely informational and does not auto-update your local file.

---

## Known Limitations

- `ffmpeg` must be correctly installed and on `PATH` for:
  - Audio-only downloads
  - Video format conversion
  - MP3 cover embedding
- Discord integration depends on:
  - A properly configured bot token
  - Appropriate permissions in the specified channel
- Some sites may be protected by anti-bot mechanisms; in such cases:
  - Use up-to-date cookies in `cookies.txt`
  - Consider lowering concurrency and rate limits
  - Try again later if rate-limited

<div align="center">

---

## License

This project is available under the license specified in the repository.  
Please check the repository’s `LICENSE` file for details.

---

</div>
