# CROUS Housing Monitor (Telegram Edition)

Polls a CROUS housing search page (`trouverunlogement.lescrous.fr`) on a
schedule and sends you a Telegram alert with details + a screenshot as soon
as new listings appear.

## Project structure

```
crous-housing-monitor/
├── main.py         # entry point / scheduler loop
├── scraper.py      # loads the page with Selenium (Chrome)
├── analyzer.py      # parses HTML, decides if listings exist, extracts details
├── notifier.py      # sends Telegram messages + screenshots
├── storage.py        # SQLite dedup so you're not re-alerted on the same listing
├── config.py         # loads settings from .env
├── utils.py
├── requirements.txt
├── .env.example
├── screenshots/       # auto-created
└── logs/              # auto-created
```

## 1. Install dependencies

You need Google Chrome (or Chromium) installed on the machine.

```bash
pip install -r requirements.txt
```

`webdriver-manager` will automatically download the matching ChromeDriver on
first run — you don't need to install it separately.

## 2. Set up Telegram

1. Message **@BotFather** on Telegram → `/newbot` → follow the prompts → copy
   the bot token it gives you.
2. Send any message to your new bot (so it can message you back).
3. Get your chat ID by visiting, in a browser:
   `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   and finding the `"chat":{"id": ...}` field in the JSON.

## 3. Configure

```bash
cp .env.example .env
```

Edit `.env` and fill in:

- `TELEGRAM_TOKEN`
- `TELEGRAM_CHAT_ID`
- `TARGET_URL` — go to trouverunlogement.lescrous.fr, set your filters
  (city, price, room type, etc.) in the browser, and paste the resulting URL
  here.
- `CHECK_INTERVAL_SECONDS` — how often to poll. **60 seconds or more is
  recommended.** The tool will refuse to start below 30s — please don't
  hammer the CROUS servers.

## 4. Run

```bash
python main.py
```

It checks immediately on startup, then on the configured interval,
indefinitely. Press `Ctrl+C` to stop.

### Run in the background (Linux/macOS)

```bash
nohup python main.py > output.log 2>&1 &
```

Or use `systemd`, `pm2`, or `screen`/`tmux` for something more robust across
reboots.

## How it works

1. **scraper.py** loads the search page in headless Chrome and waits for the
   results to render (it's a JS-driven Angular app, so a plain HTTP request
   wouldn't see the results).
2. **analyzer.py** checks the rendered text for "aucun logement trouvé"
   (no listings) vs. positive signals, and tries to pull out individual
   listing card text.
3. **storage.py** hashes each listing's text and keeps it in a local SQLite
   file, so you only get alerted once per *new* listing, not every poll
   cycle while it's still available.
4. **notifier.py** sends you a Telegram message with the listing details and
   a screenshot of the page.

## Notes & caveats

- **Selectors may need tweaking.** CROUS's site markup can change. If
  `analyzer.py` stops extracting good detail text, open the page in a
  browser, inspect a listing card's HTML, and update `CARD_SELECTORS` in
  `analyzer.py` accordingly. The "no listings found" detection is more
  robust since it's based on the site's own status text.
- **Be a respectful client.** This uses a single Chrome instance polling on
  a fixed interval — no parallel requests, no aggressive scraping. Please
  keep the interval at 60s+ so you're not putting unnecessary load on a
  public service used by other students.
- **This is for personal use** (monitoring your own housing search), not for
  redistribution or commercial scraping.

## Optional next steps

- Add more filters in `analyzer.py` (e.g. only alert for specific
  arrondissements or price ranges) by inspecting `details` before sending.
- Swap SQLite for a simple JSON file if you don't want an extra dependency.
- Deploy on a small always-on VPS or Raspberry Pi with `systemd` for
  reliability.
