import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

API_KEY = os.getenv("CTA_API_KEY")
GECKOBOARD_API_KEY = os.getenv("GECKOBOARD_API_KEY")
BROWN_WIDGET_KEY = os.getenv("BROWN_WIDGET_KEY")
RED_WIDGET_KEY = os.getenv("RED_WIDGET_KEY")
PURPLE_WIDGET_KEY = os.getenv("PURPLE_WIDGET_KEY")

STATIONS = {
    "Brown Line (Chicago)": "40710",
    "Red Line (Chicago/State)": "41450",
    "Purple Line (Chicago)": "40710",
}

ROUTES = "Brn,Red,P"

def fetch_arrival_data(map_id, routes=None):
    base_url = "http://lapi.transitchicago.com/api/1.0/ttarrivals.aspx"
    params = {"key": API_KEY, "mapid": map_id, "rt": routes}
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        return response.text
    else:
        logging.error(f"CTA API Error: {response.status_code}")
        return None

def parse_arrival_data(xml_data):
    root = ET.fromstring(xml_data)
    arrivals = []
    for eta in root.findall(".//eta"):
        route = eta.find("rt").text if eta.find("rt") is not None else "Unknown"
        station_name = eta.find("staNm").text if eta.find("staNm") is not None else "Unknown"
        raw_arrival_time = eta.find("arrT").text if eta.find("arrT") is not None else "Unknown"
        destination = eta.find("destNm").text if eta.find("destNm") is not None else "Unknown"
        train_number = eta.find("rn").text if eta.find("rn") is not None else "Unknown"

        try:
            arrival_time_obj = datetime.strptime(raw_arrival_time, "%Y%m%d %H:%M:%S")
            formatted_arrival_time = arrival_time_obj.strftime("%b %d, %Y - %I:%M %p")
        except ValueError:
            arrival_time_obj = None
            formatted_arrival_time = "Invalid Time"

        arrivals.append({
            "route": route,
            "station": station_name,
            "arrival_time": formatted_arrival_time,
            "arrival_time_obj": arrival_time_obj,
            "destination": destination,
            "train_number": train_number
        })
    return arrivals

def remove_duplicate_trains(arrivals):
    unique_arrivals = {}
    for arrival in arrivals:
        key = (arrival["train_number"], arrival["route"], arrival["destination"])
        if key not in unique_arrivals:
            unique_arrivals[key] = arrival
    return list(unique_arrivals.values())

def group_and_sort_arrivals_by_line(arrivals, line):
    filtered_trains = [train for train in arrivals if train["route"] == line]
    grouped = {}
    for train in filtered_trains:
        direction = train["destination"]
        if direction not in grouped:
            grouped[direction] = []
        grouped[direction].append(train)
    for direction in grouped:
        grouped[direction].sort(key=lambda x: x["arrival_time_obj"] or datetime.max)
        grouped[direction] = grouped[direction][:5]
    return grouped

def push_to_geckoboard_for_line(line, line_name, line_color, arrivals, widget_key, directions):
    headers = {"Content-Type": "application/json"}
    html_block = f"<div style='font-family: Arial, sans-serif;'>"
    for direction in directions:
        html_block += (
            f"<h2 style='color: {line_color}; font-weight: bold; font-size: 40px;'>"
            f"{line_name} - {direction}</h2>"
        )
        if direction not in arrivals or not arrivals[direction]:
            html_block += (
                "<table style='width: 100%; border-collapse: collapse; text-align: left;'>"
                "<thead><tr>"
                "<th style='padding: 10px; font-size: 30px;'>Train #</th>"
                "<th style='padding: 10px; font-size: 30px;'>Arrival Time</th>"
                "</tr></thead><tbody>"
                "<tr><td style='padding: 10px; font-size: 30px;'>No trains</td>"
                "<td style='padding: 10px; font-size: 30px;'>N/A</td></tr>"
                "</tbody></table><br>"
            )
        else:
            html_block += (
                "<table style='width: 100%; border-collapse: collapse; text-align: left;'>"
                "<thead><tr>"
                "<th style='padding: 10px; font-size: 30px;'>Train #</th>"
                "<th style='padding: 10px; font-size: 30px;'>Arrival Time</th>"
                "</tr></thead><tbody>"
            )
            for train in arrivals[direction]:
                html_block += (
                    "<tr>"
                    f"<td style='padding: 10px; font-size: 30px;'>{train['train_number']}</td>"
                    f"<td style='padding: 10px; font-size: 30px;'>{train['arrival_time']}</td>"
                    "</tr>"
                )
            html_block += "</tbody></table><br>"
    html_block += "</div>"

    payload = {
        "api_key": GECKOBOARD_API_KEY,
        "data": {
            "item": [{"text": html_block}]
        }
    }

    response = requests.post(widget_key, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        logging.info(f"Data successfully pushed to {line_name} widget!")
    else:
        logging.error(f"Error pushing to {line_name} widget: {response.status_code}, {response.text}")

def main():
    all_arrivals = []
    for station_name, map_id in STATIONS.items():
        logging.info(f"Fetching data for {station_name}...")
        xml_data = fetch_arrival_data(map_id, ROUTES)
        if xml_data:
            arrivals = parse_arrival_data(xml_data)
            all_arrivals.extend(arrivals)

    all_arrivals = remove_duplicate_trains(all_arrivals)

    brown_arrivals = group_and_sort_arrivals_by_line(all_arrivals, "Brn")
    push_to_geckoboard_for_line("Brn", "Brown Line", "#63361c", brown_arrivals, BROWN_WIDGET_KEY, ["Kimball", "Loop"])

    red_arrivals = group_and_sort_arrivals_by_line(all_arrivals, "Red")
    push_to_geckoboard_for_line("Red", "Red Line", "red", red_arrivals, RED_WIDGET_KEY, ["Howard", "95th/Dan Ryan"])

    purple_arrivals = group_and_sort_arrivals_by_line(all_arrivals, "P")
    push_to_geckoboard_for_line("P", "Purple Line", "purple", purple_arrivals, PURPLE_WIDGET_KEY, ["Linden", "Loop"])

if __name__ == "__main__":
    main()