// Minimal Node-RED settings for the demo dashboard.
// Broker host comes from MQTT_HOST (default: localhost; docker compose sets "mosquitto").
process.env.MQTT_HOST = process.env.MQTT_HOST || "localhost";
module.exports = {
    uiPort: process.env.PORT || 1880,
    httpAdminRoot: "/editor",   // flow editor; "/" redirects to the dashboard
    flowFile: "flows.json",
    credentialSecret: false,
    flowFilePretty: true,
    editorTheme: { projects: { enabled: false } },
    logging: { console: { level: "info", metrics: false, audit: false } }
};
