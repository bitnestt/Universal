# universal - v1.2.7
import sys
import subprocess
import os
import json
import tempfile
import time
from pathlib import Path
import asyncio
import re
import string
import shutil
import datetime
import aiohttp
import webbrowser

try:
    import requests
    import yt_dlp
    import discord
    import cloudscraper
    import aiohttp
    from yt_dlp.utils import DownloadError, ExtractorError
except ImportError:
    print("Missing libraries will be installed...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "yt-dlp", "discord.py", "cloudscraper", "aiohttp"])
        print("Installation complete. Please restart the script.")
    except Exception as e:
        print(f"Error installing dependencies: {e}")
    sys.exit()

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
#---------------Update check(start)---------------
GITHUB_REPO = "bitnestt/Universal"
GITHUB_FILE_PATH = "universal.py"
GITHUB_BRANCH = "main"

def _terminal_width(default=100):
    try:
        import shutil as _shutil
        return max(40, _shutil.get_terminal_size((default, 25)).columns)
    except Exception:
        return default

def _bold(s):
    return f"\033[1m{s}\033[0m"

def _clear_screen():
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
    except Exception:
        print("\n" * 3)

def _format_commit_date_utc(iso_str: str) -> str:
    try:
        dt = datetime.datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%SZ")
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return None

async def _fetch_latest_universal_commit():
    api = f"https://api.github.com/repos/{GITHUB_REPO}/commits"
    params = {"path": GITHUB_FILE_PATH, "sha": GITHUB_BRANCH, "per_page": 1}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api, params=params, headers={"Accept": "application/vnd.github+json"}) as r:
                if r.status != 200:
                    return None
                data = await r.json()
    except Exception:
        return None
    if not data:
        return None

    latest = data[0]
    sha_full = (latest.get("sha") or "")
    sha_short = sha_full[:12] if sha_full else ""
    raw_msg = ((latest.get("commit") or {}).get("message") or "").strip()

    lines = raw_msg.splitlines()
    title_line = lines[0] if lines else ""
    desc_text = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""

    commit_obj = (latest.get("commit") or {})
    committer_obj = (commit_obj.get("committer") or {})
    author_obj = (commit_obj.get("author") or {})
    date_iso = committer_obj.get("date") or author_obj.get("date") or ""

    html_url = latest.get("html_url") or (f"https://github.com/{GITHUB_REPO}/commit/{sha_full}" if sha_full else None)
    return {
        "sha_short": sha_short,
        "title": title_line,
        "description": desc_text,
        "html_url": html_url,
        "sha_full": sha_full,
        "date_iso": date_iso
    }

def _last_seen_cache_path():
    return os.path.join(os.path.dirname(__file__), ".universal_commit")

def _read_last_seen_sha():
    p = _last_seen_cache_path()
    try:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return f.read().strip()
    except Exception:
        return None
    return None

def _write_last_seen_sha(sha_short):
    p = _last_seen_cache_path()
    try:
        with open(p, "w", encoding="utf-8") as f:
            f.write(sha_short or "")
    except Exception:
        pass

def _draw_update_box_left(title, description, date_human=None):
    w = _terminal_width()
    box_width = max(50, min(w - 4, 100))
    border = "═" * box_width

    print("")
    print(border)
    print(_bold(title))
    if date_human:
        print(date_human)
    print("")

    import textwrap
    if description:
        for line in description.splitlines():
            for sub in textwrap.wrap(line, width=box_width):
                print(sub)
    else:
        print("No description provided.")

    print(border)
    print("")

async def show_update_notice_if_any():
    info = await _fetch_latest_universal_commit()
    if not info:
        return

    last_seen = _read_last_seen_sha()
    latest = info["sha_short"]

    if not last_seen:
        _write_last_seen_sha(latest)
        return
    if last_seen == latest:
        return

    title = info.get("title") or "New commit for universal.py"
    desc = info.get("description") or "No description provided."
    date_h = _format_commit_date_utc(info.get("date_iso")) if info.get("date_iso") else None
    _draw_update_box_left(title, desc, date_human=date_h)

    print("[Press Enter to continue]   [O] Open commit link")
    choice = input("> ").strip().lower()
    if choice == "o" and info.get("html_url"):
        confirm = input("Open the commit in your default browser? (y/n): ").strip().lower()
        if confirm == "y":
            try:
                webbrowser.open(info["html_url"])
                print("Opening browser...")
            except Exception as e:
                print(f"Could not open browser: {e}")
        input("Press Enter to continue...")

    _write_last_seen_sha(latest)
    _clear_screen()
#---------------Update check(end)---------------

def ensure_console_size(cols=140, lines=50, buffer_lines=5000):
    if os.name != 'nt':
        return
    try:
        os.system(f"mode con: cols={cols} lines={lines}")
    except Exception:
        pass
    try:
        import ctypes
        class COORD(ctypes.Structure):
            _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]
        kernel32 = ctypes.windll.kernel32
        hOut = kernel32.GetStdHandle(-11)
        kernel32.SetConsoleScreenBufferSize(hOut, COORD(cols, max(lines, buffer_lines)))
    except Exception:
        pass

def pause_on_error():
    input(f"\n{Colors.CYAN}[Press Enter to exit...]{Colors.RESET}")

def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True, text=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False

def load_config():
    config_file_path = "config.json"
    default_config = {
        "download_path": "",
        "gofile_Account_Token": "",
        "gofile_folder_id": "",
        "discord_bot_token": "",
        "discord_channel_id": "",
        "max_download_rate_bps": 0
    }
    if os.path.exists(config_file_path):
        try:
            with open(config_file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            for key in default_config:
                if key not in config:
                    config[key] = default_config[key]
            return config
        except json.JSONDecodeError as e:
            print(f"{Colors.RED}Config file is corrupted: {e}. Please fix or delete '{config_file_path}'.{Colors.RESET}")
            return None
        except Exception as e:
            print(f"{Colors.RED}Error reading config file: {e}{Colors.RESET}")
            return None

    try:
        with open(config_file_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2)
    except Exception as e:
        print(f"{Colors.RED}Failed to write config: {e}{Colors.RESET}")
        return None
    return default_config

def save_config(config):
    config_file_path = "config.json"
    try:
        with open(config_file_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"{Colors.RED}Failed to save config: {e}{Colors.RESET}")

def get_gofile_server():
    try:
        response = requests.get("https://api.gofile.io/servers")
        response.raise_for_status()
        servers = response.json()
        if servers['status'] == 'ok' and servers['data']['servers']:
            return servers['data']['servers'][0]['name']
    except requests.exceptions.RequestException as e:
        print(f"{Colors.RED}Failed to get Gofile server: {e}{Colors.RESET}")
        return None
    return None

def upload_to_gofile(file_path, server, account_token=None, folder_id=None):
    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            url = f"https://{server}.gofile.io/uploadFile"
            data = {}
            if account_token:
                data['token'] = account_token
            if folder_id:
                data['folderId'] = folder_id

            response = requests.post(url, files=files, data=data)
            response.raise_for_status()

            upload_data = response.json()
            if upload_data['status'] == 'ok':
                return True, "Successfully uploaded to Gofile."
            else:
                return False, f"Gofile upload failed: {upload_data.get('message', 'Unknown error')}"
    except requests.exceptions.RequestException as e:
        return False, f"Error uploading to Gofile: {e}"
    except Exception as e:
        return False, f"An unexpected error occurred during upload: {e}"

def sanitize_filename(text):
    valid_chars = f"-_.() {string.ascii_letters}{string.digits}"
    sanitized_text = ''.join(c for c in text if c in valid_chars)
    sanitized_text = sanitized_text.replace(' ', '_')
    return sanitized_text[:100]

def get_unique_filename(base_dir, base_name, ext):
    candidate = f"{base_name}.{ext}"
    candidate_path = os.path.join(base_dir, candidate)
    if not os.path.exists(candidate_path):
        return candidate_path

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    candidate = f"{base_name}_{ts}.{ext}"
    candidate_path = os.path.join(base_dir, candidate)
    if not os.path.exists(candidate_path):
        return candidate_path

    for i in range(100):
        candidate = f"{base_name}_{ts}_{i}.{ext}"
        candidate_path = os.path.join(base_dir, candidate)
        if not os.path.exists(candidate_path):
            return candidate_path
    raise RuntimeError("Could not generate unique filename for download.")

TRAILING_CHARS = '>)],.;\'"“”„`´’!?'

def clean_url(u: str) -> str:
    if not u:
        return u
    u = u.strip()
    if u.startswith('<') and u.endswith('>') and len(u) > 2:
        u = u[1:-1]
    while len(u) > 0 and u[-1] in TRAILING_CHARS:
        u = u[:-1]
    return u

def dedupe_and_clean(url_list):
    seen = set()
    cleaned = []
    for u in url_list:
        cu = clean_url(u)
        if cu and cu not in seen:
            seen.add(cu)
            cleaned.append(cu)
    return cleaned

ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')
def visible_len(s):
    return len(ANSI_RE.sub('', s))

def format_bytes(n):
    try:
        n = float(n)
    except:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while n >= 1024 and i < len(units) - 1:
        n /= 1024.0
        i += 1
    return f"{n:.2f} {units[i]}"

def format_seconds(s):
    try:
        s = int(round(float(s)))
    except:
        return "--:--"
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{sec:02d}"
    return f"{m:02d}:{sec:02d}"

def make_bar(pct, width=34):
    try:
        pct = float(pct)
    except:
        pct = 0.0
    pct = max(0.0, min(1.0, pct))
    filled = int(pct * width)
    if filled >= width:
        return "[" + "█" * width + "]"
    return "[" + "█" * filled + ">" + "═" * (width - filled - 1) + "]"

class QuietLogger:
    def debug(self, msg): 
        pass
    def warning(self, msg): 
        pass
    def error(self, msg):
        try:
            print(f"{Colors.RED}{msg}{Colors.RESET}")
        except:
            print(msg)

def _rate_label(bps: int) -> str:
    if not bps or bps <= 0:
        return "Unlimited"
    mb = bps / (1024 * 1024)
    if mb.is_integer():
        return f"{int(mb)} MB/s"
    return f"{mb:.2f} MB/s"

#---------------Daily stats(start)---------------
STATS_PATH = os.path.join(os.path.dirname(__file__), ".universal_stats.json")
STATS_RETENTION_DAYS = 14

def _load_stats_raw():
    try:
        if os.path.exists(STATS_PATH):
            with open(STATS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {"events": []}

def _save_stats_raw(data):
    try:
        tmp = STATS_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, STATS_PATH)
    except Exception:
        pass

def _prune_stats(data):
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=STATS_RETENTION_DAYS)
    new_events = []
    for ev in data.get("events", []):
        try:
            t = ev.get("ts", "")
            if t.endswith("Z"):
                dt = datetime.datetime.fromisoformat(t.replace("Z", "+00:00"))
            else:
                dt = datetime.datetime.fromisoformat(t)
            if dt >= cutoff:
                new_events.append(ev)
        except Exception:
            continue
    data["events"] = new_events
    return data

def _init_stats_file():
    if not os.path.exists(STATS_PATH):
        try:
            _save_stats_raw({"events": []})
        except Exception:
            pass

def record_download_stat(size_bytes):
    try:
        data = _load_stats_raw()
        ev = {
            "ts": datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "size": int(size_bytes or 0)
        }
        data.setdefault("events", []).append(ev)
        data = _prune_stats(data)
        _save_stats_raw(data)
    except Exception:
        pass

def get_today_stats():
    try:
        tz = datetime.datetime.now().astimezone().tzinfo
    except Exception:
        tz = datetime.timezone.utc
    now = datetime.datetime.now(tz)
    today = now.date()
    data = _load_stats_raw()
    count = 0
    total = 0
    for ev in data.get("events", []):
        try:
            t = ev.get("ts", "")
            if t.endswith("Z"):
                dt = datetime.datetime.fromisoformat(t.replace("Z", "+00:00"))
            else:
                dt = datetime.datetime.fromisoformat(t)
            dt_local = dt.astimezone(tz)
            if dt_local.date() == today:
                count += 1
                total += int(ev.get("size") or 0)
        except Exception:
            continue
    return count, total
#---------------Daily stats(end)---------------

def download_universal_video(url, config, upload_to_gofile_enabled, gofile_server=None):
    download_target_dir = tempfile.mkdtemp() if upload_to_gofile_enabled else config["download_path"]

    script_dir = os.path.dirname(os.path.abspath(__file__))
    generic_cookie_file = os.path.join(script_dir, "cookies.txt")

    ydl_opts_info = {
        'quiet': True,
        'no_warnings': True,
        'noprogress': True,
        'skip_download': True,
        'logger': QuietLogger(),
        'extractor_args': {'generic': ['impersonate']},
    }
    rate_bps = int(config.get("max_download_rate_bps") or 0)
    if rate_bps > 0:
        ydl_opts_info['ratelimit'] = rate_bps

    if os.path.exists(generic_cookie_file):
        ydl_opts_info['cookiefile'] = generic_cookie_file

    try:
        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            title = info_dict.get("title", "video")
            ext = info_dict.get("ext", "mp4")
    except Exception as e:
        if upload_to_gofile_enabled and os.path.isdir(download_target_dir):
            shutil.rmtree(download_target_dir, ignore_errors=True)
        return False, f"Could not fetch video info: {e}", 0, 0

    safe_title = sanitize_filename(title)
    final_path = get_unique_filename(download_target_dir, safe_title, ext)
    base_no_ext = os.path.splitext(final_path)[0]

    prog = {'len': 0, 't': 0.0, 'pct': -1.0, 'delta': 1.0, 'started': False}

    def write_progress(line):
        now = time.time()
        if (now - prog['t'] < 0.12) and (abs(prog['delta']) < 0.004):
            return
        prog['t'] = now
        vis = visible_len(line)
        pad = max(0, prog['len'] - vis)
        try:
            sys.stdout.write('\r' + line + (' ' * pad))
            sys.stdout.flush()
            prog['len'] = max(prog['len'], vis)
        except:
            pass

    def clear_progress():
        if prog['len'] > 0:
            try:
                sys.stdout.write('\r' + (' ' * prog['len']) + '\r')
                sys.stdout.flush()
            except:
                pass
            prog['len'] = 0

    def progress_hook(d):
        status = d.get('status')
        if status == 'downloading':
            if not prog['started']:
                print("")
                prog['started'] = True
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes', 0)
            pct = (downloaded / total) if total else 0.0
            prog['delta'] = (pct - prog['pct']) if prog['pct'] >= 0 else 1.0
            prog['pct'] = pct
            bar = make_bar(pct, 34)
            spd = d.get('speed') or 0
            speed_str = f"{format_bytes(spd)}/s" if spd else "--/s"
            eta = d.get('eta')
            eta_str = format_seconds(eta) if eta is not None else "--:--"
            dl_str = format_bytes(downloaded)
            tot_str = format_bytes(total) if total else "?"
            pct_str = f"{pct*100:5.1f}%"
            line = f"{bar} {pct_str} {dl_str}/{tot_str} {speed_str:>9} ETA {eta_str}"
            write_progress(line)
        elif status == 'finished':
            clear_progress()

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': base_no_ext + ".%(ext)s",
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
        'quiet': True,
        'no_warnings': True,
        'noprogress': True,
        'logger': QuietLogger(),
        'extractor_args': {'generic': ['impersonate']},
        'progress_hooks': [progress_hook],
    }
    if rate_bps > 0:
        ydl_opts['ratelimit'] = rate_bps
    if os.path.exists(generic_cookie_file):
        ydl_opts['cookiefile'] = generic_cookie_file

    def find_final_output(base_root):
        exts = ["mp4", "webm", "mkv", "mov", "m4a", "mp3"]
        for e in exts:
            p = f"{base_root}.{e}"
            if os.path.exists(p):
                return p
        return base_root + "." + ext

    def attempt_download(url_dl, session=None):
        opts = ydl_opts.copy()
        if session:
            opts['http_session'] = session
        start_time = time.time()
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.extract_info(url_dl, download=True)
            end_time = time.time()
            clear_progress()
            final_effective = find_final_output(base_no_ext)
            download_duration = end_time - start_time
            file_size = os.path.getsize(final_effective)
            try:
                record_download_stat(file_size)
            except Exception:
                pass
            return True, final_effective, "", file_size, download_duration
        except DownloadError as e:
            clear_progress()
            if "Cloudflare" in str(e) or "403" in str(e):
                return False, None, "cloudflare_error", 0, 0
            return False, None, str(e), 0, 0
        except ExtractorError as e:
            clear_progress()
            return False, None, f"Extractor Error: {str(e)}", 0, 0
        except Exception as e:
            clear_progress()
            return False, None, f"An unexpected error occurred: {type(e).__name__} - {e}", 0, 0

    success, final_path_real, error_message, file_size, download_duration = attempt_download(url)

    if not success and error_message == "cloudflare_error":
        try:
            session = cloudscraper.create_scraper()
            success, final_path_real, error_message, file_size, download_duration = attempt_download(url, session)
        except Exception as e:
            if upload_to_gofile_enabled and os.path.isdir(download_target_dir):
                shutil.rmtree(download_target_dir, ignore_errors=True)
            return False, f"An unexpected error occurred during bypass: {type(e).__name__} - {e}", 0, 0

    if success:
        if upload_to_gofile_enabled:
            success_up, message = upload_to_gofile(final_path_real, gofile_server, config.get("gofile_Account_Token"), config.get("gofile_folder_id"))
            try:
                os.remove(final_path_real)
            except Exception as e:
                print(f"{Colors.YELLOW}Warning: Could not remove file {final_path_real}: {e}{Colors.RESET}")
            try:
                shutil.rmtree(os.path.dirname(final_path_real), ignore_errors=True)
            except Exception as e:
                print(f"{Colors.YELLOW}Warning: Could not remove temp dir: {e}{Colors.RESET}")
            return success_up, "", file_size, download_duration
        else:
            return True, "", file_size, download_duration
    else:
        if upload_to_gofile_enabled and os.path.isdir(download_target_dir):
            shutil.rmtree(download_target_dir, ignore_errors=True)
        return False, "", file_size, download_duration

async def get_links_from_discord(config):
    if not config.get("discord_bot_token"):
        token = input(f"{Colors.CYAN}Please enter your Discord bot token: {Colors.RESET}")
        config["discord_bot_token"] = token.strip()
        save_config(config)

    if not config.get("discord_channel_id"):
        channel_id = input(f"{Colors.CYAN}Please enter the Discord channel ID: {Colors.RESET}")
        config["discord_channel_id"] = channel_id.strip()
        save_config(config)

    if not config.get("discord_bot_token") or not config.get("discord_channel_id"):
        print(f"{Colors.RED}Discord bot token or channel ID is missing. The function cannot be executed.{Colors.RESET}")
        return []

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)
    raw_links = []

    url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')

    @client.event
    async def on_ready():
        print(f'{Colors.CYAN}Logged in as bot "{client.user}".{Colors.RESET}')
        try:
            channel_id = int(config["discord_channel_id"])
            channel = client.get_channel(channel_id)
            if not channel:
                print(f"{Colors.RED}Channel with ID {channel_id} could not be found.{Colors.RESET}")
                client.cleaned_links = []
                await client.close()
                return

            print(f"{Colors.YELLOW}Reading messages from channel '{channel.name}'...{Colors.RESET}")
            async for message in channel.history(limit=1000):
                found = url_pattern.findall(message.content)
                if found:
                    raw_links.extend(found)

            client.cleaned_links = dedupe_and_clean(raw_links)
            print(f" {Colors.GREEN}{len(client.cleaned_links)} links found on Discord.{Colors.RESET}")
            await client.close()
        except Exception as e:
            print(f"{Colors.RED}Error accessing Discord: {e}{Colors.RESET}")
            client.cleaned_links = []
            await client.close()

    try:
        await client.start(config["discord_bot_token"])
    except discord.errors.LoginFailure:
        print(f"{Colors.RED}The Discord token is invalid. Please check it in config.json and restart the tool.{Colors.RESET}")
        return []
    except Exception as e:
        print(f"{Colors.RED}An unexpected error occurred while connecting to Discord: {e}{Colors.RESET}")
        return []

    return getattr(client, "cleaned_links", [])

def open_settings_menu(config):
    def _clear():
        try:
            os.system('cls' if os.name == 'nt' else 'clear')
        except Exception:
            pass

    def _render():
        nonlocal entries, label_width
        rate_bps_local = int(config.get("max_download_rate_bps") or 0)
        rate_label_colored = f"{Colors.GREEN}{_rate_label(rate_bps_local)}{Colors.RESET}"
        entries = [
            ("Bandwidth limit", rate_label_colored, "    "),
            ("Download path", str(config.get('download_path', '') or ''), "    "),
            ("Gofile Account Token", str(config.get('gofile_Account_Token', '') or ''), "YES" if str(config.get('gofile_Account_Token', '')).strip() else "NO "),
            ("Gofile Folder ID", str(config.get('gofile_folder_id', '') or ''), "YES" if str(config.get('gofile_folder_id', '')).strip() else "NO "),
            ("Discord bot token", str(config.get('discord_bot_token', '') or ''), "YES" if str(config.get('discord_bot_token', '')).strip() else "NO "),
            ("Discord channel ID", str(config.get('discord_channel_id', '') or ''), "YES" if str(config.get('discord_channel_id', '')).strip() else "NO "),
        ]
        _clear()
        print(f"{Colors.CYAN}------------------- Settings --------------------{Colors.RESET}")
        label_width = max((len(label) for label, _, _ in entries), default=0)
        for label, value, flag in entries:
            prefix = f"{Colors.GREEN}YES{Colors.RESET}" if flag.strip() == "YES" else (f"{Colors.RED}NO {Colors.RESET}" if flag.strip() == "NO" else "    ")
            print(f"  {prefix} - {label:<{label_width}} : {value}")
        print(f"{Colors.CYAN}--------------------------------------------------{Colors.RESET}")

    entries = []
    label_width = 0
    _render()

    while True:
        print("Choose an option:")
        print("  [1] Change download path")
        print("  [2] Set/Change Gofile Account Token")
        print("  [3] Set/Change Gofile Folder ID")
        print("  [4] Set/Change Discord bot token")
        print("  [5] Set/Change Discord channel ID")
        print("  [6] Global bandwidth limit")
        print("  [0] Back to menu")
        print(f"{Colors.CYAN}--------------------------------------------------{Colors.RESET}")
        choice = input(f"{Colors.CYAN}Selection: {Colors.RESET}").strip().lower()

        if choice == '0':
            break

        if choice not in {'1','2','3','4','5','6'}:
            _clear()
            print(f"{Colors.RED}Invalid selection.{Colors.RESET}")
            _render()
            continue

        if choice == '1':
            _clear()
            print("Selection: 1")
            new_path = input(f"{Colors.CYAN}Enter new download path: {Colors.RESET}").strip()
            if new_path == "":
                print(f"{Colors.YELLOW}No changes were made.{Colors.RESET}")
            else:
                current_path = str(config.get("download_path", "") or "")
                normalized = str(Path(new_path).resolve()).replace('\\', '/')
                if normalized == current_path:
                    print(f"{Colors.YELLOW}No changes were made.{Colors.RESET}")
                elif is_valid_download_path(new_path):
                    config["download_path"] = normalized
                    save_config(config)
                    print(f"{Colors.GREEN}Download path updated.{Colors.RESET}")
                else:
                    print(f"{Colors.RED}Invalid path or not writable.{Colors.RESET}")
            _render()

        elif choice == '2':
            _clear()
            print("Selection: 2")
            current = str(config.get("gofile_Account_Token", "") or "")
            token = input(f"{Colors.CYAN}Enter Gofile Account Token: {Colors.RESET}").strip()
            if token == "" or token == current:
                print(f"{Colors.YELLOW}No changes were made.{Colors.RESET}")
            else:
                config["gofile_Account_Token"] = token
                save_config(config)
                print(f"{Colors.GREEN}Gofile Account Token updated.{Colors.RESET}")
            _render()

        elif choice == '3':
            _clear()
            print("Selection: 3")
            current = str(config.get("gofile_folder_id", "") or "")
            fid = input(f"{Colors.CYAN}Enter Gofile Folder ID: {Colors.RESET}").strip()
            if fid == "" or fid == current:
                print(f"{Colors.YELLOW}No changes were made.{Colors.RESET}")
            else:
                config["gofile_folder_id"] = fid
                save_config(config)
                print(f"{Colors.GREEN}Gofile Folder ID updated.{Colors.RESET}")
            _render()

        elif choice == '4':
            _clear()
            print("Selection: 4")
            current = str(config.get("discord_bot_token", "") or "")
            token = input(f"{Colors.CYAN}Enter Discord bot token: {Colors.RESET}").strip()
            if token == "" or token == current:
                print(f"{Colors.YELLOW}No changes were made.{Colors.RESET}")
            else:
                config["discord_bot_token"] = token
                save_config(config)
                print(f"{Colors.GREEN}Discord bot token updated.{Colors.RESET}")
            _render()

        elif choice == '5':
            _clear()
            print("Selection: 5")
            current = str(config.get("discord_channel_id", "") or "")
            cid = input(f"{Colors.CYAN}Enter Discord channel ID: {Colors.RESET}").strip()
            if cid == "" or cid == current:
                print(f"{Colors.YELLOW}No changes were made.{Colors.RESET}")
            else:
                config["discord_channel_id"] = cid
                save_config(config)
                print(f"{Colors.GREEN}Discord channel ID updated.{Colors.RESET}")
            _render()

        elif choice == '6':
            _clear()
            print("Selection: 6")
            print("Enter global bandwidth limit in MB/s (0 = Unlimited). Leave empty to cancel.")
            raw = input(f"{Colors.CYAN}MB/s: {Colors.RESET}").strip()
            if raw == "":
                print(f"{Colors.YELLOW}No changes were made.{Colors.RESET}")
                _render()
                continue
            try:
                val_mb = float(raw)
                if val_mb < 0:
                    print(f"{Colors.RED}Invalid value.{Colors.RESET}")
                    _render()
                    continue
                new_bps = 0 if val_mb == 0 else int(val_mb * 1024 * 1024)
                current_bps = int(config.get("max_download_rate_bps") or 0)
                if new_bps == current_bps:
                    print(f"{Colors.YELLOW}No changes were made.{Colors.RESET}")
                else:
                    config["max_download_rate_bps"] = new_bps
                    save_config(config)
                    print(f"{Colors.GREEN}Bandwidth limit updated to {_rate_label(new_bps)}.{Colors.RESET}")
            except ValueError:
                print(f"{Colors.RED}Invalid number.{Colors.RESET}")
            _render()

async def process_links(links, config, upload_to_gofile_enabled):
    total_links = len(links)
    if total_links == 0:
        return

    gofile_server = None
    if upload_to_gofile_enabled:
        gofile_server = get_gofile_server()
        if not gofile_server:
            print(f"{Colors.RED}Could not find a Gofile server. Cannot upload.{Colors.RESET}")
            upload_to_gofile_enabled = False

    for idx, raw_url in enumerate(links, start=1):
        url = clean_url(raw_url)
        try:
            success, message, file_size, download_duration = await asyncio.to_thread(
                download_universal_video, url, config, upload_to_gofile_enabled, gofile_server
            )
        except Exception as e:
            print(f"{Colors.RED}Download error: {e}{Colors.RESET}")
            continue

        if success:
            try:
                size_str = format_bytes(file_size)
                dur_str = f"{download_duration:.2f} seconds"
                print(f"{Colors.GREEN}    - Download completed ({idx}/{total_links}){Colors.RESET}")
                print(f"{Colors.GREEN}      - Size: {size_str}{Colors.RESET}")
                print(f"{Colors.GREEN}      - Time: {dur_str}{Colors.RESET}")
            except Exception:
                pass
        else:
            print(f"{Colors.RED}    - Download failed ({idx}/{total_links}){Colors.RESET}")

def is_valid_download_path(path_str):
    try:
        path = Path(path_str).resolve()
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
        return path.is_dir() and os.access(str(path), os.W_OK)
    except Exception as e:
        print(f"{Colors.RED}Invalid path '{path_str}': {e}{Colors.RESET}")
        return False

def render_header(config):
    _clear_screen()
    header_lines = [   
        r" ____ ___       __                                   __   ",
        r"|    |   \____ |__|__  __ ___________  ___________  |  |  ",
        r"|    |   /    \|  \  \/ // __ \_  __ \/  ___/\__  \ |  |  ",
        r"|    |  /   |  \  |\   /\  ___/|  | \/\___ \  / __ \|  |__",
        r"|______/|___|  /__| \_/  \___  >__|  /____  >(____  /____/",
        r"             \/              \/           \/      \/      ",
    ]
    for l in header_lines:
        print(f"{Colors.CYAN}{l}{Colors.RESET}")
    try:
        count_today, size_today = get_today_stats()
        stats_line = f"Daily Downloads Today: {count_today}    |    Total Size Today: {format_bytes(size_today)}"
        print(stats_line)
    except Exception:
        pass
    if not check_ffmpeg():
        print(f"{Colors.YELLOW}WARNING: FFmpeg not found. Video and audio conversion may fail.{Colors.RESET}")
        print("Please install FFmpeg to use all features.")

def countdown_blocking(seconds, prefix):
    try:
        import msvcrt
    except ImportError:
        msvcrt = None
    for i in range(seconds, 0, -1):
        sys.stdout.write(f"\r{prefix} {i} seconds...   ")
        sys.stdout.flush()
        t_end = time.time() + 1
        while time.time() < t_end:
            if msvcrt and msvcrt.kbhit():
                try:
                    msvcrt.getwch()
                except Exception:
                    try:
                        msvcrt.getch()
                    except Exception:
                        pass
            time.sleep(0.01)
    print("")

async def main():
    ensure_console_size(cols=134, lines=30, buffer_lines=5000)

    try:
        await show_update_notice_if_any()
    except Exception:
        pass

    config = load_config()
    if config is None:
        pause_on_error()
        return

    _init_stats_file()

    download_path = config.get("download_path")
    while not download_path or not is_valid_download_path(download_path):
        download_path_input = input(f"{Colors.CYAN}Please enter the desired download path: {Colors.RESET}")
        if not is_valid_download_path(download_path_input):
            print(f"{Colors.RED}Path is invalid or not writeable. Try again.{Colors.RESET}")
            continue
        download_path = str(Path(download_path_input).resolve())
        config["download_path"] = download_path.replace('\\', '/')
        save_config(config)

    render_header(config)

    while True:
        links_to_download = []
        user_choice = input(f"""
{Colors.CYAN}----------------------------------------------------{Colors.RESET}
{Colors.YELLOW}How would you like to provide the links?{Colors.RESET}
  {Colors.CYAN}[1] Enter a link{Colors.RESET}
  {Colors.CYAN}[2] From a .txt file{Colors.RESET}
  {Colors.CYAN}[3] From a Discord channel{Colors.RESET}
  {Colors.CYAN}[S] Settings{Colors.RESET}
{Colors.CYAN}----------------------------------------------------{Colors.RESET}
{Colors.CYAN}Selection: {Colors.RESET}""").strip().lower()

        valid_choices = {'1', '2', '3', 's'}
        if user_choice not in valid_choices:
            print(f"{Colors.RED}Invalid selection. Please enter '1', '2', '3' or 's'{Colors.RESET}")
            countdown_blocking(4, "Returning to menu in")
            render_header(config)
            continue

        if user_choice == '1':
            user_input = input(f"{Colors.CYAN}enter the link\n{Colors.RESET}").strip()
            if user_input:
                links_to_download.extend(dedupe_and_clean([user_input]))
            else:
                print(f"{Colors.RED}No link provided.{Colors.RESET}")
                countdown_blocking(4, "Returning to menu in")
                render_header(config)
                continue

        elif user_choice == '2':
            file_name = input(f"{Colors.CYAN}Please enter the name of the .txt file: {Colors.RESET}").strip()
            if (not file_name) or (not file_name.lower().endswith(".txt")) or (not os.path.exists(file_name)):
                print(f"{Colors.RED}No .txt file with that name was found.{Colors.RESET}")
                countdown_blocking(4, "Returning to menu in")
                render_header(config)
                continue
            collected = []
            with open(file_name, 'r', encoding='utf-8') as f:
                for line in f:
                    url = line.strip()
                    if url and url.startswith(("http://", "https://")):
                        collected.append(url)
            links_to_download = dedupe_and_clean(collected)
            if not links_to_download:
                print(f"{Colors.RED}The file '{file_name}' was found, but it contains no valid links.{Colors.RESET}")
                countdown_blocking(4, "Returning to menu in")
                render_header(config)
                continue
            else:
                print(f"{Colors.GREEN}Successfully found {len(links_to_download)} links in '{file_name}'.{Colors.RESET}")

        elif user_choice == '3':
            links_to_download = await get_links_from_discord(config)

        else:
            open_settings_menu(config)
            render_header(config)
            continue

        if not links_to_download:
            continue

        print(f"\n{Colors.YELLOW}Would you like to save the videos locally (1) or upload them to Gofile (2)?{Colors.RESET}")
        upload_choice = input(f"{Colors.CYAN}Selection: {Colors.RESET}").lower()
        upload_to_gofile_enabled = upload_choice == '2'

        if upload_to_gofile_enabled:
            while not config.get("gofile_Account_Token"):
                api_key = input(f"{Colors.CYAN}Please enter your Gofile Account Token (This is mandatory for uploads): {Colors.RESET}")
                if api_key.strip():
                    config["gofile_Account_Token"] = api_key.strip()
                    save_config(config)
                else:
                    print(f"{Colors.RED}Gofile Account Token cannot be empty. Please enter a valid key.{Colors.RESET}")

            while not config.get("gofile_folder_id"):
                folder_id = input(f"{Colors.CYAN}Please enter the destination folder ID (This is mandatory for uploads): {Colors.RESET}")
                if folder_id.strip():
                    config["gofile_folder_id"] = folder_id.strip()
                    save_config(config)
                else:
                    print(f"{Colors.RED}Folder ID cannot be empty. Please enter a valid ID.{Colors.RESET}")

        await process_links(links_to_download, config, upload_to_gofile_enabled)

        countdown_blocking(10, "Restarting to menu in")
        render_header(config)

    time.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
