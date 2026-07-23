# filter_bot

A small Discord bot that watches the [speedyapply](https://speedyapply.com) job feed and reposts only the Canadian internships into a separate channel.

speedyapply posts every new internship it finds into one channel, worldwide. Most of them aren't relevant for people only looking in Canada. This bot reads that once an hour and forwards just the Canadian ones somewhere quieter.

## How it works

Every run:

1. Fetch the last 100 messages from the speedyapply channel
2. Ignore anything already handled (see [the marker](#the-marker) below)
3. Keep only messages posted by the speedyapply bot itself
4. Read the `Location` field out of each job's embed
5. If the location matches a Canadian keyword (`canada`, `toronto`, `vancouver`, etc), post the
   job title and location to the Canada channel

**The marker:** `last_seen_id.json` stores the ID of the newest message already handled to keep track of already seen posts. Discord IDs increase over time, so anything smaller is old news. The ID only updates after posting succeeds, so a failed run retries instead of skipping.

## Scheduling

The bot runs hourly on GitHub Actions (`.github/workflows/filter_jobs.yml`), which installs dependencies, runs the script, and commits the updated marker back to the repo.

GitHub's own `schedule:` trigger isn't used since it often skips runs and is unreliable. Instead a [cron-job.org](https://cron-job.org) job POSTs to the workflow's `dispatches` endpoint every hour, which is why the workflow declares `workflow_dispatch`.

## Setup

See [SETUP.md](SETUP.md) for the full installation guide if you want to add this Discord bot into your own servers. It details the specifics about permissions, running the bot, and the hourly trigger.

## Files

| File | |
|---|---|
| `filter_jobs.py` | the whole bot |
| `last_seen_id.json` | the marker, committed back after each run |
| `token.env` | your bot token (gitignored) |
| `requirements.txt` | `requests`, `python-dotenv` |
| `.github/workflows/filter_jobs.yml` | the hourly run |
| `SETUP.md` | setup instructions |

## Known limits

- Only fetches the most recent 100 messages, so a long outage could miss older jobs
- A rate-limited post fails the run rather than retrying. The next run picks it up
- A job whose text exceeds Discord's 2000 character limit would fail every run
