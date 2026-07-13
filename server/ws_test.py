import asyncio
import json

import websockets
from websockets.exceptions import ConnectionClosed, InvalidURI, WebSocketException


WS_URL = "ws://127.0.0.1:8001/ws/pipeline/run"


def preview_text(text: str, max_length: int = 200) -> str:
    single_line = " ".join(text.split())
    if len(single_line) <= max_length:
        return single_line
    return single_line[: max_length - 3] + "..."


def print_progress(event: dict) -> None:
    event_type = event.get("event_type", "unknown")
    processed_count = event.get("processed_count", "?")
    total_expected = event.get("total_expected", "?")
    print(f"[{event_type}] {processed_count}/{total_expected}")


def print_cluster(event: dict) -> None:
    print_progress(event)

    cluster = event.get("current_cluster")
    if not isinstance(cluster, dict):
        print("  WARNING: cluster_ready event did not include current_cluster data.")
        return

    title = cluster.get("title", "Untitled")
    mode = cluster.get("mode", "unknown")
    summary = cluster.get("summary", "")

    print(f"  title: {title}")
    print(f"  mode: {mode}")
    print(f"  summary: {preview_text(summary)}")


async def main() -> None:
    cluster_ready_count = 0
    completed_cleanly = False

    try:
        async with websockets.connect(WS_URL) as websocket:
            while True:
                try:
                    message = await websocket.recv()
                except ConnectionClosed:
                    break

                try:
                    event = json.loads(message)
                except json.JSONDecodeError as e:
                    print(f"WARNING: received malformed JSON message: {e}")
                    print(f"Raw message: {message!r}")
                    continue

                event_type = event.get("event_type")

                if event_type == "cluster_ready":
                    cluster_ready_count += 1
                    print_cluster(event)
                elif event_type in {"fetched", "clustered"}:
                    print_progress(event)
                elif event_type == "completed":
                    completed_cleanly = True
                    print_progress(event)
                    break
                else:
                    print(f"[unknown] received event: {event}")

    except (OSError, InvalidURI, WebSocketException) as e:
        print(f"ERROR: could not connect to {WS_URL}")
        print("Check that the FastAPI/uvicorn server is running on http://127.0.0.1:8001.")
        print(f"Details: {e}")
    finally:
        if completed_cleanly:
            status = "completed cleanly"
        else:
            status = "interrupted before completed event"
            print("WARNING: WebSocket run ended before a completed event was received.")

        print("\n--- WebSocket test summary ---")
        print(f"cluster_ready events received: {cluster_ready_count}")
        print(f"status: {status}")


if __name__ == "__main__":
    asyncio.run(main())
