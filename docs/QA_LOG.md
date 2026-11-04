# QA Test Log

Tester: ____________   Date: ____________   Commit tested: ____________

Run the automated tests first:  `python -m unittest discover -s tests -t . -v`
Then run the manual tests below with a real API key (`python main.py`).

| # | Test | Steps / input | Expected result | Pass / Fail | Notes |
|---|------|---------------|-----------------|-------------|-------|
| 1 | Normal car route | car, miles, Washington D.C. to Baltimore, Maryland | Summary shows about 38.6 mi and 00:51:29; table of steps | | |
| 2 | Bike route | bike, same locations | Different distance and duration; no fuel question | | |
| 3 | Foot route | foot, same locations | Different distance and duration; no fuel question | | |
| 4 | Unit choice: km | Choose km at start | Distances in km everywhere | | |
| 5 | Change units | After a route type `units`, choose the other unit | Next route uses the new unit | | |
| 6 | Fuel estimate (miles) | car, y, 25 mpg, 3.50 per gallon | Cost about 5.40 for the Washington to Baltimore trip | | |
| 7 | Fuel estimate (km) | km, car, y, 9 L/100km, 1.80 per liter | Cost matches distance x 9 / 100 x 1.80 | | |
| 8 | Bad fuel numbers | At fuel prompts enter `abc`, `0`, `-3` | Error message each time and asks again | | |
| 9 | Declined fuel estimate | car, answer `n` | No fuel line in the summary | | |
| 10 | Invalid vehicle | Enter `scooter`, then empty | Error message, asks again (no crash) | | |
| 11 | Vehicle in capitals | Enter `CAR` | Accepted as car | | |
| 12 | Empty location | Press Enter at Starting Location | "Location cannot be empty", asks again | | |
| 13 | Symbols only | Enter `#` then `!!!` | "does not look like a place", asks again | | |
| 14 | Unknown place | Enter `slkdjf` | "No match found", asks again | | |
| 15 | Same start and end | Washington, D.C. twice | "same place" message | | |
| 16 | No route possible | Beijing, China to Washington, D.C. by car | Clear routing error, back to vehicle prompt | | |
| 17 | Wrong API key | Set `GRAPHHOPPER_KEY` to `abc123`, run a route | Message about rejected key, program exits cleanly | | |
| 18 | Missing API key | Remove `GRAPHHOPPER_KEY`, run | Message explaining how to set it | | |
| 19 | No internet | Turn off Wi-Fi, run a route | "Network error" or timeout message, no crash | | |
| 20 | Quit at each prompt | Type `q`, `Q`, `quit` at vehicle, start, destination, units, fuel and next-action prompts | Prints Goodbye and exits | | |
| 21 | Long step text | Leeds, England to London, England by car | Long instructions wrap inside the table | | |
| 22 | Colors | Run on Windows terminal and on macOS/Linux | Colors show; no stray characters like `[32m` | | |

## Bugs found

| Bug # | Found in test # | Description | Reported to | Fixed in PR | Retested |
|-------|-----------------|-------------|-------------|-------------|----------|
| | | | | | |
