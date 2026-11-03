"""Automated tests for the Route Planner.

Owner: Mica Ong (QA and documentation)

Run from the project root (the folder containing main.py):
    python -m unittest discover -s tests -t . -v

The tests never call the real Graphhopper API: network calls are replaced with
fake replies using unittest.mock, so they run offline and need no API key.
Run them after the api, display and main branches have been merged.
"""
import io
import unittest
from contextlib import redirect_stdout
from unittest import mock

import api
import display
import main
from utils import QuitRequested

WASHINGTON = (38.8950368, -77.0365427, "Washington, District of Columbia, United States")
BALTIMORE = (39.2908816, -76.610759, "Baltimore, Maryland, United States")

SAMPLE_PATH = {
    "distance": 62074.8,
    "time": 3089865,
    "instructions": [
        {"text": "Continue onto 15th Street Northwest", "distance": 424.3},
        {"text": "Arrive at destination", "distance": 0.0},
    ],
}

HIT = {"point": {"lat": 38.8950368, "lng": -77.0365427}, "name": "Washington",
       "state": "District of Columbia", "country": "United States",
       "osm_value": "city"}


def quiet(function, *args, **kwargs):
    """Call a function, hide what it prints, and return (result, printed_text)."""
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        result = function(*args, **kwargs)
    return result, buffer.getvalue()


class CalculationTest(unittest.TestCase):
    def test_format_duration(self):
        self.assertEqual(display.format_duration(3089865), "00:51:29")
        self.assertEqual(display.format_duration(0), "00:00:00")
        self.assertEqual(display.format_duration(12800000), "03:33:20")

    def test_convert_distance_km(self):
        self.assertAlmostEqual(display.convert_distance(62074.8, "km"), 62.0748, places=4)

    def test_convert_distance_miles(self):
        self.assertAlmostEqual(display.convert_distance(160934.4, "miles"), 100.0, places=4)

    def test_unit_label(self):
        self.assertEqual(display.unit_label("miles"), "mi")
        self.assertEqual(display.unit_label("km"), "km")

    def test_fuel_cost_miles(self):
        # 100 miles at 25 mpg = 4 gallons; 4 gallons at 4.00 = 16.00
        info = {"unit": "miles", "efficiency": 25, "price": 4.0}
        self.assertAlmostEqual(display.estimate_fuel_cost(160934.4, info), 16.0, places=4)

    def test_fuel_cost_km(self):
        # 100 km at 8 L/100km = 8 liters; 8 liters at 1.50 = 12.00
        info = {"unit": "km", "efficiency": 8, "price": 1.5}
        self.assertAlmostEqual(display.estimate_fuel_cost(100000, info), 12.0, places=4)


class UserInputTest(unittest.TestCase):
    def test_fuel_info_skipped_for_bike_and_foot(self):
        self.assertIsNone(display.ask_fuel_info("miles", "bike"))
        self.assertIsNone(display.ask_fuel_info("km", "foot"))

    def test_fuel_info_declined(self):
        with mock.patch.object(display, "ask", return_value="n"):
            self.assertIsNone(display.ask_fuel_info("miles", "car"))

    def test_fuel_info_collected_and_bad_numbers_retried(self):
        answers = iter(["y", "abc", "-5", "25", "3.5"])
        with mock.patch.object(display, "ask", side_effect=lambda prompt: next(answers)):
            info, _ = quiet(display.ask_fuel_info, "miles", "car")
        self.assertEqual(info, {"unit": "miles", "efficiency": 25.0, "price": 3.5})

    def test_choose_unit_retries_until_valid(self):
        answers = iter(["feet", "KM"])
        with mock.patch.object(display, "ask", side_effect=lambda prompt: next(answers)):
            unit, _ = quiet(display.choose_unit)
        self.assertEqual(unit, "km")

    def test_choose_vehicle_retries_and_ignores_case(self):
        answers = iter(["scooter", "", "CAR"])
        with mock.patch.object(main, "ask", side_effect=lambda prompt: next(answers)):
            vehicle, printed = quiet(main.choose_vehicle)
        self.assertEqual(vehicle, "car")
        self.assertIn("not valid", printed)

    def test_quit_word_raises(self):
        with mock.patch("builtins.input", return_value=" Quit "):
            with self.assertRaises(QuitRequested):
                main.ask("anything: ")


class LocationValidationTest(unittest.TestCase):
    def test_valid_location_is_cleaned(self):
        self.assertEqual(api.validate_location("  Tempe,   Arizona "),
                         ("Tempe, Arizona", None))

    def test_non_latin_location_allowed(self):
        self.assertEqual(api.validate_location("北京市"), ("北京市", None))

    def test_invalid_locations(self):
        for text in ["", "   ", "#", "!!!", "a" * 101, "Tem<pe"]:
            cleaned, error = api.validate_location(text)
            self.assertIsNone(cleaned, msg=repr(text))
            self.assertTrue(error, msg=repr(text))


class GeocodingTest(unittest.TestCase):
    def test_success(self):
        with mock.patch("api.get_json", return_value=(200, {"hits": [HIT]})):
            result, printed = quiet(api.geocoding, "Washington, D.C.", "fake-key")
        status, lat, lng, name = result
        self.assertEqual(status, 200)
        self.assertEqual((lat, lng), (38.8950368, -77.0365427))
        self.assertEqual(name, "Washington, District of Columbia, United States")
        self.assertIn("Found:", printed)

    def test_missing_state_and_country(self):
        hit = {"point": {"lat": 1.0, "lng": 2.0}, "name": "Somewhere"}
        with mock.patch("api.get_json", return_value=(200, {"hits": [hit]})):
            result, _ = quiet(api.geocoding, "Somewhere", "fake-key")
        self.assertEqual(result[3], "Somewhere")

    def test_no_hits(self):
        with mock.patch("api.get_json", return_value=(200, {"hits": []})):
            result, printed = quiet(api.geocoding, "slkdjf", "fake-key")
        self.assertEqual(result[:3], (200, None, None))
        self.assertIn("No match found", printed)

    def test_bad_key(self):
        with mock.patch("api.get_json", return_value=(401, {"message": "Wrong credentials"})):
            result, printed = quiet(api.geocoding, "Washington", "bad-key")
        self.assertEqual(result[:3], (401, None, None))
        self.assertIn("rejected the API key", printed)

    def test_network_failure(self):
        with mock.patch("api.get_json", return_value=(None, {"message": "Network error: x"})):
            result, printed = quiet(api.geocoding, "Washington", "fake-key")
        self.assertEqual(result[:3], (None, None, None))
        self.assertIn("Network error", printed)

    def test_key_not_sent_to_screen(self):
        with mock.patch("api.get_json", return_value=(200, {"hits": [HIT]})):
            _, printed = quiet(api.geocoding, "Washington", "SECRET-KEY-123")
        self.assertNotIn("SECRET-KEY-123", printed)


class RouteTest(unittest.TestCase):
    def test_success(self):
        with mock.patch("api.get_json", return_value=(200, {"paths": [SAMPLE_PATH]})):
            path, error = api.get_route(WASHINGTON, BALTIMORE, "car", "fake-key")
        self.assertIsNone(error)
        self.assertEqual(path["time"], 3089865)

    def test_route_url_contains_vehicle_and_both_points(self):
        with mock.patch("api.get_json", return_value=(200, {"paths": [SAMPLE_PATH]})) as fake:
            api.get_route(WASHINGTON, BALTIMORE, "bike", "fake-key")
        url = fake.call_args[0][0]
        self.assertIn("vehicle=bike", url)
        self.assertEqual(url.count("point="), 2)

    def test_no_connection_between_locations(self):
        reply = (400, {"message": "Connection between locations not found"})
        with mock.patch("api.get_json", return_value=reply):
            path, error = api.get_route(WASHINGTON, BALTIMORE, "car", "fake-key")
        self.assertIsNone(path)
        self.assertIn("Connection between locations not found", error)

    def test_same_start_and_destination(self):
        path, error = api.get_route(WASHINGTON, WASHINGTON, "car", "fake-key")
        self.assertIsNone(path)
        self.assertIn("same place", error)

    def test_rate_limit(self):
        with mock.patch("api.get_json", return_value=(429, {})):
            path, error = api.get_route(WASHINGTON, BALTIMORE, "car", "fake-key")
        self.assertIn("429", error)

    def test_network_failure(self):
        with mock.patch("api.get_json", return_value=(None, {"message": "Network error: x"})):
            path, error = api.get_route(WASHINGTON, BALTIMORE, "car", "fake-key")
        self.assertIn("Network error", error)

    def test_bad_key_exits(self):
        with mock.patch("api.get_json", return_value=(401, {"message": "Wrong credentials"})):
            with self.assertRaises(SystemExit):
                quiet(api.get_route, WASHINGTON, BALTIMORE, "car", "bad-key")


class GetLocationTest(unittest.TestCase):
    def test_reasks_until_found(self):
        answers = iter(["", "#", "slkdjf", "Washington, D.C."])

        def fake_geocoding(text, key):
            if text == "slkdjf":
                return 200, None, None, text
            return 200, 38.89, -77.03, "Washington, District of Columbia, United States"

        with mock.patch.object(main, "ask", side_effect=lambda prompt: next(answers)), \
                mock.patch("api.geocoding", side_effect=fake_geocoding):
            location, printed = quiet(main.get_location, "Start: ", "fake-key")
        self.assertEqual(location, (38.89, -77.03, "Washington, District of Columbia, United States"))
        self.assertIn("cannot be empty", printed)
        self.assertIn("does not look like a place", printed)

    def test_bad_key_exits(self):
        with mock.patch.object(main, "ask", return_value="Washington"), \
                mock.patch("api.geocoding", return_value=(401, None, None, "Washington")):
            with self.assertRaises(SystemExit):
                quiet(main.get_location, "Start: ", "bad-key")


class DisplayRouteTest(unittest.TestCase):
    def test_prints_summary_table_and_fuel_cost(self):
        info = {"unit": "miles", "efficiency": 25, "price": 3.5}
        _, out = quiet(display.display_route, SAMPLE_PATH, WASHINGTON, BALTIMORE,
                       "car", "miles", info)
        self.assertIn("Directions from Washington", out)
        self.assertIn("38.6 mi", out)
        self.assertIn("00:51:29", out)
        self.assertIn("5.40", out)
        self.assertIn("Continue onto 15th Street Northwest", out)

    def test_no_fuel_line_without_fuel_info(self):
        _, out = quiet(display.display_route, SAMPLE_PATH, WASHINGTON, BALTIMORE,
                       "bike", "km", None)
        self.assertIn("62.1 km", out)
        self.assertNotIn("fuel", out.lower())

    def test_long_instruction_wraps_inside_table(self):
        path = {"distance": 1000, "time": 60000, "instructions": [
            {"text": "Keep left onto Baltimore-Washington Parkway and drive toward "
                     "Baltimore and continue for a long distance along the parkway",
             "distance": 1000}]}
        _, out = quiet(display.display_route, path, WASHINGTON, BALTIMORE, "car", "km")
        for line in out.splitlines():
            self.assertLessEqual(len(line), display.WIDTH + 40)  # allows long title line


if __name__ == "__main__":
    unittest.main()
