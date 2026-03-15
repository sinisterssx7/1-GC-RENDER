import asyncio
import uuid
import os
import json
import threading
from collections import defaultdict
from flask import Flask, jsonify, Response

from instagrapi import Client
from instagrapi.exceptions import RateLimitError

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.align import Align

ACC_FILE = "acc.txt"
MESSAGE_FILE = "text.txt"
TITLE_FILE = "nc.txt"

MSG_DELAY = 30
RENAME_DELAY = 180

THREAD_ID = "959591573159671"

DOC_ID = "29088580780787855"
IG_APP_ID = "936619743392459"

app = Flask(__name__)
LOG_BUFFER = []

logs_ui = defaultdict(list)
console = Console()
USERS = []


@app.route('/')
def home():
    return "alive"


@app.route('/status')
def status():
    return jsonify({
        user: logs_ui[user]
        for user in USERS
    })


@app.route('/logs')
def logs_route():
    output = []

    header_text = "✦  SINISTERS | SX⁷  ✦"
    output.append(header_text)
    output.append("=" * len(header_text))
    output.append("")

    for user in USERS:
        output.append(f"[ {user} ]")
        output.append("-" * (len(user) + 4))

        for line in logs_ui[user]:
            output.append(line)

        output.append("")

    return Response("\n".join(output), mimetype="text/plain")


@app.route("/dashboard")
def dashboard():
    html = """
    <html>
    <head>
        <title>SINISTERS | SX⁷</title>
        <meta http-equiv="refresh" content="2">
        <style>
            body {
                background-color: #0d1117;
                font-family: monospace;
                margin: 0;
                padding: 20px;
                color: #00ff88;
            }
            .header {
                text-align: center;
                font-size: 28px;
                font-weight: bold;
                margin-bottom: 30px;
                border: 2px solid #00ff88;
                padding: 10px;
            }
            .container {
                display: flex;
                flex-direction: row;
                gap: 20px;
                align-items: flex-start;
            }
            .panel {
                flex: 1;
                min-width: 300px;
                border: 2px solid #00ff88;
                background-color: #111827;
                padding: 15px;
                height: 80vh;
                overflow-y: auto;
            }
            .panel-title {
                font-weight: bold;
                margin-bottom: 10px;
                border-bottom: 1px solid #00ff88;
                padding-bottom: 5px;
            }
            .log-line {
                margin-bottom: 6px;
                white-space: pre-wrap;
            }
        </style>
    </head>
    <body>
        <div class="header">
            ✦ SINISTERS | SX⁷ ✦
        </div>
        <div class="container">
    """

    for user in USERS:
        html += f"""
            <div class="panel">
                <div class="panel-title">{user}</div>
        """

        for line in logs_ui[user]:
            html += f'<div class="log-line">{line}</div>'

        html += "</div>"

    html += """
        </div>
        <script>
        function scrollPanels() {
            document.querySelectorAll('.panel').forEach(function(panel) {
                panel.scrollTop = panel.scrollHeight;
            });
        }
        window.onload = scrollPanels;
        setInterval(scrollPanels, 1500);
        </script>
    </body>
    </html>
    """

    return html


def log(console_message, clean_message=None):
    LOG_BUFFER.append(clean_message if clean_message else console_message)


MAX_PANEL_LINES = 35


def ui_log(user, message):

    if message.startswith("⏳ ROUND"):
        header = logs_ui[user][0]
        logs_ui[user] = [header, message]
        log(f"{user} | {message}", message)
        return

    logs_ui[user].append(message)

    if len(logs_ui[user]) < 2:
        log(f"{user} | {message}", message)
        return

    header = logs_ui[user][0]
    round_line = logs_ui[user][1]
    body = logs_ui[user][2:]

    if len(body) > MAX_PANEL_LINES:
        body.pop(0)

    logs_ui[user] = [header, round_line] + body

    log(f"{user} | {message}", message)


def start_flask():
    import logging
    log = logging.getLogger('werkzeug')
    log.disabled = True
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)


def load_accounts(path):
    accounts = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("|")
            if len(parts) >= 2:
                username = parts[0].strip()
                password = parts[1].strip()
                proxy = parts[2].strip() if len(parts) >= 3 and parts[2].strip() else None
                accounts.append((username, password, proxy))
    return accounts[:5]


def load_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def load_lines(path):
    with open(path, "r", encoding="utf-8") as f:
        return [x.strip() for x in f if x.strip()]


def build_layout():
    layout = Layout()

    layout.split_column(
        Layout(name="header", size=6),
        Layout(name="body")
    )

    layout["body"].split_row(
        *[Layout(name=user) for user in USERS]
    )

    header_layout = Layout()
    header_layout.split_column(
        Layout(
            Panel(
                Align.center("[bold bright_green]SINISTERS | SX⁷[/bold bright_green]"),
                border_style="bright_green"
            ),
            size=3
        ),
        Layout(
            Panel(
                Align.center("[bold bright_green]MAHABHARAT | ASTRA[/bold bright_green]"),
                border_style="bright_green"
            ),
            size=3
        ),
    )

    layout["header"].update(header_layout)

    return layout


def render_layout(layout):
    for user in USERS:
        content = "\n".join(logs_ui[user])

        panel = Panel(
            content,
            title=f"[bold bright_green]{user}[/bold bright_green]",
            border_style="bright_green",
            padding=(0, 1),
            expand=True
        )

        layout["body"][user].update(panel)


def setup_mobile_fingerprint(cl):
    cl.set_user_agent("Instagram 312.0.0.22.114 Android")
    uuids = {
        "phone_id": str(uuid.uuid4()),
        "uuid": str(uuid.uuid4()),
        "client_session_id": str(uuid.uuid4()),
        "advertising_id": str(uuid.uuid4()),
        "device_id": "android-" + uuid.uuid4().hex[:16]
    }
    cl.set_uuids(uuids)
    cl.private.headers.update({
        "X-IG-App-ID": IG_APP_ID,
        "X-IG-Device-ID": uuids["uuid"],
        "X-IG-Android-ID": uuids["device_id"],
    })


async def login(username, password, proxy):
    cl = Client()
    if proxy:
        cl.set_proxy(proxy)
    setup_mobile_fingerprint(cl)

    session_file = f"session_{username}.json"

    try:
        if os.path.exists(session_file):
            cl.load_settings(session_file)

        cl.login(username, password)
        cl.dump_settings(session_file)
        return cl
    except Exception:
        return None


def rename_thread(cl, thread_id, title):
    try:
        cl.private_request(
            f"direct_v2/threads/{thread_id}/update_title/",
            data={"title": title}
        )
        return True
    except RateLimitError:
        return False
    except Exception:
        return False


async def worker(username, password, proxy, cl, start_delay):
    await asyncio.sleep(start_delay)

    rename_index = 0
    last_rename = 0

    titles = load_lines(TITLE_FILE) if os.path.exists(TITLE_FILE) else []

    while True:

        try:
            await asyncio.to_thread(
                cl.direct_send,
                MESSAGE_TEXT,
                thread_ids=[THREAD_ID]
            )

            ui_log(username, "📨 → SENT")

        except Exception:
            ui_log(username, "⚠ SEND FAILED")

        now = asyncio.get_event_loop().time()

        if titles and now - last_rename >= RENAME_DELAY:

            title = titles[rename_index % len(titles)]
            rename_index += 1

            try:
                success = await asyncio.to_thread(
                    rename_thread,
                    cl,
                    THREAD_ID,
                    title
                )

                if success:
                    ui_log(username, f"💠 → {title}")
                else:
                    ui_log(username, "⚠ RENAME FAILED")

            except Exception:
                ui_log(username, "⚠ RENAME ERROR")

            last_rename = now

        await asyncio.sleep(MSG_DELAY)


async def main():
    ACCOUNTS = load_accounts(ACC_FILE)
    MESSAGE_TEXT_GLOBAL = load_text(MESSAGE_FILE)

    global MESSAGE_TEXT
    MESSAGE_TEXT = MESSAGE_TEXT_GLOBAL

    clients = []

    for username, password, proxy in ACCOUNTS:
        cl = await login(username, password, proxy)
        if cl:
            USERS.append(username)
            ui_log(username, f"🍸 ID - {username}")
            clients.append((username, password, proxy, cl))

    if not USERS:
        return

    layout = build_layout()

    for index, (u, p, pr, cl) in enumerate(clients):
        asyncio.create_task(worker(u, p, pr, cl, index * MSG_DELAY))

    with Live(layout, console=console, refresh_per_second=5, screen=True) as live:
        while True:
            render_layout(layout)
            live.refresh()
            await asyncio.sleep(0.2)


if __name__ == "__main__":
    threading.Thread(target=start_flask, daemon=True).start()
    asyncio.run(main())