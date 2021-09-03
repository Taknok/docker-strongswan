#!/usr/bin/env python3

"""
This module just runs the Griffin+ container startup system.
Author: Sascha Falk <sascha@falk-online.eu>
License: MIT License
"""

import sys

from gp_startup import App

# run the application
exitcode = App.run()
sys.exit(exitcode)