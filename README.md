<div align="center">
  <pre style="white-space:pre-wrap; text-align:center; display:inline-block; max-width:95%; overflow:auto; line-height:1; font-family:monospace; margin:0 0 16px 0;">                               
 _______ _______ _______ ___ ___ _______ ______ _______ _______ _____   
|   |   |    |  |_     _|   |   |    ___|   __ \     __|   _   |     |_ 
|   |   |       |_|   |_|   |   |    ___|      <__     |       |       |
|_______|__|____|_______|\_____/|_______|___|__|_______|___|___|_______|
</details>
</div>
  
## Highlights

- Interactive menu
  - [1] Enter a single link
  - [2] Load links from a .txt file
  - [3] Collect links from a Discord channel
  - [S] Settings
- Audio‑only mode (global toggle)
  - “Only audio” in Settings
  - Downloads all inputs as MP3
  - Embeds the source thumbnail as MP3 cover art (if available)
  - The thumbnail file is NOT kept on disk; it’s embedded into the MP3 and then removed
  - If no thumbnail is available, the MP3 is still produced (without cover)
- Video downloads (default mode)
- Discord integration
  - Use a bot token and channel ID to scrape links from a channel’s message history
- .txt file source
  - One URL per line
- Global bandwidth limit
- Daily stats (header shows count and total bytes for today)
- cookies.txt support
  - If a `cookies.txt` sits next to the script, it will be used automatically (helps with protected sites, e.g., 403)

## Requirements

- Python 3.9+
- FFmpeg
  - Required for audio conversion and cover embedding
- The script will auto‑install Python deps on first run if missing:
  - yt‑dlp, discord.py, aiohttp

## Quick start

- Install FFmpeg and ensure `ffmpeg` is in your PATH
- Download `universal.py`
- Run:
  - Windows: `py universal.py`
  - macOS/Linux: `python3 universal.py`
- On first launch, set a valid download path
- Use the menu to download by link, by .txt, or via Discord

## Settings

Toggle and configure under [S] Settings:
- Download path
- Discord bot token
- Discord channel ID
- Bandwidth limit (MB/s, 0 = unlimited)
- Only audio (On/Off)

Settings are stored in `config.json`:
```json
{
  "download_path": "",
  "discord_bot_token": "",
  "discord_channel_id": "",
  "max_download_rate_bps": 0,
  "audio_only": false
}
```

Notes:
- Bandwidth limit is stored as bytes per second (bps) internally.
- If `cookies.txt` exists next to the script, it will be used automatically.

## Audio‑only mode and cover art

- When “Only audio” is On:
  - The best audio stream is downloaded and converted to MP3.
  - If a thumbnail is available, it’s embedded as cover art in the MP3.
  - Temporary thumbnail files are cleaned up; nothing extra remains on disk.
  - If no thumbnail is available, the MP3 is still produced without a cover.
- FFmpeg is required for conversion and embedding; if missing, a clear error explains it.

## Discord: how to collect links

1. Create a Discord bot at the Developer Portal and copy the bot token.
2. Invite the bot to your server with at least “Read Message History” for the target channel.
3. In Settings, paste the bot token and enter the numeric channel ID.
4. Choose menu option [3] to collect links from that channel (up to the recent history in scope).

Tip: If the bot can’t see the channel, grant it the necessary permissions or move it above role restrictions.

## .txt file input

- Prepare a text file with one URL per line.
- In the menu, choose [2], select the .txt file, confirm to start.
- Invalid or duplicate lines are skipped automatically.

## Error messages and behavior

- Errors are printed in English with short guidance on how to fix the issue.
- For non‑download contexts (Discord, file selection, setup), the app pauses with “Press Enter to continue…” so you can read the message.
- For batch downloads, errors are shown inline per link so the batch can continue.

Examples of messages:
- Network/HTTP
  - Access denied (HTTP 403). Provide cookies/login or retry later.
  - Unauthorized (HTTP 401). Authentication required (cookies/login).
  - Too many requests (HTTP 429). You are rate‑limited. Wait and retry.
  - Resource not found (HTTP 404). Check the link.
  - Server error (HTTP 5xx). Retry later.
  - Request timed out. Check your connection and retry.
  - SSL/TLS error (certificate/connection). Check network/proxy.
  - DNS resolution failed. Check your internet or DNS resolver.
- FFmpeg / Post‑processing / Filesystem
  - FFmpeg is required for audio‑only downloads and embedding thumbnails, but it was not found.
  - Post‑processing failed (FFmpeg missing/broken).  [If MP3 already exists, download is considered successful; the file may have no cover.]
  - Output file not found (conversion failed).
  - No space left on device.
  - File system error: (details).
  - Unexpected error: (Type) - (message).
- Discord
  - The Discord token is invalid. Please check it in config.json and restart the tool.
  - Invalid channel ID. It must be numeric.
  - Channel with ID (id) not found or bot has no access.
  - No permission to access the channel. Check bot roles and channel visibility.
  - Discord resource not found (channel/server). Check the ID and permissions.
  - Discord API error: (details).
  - No links found in the channel.
- File selection / .txt
  - No file selected.
  - Invalid file selected. Please choose a .txt file.
  - File not found: (path)
  - Error reading file: (details)
  - The file '(name)' contains no valid links.
- Input validation
  - Invalid link. It must start with http:// or https://

## Stats

- The header shows “Daily Downloads, Today: <count> | Total Size, Today: <human‑readable>”
- Stats are kept for the last 14 days in `.universal_stats.json`

## Update notice

- On start, the tool checks for the latest commit of `universal.py` in the repo and shows a brief box with the message.
- Press Enter to continue or press “O” to open the commit link in your browser.

## Tips

- Use `cookies.txt` to handle sites behind protection or requiring login (403/Cloudflare). Export cookies from your browser and save them next to the script. (Netscape)
- If you enable “Only audio”, ensure FFmpeg is installed.
- If link extraction fails for a specific site, try providing cookies or reduce the bandwidth limit if you are rate‑limited.

---

<div align="center">
 
If you find any buggs or inconsistencies, please report them in detail under “Issues”

 [![Ko-fi](https://www.ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/bitnestt)

</div>
