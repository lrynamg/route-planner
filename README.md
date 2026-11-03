# Route Planner (Graphhopper)

A command-line route planner. It asks for a vehicle profile (car, bike or foot), a starting
location and a destination, then uses the Graphhopper Geocoding and Routing APIs to show the
trip distance, duration and step-by-step directions.

It started as Cisco Networking Academy Lab 4.9.2 (kept in `archive/lab_4_9_2_original.py`)
and was extended by a team of four for Project Activity 3 - Social Coding.

## Features

- Vehicle profiles: car, bike, foot
- Input validation: the program re-asks for empty, symbol-only, too long, unknown or invalid input
- Clear error messages for a wrong API key, no internet, rate limits, no route and identical start and end
- Unit choice: miles or km (type `units` after any route to change it)
- Colored, table-style directions (long instructions wrap inside the table)
- Fuel cost estimate for car trips
- API key kept out of the code (environment variable), and never printed

## Requirements

- Python 3.8 or newer
- A free Graphhopper API key: sign up at https://www.graphhopper.com/ and create an API key

## Setup

```bash
git clone https://github.com/<owner>/<repo>.git
cd <repo>

python -m venv .venv
source .venv/bin/activate          # macOS / Linux
.venv\Scripts\Activate.ps1         # Windows PowerShell

pip install -r requirements.txt
```

Set your API key (never put it in the code or commit it):

```bash
export GRAPHHOPPER_KEY="your-key-here"       # macOS / Linux
$env:GRAPHHOPPER_KEY="your-key-here"         # Windows PowerShell (this window only)
```

## Run

```bash
python main.py
```

Type `q` or `quit` at any prompt to exit.

Example session:

```
Show distances in miles or km? (miles/km): miles
Enter a vehicle profile from the list above: car
Starting Location: Washington, D.C.
Found: Washington, District of Columbia, United States (Location Type: city)
Destination: Baltimore, Maryland
Found: Baltimore, Maryland, United States (Location Type: city)
Estimate the fuel cost for this trip? (y/n): y
Fuel economy (miles per gallon): 25
Fuel price per gallon: 3.50

Distance        38.6 mi
Duration        00:51:29
Est. fuel cost  5.40
```

## Project structure

| File | Purpose | Owner |
|------|---------|-------|
| `main.py` | Program flow: vehicle and location prompts, main loop | Lauryan Amigo |
| `utils.py` | Shared helpers: `ask()`, quit handling, API key, colored messages | Lauryan Amigo |
| `api.py` | Graphhopper requests, location validation, geocoding, routing, API error handling | Donjan Cagurangan |
| `display.py` | Units, calculations, fuel cost, colored table output | Guillana Domingo |
| `tests/test_planner.py` | Automated tests (no network or key needed) | Mica Ong |
| `docs/QA_LOG.md` | Manual test log | Mica Ong |
| `archive/lab_4_9_2_original.py` | The original lab code, for reference | - |

## How the modules fit together

`utils.py` has no dependencies on the other modules. `api.py` and `display.py` each import only
`utils.py`. `main.py` imports all three and runs the program. The list of public functions and
their inputs and outputs is at the top of `api.py` and `display.py`.

Data shapes passed between modules:

- **location**: a tuple `(lat, lng, name)`
- **path** (route): Graphhopper's `paths[0]`, using `distance` (meters), `time` (milliseconds) and `instructions`
- **fuel_info**: `{"unit": "miles" or "km", "efficiency": float, "price": float}`
  (miles: miles per gallon and price per gallon; km: liters per 100 km and price per liter)

## Tests

```bash
python -m unittest discover -s tests -t . -v
```

Manual test cases are listed in `docs/QA_LOG.md`.

## Team workflow

- All changes go through a pull request that a different teammate reviews and approves.
- Branches: `feature/display-units-fuel`, `feature/api-validation`, `feature/main-flow`, `feature/tests-docs`.
- Pull the latest `main` before starting new work.

## Backlog (future enhancements)

- Route options: avoid tolls and motorways
- Multiple stops
- Save directions to a text or JSON file
- Route history
- Traffic information
- Compare alternative routes
- Currency choice for fuel cost
- GUI or web front end

## Continuing the project

1. Read the public function list at the top of `api.py` and `display.py`.
2. Add new features in the module that owns that kind of work and keep the signatures stable.
3. Add a test in `tests/test_planner.py` and a row in `docs/QA_LOG.md`.
4. Open a pull request.
