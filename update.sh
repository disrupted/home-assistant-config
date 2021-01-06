#!/bin/bash
# echo "Checking for Update"
# sudo ha supervisor reload
# sleep 5
# echo "Installing Update if available"
# sudo ha core update
git add .HA_VERSION
git commit --no-verify -m "⬆️ Upgrade Home Assistant to $(cat .HA_VERSION)"
