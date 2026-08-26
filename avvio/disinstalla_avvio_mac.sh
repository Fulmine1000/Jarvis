#!/bin/bash
set -e

PLIST_TARGET="$HOME/Library/LaunchAgents/com.fulmine1000.jarvis.plist"

launchctl bootout "gui/$(id -u)" "$PLIST_TARGET" 2>/dev/null || true
rm -f "$PLIST_TARGET"

echo "Avvio automatico di J.A.R.V.I.S. rimosso."
