#!/bin/bash
# Glorious Skills Installer - Interactive TUI for installing agent skills
#
# Usage: ./install-skills.sh
#
# This script launches an interactive terminal UI that lets you:
#   • Browse all available skills with descriptions
#   • Select which skills to install
#   • Install them one by one with progress tracking
#   • See a detailed summary of results
#

uv run python scripts/install_skills.py "$@"
