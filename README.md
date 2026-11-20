# NITRO CITY — 2.5D City Builder

A Persian, browser-based 2.5D city-building game prototype for the NITRO AI repository. The original `شهر اینستاگرامی.html` concept was video/replay-oriented and drawn on a 2D canvas. This version turns its city, economy, followers and likes theme into a playable 3D scene with an isometric/orthographic presentation.

## Run

Open `index.html` through GitHub Pages or a local static web server. The game uses Three.js 0.160.0 and OrbitControls from jsDelivr, so the first load requires an internet connection. A browser with WebGL support is required.

## Current features

- 22×22 buildable city grid with low-poly 3D buildings, shadows, lighting, fog and a soft isometric camera.
- Orbit, pan and zoom camera controls; quick camera rotation and day/night lighting.
- Build menu: homes, apartments, residential towers, shops, police station, hospital, school, farm, power plant, park, cafe, plaza and landmark tower.
- Roads, road-access checks, placement preview, building construction animation, selection, upgrades and demolition refunds.
- City economy: coins, population, food, daily income, city level, XP and rating.
- Animated pedestrians that walk along connected roads; animated fountain and landmark details.
- Social hub with city posts, likes and follow actions; sample community cities and local events.
- Rename city, local save/load with `localStorage`, responsive desktop/mobile interface.

## Important scope note

This is a playable front-end prototype. Save data is local to the current browser. The social feed, likes, follows, sample cities and rewards are simulated locally; they are **not** synchronized between real users. Real accounts, online city visits, persistent global likes/follows, moderation and multiplayer require a backend (for example, an authenticated API plus a database and realtime service). No fake claim of online multiplayer is made.

## Controls

- Left mouse drag: orbit camera.
- Right mouse drag: pan camera.
- Mouse wheel: zoom.
- Select a building from the right panel, then click an empty tile to place it.
- Use the road tool to draw road tiles; most buildings require an adjacent road.
- Select a building to inspect it, upgrade it or demolish it.
- Use the day/night button to change lighting.

## Source preservation

`reference/original-city-instagram.html` preserves the original uploaded HTML concept. `index.html` is the new 2.5D city-builder implementation.
