"""Example demonstrating Sugar protocol bridge integration with pygame UI.

This example shows how to:
1. Initialize the Sugar bridge with the event bus
2. Subscribe to Sugar lifecycle events
3. Process commands in the main game loop
4. Send notifications back to the Sugar GTK wrapper
5. Handle graceful shutdown

Run this example:
    uv run python docs/examples/sugar_bridge_example.py

For testing with actual Sugar wrapper, redirect stdin/stdout:
    echo "SugarStartUp file:///test.cty" | \
        uv run python docs/examples/sugar_bridge_example.py
"""

from __future__ import annotations

import time

from micropolis.ui import (
    get_default_event_bus,
    get_default_sugar_bridge,
)


def main() -> None:
    """Main example demonstrating Sugar bridge usage."""
    print("Sugar Bridge Example")
    print("=" * 60)

    # Get singleton instances
    bus = get_default_event_bus()
    bridge = get_default_sugar_bridge()

    # Subscribe to Sugar events
    print("\n1. Subscribing to Sugar events...")

    def on_startup(event):
        print(f"   → Sugar startup: URI = {event.payload.get('uri', 'None')}")
        bridge.send_ui_ready("ExamplePanel")

    def on_nickname(event):
        print(f"   → Nickname set: {event.payload.get('nickname', 'Unknown')}")

    def on_activate(event):
        print("   → Activity activated (gained focus)")

    def on_deactivate(event):
        print("   → Activity deactivated (lost focus)")

    def on_share(event):
        print("   → Activity shared with buddies")

    def on_buddy_add(event):
        nick = event.payload.get("nick", "Unknown")
        color = event.payload.get("color", "unknown")
        print(f"   → Buddy joined: {nick} ({color})")

    def on_buddy_del(event):
        nick = event.payload.get("nick", "Unknown")
        print(f"   → Buddy left: {nick}")

    def on_quit(event):
        print("   → Quit requested by Sugar")

    # Register all handlers
    bus.subscribe("sugar.startup", on_startup)
    bus.subscribe("sugar.nickname", on_nickname)
    bus.subscribe("sugar.activate", on_activate)
    bus.subscribe("sugar.deactivate", on_deactivate)
    bus.subscribe("sugar.share", on_share)
    bus.subscribe("sugar.buddy_add", on_buddy_add)
    bus.subscribe("sugar.buddy_del", on_buddy_del)
    bus.subscribe("sugar.quit", on_quit)

    # Start the bridge reader thread
    print("\n2. Starting Sugar bridge...")
    bridge.start()

    # Simulate game loop
    print("\n3. Running game loop (press Ctrl+C to exit)...")
    print("   (Send Sugar commands to stdin to test)")
    print()

    running = True
    frame_count = 0

    try:
        while running:
            # Process any queued Sugar commands
            commands_processed = bridge.process_commands()
            if commands_processed > 0:
                print(
                    f"   [Frame {frame_count}] "
                    f"Processed {commands_processed} command(s)"
                )

            # Check for shutdown request
            if bridge.shutdown_requested:
                print("\n   Shutdown requested, sending acknowledgment...")
                bridge.send_quit_ack()
                running = False
                break

            # Simulate game logic
            frame_count += 1

            # Example: Send notifications periodically
            if frame_count == 10:
                print("   [Frame 10] Sending UI ready notification...")
                bridge.send_ui_ready("HeadPanel")

            if frame_count == 20:
                print("   [Frame 20] Simulating city save...")
                bridge.send_city_saved("example.cty")

            if frame_count == 30:
                print("   [Frame 30] Simulating sound playback...")
                bridge.send_sound_play("edit", "click")

            # Display bridge state every 50 frames
            if frame_count % 50 == 0:
                print(f"\n   [Frame {frame_count}] Bridge state:")
                print(f"     URI: {bridge.uri or '(none)'}")
                print(f"     Nickname: {bridge.nickname or '(none)'}")
                print(f"     Activated: {bridge.activated}")
                print(f"     Shared: {bridge.shared}")
                print(f"     Buddies: {len(bridge.buddies)}")
                if bridge.buddies:
                    for buddy in bridge.buddies:
                        print(f"       - {buddy[1]} ({buddy[2]})")
                print()

            # Limit frame rate
            time.sleep(0.05)  # 20 FPS

            # Exit after 100 frames for demo purposes
            if frame_count >= 100:
                print("\n   Demo complete (100 frames)")
                running = False

    except KeyboardInterrupt:
        print("\n\n   Interrupted by user")

    finally:
        # Clean shutdown
        print("\n4. Shutting down bridge...")
        bridge.stop(timeout=2.0)
        print("   Bridge stopped")

    print("\n5. Final bridge state:")
    print(f"   URI: {bridge.uri or '(none)'}")
    print(f"   Nickname: {bridge.nickname or '(none)'}")
    print(f"   Activated: {bridge.activated}")
    print(f"   Shared: {bridge.shared}")
    print(f"   Buddies: {len(bridge.buddies)}")
    print(f"   Shutdown requested: {bridge.shutdown_requested}")

    print("\n" + "=" * 60)
    print("Example complete!")


if __name__ == "__main__":
    main()
