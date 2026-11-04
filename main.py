"""Program flow: ties utils.py, api.py and display.py together.

Owner: Lauryan Amigo (Scrum Leader)

Run with:  python main.py     (after setting GRAPHHOPPER_KEY, see README.md)

Flow: choose units once, then loop { vehicle, start, destination -> route ->
optional fuel estimate -> show directions -> next action }.
Typing q or quit at ANY prompt ends the program (see utils.ask).
"""
import sys

from colorama import Fore

import api
import display
from utils import QuitRequested, ask, get_api_key, print_error, print_info


def choose_vehicle():
    """Ask for a vehicle profile until a valid one is entered."""
    print("\n" + Fore.CYAN + "+" * 45)
    print(Fore.CYAN + "Vehicle profiles available on Graphhopper:")
    print(Fore.CYAN + "+" * 45)
    print(", ".join(api.PROFILES))
    print(Fore.CYAN + "+" * 45)
    while True:
        vehicle = ask("Enter a vehicle profile from the list above: ").lower()
        if vehicle in api.PROFILES:
            return vehicle
        print_error("'{0}' is not valid. Choose from: {1}.".format(
            vehicle, ", ".join(api.PROFILES)))


def get_location(prompt, key):
    """Ask for a place until it is valid and found. Returns (lat, lng, name)."""
    while True:
        text, error = api.validate_location(ask(prompt))
        if error:
            print_error(error)
            continue

        json_status, lat, lng, new_loc = api.geocoding(text, key)
        if lat is not None:
            return lat, lng, new_loc

        if json_status in (401, 403):  # re-typing cannot fix a bad key
            sys.exit(1)
        if json_status is None:
            print_info("Check your internet connection, then try again "
                       "(or type q to quit).")


def next_action(unit):
    """After a route: Enter = another route, 'units' = change units, q = quit."""
    answer = ask("\nPress Enter for another route, type 'units' to change "
                 "units, or q to quit: ").lower()
    if answer == "units":
        return display.choose_unit()
    return unit


def main():
    key = get_api_key()
    print_info("Route Planner - type q or quit at any prompt to exit.")

    try:
        unit = display.choose_unit()

        while True:
            vehicle = choose_vehicle()
            orig = get_location("Starting Location: ", key)
            dest = get_location("Destination: ", key)

            path, error = api.get_route(orig, dest, vehicle, key)
            if error:
                print_error(error)
                print_info("Try a different pair of locations or vehicle.")
                continue

            fuel_info = display.ask_fuel_info(unit, vehicle)
            display.display_route(path, orig, dest, vehicle, unit, fuel_info)
            unit = next_action(unit)
    except QuitRequested:
        print_info("Goodbye!")
    except KeyboardInterrupt:
        print_info("\nGoodbye!")


if __name__ == "__main__":
    main()
