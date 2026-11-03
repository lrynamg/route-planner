"""Graphhopper API access, input validation and error handling.

Owner: Donjan Cagurangan

Public functions (main.py relies on these; tell the team before changing them):
  get_json(url)                  -> (status_code or None, dict)
  validate_location(text)        -> (cleaned_text, None) or (None, error_message)
  geocoding(location, key)       -> (json_status, lat, lng, new_loc)
                                    lat and lng are None if the lookup failed
  get_route(orig, dest, vehicle, key) -> (path, None) or (None, error_message)
                                    orig and dest are (lat, lng, name) tuples
                                    path is the "paths"[0] dict of the reply
  PROFILES                       -> ["car", "bike", "foot"]

Errors are shown with utils.print_error. A rejected API key (401/403) ends
the program with exit code 1, because re-typing input cannot fix it.
"""
import sys
import urllib.parse

import requests
from colorama import Fore

from utils import print_error

GEOCODE_URL = "https://graphhopper.com/api/1/geocode?"
ROUTE_URL = "https://graphhopper.com/api/1/route?"
PROFILES = ["car", "bike", "foot"]
TIMEOUT_SECONDS = 10

MAX_LOCATION_LENGTH = 100
BAD_LOCATION_CHARS = set("<>{}|\\^`")


def get_json(url):
    """
    Request a URL and return (status_code, json_dict).

    status_code is None when no reply arrived (no internet, timeout), and the
    dictionary then holds a "message" explaining what went wrong.
    """
    try:
        reply = requests.get(url, timeout=TIMEOUT_SECONDS)
    except requests.exceptions.Timeout:
        return None, {"message": "The request timed out. Check your internet connection."}
    except requests.exceptions.RequestException as err:
        return None, {"message": "Network error: " + str(err)}

    try:
        data = reply.json()
    except ValueError:
        data = {"message": "The server's reply was not valid JSON."}
    if not isinstance(data, dict):
        data = {"message": "The server's reply had an unexpected format."}
    return reply.status_code, data


def validate_location(text):
    """
    Return (cleaned_text, None) if the text can be a place name, otherwise
    (None, error_message). Rejects empty input, input with no letters or
    digits (such as # or !!!), very long input and a few unusual characters.
    """
    cleaned = " ".join(text.split())  # trim and collapse extra spaces
    if not cleaned:
        return None, "Location cannot be empty."
    if len(cleaned) > MAX_LOCATION_LENGTH:
        return None, "Location is too long (maximum {0} characters).".format(
            MAX_LOCATION_LENGTH)
    if not any(ch.isalnum() for ch in cleaned):
        return None, "'{0}' does not look like a place. Use letters or numbers.".format(
            cleaned)
    if BAD_LOCATION_CHARS & set(cleaned):
        return None, "Location contains characters that are not allowed."
    return cleaned, None


def geocoding(location, key):
    """
    Look up a location with the Graphhopper Geocoding API.

    Returns (json_status, lat, lng, new_loc), the same shape as the lab code.
    lat and lng are None when the lookup failed, and a message is printed.
    new_loc is a readable name such as "Baltimore, Maryland, United States".
    """
    url = GEOCODE_URL + urllib.parse.urlencode(
        {"q": location, "limit": "1", "key": key})
    json_status, json_data = get_json(url)

    lat = None
    lng = None
    new_loc = location

    if json_status == 200 and json_data.get("hits"):
        hit = json_data["hits"][0]
        point = hit.get("point") or {}
        if "lat" in point and "lng" in point:
            lat = point["lat"]
            lng = point["lng"]
            # Not every result has a state or country, so only join what exists.
            parts = [hit.get("name"), hit.get("state"), hit.get("country")]
            new_loc = ", ".join(part for part in parts if part)
            print(Fore.GREEN + "Found: {0} (Location Type: {1})".format(
                new_loc, hit.get("osm_value", "unknown")))
        else:
            print_error("The service returned an incomplete result. "
                        "Try another spelling.")
    elif json_status == 200:
        print_error("No match found for '{0}'. Try adding a city and "
                    "state or country.".format(location))
    elif json_status in (401, 403):
        print_error("Graphhopper rejected the API key (status {0}). "
                    "Check your GRAPHHOPPER_KEY value.".format(json_status))
    elif json_status == 429:
        print_error("Too many requests or the daily limit was reached "
                    "(status 429). Wait a while and try again.")
    elif json_status is None:  # no reply at all (no internet, timeout)
        print_error(json_data.get("message", "No response received."))
    else:
        print_error("Geocoding failed (status {0}): {1}".format(
            json_status, json_data.get("message", "Unknown error")))

    return json_status, lat, lng, new_loc


def get_route(orig, dest, vehicle, key):
    """
    Request a route with the Graphhopper Routing API.

    orig and dest are (lat, lng, name) tuples. Returns (path, None) on
    success, where path is the "paths"[0] dictionary of the reply, or
    (None, error_message) on failure.
    """
    if (orig[0], orig[1]) == (dest[0], dest[1]):
        return None, "The starting location and destination are the same place."

    query = [
        ("key", key),
        ("vehicle", vehicle),
        ("point", "{0},{1}".format(orig[0], orig[1])),
        ("point", "{0},{1}".format(dest[0], dest[1])),
    ]
    paths_url = ROUTE_URL + urllib.parse.urlencode(query)
    paths_status, paths_data = get_json(paths_url)

    if paths_status in (401, 403):
        print_error("Graphhopper rejected the API key (status {0}). "
                    "Check your GRAPHHOPPER_KEY value.".format(paths_status))
        sys.exit(1)
    if paths_status == 429:
        return None, ("Too many requests or the daily limit was reached "
                      "(status 429). Wait a while and try again.")
    if paths_status is None:  # no reply at all (no internet, timeout)
        return None, paths_data.get("message", "No response received.")
    if paths_status != 200:
        return None, "Routing failed (status {0}): {1}".format(
            paths_status, paths_data.get("message", "Unknown error"))

    paths = paths_data.get("paths")
    if not paths or "distance" not in paths[0] or "time" not in paths[0]:
        return None, "No route was returned for these locations."
    return paths[0], None
