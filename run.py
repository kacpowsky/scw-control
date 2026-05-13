import subprocess
import sys
import json
import os
import time

POLL_INTERVAL = 5
POLL_TIMEOUT = 300


def get_instance_ids():
    raw = os.environ.get("INSTANCE_ID", "").strip()
    if not raw:
        print("ERROR: INSTANCE_ID environment variable is not set.")
        sys.exit(1)
    return [iid.strip() for iid in raw.split(",") if iid.strip()]


def get_instance_state(instance_id):
    result = subprocess.run(
        ["scw", "instance", "server", "get", instance_id, "-o", "json"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"  ERROR: Failed to get instance info: {result.stderr.strip()}")
        return None
    server = json.loads(result.stdout)
    return server["state"]


def poweroff_instance(instance_id):
    result = subprocess.run(
        ["scw", "instance", "server", "stop", instance_id],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"  ERROR: Failed to power off instance: {result.stderr.strip()}")
        return False
    print(f"  Power off signal sent. Waiting for instance to stop...")
    return wait_for_stopped(instance_id)


def wait_for_stopped(instance_id):
    elapsed = 0
    while elapsed < POLL_TIMEOUT:
        time.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL
        state = get_instance_state(instance_id)
        if state == "stopped":
            print(f"  Confirmed: instance is now stopped. ({elapsed}s)")
            return True
        if state is None:
            return False
        print(f"  Still waiting... state: {state} ({elapsed}s)")
    print(f"  ERROR: Timeout after {POLL_TIMEOUT}s. Instance did not stop.")
    return False


def main():
    instance_ids = get_instance_ids()
    print(f"Processing {len(instance_ids)} instance(s)...\n")
    errors = 0

    for instance_id in instance_ids:
        print(f"[{instance_id}]")
        state = get_instance_state(instance_id)

        if state is None:
            errors += 1
            print()
            continue

        print(f"  Current state: {state}")

        if state == "stopped":
            print("  Already powered off. Nothing to do.")
        elif state == "running":
            print("  Running. Initiating graceful power off...")
            if not poweroff_instance(instance_id):
                errors += 1
        else:
            print(f"  In '{state}' state. No action taken.")

        print()

    if errors > 0:
        print(f"Completed with {errors} error(s).")
        sys.exit(1)

    print("All done.")


if __name__ == "__main__":
    main()
