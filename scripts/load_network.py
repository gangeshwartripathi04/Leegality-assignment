import json
import subprocess
import sys
from pathlib import Path

BASE_URL = "http://localhost:8000"
DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "network.json"


def post(endpoint, payload):
    result = subprocess.run(
        [
            "curl", "-sS", "-f",
            "-X", "POST",
            f"{BASE_URL}{endpoint}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps(payload),
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"FAILED {endpoint}: {result.stderr or result.stdout}")
        sys.exit(1)

    print(f"OK {endpoint}: {result.stdout}")


def main():
    with DATA_FILE.open() as file:
        network = json.load(file)

    print(f"Loading {len(network['nodes'])} nodes...")
    for name in network["nodes"]:
        post("/nodes", {"name": name})

    print(f"\nLoading {len(network['edges'])} edges...")
    for edge in network["edges"]:
        post("/edges", edge)

    print("\nNetwork loaded successfully.")


if __name__ == "__main__":
    main()
