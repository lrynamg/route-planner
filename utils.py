"""Shared helpers used by every module.

Owner: Lauryan Amigo (Scrum Leader)

Contains:
  QuitRequested   exception raised when the user types q or quit
  ask(prompt)     input() that strips spaces and raises QuitRequested on q/quit
  get_api_key()   reads the Graphhopper key from GRAPHHOPPER_KEY
  print_error(m)  red error message
  print_info(m)   yellow information message

Keep this file small and stable: api.py, display.py and main.py all import it.
"""
import os
import sys

from colorama import Fore, Style, init

init(autoreset=True)  # colors reset after every print; also works on Windows

QUIT_WORDS = ("q", "quit")


class QuitRequested(Exception):
    """Raised when the user types q or quit at any prompt."""


def print_error(message):
    print(Fore.RED + Style.BRIGHT + "Error: " + message)


def print_info(message):
    print(Fore.YELLOW + message)


def get_api_key():
    """Read the Graphhopper API key from the GRAPHHOPPER_KEY variable."""
    key = os.environ.get("GRAPHHOPPER_KEY")
    if not key:
        sys.exit("Error: set the GRAPHHOPPER_KEY environment variable first "
                 "(see README.md).")
    return key


def ask(prompt):
    """input() that strips spaces and raises QuitRequested on q / quit."""
    answer = input(prompt).strip()
    if answer.lower() in QUIT_WORDS:
        raise QuitRequested
    return answer
