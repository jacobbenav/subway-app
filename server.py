from flask import Flask, jsonify
from flask_cors import CORS
import requests
from google.transit import gtfs_realtime_pb2
import time

app = Flask(__name__)
CORS(app)

# --- CONFIGURATION ---
# We added "-trip-updates" to the end of the URL
MTA_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw-trip-updates"

# Change this to your specific Station Stop ID
TARGET_STOP_ID = "423" 

@app.route('/subway-data')
def get_subway_data():
    try:
        response = requests.get(MTA_URL)
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(response.content)

        arrivals = []

        # SAFETY CHECK: Check if the feed actually contains 'trip_update'
        # This prevents the "trip_update" error you just saw.
        if not feed.HasField('trip_update'):
            return jsonify({"error": "Feed does not contain trip updates"}), 500

        for entity in feed.trip_update:
            # Double check this specific entity has stop_time_updates
            if entity.HasField('stop_time_update'):
                for stop_time_update in entity.stop_time_update:
                    if stop_time_update.stop_id == TARGET_STOP_ID:
                        
                        # Get the arrival time (Unix timestamp)
                        arrival_time = stop_time_update.arrival_time
                        now = time.time()
                        diff_minutes = int((arrival_time - now) / 60)

                        # Only include trains arriving in the next 30 minutes
                        if 0 <= diff_minutes <= 30:
                            arrivals.append({
                                "line": entity.trip.route_id,
                                "time": diff_minutes
                            })

        # Sort by time
        arrivals = sorted(arrivals, key=lambda x: x['time'])

        # Mapping names and colors
        line_map = {
            "N": {"name": "N", "color": "#FCCC02"},
            "Q": {"name": "Q", "color": "#FCCC02"},
            "R": {"name": "R", "color": "#FCCC02"},
            "W": {"name": "W", "color": "#FCCC02"}
        }

        formatted_arrivals = []
        for a in arrivals:
            info = line_map.get(a['line'], {"name": a['line'], "color": "#FCCC02"})
            formatted_arrivals.append({
                "line": info['name'],
                "color": info['color'],
                "time": a['time']
            })

        return jsonify(formatted_arrivals)

    except Exception as e:
        # This will now print the REAL error to your terminal 
        # instead of just sending a confusing string to the browser.
        print(f"CRITICAL ERROR: {e}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)