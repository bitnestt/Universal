# universal - v1.5.0
import sys
import subprocess
import os
import json
import time
from pathlib import Path
import asyncio
import re
import string
import datetime
import aiohttp
import webbrowser
import errno
import random
import tempfile

try:
    import yt_dlp
    import discord
    from yt_dlp.utils import DownloadError, ExtractorError, PostProcessingError
except ImportError:
    print("Missing libraries will be installed...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp", "discord.py", "aiohttp"])
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

if "__file__" in globals():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
else:
    BASE_DIR = os.getcwd()

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
    return os.path.join(BASE_DIR, ".universal_commit")

def _read_last_seen_sha():
    try:
        p = _last_seen_cache_path()
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return f.read().strip()
    except Exception:
        return None
    return None

def _write_last_seen_sha(sha_short):
    try:
        with open(_last_seen_cache_path(), "w", encoding="utf-8") as f:
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
            if line == "":
                print("")
                continue
            wrapped = textwrap.wrap(
                line,
                width=box_width,
                replace_whitespace=False,
                drop_whitespace=False
            )
            if not wrapped:
                print(line)
            else:
                for sub in wrapped:
                    print(sub)
    else:
        print("No description provided.")

    print(border)
    print("")

def _wait_for_enter_or_char(alt_char: str = None):
    try:
        import msvcrt
        sys.stdout.write("> ")
        sys.stdout.flush()
        while True:
            ch = msvcrt.getwch()
            if ch in ("\r", "\n"):
                return "enter"
            if alt_char and ch and ch.lower() == alt_char.lower():
                return alt_char.lower()
    except Exception:
        sys.stdout.write("> ")
        sys.stdout.flush()
        try:
            import termios, tty
            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            tty.setraw(fd)
            try:
                while True:
                    ch = sys.stdin.read(1)
                    if ch in ("\r", "\n"):
                        return "enter"
                    if alt_char and ch and ch.lower() == alt_char.lower():
                        return alt_char.lower()
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
        except Exception:
            while True:
                choice = input().strip().lower()
                if choice == "":
                    return "enter"
                if alt_char and choice == alt_char.lower():
                    return alt_char.lower()

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
    result = _wait_for_enter_or_char("o")
    if result == "o" and info.get("html_url"):
        try:
            webbrowser.open(info["html_url"])
        except Exception as e:
            print(f"Could not open browser: {e}")

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

def wait_enter():
    try:
        input(f"{Colors.CYAN}Press Enter to continue...{Colors.RESET}")
    except Exception:
        pass

def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True, text=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False

# ----------------------- Config -----------------------
def load_config():
    config_file_path = "config.json"
    default_config = {
        "download_path": "",
        "discord_bot_token": "",
        "discord_channel_id": "",
        "max_download_rate_bps": 0,
        "audio_only": False,
        "multi_download": False,
        "max_concurrent_downloads": 3,
        "embed_mp3_cover": True
    }
    if os.path.exists(config_file_path):
        try:
            with open(config_file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            for k, v in default_config.items():
                if k not in config:
                    config[k] = v
            return config
        except json.JSONDecodeError as e:
            print(f"{Colors.RED}Config file is corrupted: {e}. Fix or delete 'config.json'.{Colors.RESET}")
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
    try:
        with open("config.json", 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"{Colors.RED}Failed to save config: {e}{Colors.RESET}")

# ----------------------- Utils -----------------------
def sanitize_filename(text):
    valid_chars = f"-_.() {string.ascii_letters}{string.digits}"
    sanitized_text = ''.join(c for c in text if c in valid_chars)
    sanitized_text = sanitized_text.replace(' ', '_')
    return sanitized_text[:100]

def _random_digits(min_len=4, max_len=8):
    n = random.randint(min_len, max_len)
    return ''.join(random.choice("0123456789") for _ in range(n))

def get_unique_filename(base_dir, base_name, ext):
    candidate = f"{base_name}.{ext}"
    path_candidate = os.path.join(base_dir, candidate)
    if not os.path.exists(path_candidate):
        return path_candidate
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    candidate = f"{base_name}_{ts}.{ext}"
    path_candidate = os.path.join(base_dir, candidate)
    if not os.path.exists(path_candidate):
        return path_candidate
    for i in range(100):
        candidate = f"{base_name}_{ts}_{i}.{ext}"
        path_candidate = os.path.join(base_dir, candidate)
        if not os.path.exists(path_candidate):
            return path_candidate
    raise RuntimeError("Could not generate unique filename.")

TRAILING_CHARS = '>)],.;\'"\u2018\u2019\u201c\u201d\u201e`\u00b4!?'

def clean_url(u: str) -> str:
    if not u:
        return u
    u = u.strip()
    if u.startswith('<') and u.endswith('>') and len(u) > 2:
        u = u[1:-1]
    while len(u) > 0 and u[-1] in TRAILING_CHARS:
        u = u[:-1]
    return u

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
        pass

def _rate_label(bps: int) -> str:
    if not bps or bps <= 0:
        return "Unlimited"
    mb = bps / (1024 * 1024)
    if mb.is_integer():
        return f"{int(mb)} MB/s"
    return f"{mb:.2f} MB/s"

STATS_PATH = os.path.join(BASE_DIR, ".universal_stats.json")
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

def parse_event_timestamp(ts: str):
    if not ts:
        return None
    try:
        if ts.endswith("Z"):
            return datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return datetime.datetime.fromisoformat(ts)
    except Exception:
        return None

def _prune_stats(data):
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=STATS_RETENTION_DAYS)
    new_events = []
    for ev in data.get("events", []):
        dt = parse_event_timestamp(ev.get("ts", ""))
        if dt and dt >= cutoff:
            new_events.append(ev)
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
    today = datetime.datetime.now(tz).date()
    data = _load_stats_raw()
    count = 0
    total = 0
    for ev in data.get("events", []):
        dt = parse_event_timestamp(ev.get("ts", ""))
        if not dt:
            continue
        try:
            dt_local = dt.astimezone(tz)
        except Exception:
            dt_local = dt
        if dt_local.date() == today:
            count += 1
            total += int(ev.get("size") or 0)
    return count, total

def _friendly_protection_message(raw_msg: str) -> str:
    raw = (raw_msg or "").strip()
    lower = raw.lower()
    if "cloudflare" in lower:
        return "Blocked by site protection (e.g., Cloudflare). Provide cookies or try later."
    if "403" in lower:
        return "Access denied (HTTP 403). Provide cookies/login or retry later."
    if "429" in lower:
        return "Too many requests (HTTP 429). You are rate-limited, Wait and retry."
    if "401" in lower:
        return "Unauthorized (HTTP 401). Authentication required."
    if "404" in lower or "not found" in lower:
        return "Resource not found (HTTP 404). Check the link."
    if any(c in lower for c in ("502", "503", "504", "5xx")):
        return "Server error (HTTP 5xx). Retry later."
    if "timed out" in lower or "timeout" in lower:
        return "Request timed out. Check your connection and retry."
    if "ssl" in lower or "certificate" in lower:
        return "SSL/TLS error."
    if any(c in lower for c in ("name or service not known",
                                "temporary failure in name resolution",
                                "getaddrinfo", "dns")):
        return "DNS resolution failed."
    return raw or "Download failed."

# ---------------- Smart cookie cleaning ----------------
def _iter_json_candidates(data):
    if isinstance(data, list):
        for c in data:
            yield c
        return
    if isinstance(data, dict):
        for k in ("cookies", "Cookies", "cookieStore", "CookieStore", "entries", "Entries"):
            v = data.get(k)
            if isinstance(v, list):
                for c in v:
                    yield c
                return
        for v in data.values():
            if isinstance(v, list):
                for c in v:
                    yield c
                return

def _json_cookie_to_row(c: dict):
    try:
        domain = c.get("domain") or c.get("host") or c.get("Host") or ""
        if not domain:
            return None
        path = c.get("path") or "/"
        name = c.get("name") or c.get("Name") or ""
        value = c.get("value") or c.get("Value") or ""
        if name is None or value is None:
            return None
        secure = c.get("secure") or c.get("Secure") or False
        include_sub = domain.startswith(".")
        exp = (c.get("expirationDate") or c.get("expires") or c.get("expiry") or
               c.get("Expires") or c.get("expiryDate"))
        if isinstance(exp, str) and exp.replace(".", "").isdigit():
            exp = float(exp)
        if not isinstance(exp, (int, float)):
            exp = int(time.time() + 31536000)
        row = [
            str(domain),
            "TRUE" if include_sub else "FALSE",
            str(path),
            "TRUE" if secure else "FALSE",
            str(int(exp)),
            str(name),
            str(value),
        ]
        return "\t".join(row)
    except Exception:
        return None

def _parse_and_clean_cookies_txt_bytes(raw_bytes):
    text = None
    for enc in ("utf-8-sig", "utf-8", "utf-16", "latin-1"):
        try:
            text = raw_bytes.decode(enc)
            break
        except Exception:
            continue
    if not text:
        return []
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    out = []
    ws_re = re.compile(r'^(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\d+)\s+(\S+)\s+(.+)$')
    for ln in text.splitlines():
        s = ln.strip()
        if not s:
            continue
        if s.startswith("#HttpOnly_"):
            s = s.lstrip("#")
        if s.startswith("#"):
            continue
        if "\t" in s:
            parts = s.split("\t")
            parts = [p.strip() for p in parts if p is not None]
            if len(parts) >= 7:
                if len(parts) > 7:
                    head = parts[:6]
                    tail_value = "\t".join(parts[6:])
                    parts = head + [tail_value]
                out.append("\t".join(parts[:7]))
                continue
        m = ws_re.match(s)
        if m:
            parts = [m.group(i).strip() for i in range(1, 8)]
            out.append("\t".join(parts))
            continue
    return out

def _convert_json_to_netscape_lines(data):
    lines = []
    for c in _iter_json_candidates(data):
        if not isinstance(c, dict):
            continue
        row = _json_cookie_to_row(c)
        if row:
            lines.append(row)
    return lines

def prepare_clean_cookie_tempfile():
    cookie_path = os.path.join(BASE_DIR, "cookies.txt")
    if not os.path.exists(cookie_path):
        return None
    try:
        with open(cookie_path, "rb") as f:
            raw = f.read()
    except Exception:
        return None

    text_probe = None
    for enc in ("utf-8-sig", "utf-8", "utf-16", "latin-1"):
        try:
            text_probe = raw.decode(enc)
            break
        except Exception:
            continue
    if text_probe:
        t = text_probe.strip()
        if t.startswith("{") or t.startswith("["):
            try:
                data = json.loads(text_probe)
                json_lines = _convert_json_to_netscape_lines(data)
                if json_lines:
                    tf = tempfile.NamedTemporaryFile(mode="w+", delete=False, encoding="utf-8", newline="\n")
                    tf.write("# Netscape HTTP Cookie File\n")
                    tf.write("\n".join(json_lines) + "\n")
                    tf.close()
                    return tf.name
            except Exception:
                pass

    lines = _parse_and_clean_cookies_txt_bytes(raw)
    if lines:
        tf = tempfile.NamedTemporaryFile(mode="w+", delete=False, encoding="utf-8", newline="\n")
        tf.write("# Netscape HTTP Cookie File\n")
        tf.write("\n".join(lines) + "\n")
        tf.close()
        return tf.name
    return None

# ---------------- Download function ----------------
def download_universal_video(url, config):
    download_target_dir = config["download_path"]
    temp_cookie_path = None
    try:
        temp_cookie_path = prepare_clean_cookie_tempfile()

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
        if temp_cookie_path and os.path.exists(temp_cookie_path):
            ydl_opts_info['cookiefile'] = temp_cookie_path

        try:
            with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                title = info_dict.get("title", "video")
                ext = info_dict.get("ext", "mp4")
                duration_seconds = int(info_dict.get("duration") or 0)
        except Exception as e:
            return False, f"Could not fetch video info: {e}", 0, 0

        safe_title = sanitize_filename(title)
        rand_id = _random_digits(4, 8)
        base_name = f"{safe_title}_{rand_id}"
        final_path = get_unique_filename(download_target_dir, base_name, ext)
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

        audio_only = bool(config.get("audio_only"))
        embed_cover = bool(config.get("embed_mp3_cover", True))
        multi_mode = bool(config.get("multi_download"))
        max_conc = int(config.get("max_concurrent_downloads") or 3)
        conc_frags = max(2, min(8, int(max_conc)))

        if audio_only and not check_ffmpeg():
            return False, ("FFmpeg required for audio-only and embedding thumbnails."), 0, 0

        if not audio_only:
            ydl_postprocessors = [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}]
            ydl_format = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        else:
            ydl_postprocessors = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}]
            if embed_cover:
                ydl_postprocessors += [
                    {'key': 'FFmpegThumbnailsConvertor', 'format': 'jpg'},
                    {'key': 'EmbedThumbnail'}
                ]
            ydl_format = 'bestaudio/best'

        postprocessor_args = {}
        if audio_only:
            postprocessor_args['FFmpegExtractAudio'] = ['-vn', '-sn', '-dn', '-loglevel', 'error', '-threads', '2']
            if embed_cover:
                postprocessor_args['EmbedThumbnail'] = ['-loglevel', 'error']
        else:
            postprocessor_args['FFmpegVideoConvertor'] = ['-loglevel', 'error', '-threads', '2']

        ydl_opts = {
            'format': ydl_format,
            'outtmpl': base_no_ext + ".%(ext)s",
            'postprocessors': ydl_postprocessors,
            'quiet': True,
            'no_warnings': True,
            'noprogress': True,
            'logger': QuietLogger(),
            'extractor_args': {'generic': ['impersonate']},
            'concurrent_fragment_downloads': min(8, max(3, conc_frags)),
            'http_chunk_size': 16 * 1024 * 1024,
            'retries': 10,
            'fragment_retries': 10,
            'socket_timeout': 30,
            'post_overwrites': True,
            'prefer_ffmpeg': True,
            'postprocessor_args': postprocessor_args,
        }
        if not multi_mode:
            ydl_opts['progress_hooks'] = [progress_hook]
        if audio_only and embed_cover:
            ydl_opts['writethumbnail'] = True
        if rate_bps := int(config.get("max_download_rate_bps") or 0):
            ydl_opts['ratelimit'] = rate_bps
        if temp_cookie_path and os.path.exists(temp_cookie_path):
            ydl_opts['cookiefile'] = temp_cookie_path

        def find_final_output(base_root):
            exts = ["mp4", "webm", "mkv", "mov", "m4a", "mp3"]
            for e in exts:
                p = f"{base_root}.{e}"
                if os.path.exists(p):
                    return p
            return base_root + ".mp4"

        def cleanup_thumbnails(base_root):
            for e in ("jpg", "jpeg", "png", "webp"):
                p = f"{base_root}.{e}"
                try:
                    if os.path.exists(p):
                        os.remove(p)
                except Exception:
                    pass

        def finalize_success_record(final_effective, start_time):
            end_time = time.time()
            download_duration = end_time - start_time
            file_size = os.path.getsize(final_effective)
            try:
                record_download_stat(file_size)
            except Exception:
                pass
            return True, final_effective, "", file_size, download_duration

        def attempt_download(url_dl):
            opts = ydl_opts.copy()
            start_time = time.time()
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.extract_info(url_dl, download=True)
                clear_progress()
                final_effective = find_final_output(base_no_ext)
                if not os.path.exists(final_effective):
                    return False, None, "Output file not found.", 0, 0
                if audio_only:
                    cleanup_thumbnails(base_no_ext)
                return finalize_success_record(final_effective, start_time)
            except PostProcessingError:
                clear_progress()
                final_effective = find_final_output(base_no_ext)
                if audio_only and os.path.exists(final_effective):
                    if audio_only:
                        cleanup_thumbnails(base_no_ext)
                    return finalize_success_record(final_effective, start_time)
                return False, None, "Post-processing failed.", 0, 0
            except OSError as e:
                clear_progress()
                if getattr(e, "errno", None) == errno.ENOSPC:
                    return False, None, "No space left on device.", 0, 0
                return False, None, f"File system error: {e}", 0, 0
            except DownloadError as e:
                clear_progress()
                msg = _friendly_protection_message(str(e))
                return False, None, msg, 0, 0
            except ExtractorError as e:
                clear_progress()
                msg = _friendly_protection_message(str(e))
                return False, None, msg, 0, 0
            except Exception as e:
                clear_progress()
                return False, None, f"Unexpected: {type(e).__name__} - {e}", 0, 0

        success, _, error_message, file_size, _download_time = attempt_download(url)
        if success:
            return True, "", file_size, duration_seconds
        else:
            return False, error_message, file_size, duration_seconds
    finally:
        if temp_cookie_path and os.path.exists(temp_cookie_path):
            try:
                os.remove(temp_cookie_path)
            except Exception:
                pass

# ---------------- Discord ----------------
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
        print(f"{Colors.RED}Discord bot token or channel ID missing.{Colors.RESET}")
        wait_enter()
        return []

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)
    collected = []

    url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')

    @client.event
    async def on_ready():
        print(f'{Colors.CYAN}Logged in as bot "{client.user}".{Colors.RESET}')
        try:
            try:
                channel_id_int = int(config["discord_channel_id"])
            except ValueError:
                print(f"{Colors.RED}Invalid channel ID (numeric required).{Colors.RESET}")
                client.cleaned_links = []
                await client.close()
                wait_enter()
                return

            channel = client.get_channel(channel_id_int)
            if not channel:
                print(f"{Colors.RED}Channel not found or no access.{Colors.RESET}")
                client.cleaned_links = []
                await client.close()
                wait_enter()
                return

            print(f"{Colors.YELLOW}Reading messages in '{channel.name}'...{Colors.RESET}")
            async for message in channel.history(limit=1000):
                found = url_pattern.findall(message.content)
                if found:
                    collected.extend(found)

            seen = set()
            cleaned = []
            for u in collected:
                cu = clean_url(u)
                if cu and cu.startswith(("http://", "https://")) and cu not in seen:
                    seen.add(cu)
                    cleaned.append(cu)

            client.cleaned_links = cleaned
            print(f"{Colors.GREEN}Found {len(cleaned)} links.{Colors.RESET}")
            await client.close()
        except discord.Forbidden:
            print(f"{Colors.RED}No permission to access the channel, Check bot roles.{Colors.RESET}")
            client.cleaned_links = []
            await client.close()
            wait_enter()
        except discord.NotFound:
            print(f"{Colors.RED}Channel/server not found.{Colors.RESET}")
            client.cleaned_links = []
            await client.close()
            wait_enter()
        except discord.HTTPException as e:
            print(f"{Colors.RED}Discord API error: {e}{Colors.RESET}")
            client.cleaned_links = []
            await client.close()
            wait_enter()
        except Exception as e:
            print(f"{Colors.RED}Error accessing Discord: {e}{Colors.RESET}")
            client.cleaned_links = []
            await client.close()
            wait_enter()

    try:
        await client.start(config["discord_bot_token"])
    except discord.errors.LoginFailure:
        print(f"{Colors.RED}Invalid Discord token in config.json.{Colors.RESET}")
        wait_enter()
        return []
    except Exception as e:
        print(f"{Colors.RED}Unexpected Discord error: {e}{Colors.RESET}")
        wait_enter()
        return []

    return getattr(client, "cleaned_links", [])

# ---------------- Settings menu ----------------
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
        audio_only_local = bool(config.get("audio_only"))
        audio_only_label = f"{Colors.GREEN}On{Colors.RESET}" if audio_only_local else f"{Colors.YELLOW}Off{Colors.RESET}"
        embed_cover_local = bool(config.get("embed_mp3_cover", True))
        embed_cover_label = f"{Colors.GREEN}On{Colors.RESET}" if embed_cover_local else f"{Colors.YELLOW}Off{Colors.RESET}"
        multi_local = bool(config.get("multi_download"))
        multi_label = f"{Colors.GREEN}On{Colors.RESET}" if multi_local else f"{Colors.YELLOW}Off{Colors.RESET}"
        max_conc_local = int(config.get("max_concurrent_downloads") or 3)

        entries = [
            ("Bandwidth limit", rate_label_colored),
            ("Download path", str(config.get('download_path', '') or '')),
            ("Discord bot token", str(config.get('discord_bot_token', '') or '')),
            ("Discord channel ID", str(config.get('discord_channel_id', '') or '')),
            ("Only audio", audio_only_label),
            ("MP3 cover embedding", embed_cover_label),
            ("Multi download", multi_label),
            ("Max concurrent downloads", str(max_conc_local)),
        ]
        _clear()
        print(f"{Colors.CYAN}------------------- Settings --------------------{Colors.RESET}")
        label_width = max((len(label) for label, _ in entries), default=0)
        for label, value in entries:
            print(f"  - {label:<{label_width}} : {value}")
        print(f"{Colors.CYAN}--------------------------------------------------{Colors.RESET}")

    entries = []
    label_width = 0
    _render()

    while True:
        print("Choose an option:")
        print("  [1] Change download path")
        print("  [2] Set/Change Discord bot token")
        print("  [3] Set/Change Discord channel ID")
        print("  [4] Global bandwidth limit")
        print("  [5] Toggle Only audio")
        print("  [6] Toggle MP3 cover embedding")
        print("  [7] Toggle Multi download")
        print("  [8] Set Max concurrent downloads")
        print("  [0] Back to menu")
        print(f"{Colors.CYAN}--------------------------------------------------{Colors.RESET}")
        choice = input(f"{Colors.CYAN}Selection: {Colors.RESET}").strip().lower()

        if choice == '0':
            break
        if choice not in {'1','2','3','4','5','6','7','8'}:
            _clear()
            print(f"{Colors.RED}Invalid selection.{Colors.RESET}")
            _render()
            continue

        if choice == '1':
            _clear()
            print("Selection: 1")
            new_path = input(f"{Colors.CYAN}Enter new download path: {Colors.RESET}").strip()
            if new_path == "":
                print(f"{Colors.YELLOW}No changes.{Colors.RESET}")
            else:
                current_path = str(config.get("download_path", "") or "")
                normalized = str(Path(new_path).resolve()).replace('\\', '/')
                if normalized == current_path:
                    print(f"{Colors.YELLOW}No changes.{Colors.RESET}")
                elif is_valid_download_path(new_path):
                    config["download_path"] = normalized
                    save_config(config)
                    print(f"{Colors.GREEN}Download path updated.{Colors.RESET}")
                else:
                    print(f"{Colors.RED}Invalid or not writable.{Colors.RESET}")
            _render()

        elif choice == '2':
            _clear()
            print("Selection: 2")
            current = str(config.get("discord_bot_token", "") or "")
            token = input(f"{Colors.CYAN}Enter Discord bot token: {Colors.RESET}").strip()
            if token == "" or token == current:
                print(f"{Colors.YELLOW}No changes.{Colors.RESET}")
            else:
                config["discord_bot_token"] = token
                save_config(config)
                print(f"{Colors.GREEN}Discord bot token updated.{Colors.RESET}")
            _render()

        elif choice == '3':
            _clear()
            print("Selection: 3")
            current = str(config.get("discord_channel_id", "") or "")
            cid = input(f"{Colors.CYAN}Enter Discord channel ID: {Colors.RESET}").strip()
            if cid == "" or cid == current:
                print(f"{Colors.YELLOW}No changes.{Colors.RESET}")
            else:
                if not cid.isdigit():
                    print(f"{Colors.RED}Invalid channel ID (numeric).{Colors.RESET}")
                else:
                    config["discord_channel_id"] = cid
                    save_config(config)
                    print(f"{Colors.GREEN}Discord channel ID updated.{Colors.RESET}")
            _render()

        elif choice == '4':
            _clear()
            print("Selection: 4")
            print("Enter global bandwidth limit in MB/s (0 = Unlimited). Empty = cancel.")
            raw = input(f"{Colors.CYAN}MB/s: {Colors.RESET}").strip()
            if raw == "":
                print(f"{Colors.YELLOW}No changes.{Colors.RESET}")
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
                    print(f"{Colors.YELLOW}No changes.{Colors.RESET}")
                else:
                    config["max_download_rate_bps"] = new_bps
                    save_config(config)
                    print(f"{Colors.GREEN}Bandwidth updated to {_rate_label(new_bps)}.{Colors.RESET}")
            except ValueError:
                print(f"{Colors.RED}Invalid number.{Colors.RESET}")
            _render()

        elif choice == '5':
            _clear()
            print("Selection: 5")
            config["audio_only"] = not bool(config.get("audio_only"))
            save_config(config)
            state = "On" if config["audio_only"] else "Off"
            print(f"{Colors.GREEN}Only audio: {state}{Colors.RESET}")
            _render()

        elif choice == '6':
            _clear()
            print("Selection: 6")
            config["embed_mp3_cover"] = not bool(config.get("embed_mp3_cover", True))
            save_config(config)
            state = "On" if config["embed_mp3_cover"] else "Off"
            print(f"{Colors.GREEN}MP3 cover embedding: {state}{Colors.RESET}")
            _render()

        elif choice == '7':
            _clear()
            print("Selection: 7")
            config["multi_download"] = not bool(config.get("multi_download"))
            save_config(config)
            state = "On" if config["multi_download"] else "Off"
            print(f"{Colors.GREEN}Multi download: {state}{Colors.RESET}")
            _render()

        elif choice == '8':
            _clear()
            print("Selection: 8")
            print("Enter max concurrent downloads (1-12). Empty = cancel.")
            raw = input(f"{Colors.CYAN}Count: {Colors.RESET}").strip()
            if raw == "":
                print(f"{Colors.YELLOW}No changes.{Colors.RESET}")
                _render()
                continue
            try:
                v = int(raw)
                if v < 1 or v > 12:
                    print(f"{Colors.RED}Invalid value (1-12).{Colors.RESET}")
                else:
                    config["max_concurrent_downloads"] = v
                    save_config(config)
                    print(f"{Colors.GREEN}Max concurrent set to {v}.{Colors.RESET}")
            except ValueError:
                print(f"{Colors.RED}Invalid number.{Colors.RESET}")
            _render()

# ---------------- Common UI prompt helper ----------------
def prompt_start_or_back():
    print(f"{Colors.CYAN}Press Enter to start download or press B to return...{Colors.RESET}", end="", flush=True)
    result = _wait_for_enter_or_char("b")
    print()
    return result == "enter"

# ---------------- Process links ----------------
async def process_links(links, config):
    seen_raw = set()
    normalized = []
    for raw in links:
        cu = clean_url(raw)
        if cu and cu not in seen_raw:
            seen_raw.add(cu)
            normalized.append(cu)

    final_queue = []
    seen_in_batch = set()
    for u in normalized:
        if not u.startswith(("http://", "https://")):
            print(f"{Colors.RED}    - Invalid link (http/https required){Colors.RESET}")
            print(f"{Colors.YELLOW}      - Link: {u}{Colors.RESET}")
            continue
        if u in seen_in_batch:
            print(f"{Colors.RED}    - Duplicate link skipped{Colors.RESET}")
            print(f"{Colors.YELLOW}      - Link: {u}{Colors.RESET}")
            continue
        seen_in_batch.add(u)
        final_queue.append(u)

    total = len(final_queue)
    if total == 0:
        return

    multi_mode = bool(config.get("multi_download"))
    max_conc = int(config.get("max_concurrent_downloads") or 3)

    if not multi_mode or total == 1:
        idx_seq = 0
        for url in final_queue:
            idx_seq += 1
            try:
                success, message, file_size, video_duration = await asyncio.to_thread(
                    download_universal_video, url, config
                )
            except Exception as e:
                print(f"{Colors.RED}    - Download failed ({idx_seq}/{total}){Colors.RESET}")
                print(f"{Colors.RED}      - Error: {e}{Colors.RESET}")
                print(f"{Colors.YELLOW}      - Link: {url}{Colors.RESET}")
                continue

            if success:
                try:
                    size_str = format_bytes(file_size)
                    length_str = format_seconds(video_duration)
                    print(f"{Colors.GREEN}    - Download completed ({idx_seq}/{total}){Colors.RESET}")
                    print(f"{Colors.GREEN}      - Size: {size_str}{Colors.RESET}")
                    print(f"{Colors.GREEN}      - Length: {length_str}{Colors.RESET}")
                except Exception:
                    pass
            else:
                print(f"{Colors.RED}    - Download failed ({idx_seq}/{total}){Colors.RESET}")
                if message:
                    print(f"{Colors.RED}      - Error: {message}{Colors.RESET}")
                print(f"{Colors.YELLOW}      - Link: {url}{Colors.RESET}")
        return

    sem = asyncio.Semaphore(max(1, max_conc))
    counter_lock = asyncio.Lock()
    completed = 0

    async def next_done():
        nonlocal completed
        async with counter_lock:
            completed += 1
            return completed

    async def worker(url):
        async with sem:
            try:
                success, message, file_size, video_duration = await asyncio.to_thread(
                    download_universal_video, url, config
                )
            except Exception as e:
                c = await next_done()
                print(f"{Colors.RED}    - Download failed ({c}/{total}){Colors.RESET}")
                print(f"{Colors.RED}      - Error: {e}{Colors.RESET}")
                print(f"{Colors.YELLOW}      - Link: {url}{Colors.RESET}")
                return
            if success:
                try:
                    size_str = format_bytes(file_size)
                    length_str = format_seconds(video_duration)
                    c = await next_done()
                    print(f"{Colors.GREEN}    - Download completed ({c}/{total}){Colors.RESET}")
                    print(f"{Colors.GREEN}      - Size: {size_str}{Colors.RESET}")
                    print(f"{Colors.GREEN}      - Length: {length_str}{Colors.RESET}")
                except Exception:
                    pass
            else:
                c = await next_done()
                print(f"{Colors.RED}    - Download failed ({c}/{total}){Colors.RESET}")
                if message:
                    print(f"{Colors.RED}      - Error: {message}{Colors.RESET}")
                print(f"{Colors.YELLOW}      - Link: {url}{Colors.RESET}")

    await asyncio.gather(*(worker(u) for u in final_queue))

# ---------------- UI helpers ----------------
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
r" _____ _____ _____ _____ _____ _____ _____ _____ __",
r"|  |  |   | |     |  |  |   __| __  |   __|  _  |  |",
r"|  |  | | | |-   -|  |  |   __|    -|__   |     |  |__",
r"|_____|_|___|_____|\___/|_____|__|__|_____|__|__|_____|",
    ]
    for l in header_lines:
        print(f"{Colors.CYAN}{l}{Colors.RESET}")
    try:
        count_today, size_today = get_today_stats()
        stats_line = f"Daily Downloads Today: {count_today} | Total Size Today: {format_bytes(size_today)}"
        print(stats_line)
    except Exception:
        pass
    if not check_ffmpeg():
        print(f"{Colors.YELLOW}WARNING: FFmpeg not found. Conversion may fail.{Colors.RESET}")

def select_txt_file():
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.update()
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        root.destroy()
        if not file_path:
            print(f"{Colors.YELLOW}No file selected.{Colors.RESET}")
            return None
        if not file_path.lower().endswith(".txt"):
            print(f"{Colors.RED}Invalid file selected, Please choose a .txt file.{Colors.RESET}")
            return None
        return file_path
    except Exception:
        try:
            fp = input(f"{Colors.CYAN}Enter .txt filename: {Colors.RESET}").strip()
            if not fp:
                print(f"{Colors.YELLOW}No file provided.{Colors.RESET}")
                return None
            if not fp.lower().endswith(".txt"):
                print(f"{Colors.RED}Invalid file (need .txt).{Colors.RESET}")
                return None
            if os.path.exists(fp):
                return fp
            print(f"{Colors.RED}File not found: {fp}{Colors.RESET}")
            return None
        except Exception:
            return None

# ---------------- Main loop ----------------
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
        download_path_input = input(f"{Colors.CYAN}Enter download path: {Colors.RESET}")
        if not is_valid_download_path(download_path_input):
            print(f"{Colors.RED}Path invalid or not writable.{Colors.RESET}")
            continue
        download_path = str(Path(download_path_input).resolve())
        config["download_path"] = download_path.replace('\\', '/')
        save_config(config)

    render_header(config)

    while True:
        links_to_download = []
        user_choice = input(f"""
{Colors.CYAN}----------------------------------------------------{Colors.RESET}
  {Colors.CYAN}[1] Enter a link{Colors.RESET}
  {Colors.CYAN}[2] From a .txt file{Colors.RESET}
  {Colors.CYAN}[3] From a Discord channel{Colors.RESET}
  {Colors.CYAN}[S] Settings{Colors.RESET}
{Colors.CYAN}----------------------------------------------------{Colors.RESET}
{Colors.CYAN}Selection: {Colors.RESET}""").strip().lower()

        if user_choice not in {'1', '2', '3', 's'}:
            print(f"{Colors.RED}Invalid selection (1/2/3/s).{Colors.RESET}")
            input(f"{Colors.CYAN}Press Enter to return...{Colors.RESET}")
            render_header(config)
            continue

        if user_choice == '1':
            first_loop = True
            while True:
                if first_loop:
                    print(f"{Colors.CYAN}Enter the link{Colors.RESET}")
                    user_input = input().strip()
                else:
                    print(f"{Colors.CYAN}Enter another link or press Enter to return...{Colors.RESET}")
                    user_input = input().strip()
                if user_input == "":
                    render_header(config)
                    break
                links_to_download = [user_input]
                await process_links(links_to_download, config)
                first_loop = False
            continue

        elif user_choice == '2':
            file_name = select_txt_file()
            if (not file_name) or (not os.path.exists(file_name)):
                print(f"{Colors.YELLOW}No valid file selected.{Colors.RESET}")
                wait_enter()
                render_header(config)
                continue
            collected = []
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    for line in f:
                        url = line.strip()
                        if url:
                            collected.append(url)
            except Exception as e:
                print(f"{Colors.RED}Error reading file: {e}{Colors.RESET}")
                wait_enter()
                render_header(config)
                continue
            links_to_download = collected
            if not links_to_download:
                print(f"{Colors.RED}No valid links in file.{Colors.RESET}")
                input(f"{Colors.CYAN}Press Enter to return...{Colors.RESET}")
                render_header(config)
                continue
            else:
                if not prompt_start_or_back():
                    render_header(config)
                    continue

        elif user_choice == '3':
            links_to_download = await get_links_from_discord(config)
            if links_to_download:
                if not prompt_start_or_back():
                    render_header(config)
                    continue
            else:
                print(f"{Colors.YELLOW}No links found / Discord access failed.{Colors.RESET}")
                wait_enter()
                render_header(config)
                continue
        else:
            open_settings_menu(config)
            render_header(config)
            continue

        if not links_to_download:
            continue

        await process_links(links_to_download, config)

        input(f"\n{Colors.CYAN}Press Enter to return...{Colors.RESET}")
        render_header(config)

_INTERFACE_HOLDERS = (QuietLogger.debug, QuietLogger.warning, QuietLogger.error, download_universal_video)

if __name__ == "__main__":
    asyncio.run(main())
