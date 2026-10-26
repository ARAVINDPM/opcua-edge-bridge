# Hardware runbook: NUCLEO-H753ZI with the OPC UA SDK demo

Based on the vendor's quick installation guide that came with the board. Status: **not yet executed.**

## Needed
- STM32 NUCLEO-H753ZI, USB cable (ST-LINK), Ethernet cable
- STM32CubeProgrammer, to flash the precompiled demo HEX
- An OPC UA client for browsing:
  - UaExpert or Matrikon Explorer for security `None` + Anonymous;
  - the Softing OPC UA client for `ECC_nistP256`.

## Network (static, from the guide)
| | Address |
|---|---|
| Board | 192.168.1.102 / 255.255.255.0 |
| PC (example) | 192.168.1.100 / 255.255.255.0 |
| OPC UA endpoint | `opc.tcp://192.168.1.102:4842` |

Check the link with `ping 192.168.1.102`. Two LEDs flash while a client is connected.

**Only one OPC UA client connection at a time** is supported by the demo. Disconnect UaExpert before starting the bridge.

## Steps
1. Flash the HEX with STM32CubeProgrammer.
2. Set the PC's Ethernet adapter to 192.168.1.100/24 and ping the board.
3. Connect with UaExpert (None + Anonymous). Note the following and write them into `config/board.json`, copied from `board.template.json`:
   - the namespace URI;
   - the browse name of the demo object;
   - the browse paths of the sample variables, `LED_1`, the I/O nodes and memory usage.
4. Disconnect UaExpert. Run `python -m tools.security_report --endpoint opc.tcp://192.168.1.102:4842` and save the output.
5. Run `python -m bridge.main --config config/board.json --dry-run --seconds 20` and check that the values increase.
6. With a broker (`docker compose up -d mosquitto`), run without `--dry-run`. Toggle the LED via MQTT and watch the green LED.
7. Record evidence: a photo or short video, the security report, and messages per minute. Then update the README status.

## Things to measure on the real device
- Update rate actually delivered vs. requested publishing interval
- Memory usage while browsing and after `CreateSetOfVariables`
- Behaviour after an Ethernet unplug/replug: does the bridge reconnect, and does the death message appear?
