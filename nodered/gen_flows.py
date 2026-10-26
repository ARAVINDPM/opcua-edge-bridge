"""Generates flows.json for the Node-RED demo dashboard (run: python3 gen_flows.py)."""
import json

BASE = "factory/lab/nucleo-h753zi"
TAB = "tab_bridge"
nodes = []
y = [40]


def add(n):
    nodes.append(n)
    return n["id"]


def at(x):
    y[0] += 60
    return {"x": x, "y": y[0], "z": TAB}


add({"id": TAB, "type": "tab", "label": "Edge bridge demo", "disabled": False,
     "info": "Subscribes to the bridge's MQTT topics and shows values, bridge state and the write audit trail."})
add({"id": "broker", "type": "mqtt-broker", "name": "local broker", "broker": "${MQTT_HOST}", "port": "1883",
     "clientid": "", "autoConnect": True, "usetls": False, "protocolVersion": "4", "keepalive": "30",
     "cleansession": True, "autoUnsubscribe": True})
add({"id": "ui_base", "type": "ui-base", "name": "Edge bridge", "path": "/dashboard", "appIcon": "",
     "includeClientData": True, "acceptsClientConfig": ["ui-notification", "ui-control"],
     "showPathInSidebar": False, "headerContent": "page", "navigationStyle": "none", "titleBarStyle": "default",
     "showReconnectNotification": True, "notificationDisplayTime": 1, "showDisconnectNotification": True})
add({"id": "ui_theme", "type": "ui-theme", "name": "Default",
     "colors": {"surface": "#1f3a5f", "primary": "#1f6feb", "bgPage": "#eef1f5", "groupBg": "#ffffff",
                "groupOutline": "#cccccc"},
     "sizes": {"density": "default", "pagePadding": "12px", "groupGap": "12px", "groupBorderRadius": "4px",
               "widgetGap": "12px"}})
add({"id": "ui_page", "type": "ui-page", "name": "OPC UA → MQTT edge bridge (learning prototype)",
     "ui": "ui_base", "path": "/", "icon": "lan", "layout": "grid", "theme": "ui_theme",
     "breakpoints": [{"name": "Default", "px": "0", "cols": "3"}, {"name": "Tablet", "px": "576", "cols": "6"},
                     {"name": "Desktop", "px": "1024", "cols": "12"}],
     "order": 1, "className": "", "visible": "true", "disabled": "false"})


def group(gid, name, width, order):
    add({"id": gid, "type": "ui-group", "name": name, "page": "ui_page", "width": str(width), "height": "1",
         "order": order, "showTitle": True, "className": "", "visible": "true", "disabled": "false",
         "groupType": "default"})


group("g_status", "Bridge status", 4, 1)
group("g_values", "Process values (report by exception)", 8, 2)
group("g_write", "Guarded write-back", 4, 3)
group("g_audit", "Audit trail of write commands", 8, 4)


def text(nid, label, grp, order):
    return add({"id": nid, "type": "ui-text", "group": grp, "order": order, "width": "0", "height": "0",
                "name": label, "label": label, "format": "{{msg.payload}}", "layout": "row-spread",
                "style": False, "font": "", "fontSize": 16, "color": "#1f3a5f", "wrapText": False,
                "className": "", **at(900)})


# --- state ---
t_state = text("t_state", "Bridge", "g_status", 1)
t_ver = text("t_ver", "Version", "g_status", 2)
f_state = add({"id": "f_state", "type": "function", "name": "state → text",
               "func": "const p = msg.payload || {};\n"
                       "return [{payload: p.online ? '✅ online' : '❌ OFFLINE (last will)'},"
                       " {payload: p.bridge_version || '-'}];",
               "outputs": 2, "wires": [[t_state], [t_ver]], **at(600)})
add({"id": "in_state", "type": "mqtt in", "name": "state (retained)", "topic": BASE + "/state", "qos": "1",
     "datatype": "json", "broker": "broker", "nl": False, "rap": True, "rh": 0, "inputs": 0,
     "wires": [[f_state]], **at(250)})

# --- data ---
chart = add({"id": "c_samples", "type": "ui-chart", "group": "g_values", "name": "samples", "label": "Sample variables",
             "order": 1, "chartType": "line", "category": "topic", "categoryType": "msg", "xAxisLabel": "",
             "xAxisProperty": "", "xAxisPropertyType": "timestamp", "xAxisType": "time", "xAxisFormat": "",
             "xAxisFormatType": "auto", "xmin": "", "xmax": "", "yAxisLabel": "count", "yAxisProperty": "payload",
             "yAxisPropertyType": "msg", "ymin": "", "ymax": "", "bins": 10, "action": "append",
             "stackSeries": False, "pointShape": "circle", "pointRadius": 2, "showLegend": True,
             "removeOlder": "2", "removeOlderUnit": "60", "removeOlderPoints": "300",
             "colors": ["#1f6feb", "#2ca02c", "#ff7f0e", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
                        "#bcbd22"], "textColor": ["#666666"], "textColorDefault": True,
             "gridColor": ["#e5e5e5"], "gridColorDefault": True, "width": "8", "height": "6", "className": "",
             "interpolation": "linear", **at(900)})
gauge = add({"id": "g_mem", "type": "ui-gauge", "group": "g_values", "name": "memory", "order": 2, "width": "4",
             "height": "3", "gtype": "gauge-half", "gstyle": "needle", "title": "Device memory usage",
             "units": "bytes", "icon": "", "prefix": "", "suffix": "",
             "segments": [{"from": "0", "color": "#2ca02c"}, {"from": "60000", "color": "#ff7f0e"},
                          {"from": "80000", "color": "#d62728"}],
             "min": 0, "max": 100000, "sizeThickness": 16, "sizeGap": 4, "sizeKeyThickness": 8,
             "styleRounded": True, "styleGlow": False, "className": "", **at(900)})
t_delay = text("t_delay", "Source → bridge delay", "g_status", 3)
t_count = text("t_count", "Messages received", "g_status", 4)
t_di = text("t_di", "Digital input DI_1", "g_write", 3)
sw_led = add({"id": "sw_led", "type": "ui-switch", "group": "g_write", "name": "LED_1", "label": "LED_1 (writable)",
              "order": 1, "width": "0", "height": "0", "passthru": False, "decouple": "true", "topic": "led_1",
              "topicType": "str", "style": "", "className": "", "layout": "row-spread", "clickableArea": "switch",
              "onvalue": "true", "onvalueType": "bool", "onicon": "", "oncolor": "", "offvalue": "false",
              "offvalueType": "bool", "officon": "", "offcolor": "", "wires": [["f_cmd"]], **at(900)})
sw_do = add({"id": "sw_do", "type": "ui-switch", "group": "g_write", "name": "DO_1", "label": "DO_1 (writable)",
             "order": 2, "width": "0", "height": "0", "passthru": False, "decouple": "true", "topic": "do_1",
             "topicType": "str", "style": "", "className": "", "layout": "row-spread", "clickableArea": "switch",
             "onvalue": "true", "onvalueType": "bool", "onicon": "", "oncolor": "", "offvalue": "false",
             "offvalueType": "bool", "officon": "", "offcolor": "", "wires": [["f_cmd"]], **at(900)})
f_data = add({"id": "f_data", "type": "function", "name": "route by signal",
              "func": "const p = msg.payload || {};\n"
                      "const n = (context.get('n') || 0) + 1; context.set('n', n);\n"
                      "const out = [null, null, null, null, null, null, {payload: n}];\n"
                      "const v = {topic: p.signal, payload: p.value};\n"
                      "if (p.signal && p.signal.startsWith('sample_')) {\n"
                      "  out[0] = v;\n"
                      "  if (p.source_ts) out[5] = {payload: Math.round((p.bridge_ts - p.source_ts) * 1000) + ' ms'};\n"
                      "}\n"
                      "else if (p.signal === 'memory_usage') out[1] = v;\n"
                      "else if (p.signal === 'led_1') out[2] = {payload: !!p.value};\n"
                      "else if (p.signal === 'do_1') out[3] = {payload: !!p.value};\n"
                      "else if (p.signal === 'di_1') out[4] = {payload: p.value ? 'HIGH' : 'LOW'};\n"
                      "return out;",
              "outputs": 7, "wires": [[chart], [gauge], [sw_led], [sw_do], [t_di], [t_delay], [t_count]],
              **at(600)})
add({"id": "in_data", "type": "mqtt in", "name": "data/+", "topic": BASE + "/data/+", "qos": "1",
     "datatype": "json", "broker": "broker", "nl": False, "rap": True, "rh": 0, "inputs": 0,
     "wires": [[f_data]], **at(250)})

# --- commands ---
out_cmd = add({"id": "out_cmd", "type": "mqtt out", "name": "cmd/<signal>", "topic": "", "qos": "1",
               "retain": "false", "broker": "broker", **at(1150)})
add({"id": "f_cmd", "type": "function", "name": "switch → command",
     "func": "msg.topic = '" + BASE + "/cmd/' + msg.topic;\n"
             "msg.payload = JSON.stringify({value: msg.payload});\nreturn msg;",
     "outputs": 1, "wires": [[out_cmd]], **at(1150)})
add({"id": "b_bad", "type": "ui-button", "group": "g_write", "name": "forbidden write",
     "label": "Try writing read-only sample_01", "order": 4, "width": "0", "height": "0", "emulateClick": False,
     "tooltip": "Should be rejected and appear in the audit trail", "color": "", "bgcolor": "#d62728",
     "className": "", "icon": "block", "iconPosition": "left", "payload": "{\"value\": 5}", "payloadType": "str",
     "topic": BASE + "/cmd/sample_01", "topicType": "str", "buttonColor": "#d62728", "textColor": "", "iconColor": "",
     "enableClick": True, "enablePointerdown": False, "pointerdownPayload": "", "pointerdownPayloadType": "str",
     "enablePointerup": False, "pointerupPayload": "", "pointerupPayloadType": "str",
     "wires": [[out_cmd]], **at(900)})

# --- audit ---
table = add({"id": "tbl_audit", "type": "ui-table", "group": "g_audit", "name": "audit", "label": "",
             "order": 1, "width": "8", "height": "6", "maxrows": 10, "passthru": False, "autocols": False,
             "showSearch": False, "selectionType": "none",
             "columns": [{"title": "Time", "key": "time", "keyType": "key", "type": "text", "width": "",
                          "align": "start"},
                         {"title": "Signal", "key": "signal", "keyType": "key", "type": "text", "width": "",
                          "align": "start"},
                         {"title": "Requested", "key": "requested", "keyType": "key", "type": "text",
                          "width": "", "align": "start"},
                         {"title": "Before", "key": "previous", "keyType": "key", "type": "text", "width": "",
                          "align": "start"},
                         {"title": "Result", "key": "result", "keyType": "key", "type": "text", "width": "",
                          "align": "start"},
                         {"title": "Reason", "key": "reason", "keyType": "key", "type": "text", "width": "",
                          "align": "start"}],
             "mobileBreakpoint": "sm", "mobileBreakpointType": "defaults", "action": "replace", **at(900)})
add({"id": "f_audit", "type": "function", "name": "keep last 20",
     "func": "const rows = context.get('rows') || [];\nconst r = msg.payload || {};\n"
             "rows.unshift({time: new Date(r.ts * 1000).toLocaleTimeString(), signal: r.signal,\n"
             "  requested: JSON.stringify(r.requested), previous: JSON.stringify(r.previous),\n"
             "  result: r.result, reason: r.reason || ''});\n"
             "rows.length = Math.min(rows.length, 20);\ncontext.set('rows', rows);\n"
             "return {payload: rows};",
     "outputs": 1, "wires": [[table]], **at(600)})
add({"id": "in_audit", "type": "mqtt in", "name": "audit", "topic": BASE + "/audit", "qos": "1",
     "datatype": "json", "broker": "broker", "nl": False, "rap": True, "rh": 0, "inputs": 0,
     "wires": [["f_audit"]], **at(250)})

for n in nodes:
    if "wires" not in n and n["type"] in ("ui-text", "ui-chart", "ui-gauge", "ui-table", "mqtt out"):
        n["wires"] = [] if n["type"] == "mqtt out" else [[]]

json.dump(nodes, open("flows.json", "w"), indent=2, ensure_ascii=False)
print(len(nodes), "nodes written to flows.json")
