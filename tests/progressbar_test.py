#!/usr/bin/env python3

import random
import string
import time


# autopep8: off
import sys
import os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
# Import the progress bar
from distexprunner import _progressbar as progress_bar
# autopep8: on


def random_string(string_length=30):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(string_length))


def generate_some_output_and_sleep():
    print("Here is some output")
    print(random_string())
    print(random_string())
    print(random_string())
    print(random_string())
    print("\n\n------------------------------------------------------------------")
    print("\n\n Now sleeping briefly")
    time.sleep(0.3)


def main():
    # Make sure that the progress bar is cleaned up when user presses ctrl+c
    progress_bar.enable_trapping()
    # Create progress bar
    progress_bar.setup_scroll_area()
    for i in range(99):
        if i == 50:
            print("waiting for user input: ")
            progress_bar.block_progress_bar(i)
            input("User input: ")
        else:
            generate_some_output_and_sleep()
            progress_bar.draw_progress_bar(i)
    progress_bar.destroy_scroll_area()


main()
