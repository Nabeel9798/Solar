import os
import json
from flask import Flask, jsonify, request
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask_cors import CORS
import time

def find_nearest(lat, lon, data):
    nearest = None
    min_dist = float("inf")
    for (lat_key, lon_key), row in data.items():
        dist = (float(lat) - float(lat_key))**2 + (float(lon) - float(lon_key))**2
        if dist < min_dist:
            min_dist = dist
            nearest = row
    return nearest

app = Flask(__name__)
CORS(app)

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
        key = (str(row["Latitude"]), str(row["Longitude"]))
        data_dict[key] = row

    return data_dict

# Load data once (this will make lookups very fast)
data_cache = load_data()

@app.route("/")
def home():
    return "Flask is running!"

@app.route("/get_data", methods=["GET"])
def get_data():
    start_time = time.time()

    latitude = request.args.get("lat")
    longitude = request.args.get("lon")

    if not latitude or not longitude:
        return jsonify({"error": "Missing lat/lon parameters"}), 400

    key = (latitude, longitude)
    result = data_cache.get(key, None)

    if not result:
        result = find_nearest(latitude, longitude, data_cache)

    result["execution_time"] = f"{time.time() - start_time:.4f} seconds"
    return jsonify(result)

@app.route("/reload_data", methods=["POST"])  # Added reload endpoint
def reload_data():
    global data_cache
    data_cache = load_data()
    return jsonify({"message": "Data reloaded successfully"})

if __name__ == "__main__":
    app.run(debug=True)
