.PHONY: install test sim dry security sbom demo dashboard
install: ; pip install -r requirements-dev.txt
test: ; pytest -q
sim: ; python -m sim.eflex_demo_sim
dry: ; python -m bridge.main --config config/sim.json --dry-run --seconds 5
security: ; python -m tools.security_report --endpoint opc.tcp://127.0.0.1:4842
sbom: ; cyclonedx-py requirements requirements.txt --of JSON -o sbom.cdx.json
demo: ; ./scripts/demo.sh
dashboard: ; cd nodered && npm install --no-audit --no-fund && npx node-red -u . -s settings.js
