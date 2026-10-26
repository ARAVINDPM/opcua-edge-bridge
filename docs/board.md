# Running it on the board

Not done yet. These are my notes from the quick guide that came with the board.

1. Flash the demo HEX with STM32CubeProgrammer.
2. Board IP: 192.168.1.102/24. Set the laptop to 192.168.1.100/24, then check with `ping 192.168.1.102`.
3. Connect with UaExpert (security None, anonymous) to `opc.tcp://192.168.1.102:4842`. Note the namespace and the node names and put them in `config/board.json` (copy it from `board.template.json`).
4. Close UaExpert. The demo allows only one client at a time.
5. `python -m bridge.main --config config/board.json --dry-run --seconds 20` should show the counters going up.
6. With Mosquitto running, start it without `--dry-run` and switch the LED from the dashboard.

Things I want to check on the real hardware: what update rate it actually delivers, how memory changes when variables are added, and what happens when I pull the Ethernet cable.
