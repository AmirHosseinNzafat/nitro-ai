#!/usr/bin/env python3
# NITRO CITY - Local strategy bot
# Python standard library only. No API key or internet connection required.
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import json
import os

ROOT = Path(__file__).resolve().parent
HOST = "127.0.0.1"
PORT = 8765

COSTS = {
    "home": 180, "apartment": 520, "tower": 1300,
    "market": 260, "police": 420, "hospital": 760,
    "school": 480, "farm": 240, "power": 620,
    "park": 160, "cafe": 300, "plaza": 580, "landmark": 1800
}

def make_plan(payload):
    state = payload.get("state") or {}
    buildings = payload.get("buildings") or []
    width = int((payload.get("grid") or {}).get("width", 22))
    height = int((payload.get("grid") or {}).get("height", 22))
    money = max(0, int(state.get("money", 0)))
    pop = max(0, int(state.get("pop", 0)))
    food = max(0, int(state.get("food", 0)))
    level = max(1, int(state.get("level", 1)))

    occupied = {(int(b["x"]), int(b["z"])) for b in buildings
                if "x" in b and "z" in b}
    roads = {(int(b["x"]), int(b["z"])) for b in buildings
             if b.get("type") == "road" and "x" in b and "z" in b}
    counts = {}
    income = 0
    food_prod = 0
    housing = 120
    for b in buildings:
        typ = b.get("type")
        counts[typ] = counts.get(typ, 0) + 1
        lvl = max(1, int(b.get("level", 1)))
        if typ == "home":
            income += 3 * lvl; food_prod -= 2 * lvl; housing += 12 * lvl
        elif typ == "apartment":
            income += 8 * lvl; food_prod -= 8 * lvl; housing += 45 * lvl
        elif typ == "tower":
            income += 20 * lvl; food_prod -= 20 * lvl; housing += 120 * lvl
        elif typ == "market": income += 18 * lvl
        elif typ == "farm": income += 1 * lvl; food_prod += 28 * lvl
        elif typ == "power": income += 12 * lvl
        elif typ == "park": income += 4 * lvl
        elif typ == "cafe": income += 22 * lvl; food_prod -= 1 * lvl
        elif typ == "plaza": income += 12 * lvl
        elif typ == "landmark": income += 55 * lvl
        elif typ == "police": income -= 4 * lvl
        elif typ == "hospital": income -= 8 * lvl
        elif typ == "school": income -= 5 * lvl

    def adjacent_to_road(x, z):
        return any((x + dx, z + dz) in roads for dx, dz in
                   ((1, 0), (-1, 0), (0, 1), (0, -1)))

    def score_tile(x, z):
        # Prefer central, road-accessible parcels.
        center = abs(x - (width - 1) / 2) + abs(z - (height - 1) / 2)
        return center

    actions = []
    summary = "شهر بررسی شد؛ فعلاً نیازی به ساخت‌وساز فوری نیست."
    for _ in range(3):
        # Decide what the city needs most at this moment.
        if food < max(70, pop * 0.65) and counts.get("farm", 0) < 5:
            desired = "farm"
        elif pop >= housing - 15 and counts.get("home", 0) + counts.get("apartment", 0) < 8:
            desired = "home" if level < 2 else "apartment"
        elif income < 45 and counts.get("market", 0) < 4:
            desired = "market"
        elif counts.get("park", 0) < 3:
            desired = "park"
        elif counts.get("cafe", 0) < 3:
            desired = "cafe"
        elif counts.get("farm", 0) < 2 and food_prod < 30:
            desired = "farm"
        elif counts.get("home", 0) < 4:
            desired = "home"
        else:
            desired = "market"

        if desired == "tower" and level < 2:
            desired = "apartment"
        candidates = []
        for z in range(height):
            for x in range(width):
                if (x, z) in occupied:
                    continue
                if adjacent_to_road(x, z):
                    candidates.append((score_tile(x, z), x, z))
        candidates.sort()
        cost = COSTS.get(desired, 999999)
        if candidates and money >= cost:
            _, x, z = candidates[0]
            actions.append({"type": "build", "building": desired, "x": x, "z": z})
            occupied.add((x, z))
            counts[desired] = counts.get(desired, 0) + 1
            money -= cost
            if desired == "farm": food += 28
            elif desired == "home": housing += 12; pop += 12
            elif desired == "apartment": housing += 45; pop += 45
            elif desired == "market": income += 18
            elif desired == "park": income += 4
            elif desired == "cafe": income += 22
            summary = "بر اساس منابع و نیازهای شهر، ساختمان‌های اولویت‌دار انتخاب شدند."
            continue

        # If no road-adjacent parcel exists, extend the road network by one tile.
        road_candidates = []
        for z in range(height):
            for x in range(width):
                if (x, z) in occupied:
                    continue
                if any((x + dx, z + dz) in roads for dx, dz in
                       ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    road_candidates.append((score_tile(x, z), x, z))
        road_candidates.sort()
        if road_candidates and money >= 35:
            _, x, z = road_candidates[0]
            actions.append({"type": "road", "x": x, "z": z})
            occupied.add((x, z)); roads.add((x, z)); money -= 35
            summary = "شبکه جاده برای دسترسی به قطعات تازه گسترش یافت."
        else:
            break

    return {"actions": actions, "summary": summary, "engine": "NITRO Local Strategy 1.0"}

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "http://127.0.0.1:8765")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_POST(self):
        if self.path != "/api/decide":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 1_000_000:
                self.send_error(400, "Invalid request size")
                return
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            result = make_plan(payload)
            body = json.dumps(result, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as exc:
            body = json.dumps({"error": str(exc)}, ensure_ascii=False).encode("utf-8")
            self.send_response(400)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

if __name__ == "__main__":
    os.chdir(ROOT)
    print(f"NITRO AI is running: http://{HOST}:{PORT}")
    print("Open the game at http://127.0.0.1:8765")
    print("Keep this window open while playing. Press Ctrl+C to stop.")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
