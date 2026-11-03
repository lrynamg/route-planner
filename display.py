"""Units, calculations, fuel cost and colored table-style output.

Owner: Guillana Domingo

Public functions (main.py relies on these; tell the team before changing them):
  choose_unit()                          -> "miles" or "km"
  convert_distance(meters, unit)         -> float
  unit_label(unit)                       -> "mi" or "km"
  format_duration(milliseconds)          -> "hh:mm:ss"
  estimate_fuel_cost(distance_m, fuel_info) -> float
  ask_fuel_info(unit, vehicle)           -> fuel_info dict, or None
  display_route(path, orig, dest, vehicle, unit, fuel_info=None)

  fuel_info = {"unit": "miles" or "km", "efficiency": float, "price": float}
      miles: efficiency = miles per gallon,   price = price per gallon
      km:    efficiency = liters per 100 km,  price = price per liter

  path  = the "paths"[0] dict from the Routing API (distance in meters,
          time in milliseconds, and an "instructions" list)
  orig / dest = (lat, lng, name) tuples
"""
import textwrap

from colorama import Fore, Style

from utils import ask, print_error

KM_PER_MILE = 1.609344

# Table layout for the directions
WIDTH = 78
DISTANCE_W = 10
TEXT_W = WIDTH - 4 - DISTANCE_W - 2


# ------------------------------------------------------------ units and math
def choose_unit():
    """Ask whether distances are shown in miles or km."""
    while True:
        answer = ask("Show distances in miles or km? (miles/km): ").lower()
        if answer in ("miles", "mi"):
            return "miles"
        if answer == "km":
            return "km"
        print_error("Please type miles or km.")


def convert_distance(meters, unit):
    """Convert meters to miles or km."""
    km = meters / 1000
    return km / KM_PER_MILE if unit == "miles" else km


def unit_label(unit):
    return "mi" if unit == "miles" else "km"


def format_duration(milliseconds):
    """Convert milliseconds to an hh:mm:ss string."""
    total_seconds = int(milliseconds / 1000)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return "{0:02d}:{1:02d}:{2:02d}".format(hours, minutes, seconds)


# ----------------------------------------------------------------- fuel cost
def estimate_fuel_cost(distance_m, fuel_info):
    """
    Return the estimated fuel cost for a trip of distance_m meters.

    fuel_info = {"unit": "miles" or "km", "efficiency": float, "price": float}
      miles: efficiency = miles per gallon,   price = price per gallon
      km:    efficiency = liters per 100 km,  price = price per liter
    """
    km = distance_m / 1000
    if fuel_info["unit"] == "miles":
        miles = km / KM_PER_MILE
        return miles / fuel_info["efficiency"] * fuel_info["price"]
    return km * fuel_info["efficiency"] / 100 * fuel_info["price"]


def ask_number(prompt):
    """Keep asking until the user enters a number greater than zero."""
    while True:
        text = ask(prompt)
        try:
            value = float(text)
        except ValueError:
            print_error("Please enter a number, for example 7.5")
            continue
        if value <= 0:
            print_error("The number must be greater than zero.")
            continue
        return value


def ask_fuel_info(unit, vehicle):
    """Offer a fuel cost estimate (cars only). Returns fuel_info or None."""
    if vehicle != "car":
        return None
    answer = ask("Estimate the fuel cost for this trip? (y/n): ").lower()
    if answer not in ("y", "yes"):
        return None

    if unit == "miles":
        efficiency = ask_number("Fuel economy (miles per gallon): ")
        price = ask_number("Fuel price per gallon: ")
    else:
        efficiency = ask_number("Fuel consumption (liters per 100 km): ")
        price = ask_number("Fuel price per liter: ")
    return {"unit": unit, "efficiency": efficiency, "price": price}


# ------------------------------------------------------------ route display
def display_route(path, orig, dest, vehicle, unit, fuel_info=None):
    """Print a colored summary and a table of step-by-step directions."""
    label = unit_label(unit)
    distance = convert_distance(path["distance"], unit)

    print()
    print(Fore.CYAN + Style.BRIGHT + "=" * WIDTH)
    print(Fore.CYAN + Style.BRIGHT + "Directions from {0} to {1} by {2}".format(
        orig[2], dest[2], vehicle))
    print(Fore.CYAN + Style.BRIGHT + "=" * WIDTH)

    summary = [
        ("Distance", "{0:.1f} {1}".format(distance, label)),
        ("Duration", format_duration(path["time"])),
    ]
    if fuel_info:
        cost = estimate_fuel_cost(path["distance"], fuel_info)
        summary.append(("Est. fuel cost", "{0:.2f}".format(cost)))
    for name, value in summary:
        print("{0:<16}".format(name) + Fore.GREEN + Style.BRIGHT + value)
    if fuel_info:
        print(Fore.YELLOW + "(Fuel cost is an estimate based on the values you entered.)")

    print()
    print(Fore.CYAN + Style.BRIGHT + "{0:<4} {1:<{w}} {2:>{d}}".format(
        "#", "Instruction", "Distance", w=TEXT_W, d=DISTANCE_W))
    print(Fore.CYAN + "-" * WIDTH)

    for number, step in enumerate(path.get("instructions", []), start=1):
        step_distance = "{0:.1f} {1}".format(
            convert_distance(step["distance"], unit), label)
        # Long instructions wrap onto extra lines inside the table.
        lines = textwrap.wrap(step["text"], TEXT_W) or [""]
        for index, line in enumerate(lines):
            num_text = str(number) if index == 0 else ""
            dist_text = step_distance if index == 0 else ""
            print("{0:<4} {1:<{w}} ".format(num_text, line, w=TEXT_W)
                  + Fore.GREEN + "{0:>{d}}".format(dist_text, d=DISTANCE_W))
    print(Fore.CYAN + "=" * WIDTH)
