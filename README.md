# The Cozy Desk 🕯️

For slow evenings, heavy days, and anyone who needs the internet to be soft for a minute: dreamy cozy places, a tiny comfort ritual for tonight, a gentle prompt to write on, the cutest break we could find, and a few warm little things on sale. Stay as long as you like.

- Live page: https://bishowpratap7.github.io/thecozydesk/
- Run by **Bishow Pandey** — follow on X: https://x.com/bishowppandey
- Sister desks: The Dev Desk (developer news), Scroll Patrol (trending posts & memes), The World Desk (world news), The Stock Desk (stock deep dives), plus The Shopping Desk, The Cozy Desk, The Foodie Desk and The Style Desk

## What's on the desk
- **🕯️ Tonight, Gently**
- **🏡 Cozy Places to Daydream About**
- **🐾 A Little Comfort Break**
- **🧣 Warm Little Finds**

An original nightly journaling prompt, comfort ritual and short attributed quote; cozy place photos from r/CozyPlaces; a cute break from r/aww; warm little finds from community deal feeds.

## How it works
- `tools/scan.py` reads the public sources above (no API keys), writes `data/feed.json`, bakes an SEO summary of every item into `index.html`, and regenerates `feed.xml` and `sitemap.xml`. If a source fails, the desk keeps its last good data and flags it stale.
- A GitHub Actions loop (`.github/workflows/loop-scan.yml`) re-runs the scanner every 30 minutes around the clock and commits only when something changed; each loop job hands off to its successor, so the desk stays current on its own.
- The page is a single static file — no backend, no build step, no tracking.

## Repos
- `thecozydesk` (public) — the live site, served by GitHub Pages
- `the-cozy-desk` (private) — the archive twin

## Good to know
The Cozy Desk is a comfort page, not medical or mental-health advice. Photos belong to their creators and communities; every card links to the original post. If you're having a hard time beyond a cozy evening's help, please contact a professional or a local crisis line.
