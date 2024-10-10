import os
import signal
import time
import subprocess
import requests
from flask import Flask
from threading import Thread

# Set the path to the script you want to restart
script_to_restart = "sahil.py"

# Flask app for health check
app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    return "OK", 200

# Set your GitHub Personal Access Token
GITHUB_TOKEN = "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"

# GitHub API URL for interacting with Codespaces
API_URL = "https://api.github.com/user/codespaces"

headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def list_codespaces():
    # List all available codespaces for the authenticated user
    response = requests.get(API_URL, headers=headers)
    if response.status_code == 200:
        codespaces_data = response.json()
        
        # GitHub API returns a dictionary, and the Codespaces are in the 'codespaces' key
        codespaces = codespaces_data.get('codespaces', [])
        
        if not codespaces:
            print("No Codespaces found.")
            return None
        
        print("Available Codespaces:")
        for index, cs in enumerate(codespaces):
            print(f"{index + 1}: {cs['name']} (State: {cs['state']})")
        return codespaces
    else:
        print(f"Failed to list codespaces: {response.status_code}, {response.text}")
        return None

def start_codespace(codespace_name):
    # Start the Codespace if it's not running
    start_url = f"{API_URL}/{codespace_name}/start"
    response = requests.post(start_url, headers=headers)
    if response.status_code == 200:
        print(f"Successfully started codespace: {codespace_name}")
    else:
        print(f"Failed to start codespace: {response.status_code}, {response.text}")

def restart_script_in_codespace(codespace_name):
    # Assuming you can SSH into the Codespace and run commands
    print(f"Restarting script in Codespace {codespace_name}...")
    ssh_command = f"ssh -i ~/.ssh/id_rsa -p 2222 codespace@{codespace_name} 'pkill -f {script_to_restart} || true && python3 {script_to_restart}'"
    process = subprocess.Popen(ssh_command, shell=True)
    process.wait()
    print("Script restarted in Codespace.")

def turn_on_and_run_script_in_two_codespaces():
    codespaces = list_codespaces()
    if codespaces:
        selected_codespaces = []
        for cs in codespaces:
            if len(selected_codespaces) < 2 and cs['state'] != 'Running':
                start_codespace(cs['name'])
                selected_codespaces.append(cs['name'])
            elif len(selected_codespaces) == 2:
                break

        # Run the script in the two selected codespaces
        for codespace_name in selected_codespaces:
            restart_script_in_codespace(codespace_name)

def monitor_codespaces():
    # Continuously check the status of the Codespaces and restart if necessary
    while True:
        codespaces = list_codespaces()
        if codespaces:
            for cs in codespaces:
                if cs['state'] != 'Running':
                    print(f"Codespace {cs['name']} is not running. Attempting to start it...")
                    start_codespace(cs['name'])
                    restart_script_in_codespace(cs['name'])
        time.sleep(60)  # Check every 60 seconds

def restart_script_locally():
    print("LOOP START BY S4.....")
    process = subprocess.Popen(["python3", script_to_restart], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return process

def main():
    # Turn on two Codespaces and run the script in them
    turn_on_and_run_script_in_two_codespaces()

    # Run locally after 480 seconds
    process = restart_script_locally()  # Starts the script locally
    
    # Start monitoring Codespaces in the background
    monitor_codespaces()

    while True:
        time.sleep(480)  # Sleep for 480 seconds (8 minutes)
        # Send SIGINT to the process and restart it locally
        process.send_signal(signal.SIGINT)
        process.wait()
        process = restart_script_locally()

# Start the Flask app in a separate thread
def run_flask():
    app.run(host='0.0.0.0', port=10001)

Thread(target=run_flask).start()


            
  
