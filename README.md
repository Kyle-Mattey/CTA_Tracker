# CTA Tracker

**Intern Project** — Built during my internship to track and display live Chicago Transit Authority (CTA) train arrival data for nearby stations.

## Overview
This Python script pulls real-time data from the CTA's public Train Tracker API and sends it to a customized [Geckoboard](https://www.geckoboard.com/) dashboard. This allowed our office to view live ETA updates for specific CTA stops near our location.

## Features
- Fetches real-time train arrival data using CTA’s API
- Filters results to only show selected stations and directions
- Formats and sends the data to Geckoboard for live visualization

## Technologies Used
- **Python**
- **Requests** (HTTP library)
- **CTA Train Tracker API**
- **Geckoboard Push API**

## Setup & Environment

Before running the script, create a `.env` file in the root directory with the following:
```txt
CTA_API_KEY=your_cta_api_key
GECKOBOARD_API_KEY=your_geckoboard_api_key
BROWN_WIDGET_KEY=https://push.geckoboard.com/v1/send/…
RED_WIDGET_KEY=https://push.geckoboard.com/v1/send/…
PURPLE_WIDGET_KEY=https://push.geckoboard.com/v1/send/…
```

All credentials are loaded securely using `python-dotenv`, so nothing sensitive is hardcoded.

Then install required packages using:

```bash
pip install -r requirements.txt
```

## How It Works
1. Sends a GET request to the CTA API with desired station and route data.
2. Parses and formats relevant ETA info.
3. Groups and sorts trains by direction, limiting to 5 per direction.
4. Posts that data to the Geckoboard HTML widget for live dashboard display.

## Sample Output
```json
[
  {
    "station": "Clark/Lake",
    "destination": "O'Hare",
    "arrival_time": "3 min"
  },
  ...
]
