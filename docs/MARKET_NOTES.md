# Market notes and sources (retrieved October 2026)

Short notes I used for the product reasoning. Vendor material is marked as such.

## Regulation
- **Teichmann, F. (2025).** "The cyber resilience act as a new paradigm for product security: a compliance roadmap." *International Cybersecurity Law Review* 7 (2026). Main points:
  - The CRA moves product security from voluntary practice to lifecycle obligations.
  - It covers support periods, vulnerability handling and 24 h reporting of exploited vulnerabilities.
  - It recommends an SBOM.
  - Harmonised standards are still pending.
  - https://link.springer.com/article/10.1365/s43439-025-00162-4
- **ONEKEY IoT & OT Cybersecurity Report 2025** (vendor survey, 300 respondents, DACH):
  - 12 % have a complete overview of the software in their devices.
  - 44 % have started SBOMs.
  - 40 % update firmware regularly.
  - 37 % see the 24 h reporting duty as their biggest challenge.
  - https://www.onekey.com/resource/iot-ot-cybersecurity-report-2025
- **Secomea, State of Industrial Remote Access 2026** (vendor survey, 400 leaders): only 43 % report full audit trails of vendor sessions. https://www.controleng.com/industrial-organizations-overestimate-remote-access-security-new-global-report-finds/

## embedded world 2026 (10–12 March, Nuremberg)
- Recaps describe CRA readiness, secure-by-design and SBOMs as the new baseline, and edge AI moving into deployment. https://sam-solutions.com/blog/embedded-world-2026-recap/
- **Nordic Semiconductor** announced a one-off "lifetime" FOTA and device-management licence from USD 1 per device, explicitly framed around the CRA (press release, 12 March 2026). https://www.prnewswire.com/pl/komunikat-prasowy/nordic-semiconductor-launches-lifetime-flat-rate-fota-solution-readying-customers-for-cyber-resilience-act-302711133.html

## Device-management business models
- **Golioth:** device connections free, pay by usage (OTA MB, logs). https://blog.golioth.io/device-management-should-be-free/
- **AWS IoT Device Management:** pay per device and operation. https://aws.amazon.com/iot-device-management/pricing/
- **NXP EdgeLock 2GO:** tiered service (Ready / Custom / Managed) for provisioning and credential lifecycle. https://www.everythingrf.com/news/details/11844-nxp-introduces-flexible-iot-cloud-platform-to-securely-manage-and-connect-edge-devices

## OPC UA on small devices and protocol choice
- **Matrikon Flex/eFlex SDKs:**
  - eFlex targets RTOS/bare-metal devices with micro builds of about 150 KB+ RAM.
  - It supports RSA and ECC (P-256) policies and Pub/Sub over UDP.
  - It has been validated against OPC UA 1.04, with 1.05 planned for 2026.
  - https://matrikon.com/oem/flex-eflex-sdks/
- **BE.services** is a strategic partner for Matrikon SDK integration and porting. https://be-services.com/en/opc-ua
- **open62541** documents ECC security policies in its 1.5 line. https://open62541.org/doc/1.5/security/policies.html
- **HiveMQ white paper** (vendor) compares OPC UA client/server with MQTT Sparkplug B, including report-by-exception and birth/death certificates. https://www.hivemq.com/iiot-protocols-opc-ua-mqtt-sparkplug-comparison/
- **Secure OTA research:**
  - "Secure firmware Over-The-Air updates for IoT: Survey, challenges, and discussions" (*Internet of Things*, 2022). https://www.sciencedirect.com/science/article/abs/pii/S2542660522000142
  - CI/CD-based OTA proposal (*Sensors* 2026). https://www.mdpi.com/1424-8220/26/5/1535
