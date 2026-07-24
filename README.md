# Govee Air Quality Dashboard

Automated collection and visualization of air quality data from Govee air quality monitors.

## Features

- **Automated collection**: Scheduled GitHub Actions workflow collects readings every 3 hours
- **Multi-device support**: Tracks data from multiple Govee devices (basement, upstairs, etc.)
- **Real-time dashboard**: Interactive charts showing CO₂, temperature, and humidity
- **14-day history**: Charts display the last 14 days of readings
- **Device comparison**: Side-by-side views of different devices

## Dashboard

### Running Locally

The dashboard **must be served over HTTP** (not opened as a `file://` URL).

**Option 1: Python HTTP Server (recommended)**
```bash
cd /path/to/govee_air_quality
python3 -m http.server 8000
```
Then open http://localhost:8000 in your browser.

**Option 2: Node.js HTTP Server**
```bash
npx http-server
```

**Option 3: GitHub Pages**
Visit: https://sugarsmax.github.io/govee_air_quality/

### What to Look For

- **Status messages**: If charts are blank, check the status text at the bottom of the page for error details
- **Device selector**: Latest readings are shown for the primary device, with a legend showing all devices
- **14-day view**: Charts show only the most recent 14 days to keep performance snappy

## Data Collection

### Workflow

The `.github/workflows/collect.yml` file runs every 3 hours via cron schedule (or manually via `workflow_dispatch`).

**Steps:**
1. Checks out the repo
2. Installs Python dependencies
3. Calls the Govee API to collect readings from all paired devices
4. Appends new readings to `data/readings.json`
5. Commits and pushes updated data

### Setup

1. **Get API Key**: Visit [Govee Developer Platform](https://developer.govee.com) and create an API key
2. **Add Secret**: In GitHub repository settings, add a secret named `GOVEE_API_KEY` with your API key
3. **Verify Collection**: Run a manual workflow dispatch or wait for the next scheduled run

## Readings Format

Each reading in `data/readings.json`:
```json
{
  "ts": "2026-05-24T21:51:04Z",
  "co2": 497,
  "temp_f": 69.98,
  "humidity": 50.5,
  "online": true,
  "device": "basement"
}
```

## Files

- `index.html` — Interactive dashboard (served over HTTP)
- `data/readings.json` — All collected readings (auto-generated)
- `collect_20260501.py` — Collection script (runs via GitHub Actions)
- `.github/workflows/collect.yml` — Scheduled automation
- `govee_api_20260303.py` — Govee API client library
- `requirements.txt` — Python dependencies

## Troubleshooting

### Charts are empty or blank

**Check:**
1. Open browser developer console (F12) and look for errors
2. Verify `data/readings.json` exists and isn't empty: `wc -l data/readings.json`
3. Ensure you're accessing via HTTP, not `file://` protocol
4. Check the status message at the bottom of the dashboard

### No new data

**Check:**
1. Go to GitHub Actions and verify the "Collect Air Quality Reading" workflow ran recently
2. Look for any error logs in the workflow run
3. Verify `GOVEE_API_KEY` secret is set in repository settings
4. Confirm your Govee device is online and paired

### API key errors

1. Double-check your API key is valid at [Govee Developer Platform](https://developer.govee.com)
2. Ensure the secret is named exactly `GOVEE_API_KEY`
3. Try re-generating your API key and updating the secret

## Data Interpretation

**CO₂ Levels (ppm):**
- ≤800: Good
- 801-1000: Acceptable
- 1001-1500: Elevated
- >1500: Concerning

**Color coding** in the dashboard reflects these thresholds.
