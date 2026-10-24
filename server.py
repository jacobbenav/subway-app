import os
from flask import Flask, jsonify
from flask_cors import CORS
import requests
from google.transit import gtfs_realtime_pb2
import time

app = Flask(__name__)
CORS(app)

# --- CONFIGURATION via Environment Variables ---
MTA_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw"
# This allows you to change the station without editing the code!
TARGET_STOP_ID = os.getenv('STOP_ID', 'D31') 

@app.route('/subway-data')
def get_subway_data():
    try:
        response = requests.get(MTA_URL)
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(response.content)

        arrivals = []

        for entity in feed.trip_update:
            for stop_time_update in entity.stop_time_update:
                if stop_time_update.stop_id == TARGET_STOP_ID:
                    arrival_time = stop_time_update.arrival_time
                    now = time.time()
                    diff_minutes = int((arrival_time - now) / 60)

                    if 0 <= diff_minutes <= 30:
                        arrivals.append({
                            "line": entity.trip.route_id,
                            "time": diff_minutes
                        })

        arrivals = sorted(arrivals, key=lambda x: x['time'])
        
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
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Run on 0.0.0.0 to be accessible on the network
    app.run(host='0.0.0.0', port=5000)