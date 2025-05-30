# Script to fetch game image URLs from RAWG API and update games.json
# Data and images provided by RAWG (https://rawg.io)

import requests
import json
import time
import os


API_KEY = "9e9b716c12c349ec8f2b02c0deb54669"

# Input and output file paths (relative to script's directory)
INPUT_JSON = "games.json"  # Assumes games.json is in the same directory as this script
OUTPUT_JSON = "games_with_images.json"

# Get the directory of the script to ensure correct path resolution
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_PATH = os.path.join(SCRIPT_DIR, INPUT_JSON)
OUTPUT_PATH = os.path.join(SCRIPT_DIR, OUTPUT_JSON)

# Load the existing games.json
try:
    with open(INPUT_PATH, "r", encoding="utf-8") as file:
        games = json.load(file)
except FileNotFoundError:
    print(f"Error: {INPUT_JSON} not found at {INPUT_PATH}. Ensure the file exists in the same directory as this script.")
    exit(1)
except json.JSONDecodeError:
    print(f"Error: {INPUT_JSON} has invalid JSON format.")
    exit(1)

# Function to fetch image URL for a game
def get_game_image(game_name):
    try:
        # Replace spaces with '+' for the search query
        search_term = game_name.replace(" ", "+")
        url = f"https://api.rawg.io/api/games?search={search_term}&key={API_KEY}"
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses (e.g., 404, 500)
        data = response.json()

        # Take the first result's background_image, if available
        if data["results"]:
            return data["results"][0]["background_image"] or "No image found"
        return "No image found"
    except requests.RequestException as e:
        print(f"Error fetching image for {game_name}: {e}")
        return "No image found"

# Add image_url to each game
for game in games:
    if "image_url" not in game:  # Skip if image_url already exists
        image_url = get_game_image(game["name"])
        game["image_url"] = image_url
        print(f"Added image for {game['name']}: {image_url}")
        # Sleep to avoid hitting rate limits (be cautious with free tier)
        time.sleep(0.5)

# Add attribution to the JSON
output_data = {
    "attribution": "Data and images provided by RAWG (https://rawg.io)",
    "games": games
}

# Save the updated JSON
try:
    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        json.dump(output_data, file, indent=4, ensure_ascii=False)
    print(f"Updated JSON saved to {OUTPUT_PATH}")
except Exception as e:
    print(f"Error saving {OUTPUT_JSON}: {e}")