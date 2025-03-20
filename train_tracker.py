import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime

API_KEY = "df1c59a26943401a8e227b49867bb97c"
GECKOBOARD_API_KEY = "33626b97ebe124b67f02855101bb5ee2"
BROWN_WIDGET_KEY = "https://push.geckoboard.com/v1/send/0ff708c9-2528-44a6-bcb1-3236713376c4"
RED_WIDGET_KEY = "https://push.geckoboard.com/v1/send/26b4c37c-cfce-4c7b-b408-59878b59e7be"
PURPLE_WIDGET_KEY = "https://push.geckoboard.com/v1/send/69ba6d1f-d6af-4156-83fe-84f67d99e44d"

STATIONS = {
    "Brown Line (Chicago)": "40710",
    "Red Line (Chicago/State)": "41450",
    "Purple Line (Chicago)": "40710",
}

ROUTES = "Brn,Red,P"  # Brown, Red, and Purple lines


def fetch_arrival_data(map_id, routes=None):
    base_url = "http://lapi.transitchicago.com/api/1.0/ttarrivals.aspx"
    params = {"key": API_KEY, "mapid": map_id, "rt": routes}
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Error: {response.status_code}")
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

        # Format the arrival time
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
    # Filter trains by line
    filtered_trains = [train for train in arrivals if train["route"] == line]

    # Group by direction
    grouped = {}
    for train in filtered_trains:
        direction = train["destination"]
        if direction not in grouped:
            grouped[direction] = []
        grouped[direction].append(train)

    # Sort by arrival time and limit to 5 trains per direction
    for direction in grouped:
        grouped[direction].sort(key=lambda x: x["arrival_time_obj"] or datetime.max)
        grouped[direction] = grouped[direction][:5]

    return grouped


def push_to_geckoboard_for_line(line, line_name, line_color, arrivals, widget_key, directions):
    headers = {"Content-Type": "application/json"}

    html_block = f"<div style='font-family: Arial, sans-serif;'>"

    # Ensure both specified directions always appear for the line
    for direction in directions:
        html_block += (
            f"<h2 style='color: {line_color}; font-weight: bold; font-size: 40px;'>"
            f"{line_name} - {direction}</h2>"
        )
        if direction not in arrivals or not arrivals[direction]:
            # Placeholder if no trains are available for the direction
            html_block += (
                "<table style='width: 100%; border-collapse: collapse; text-align: left;'>"
                "<thead>"
                "<tr>"
                "<th style='padding: 10px; font-size: 30px; border-bottom: 2px solid #ddd;'>Train #</th>"
                "<th style='padding: 10px; font-size: 30px; border-bottom: 2px solid #ddd;'>Arrival Time</th>"
                "</tr>"
                "</thead>"
                "<tbody>"
                "<tr>"
                "<td style='padding: 10px; font-size: 30px;'>No trains</td>"
                "<td style='padding: 10px; font-size: 30px;'>N/A</td>"
                "</tr>"
                "</tbody></table><br>"
            )
        else:
            # Display available trains for the direction
            html_block += (
                "<table style='width: 100%; border-collapse: collapse; text-align: left;'>"
                "<thead>"
                "<tr>"
                "<th style='padding: 10px; font-size: 30px; border-bottom: 2px solid #ddd;'>Train #</th>"
                "<th style='padding: 10px; font-size: 30px; border-bottom: 2px solid #ddd;'>Arrival Time</th>"
                "</tr>"
                "</thead>"
                "<tbody>"
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
            "item": [
                {"text": html_block}
            ]
        }
    }

    response = requests.post(widget_key, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        print(f"Data successfully pushed to {line_name} widget!")
    else:
        print(f"Error pushing to {line_name} widget: {response.status_code}, {response.text}")


def main():
    all_arrivals = []
    for station_name, map_id in STATIONS.items():
        print(f"Fetching data for {station_name}...")
        xml_data = fetch_arrival_data(map_id, ROUTES)
        if xml_data:
            arrivals = parse_arrival_data(xml_data)
            all_arrivals.extend(arrivals)

    all_arrivals = remove_duplicate_trains(all_arrivals)

    # Brown Line - Kimball and Loop
    brown_arrivals = group_and_sort_arrivals_by_line(all_arrivals, "Brn")
    push_to_geckoboard_for_line(
        "Brn", "Brown Line", "#63361c", brown_arrivals, BROWN_WIDGET_KEY, ["Kimball", "Loop"]
    )

    # Red Line - Howard and 95th/Dan Ryan
    red_arrivals = group_and_sort_arrivals_by_line(all_arrivals, "Red")
    push_to_geckoboard_for_line(
        "Red", "Red Line", "red", red_arrivals, RED_WIDGET_KEY, ["Howard", "95th/Dan Ryan"]
    )

    # Purple Line - Linden and Loop
    purple_arrivals = group_and_sort_arrivals_by_line(all_arrivals, "P")
    push_to_geckoboard_for_line(
        "P", "Purple Line", "purple", purple_arrivals, PURPLE_WIDGET_KEY, ["Linden", "Loop"]
    )  


if __name__ == "__main__":
    main()
