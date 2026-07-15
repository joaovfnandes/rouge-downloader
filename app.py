#!/usr/bin/env python3
import json, os, re, socket, sys, threading, time, webbrowser
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, abort, render_template, request, redirect, url_for, send_from_directory
import scraper

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
BUNDLE_ROOT = getattr(sys, "_MEIPASS", APP_ROOT)
DATA_ROOT = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else APP_ROOT
OUT_DIR  = os.path.join(DATA_ROOT, "nhentai_out")
LOG_DIR  = os.path.join(DATA_ROOT, "logs")
TAG_HISTORY_FILE = os.path.join(DATA_ROOT, "tag_history.json")
os.makedirs(LOG_DIR, exist_ok=True)

app = Flask(
    __name__,
    template_folder=os.path.join(BUNDLE_ROOT, "templates"),
    static_folder=os.path.join(BUNDLE_ROOT, "static"),
)
app.config["OUT_DIR"] = OUT_DIR

state = {
    "running": False,
    "paused": False,
    "phase": "idle",
    "tags": "",
    "count": 0,
    "parallel": 1,
    "done": 0,
    "total": 0,
    "current": "",
    "current_id": None,
    "current_title": "",
    "current_page": 0,
    "current_pages": 0,
    "downloaded_pages": 0,
    "failed_pages": 0,
    "active_downloads": 0,
    "current_image": None,
    "recent_downloads": [],
    "log": [],
    "error": "",
    "started_at": 0,
    "finished_at": 0,
}

lock = threading.Lock()
tag_lock = threading.Lock()
pause_requested = threading.Event()
stop_requested = threading.Event()
skip_gallery_requested = threading.Event()

def emit(msg):
    with lock:
        state["log"].append(f"[{time.strftime('%H:%M:%S')}] {msg}")
        if len(state["log"]) > 500:
            state["log"] = state["log"][-500:]

def update_state(**values):
    with lock:
        state.update(values)

def can_continue():
    while pause_requested.is_set():
        if stop_requested.wait(0.2):
            return False
    return not stop_requested.is_set()

def wait_or_stop(seconds):
    return not stop_requested.wait(max(0, seconds))

def register_download(gid, title, page_number, filename):
    item = {
        "id": gid,
        "title": title,
        "page": page_number,
        "filename": filename,
        "url": f"/img/{gid}/{filename}?v={time.time_ns()}",
    }
    with lock:
        state["current_image"] = item
        state["recent_downloads"].insert(0, item)
        state["recent_downloads"] = state["recent_downloads"][:12]

def existing_gallery_ids():
    if not os.path.isdir(OUT_DIR):
        return set()
    ids = set()
    for name in os.listdir(OUT_DIR):
        match = re.match(r"^(\d+)_", name)
        if match and os.path.isdir(os.path.join(OUT_DIR, name)):
            ids.add(int(match.group(1)))
    return ids

def _read_tag_history():
    try:
        with open(TAG_HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and isinstance(data.get("tags"), dict):
            data.setdefault("galleries", {})
            return data
    except (OSError, ValueError, TypeError):
        pass
    return {"version": 1, "galleries": {}, "tags": {}}

def get_tag_suggestions(limit=200):
    with tag_lock:
        records = list(_read_tag_history()["tags"].values())
    records.sort(key=lambda item: (-int(item.get("count", 0)), -float(item.get("last_seen", 0)), item.get("name", "")))
    return records[:limit]

def record_gallery_tags(gid, metadata):
    discovered = {
        str(item.get("name", "")).strip().lower()
        for item in metadata.get("tags", [])
        if item.get("type") == "tag" and str(item.get("name", "")).strip()
    }
    if not discovered:
        return False
    gallery_key = str(int(gid))
    with tag_lock:
        history = _read_tag_history()
        if gallery_key in history["galleries"]:
            return False
        now = time.time()
        history["galleries"][gallery_key] = sorted(discovered)
        for name in discovered:
            entry = history["tags"].setdefault(name, {"name": name, "count": 0, "last_seen": 0})
            entry["count"] = int(entry.get("count", 0)) + 1
            entry["last_seen"] = now
        temp_file = f"{TAG_HISTORY_FILE}.tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2, sort_keys=True)
        os.replace(temp_file, TAG_HISTORY_FILE)
    return True

def get_gallery_tag_map():
    with tag_lock:
        galleries = dict(_read_tag_history().get("galleries", {}))
    result = {}
    for gid, names in galleries.items():
        try:
            result[int(gid)] = [str(name) for name in names]
        except (TypeError, ValueError):
            continue
    return result

def find_gallery_dir(gid):
    if not os.path.isdir(OUT_DIR):
        return None
    prefix = f"{int(gid)}_"
    for name in os.listdir(OUT_DIR):
        if name.startswith(prefix) and os.path.isdir(os.path.join(OUT_DIR, name)):
            return os.path.join(OUT_DIR, name)
    return None

def list_galleries():
    if not os.path.isdir(OUT_DIR):
        return []
    tag_map = get_gallery_tag_map()
    out = []
    for name in sorted(os.listdir(OUT_DIR)):
        full = os.path.join(OUT_DIR, name)
        if not os.path.isdir(full):
            continue
        m = re.match(r"^(\d+)_(.+)$", name)
        if not m:
            continue
        gid = int(m.group(1))
        title = m.group(2).replace("_", " ")
        files = [f for f in os.listdir(full) if f.lower().endswith((".webp", ".jpg", ".jpeg", ".png"))]
        files.sort()
        out.append({"id": gid, "title": title, "folder": name, "pages": len(files), "first": files[0] if files else None, "tags": tag_map.get(gid, [])})
    return out

def run_scrape(tags, count, delay, parallel, ua):
    try:
        pause_requested.clear()
        stop_requested.clear()
        skip_gallery_requested.clear()
        update_state(
            running=True, paused=False, phase="searching", tags=tags, count=count,
            parallel=parallel,
            done=0, total=0, current="", current_id=None,
            current_title="", current_page=0, current_pages=0,
            downloaded_pages=0, failed_pages=0, active_downloads=0, current_image=None,
            recent_downloads=[], error="",
            started_at=time.time(), finished_at=0,
        )

        os.makedirs(OUT_DIR, exist_ok=True)
        manifest = os.path.join(OUT_DIR, "manifest.jsonl")

        with open(manifest, "a", encoding="utf-8") as logf:
            existing_ids = existing_gallery_ids()
            results = list(scraper.search(tags, count, ua, delay, exclude_ids=existing_ids))
            galleries = [g for g in results if int(g["id"]) not in existing_ids][:count]
            update_state(total=len(galleries))
            emit(f"search ok: {len(galleries)} galerias pra '{tags}'")
            if not galleries:
                return

            for gallery_index, g in enumerate(galleries, start=1):
                if not can_continue():
                    break
                gid, mid = g["id"], g["media_id"]
                title = g.get("english_title") or g.get("japanese_title") or f"gallery_{gid}"
                folder = os.path.join(OUT_DIR, f"{gid}_{scraper.safe(title)}")
                os.makedirs(folder, exist_ok=True)
                update_state(
                    phase="metadata", current=f"{gid} {title}",
                    current_id=gid, current_title=title, current_page=0,
                    current_pages=0,
                )

                try:
                    meta = json.loads(scraper.http(f"{scraper.API}/galleries/{gid}", ua))
                except Exception as e:
                    emit(f"[{gid}] metadata falhou: {e}")
                    update_state(done=gallery_index)
                    continue

                pages = meta.get("pages", [])
                update_state(phase="downloading", current_pages=len(pages))
                logf.write(json.dumps({
                    "id": gid, "media_id": mid, "title": title,
                    "num_pages": len(pages), "folder": folder
                }, ensure_ascii=False) + "\n")
                logf.flush()
                emit(f"[{gid}] {title} ({len(pages)} pgs)")

                def download_page(p):
                    if not can_continue() or skip_gallery_requested.is_set():
                        return "skipped"
                    num, path = p["number"], p["path"]
                    ext = path.rsplit(".", 1)[-1]
                    filename = f"{num:04d}.{ext}"
                    out = os.path.join(folder, filename)
                    with lock:
                        state["active_downloads"] += 1
                    try:
                        if os.path.exists(out):
                            with lock:
                                state["downloaded_pages"] += 1
                            register_download(gid, title, num, filename)
                            return "existing"
                        try:
                            data = scraper.http(f"{scraper.IMG}/{path}", ua)
                            with open(out, "wb") as f:
                                f.write(data)
                            with lock:
                                state["downloaded_pages"] += 1
                            register_download(gid, title, num, filename)
                            return "downloaded"
                        except Exception as e:
                            with lock:
                                state["failed_pages"] += 1
                            emit(f"[{gid}] p{num} falhou: {e}")
                            return "failed"
                    finally:
                        with lock:
                            state["active_downloads"] = max(0, state["active_downloads"] - 1)
                            state["current_page"] += 1
                        wait_or_stop(delay)

                results_for_gallery = []
                with ThreadPoolExecutor(max_workers=parallel, thread_name_prefix="photo") as pool:
                    futures = [pool.submit(download_page, p) for p in pages]
                    for future in as_completed(futures):
                        results_for_gallery.append(future.result())

                if any(result in ("downloaded", "existing") for result in results_for_gallery):
                    if record_gallery_tags(gid, meta):
                        emit(f"[{gid}] novas tags salvas para buscas futuras.")

                if stop_requested.is_set():
                    break
                if skip_gallery_requested.is_set():
                    emit(f"[{gid}] galeria pulada.")
                    skip_gallery_requested.clear()
                update_state(done=gallery_index)
                if not wait_or_stop(delay):
                    break
        emit("download parado." if stop_requested.is_set() else "fim.")
    except Exception as e:
        update_state(error=str(e), phase="error")
        emit(f"ERRO: {e}")
    finally:
        with lock:
            state["running"] = False
            state["paused"] = False
            state["finished_at"] = time.time()
            if stop_requested.is_set():
                state["phase"] = "cancelled"
            elif state["phase"] != "error":
                state["phase"] = "complete" if state["total"] else "empty"
        pause_requested.clear()
        skip_gallery_requested.clear()

@app.route("/", methods=["GET"])
def index():
    galleries = list_galleries()
    return render_template("index.html", galleries=galleries, state=state, tag_suggestions=get_tag_suggestions())

@app.route("/collection")
def collection():
    return render_template("collection.html", galleries=list_galleries())

@app.route("/scrape", methods=["POST"])
def scrape():
    if state["running"]:
        return redirect(url_for("index"))
    tags  = request.form.get("tags", "").strip()
    count = int(request.form.get("count", "5"))
    delay = float(request.form.get("delay", "1.0"))
    parallel = max(1, min(8, int(request.form.get("parallel", "3"))))
    if not tags or count < 1:
        return redirect(url_for("index"))
    with lock:
        state["log"] = []
    t = threading.Thread(target=run_scrape, args=(tags, count, delay, parallel, scraper.UA), daemon=True)
    t.start()
    return redirect(url_for("index"))

@app.route("/control/pause", methods=["POST"])
def control_pause():
    with lock:
        if not state["running"]:
            return {"ok": False, "message": "Nenhum download em andamento."}, 409
        if state["paused"]:
            state["paused"] = False
            state["phase"] = "downloading"
            pause_requested.clear()
            message = "Download retomado."
        else:
            state["paused"] = True
            state["phase"] = "paused"
            pause_requested.set()
            message = "Download pausado."
        paused = state["paused"]
    emit(message)
    return {"ok": True, "paused": paused, "message": message}

@app.route("/control/stop", methods=["POST"])
def control_stop():
    with lock:
        if not state["running"]:
            return {"ok": False, "message": "Nenhum download em andamento."}, 409
        state["phase"] = "stopping"
        state["paused"] = False
        stop_requested.set()
        pause_requested.clear()
    emit("Parada solicitada; finalizando o arquivo atual.")
    return {"ok": True, "message": "O download será parado após o arquivo atual."}

@app.route("/control/skip-gallery", methods=["POST"])
def control_skip_gallery():
    with lock:
        if not state["running"]:
            return {"ok": False, "message": "Nenhum download em andamento."}, 409
        state["phase"] = "skipping"
        state["paused"] = False
        skip_gallery_requested.set()
        pause_requested.clear()
    emit("Pulando galeria; finalizando as fotos que já começaram.")
    return {"ok": True, "message": "A próxima galeria começará após as fotos atuais."}

@app.route("/g/<int:gid>")
def gallery(gid):
    folder = find_gallery_dir(gid)
    if not folder:
        abort(404)
    files = sorted(f for f in os.listdir(folder) if f.lower().endswith((".webp", ".jpg", ".jpeg", ".png")))
    title = os.path.basename(folder).split("_", 1)[-1].replace("_", " ")
    return render_template("gallery.html", gid=gid, title=title, files=files)

@app.route("/img/<int:gid>/<path:filename>")
def image(gid, filename):
    folder = find_gallery_dir(gid)
    if not folder or not os.path.isfile(os.path.join(folder, filename)):
        abort(404)
    return send_from_directory(folder, filename)

@app.route("/status")
def status():
    with lock:
        snapshot = dict(state)
        snapshot["log"] = state["log"][-60:]
    snapshot["tag_suggestions"] = get_tag_suggestions()
    now = time.time()
    end = now if snapshot["running"] else snapshot["finished_at"] or now
    snapshot["elapsed"] = max(0, int(end - snapshot["started_at"])) if snapshot["started_at"] else 0
    if snapshot["current_pages"]:
        snapshot["page_percent"] = min(100, round(snapshot["current_page"] / snapshot["current_pages"] * 100))
    else:
        snapshot["page_percent"] = 0
    if snapshot["total"]:
        completed = snapshot["done"]
        current_fraction = 0
        if snapshot["running"] and snapshot["current_pages"]:
            completed = max(0, snapshot["done"])
            current_fraction = snapshot["current_page"] / snapshot["current_pages"]
        snapshot["overall_percent"] = min(100, round((completed + current_fraction) / snapshot["total"] * 100))
    else:
        snapshot["overall_percent"] = 0
    return snapshot

if __name__ == "__main__":
    port = 5000
    while port < 5010:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            try:
                probe.bind(("127.0.0.1", port))
                break
            except OSError:
                port += 1
    url = f"http://127.0.0.1:{port}"
    if getattr(sys, "frozen", False):
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    app.run(host="127.0.0.1", port=port, debug=False)
