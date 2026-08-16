# AK Liquidity Bot

A Python bot that monitors liquidity levels on Novig sports betting markets and posts Discord alerts whenever a market's liquidity shifts significantly. This helps users catch meaningful market moves in real time.

## Overview

Built for a client, this bot polls Novig for mainline and prop market data across supported leagues, tracks each market's liquidity difference in Redis, and sends a Discord alert whenever that difference changes by more than a configured threshold. New markets are also announced as soon as they're picked up.

## Features

- **Liquidity Monitoring** - Tracks liquidity differences per market and flags significant changes
- **Multi-League Support** - Filter configs included for NFL, NBA, NHL, MLB, NCAAF, NCAAB, WNBA, and UFC
- **Mainlines & Props** - Separately configurable thresholds for mainline markets vs. player props
- **Stateful Tracking via Redis** - Each league uses its own Redis database to track known markets, with keys set to expire shortly after game start
- **New Market Alerts** - Automatically announces newly tracked markets, not just changes to existing ones
- **Async Data Fetching** - Pulls filtered market data concurrently for faster refresh cycles
- **Discord Alerts** - Sends formatted per-league notifications via Discord

## Tech Stack

- **Language:** Python (async/await)
- **Data Storage:** Redis
- **Task Scheduling:** Celery
- **Discord Integration:** Custom Discord webhook sender


## Getting Started

### Prerequisites

- Python 3.10+
- Redis
- A Discord webhook per league (or shared, depending on configuration)

### Installation

```bash
# Clone the repository
git clone https://github.com/Hurteau101/AK_Liquidity_Bot.git
cd AK_Liquidity_Bot

# Create a virtual environment
python -m venv venv

# Activate it
# Windows - venv\Scripts\activate | Linux - venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root with your Novig API credentials, Discord webhook URLs, and Redis connection details.

### Running the Bot

```bash
python novig_bot.py
```

## How It Works

1. Filter configs (JSON) define which mainline/prop markets to pull per league
2. The bot fetches current market data from Novig, filtered by the configured difference threshold
3. Each market's liquidity difference is compared against the last known value stored in Redis
4. If a market is new, or its liquidity difference has moved past the configured amount, a Discord alert is sent
5. Redis keys automatically expire shortly after each game's start time to keep tracked data current
