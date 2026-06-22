"""Simple Streamlit app to interact with AgentForge backend.

Features:
- List agents
- View agent details
- Run agent (uses WebSocket stream if available, otherwise posts and shows result)
- View recent runs for selected agent

Run:

    pip install -r requirements.txt
    streamlit run backend/streamlit_app.py

"""
import os
import streamlit as st
import requests
import time
import threading
import json
import queue

try:
    from websocket import WebSocketApp
    WS_AVAILABLE = True
except Exception:
    WS_AVAILABLE = False


st.set_page_config(page_title="AgentForge Streamlit", layout="wide")
st.title("AgentForge — Streamlit Console")

api_base = st.text_input("API Base URL", value="http://localhost:8000")

if api_base.endswith("/"):
    api_base = api_base[:-1]

col1, col2 = st.columns([1, 2])

with col1:
    st.header("Agents")
    try:
        resp = requests.get(f"{api_base}/agents", timeout=5)
        agents = resp.json() if resp.ok else []
    except Exception:
        agents = []

    agent_map = {a.get("name") or a.get("id"): a for a in agents}
    selected_name = st.selectbox("Select an agent", options=["-- none --"] + list(agent_map.keys()))

    # Optional Streamlit auth: set ST_AUTH_TOKEN in environment to require access
    ST_AUTH_TOKEN = os.getenv("ST_AUTH_TOKEN")
    provided_token = None
    authenticated = True
    if ST_AUTH_TOKEN:
        provided_token = st.text_input("Streamlit access token", type="password")
        authenticated = (provided_token == ST_AUTH_TOKEN)
        if not authenticated:
            st.warning("Enter the correct Streamlit access token to run agents.")

    if selected_name and selected_name != "-- none --":
        agent = agent_map[selected_name]
        st.write("**Agent ID:**", agent.get("id"))
        st.write("**Goal:**", agent.get("goal"))
        st.write("**Frequency:**", agent.get("frequency"))
        st.write("**Tools:**", ", ".join(agent.get("tools_needed", [])))
        st.markdown("---")

        if st.button("Run Agent (Stream)"):
            if not authenticated:
                st.error("Not authenticated to run agents via Streamlit.")
            else:
                run_container = st.empty()
                log_box = st.empty()
                progress_bar = st.progress(0)
                current_tool = st.empty()

                q = queue.Queue()

                def enqueue(msg):
                    q.put(msg)

                finished = False

                # Try WebSocket streaming first
                if WS_AVAILABLE:
                    ws_url = api_base.replace("http://", "ws://").replace("https://", "wss://") + f"/ws/agents/{agent.get('id')}/run"

                    def on_message(ws, message):
                        try:
                            data = json.loads(message)
                        except Exception:
                            data = {"raw": message}
                        enqueue(data)

                    def on_error(ws, error):
                        enqueue({"type": "error", "message": f"WS Error: {error}"})

                    def on_close(ws, close_status_code, close_msg):
                        enqueue({"type": "closed"})

                    def on_open(ws):
                        enqueue({"type": "open"})

                    ws_app = WebSocketApp(ws_url, on_message=on_message, on_error=on_error, on_close=on_close, on_open=on_open)

                    # run websocket in thread
                    wst = threading.Thread(target=ws_app.run_forever, kwargs={"ping_interval": 10}, daemon=True)
                    wst.start()

                    # Poll queue and update UI
                    logs = []
                    while wst.is_alive() or not q.empty():
                        try:
                            item = q.get(timeout=0.5)
                        except queue.Empty:
                            continue

                        # Handle item types
                        t = item.get("type") if isinstance(item, dict) else None
                        if t == "open":
                            logs.append("[WS] Connected, running agent...")
                        elif t == "progress":
                            d = item.get("data", {})
                            # d expected to have 'event' and 'index'/'total' or similar
                            evt = d.get("event") if isinstance(d, dict) else None
                            if evt == "tool_executed":
                                idx = d.get("index", 0)
                                total = d.get("total", 1)
                                tool = d.get("tool")
                                percent = int(((idx + 1) / max(total, 1)) * 100)
                                progress_bar.progress(percent)
                                current_tool.text(f"Executing: {tool} ({idx+1}/{total})")
                                logs.append(f"[tool] {tool} -> done")
                            elif evt == "tool_error":
                                tool = d.get("tool")
                                logs.append(f"[tool error] {tool}: {d.get('error')}")
                        elif t == "complete":
                            result = item.get("data")
                            logs.append("[complete] Run finished")
                            run_container.json(result)
                            progress_bar.progress(100)
                        elif t == "error":
                            logs.append(f"[error] {item.get('message')}")
                        elif t == "closed":
                            logs.append("[WS] Connection closed")
                        else:
                            # fallback: show the raw item
                            logs.append(str(item))

                        # update log box with last lines
                        log_box.markdown("\n".join(logs[-30:]))

                    # finished
                    log_box.markdown("\n".join(logs[-100:]))

                else:
                    # REST fallback: run the agent and show result
                    log_box.markdown("WebSocket client not available; using REST fallback.")
                    try:
                        r = requests.post(f"{api_base}/agents/{agent.get('id')}/run", timeout=120)
                        if r.ok:
                            res = r.json()
                            progress_bar.progress(100)
                            current_tool.text("Completed")
                            run_container.json(res)
                            log_box.markdown("[REST] Run completed")
                            log_box.markdown(json.dumps(res, indent=2)[:4000])
                        else:
                            log_box.error(f"[REST] Run failed: {r.status_code} {r.text}")
                    except Exception as e:
                        log_box.error(f"[REST] Error: {e}")

        if st.button("Show Recent Runs"):
            try:
                r = requests.get(f"{api_base}/agents/{agent.get('id')}/runs", timeout=5)
                if r.ok:
                    runs = r.json()
                    st.write(runs[:10])
                else:
                    st.error("Failed to fetch runs")
            except Exception as e:
                st.error(str(e))

    else:
        st.info("No agent selected — create one via the web UI or API first.")

with col2:
    st.header("Quick Actions & Health")
    if st.button("Health Check"):
        try:
            h = requests.get(f"{api_base}/health", timeout=5).json()
            st.json(h)
        except Exception as e:
            st.error(str(e))

    st.markdown("---")
    st.subheader("Notes")
    st.markdown("- Streamlit app attempts to use WebSocket streaming if `websocket-client` is installed.\n- Fallback uses `POST /agents/{id}/run` and shows final result.")
