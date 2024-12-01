from flask import Flask, render_template
from netmiko import ConnectHandler
import re
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)

def get_device_info(device):
    try:
        # Connect to the device
        connection = ConnectHandler(**device)
        connection.enable()

        # Fetch hostname
        hostname_output = connection.send_command("show running-config | include hostname")
        hostname_match = re.search(r"hostname (\S+)", hostname_output)
        hostname = hostname_match.group(1) if hostname_match else "Hostname not found"

        # Fetch version
        version_output = connection.send_command("show version")
        version_match = re.search(r"Version (\d+\.\d+\(\d+[A-Z]*\)\w*)", version_output)
        version = version_match.group(1) if version_match else "Version not found"

        connection.disconnect()
        return {"ip": device["ip"], "hostname": hostname, "version": version}
    except Exception as e:
        return {"ip": device["ip"], "hostname": "Error", "version": f"Error: {e}"}


# Read devices from CSV
def read_devices():
    devices = []
    with open("devices.csv", "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            device = {
                "device_type": "cisco_ios",
                "ip": row["ip"],
                "username": row["username"],
                "password": row["password"],
                "secret": row["enable_password"],
            }
            devices.append(device)
    return devices

@app.route("/")
def index():
    devices = read_devices()
    results = []

    with ThreadPoolExecutor(max_workers=50) as executor:
        # Submit all tasks
        futures = [executor.submit(get_device_info, device) for device in devices]
        for future in as_completed(futures):
            results.append(future.result())
    
    return render_template("index.html", results=results)

if __name__ == "__main__":
    app.run(debug=True)