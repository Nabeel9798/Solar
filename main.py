import os
import json
from flask import Flask, jsonify, request
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
from math import sqrt

app = Flask(__name__)

# Google Sheets Authentication using Environment Variable
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Load Google Credentials from Environment Variable
google_creds = json.loads(os.getenv("GOOGLE_CREDENTIALS"))

# Authorize using loaded credentials
creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds, scope)
client = gspread.authorize(creds)

# Open Google Sheet
SHEET_NAME = "Solardata_2"
sheet = client.open(SHEET_NAME).sheet1

# Load the sheet into a dictionary for fast searching
def load_data():
    """Loads Google Sheet data into memory for quick searching."""
    records = sheet.get_all_records()
    data_dict = {}

    for row in records:
        key = (float(row["Latitude"]), float(row["Longitude"]))
        data_dict[key] = row  # Store row as value

    return data_dict

# Load data once (this will make lookups very fast)
data_cache = load_data()

def find_nearest(lat, lon):
    """Finds the nearest latitude and longitude in the dataset."""
    nearest_key = None
    min_distance = float("inf")

    for key in data_cache.keys():
        key_lat, key_lon = key
        distance = sqrt((lat - key_lat) ** 2 + (lon - key_lon) ** 2)

        if distance < min_distance:
            min_distance = distance
            nearest_key = key

    return nearest_key

@app.route("/")
def home():
    return "Flask is running!"

@app.route("/get_data", methods=["GET"])
def get_data():
    start_time = time.time()

    try:
        latitude = float(request.args.get("lat"))
        longitude = float(request.args.get("lon"))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid or missing lat/lon parameters"}), 400

    key = (latitude, longitude)
    result = data_cache.get(key, None)

    if not result:
        nearest_key = find_nearest(latitude, longitude)
        if nearest_key:
            result = data_cache[nearest_key]
            result["nearest_lat"] = nearest_key[0]
            result["nearest_lon"] = nearest_key[1]
            result["message"] = "Exact data not found. Returning nearest coordinate."
        else:
            return jsonify({"error": "No nearby data found"}), 404

    result["execution_time"] = f"{time.time() - start_time:.4f} seconds"
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
