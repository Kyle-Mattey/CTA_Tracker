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

## How It Works
1. Sends a GET request to the CTA API with desired station and route data.
2. Parses and formats relevant ETA info.
3. Posts that data to the Geckoboard dataset API for display.

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
