#!/usr/bin/env python3
"""
nhentai scraper enxuto via API oficial.
Uso:
  python scraper.py --tags 'tag:"glasses" -tag:"x-ray"' --count 5 --out ./out
  python scraper.py --tags 'tag:"glasses"' --count 1 --out ./out --dry-run
"""
import argparse, json, os, sys, time, urllib.request, urllib.parse

API  = "https://nhentai.net/api/v2"
IMG  = "https://i.nhentai.net"
UA   = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"

def http(url, ua):
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()

def search(query, want, ua, delay, exclude_ids=None):
    exclude_ids = set(exclude_ids or ())
    page, got = 1, 0
    while got < want:
        url = f"{API}/search?query={urllib.parse.quote(query, safe='')}&page={page}"
        try:
            data = json.loads(http(url, ua))
        except Exception as e:
            print(f"  search page {page} falhou: {e}", file=sys.stderr)
            break
        for g in data.get("result", []):
            if int(g["id"]) in exclude_ids:
                continue
            yield g
            got += 1
            if got >= want:
                break
        if not data.get("result"):
            break
        page += 1
        time.sleep(delay)

def safe(name):
    return "".join(c if c.isalnum() or c in " -_()" else "_" for c in name).strip()[:80] or "untitled"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tags",  required=True, help='filtro, ex: tag:"glasses" -tag:"x-ray"')
    ap.add_argument("--count", required=True, type=int, help="qtd de revistas pra baixar")
    ap.add_argument("--out",   default="./nhentai_out")
    ap.add_argument("--delay", type=float, default=1.0)
    ap.add_argument("--dry-run", action="store_true", help="lista o que faria, sem baixar")
    ap.add_argument("--ua", default=UA)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    log = open(os.path.join(args.out, "manifest.jsonl"), "w", encoding="utf-8")

    galleries = list(search(args.tags, args.count, args.ua, args.delay))
    print(f"[search] {len(galleries)} galerias pra: {args.tags}")
    if not galleries:
        return

    for g in galleries:
        gid, mid = g["id"], g["media_id"]
        title = g.get("english_title") or g.get("japanese_title") or f"gallery_{gid}"
        folder = os.path.join(args.out, f"{gid}_{safe(title)}")
        os.makedirs(folder, exist_ok=True)

        try:
            meta = json.loads(http(f"{API}/galleries/{gid}", args.ua))
        except Exception as e:
            print(f"  [{gid}] metadata falhou: {e}", file=sys.stderr)
            continue

        pages = meta.get("pages", [])
        log.write(json.dumps({
            "id": gid, "media_id": mid, "title": title,
            "num_pages": len(pages), "folder": folder
        }, ensure_ascii=False) + "\n")
        log.flush()

        print(f"[{gid}] {title}  ({len(pages)} pgs)")

        if args.dry_run:
            for p in pages[:3]:
                print(f"   -> {IMG}/{p['path']}")
            if len(pages) > 3:
                print(f"   ... +{len(pages)-3} mais")
            continue

        for p in pages:
            num, path = p["number"], p["path"]
            ext = path.rsplit(".", 1)[-1]
            out = os.path.join(folder, f"{num:04d}.{ext}")
            if os.path.exists(out):
                continue
            try:
                data = http(f"{IMG}/{path}", args.ua)
                with open(out, "wb") as f:
                    f.write(data)
                print(f"  {num}/{len(pages)}  {out}")
            except Exception as e:
                print(f"  [{gid}] p{num} falhou: {e}", file=sys.stderr)
            time.sleep(args.delay)
        time.sleep(args.delay)

    log.close()
    print("fim.")

if __name__ == "__main__":
    main()
