# Website Monitor

A Python script that monitors website availability and sends alerts to Slack.

## Features
- Monitors both regular websites and .onion addresses
- Sends alerts to Slack when sites are down
- Provides daily status reports
- Supports custom comments for each monitored site

## Setup
1. Clone the repository
2. Copy `config.sample.json` to `config.json`
3. Edit `config.json` with your Slack webhook URL and sites to monitor
4. Install requirements: `pip install requests socks`
5. Run the script: `python website_monitor.py`

## Configuration
The `config.json` file should contain:
- `slack_webhook_url`: Your Slack webhook URL
- `sites`: Array of sites to monitor, each with:
  - `url`: The website URL
  - `comment`: Optional description of the site 
