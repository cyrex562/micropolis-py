"""
tkinter_bridge.py - TK integration replacement with pygame event loop

This module replaces the TCL/TK integration from w_tk.c with pygame-based
event loop management. It provides timer management, command processing,
UI callbacks, and coordinates between the simulation engine and pygame UI.

Adapted from w_tk.c for pygame compatibility while maintaining Sugar
activity integration through stdin/stdout communication.
"""

import pygame
import sys
import threading
from typing import Optional, Dict, Callable
from queue import Queue
import select

from .types import Sim, SimView, SimSpeed, ShakeNow, NeedRest
from .types import Eval as TypesEval
from .engine import sim_loop
from .engine import sim_update
from .disasters import DoEarthQuake
from .audio import make_sound


# Global state (equivalent to w_tk.c globals)
tk_main_interp = None  # Simplified - no TCL interpreter
main_window = None     # Pygame screen surface
update_delayed = False
auto_scroll_edge = 16
auto_scroll_step = 16
auto_scroll_delay = 10

# Timer management
sim_timer_token: Optional[int] = None  # pygame timer event ID
sim_timer_idle = False
sim_timer_set = False
earthquake_timer_token: Optional[int] = None  # pygame timer event ID
earthquake_timer_set = False
earthquake_delay = 3000

# Performance timing
performance_timing = False
flush_time = 0.0

# Command system
command_callbacks: Dict[str, Callable] = {}
stdin_thread: Optional[threading.Thread] = None
stdin_queue = Queue()
running = False


class TkTimer:
    """Simplified timer class to replace TK timers."""
    def __init__(self, delay_ms: int, callback: Callable, data=None):
        self.delay_ms = delay_ms
        self.callback = callback
        self.data = data
        self.active = False
        self.timer_id: Optional[int] = None

    def start(self):
        """Start the timer."""
        if not self.active:
            self.active = True
            self.timer_id = pygame.time.set_timer(pygame.USEREVENT + 1, self.delay_ms)

    def stop(self):
        """Stop the timer."""
        if self.active:
            self.active = False
            if self.timer_id:
                pygame.time.set_timer(pygame.USEREVENT + 1, 0)
                self.timer_id = None

    def trigger(self):
        """Manually trigger the callback."""
        if self.callback:
            self.callback(self.data)


def tk_main_init(screen: pygame.Surface) -> None:
    """
    Initialize the TK bridge system.

    Args:
        screen: Pygame screen surface to use as main window
    """
    global main_window, tk_main_interp, running

    main_window = screen
    tk_main_interp = {}  # Simplified command registry
    running = True

    # Register core commands
    register_command("UIEarthQuake", lambda: DoEarthQuake())
    register_command("UISaveCityAs", lambda: None)  # Placeholder
    register_command("UIDidLoadCity", lambda: None)  # Placeholder
    register_command("UIDidSaveCity", lambda: None)  # Placeholder

    # Start stdin processing thread for Sugar integration
    start_stdin_processing()


def tk_main_loop() -> None:
    """Main event loop - replaces TK's Tk_MainLoop()."""
    global running

    clock = pygame.time.Clock()

    while running:
        # Handle pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            elif event.type == pygame.USEREVENT + 1:
                # Timer event - handled by individual timers
                pass
            # Additional event handling can be added here

        # Process stdin commands
        _process_stdin_commands()

        # Update display if needed
        if update_delayed:
            _do_delayed_update()

        # Maintain frame rate
        clock.tick(60)  # Target 60 FPS

    # Cleanup
    stop_stdin_processing()


def tk_main_cleanup() -> None:
    """Clean up TK bridge resources."""
    global running, sim_timer_token, earthquake_timer_token

    running = False

    if sim_timer_token is not None:
        pygame.time.set_timer(sim_timer_token, 0)
        sim_timer_token = None

    if earthquake_timer_token is not None:
        pygame.time.set_timer(earthquake_timer_token, 0)
        earthquake_timer_token = None

    stop_stdin_processing()


def register_command(name: str, callback: Callable) -> None:
    """
    Register a command callback.

    Args:
        name: Command name
        callback: Function to call when command is executed
    """
    command_callbacks[name] = callback


def eval_command(cmd: str) -> int:
    """
    Evaluate a command string.

    Args:
        cmd: Command string to evaluate

    Returns:
        0 on success, non-zero on error
    """
    try:
        # Parse command (simplified - assumes single command per call)
        parts = cmd.strip().split()
        if not parts:
            return 0

        command_name = parts[0]
        args = parts[1:]

        if command_name in command_callbacks:
            callback = command_callbacks[command_name]
            if args:
                callback(*args)
            else:
                callback()
            return 0
        else:
            print(f"Unknown command: {command_name}")
            return 1

    except Exception as e:
        print(f"Error evaluating command '{cmd}': {e}")
        return 1


# Timer management functions

def start_micropolis_timer() -> None:
    """Start the simulation timer."""
    global sim_timer_token, sim_timer_idle

    if sim_timer_idle:
        return

    sim_timer_idle = True
    # Use pygame's timer system
    pygame.time.set_timer(pygame.USEREVENT + 2, _calculate_sim_delay())


def stop_micropolis_timer() -> None:
    """Stop the simulation timer."""
    global sim_timer_token, sim_timer_idle, sim_timer_set

    sim_timer_idle = False

    if sim_timer_set:
        if sim_timer_token is not None:
            pygame.time.set_timer(sim_timer_token, 0)
            sim_timer_token = None
        sim_timer_set = False


def fix_micropolis_timer() -> None:
    """Restart simulation timer if it was set."""
    global sim_timer_set

    if sim_timer_set:
        start_micropolis_timer()


def _calculate_sim_delay() -> int:
    """Calculate simulation delay based on current state."""
    from .types import sim_delay

    delay = sim_delay

    # Adjust for special conditions (earthquake, etc.)
    if ShakeNow or NeedRest > 0:
        if ShakeNow or NeedRest:
            delay = max(delay, 50000)  # Minimum 50ms during special states

    return delay // 1000  # Convert microseconds to milliseconds


def _sim_timer_callback() -> None:
    """Simulation timer callback."""
    global sim_timer_token, sim_timer_set, NeedRest, SimSpeed

    sim_timer_token = None
    sim_timer_set = False

    if NeedRest > 0:
        NeedRest -= 1

    if SimSpeed:
        sim_loop(True)  # Changed from 1 to True
        start_micropolis_timer()
    else:
        stop_micropolis_timer()


def really_start_micropolis_timer() -> None:
    """Actually start the simulation timer (called from idle handler)."""
    global sim_timer_idle, sim_timer_set

    sim_timer_idle = False

    stop_micropolis_timer()

    delay_ms = _calculate_sim_delay()

    pygame.time.set_timer(pygame.USEREVENT + 2, delay_ms)
    sim_timer_set = True


def do_earthquake() -> None:
    """Trigger earthquake effect."""
    global ShakeNow

    make_sound("city", "Explosion-Low")
    eval_command("UIEarthQuake")
    ShakeNow = 1

    # Start earthquake timer
    pygame.time.set_timer(pygame.USEREVENT + 3, earthquake_delay)


def stop_earthquake() -> None:
    """Stop earthquake effect."""
    global earthquake_timer_set, ShakeNow

    ShakeNow = 0
    if earthquake_timer_set:
        pygame.time.set_timer(pygame.USEREVENT + 3, 0)
        earthquake_timer_set = False


def _earthquake_timer_callback() -> None:
    """Earthquake timer callback."""
    stop_earthquake()


# Stdin processing for Sugar integration

def start_stdin_processing() -> None:
    """Start stdin processing thread for Sugar integration."""
    global stdin_thread

    if stdin_thread is None:
        stdin_thread = threading.Thread(target=_stdin_reader_thread, daemon=True)
        stdin_thread.start()


def stop_stdin_processing() -> None:
    """Stop stdin processing."""
    global stdin_thread

    if stdin_thread:
        stdin_thread.join(timeout=1.0)
        stdin_thread = None


def _stdin_reader_thread() -> None:
    """Thread function to read from stdin."""
    try:
        while running:
            # Use select to check if stdin has data
            if sys.stdin in select.select([sys.stdin], [], [], 0.1)[0]:
                line = sys.stdin.readline()
                if not line:  # EOF
                    break
                line = line.strip()
                if line:
                    stdin_queue.put(line)
    except Exception as e:
        print(f"Stdin reader error: {e}")


def _process_stdin_commands() -> None:
    """Process commands from stdin queue."""
    while not stdin_queue.empty():
        try:
            cmd = stdin_queue.get_nowait()
            eval_command(cmd)
        except Exception as e:
            print(f"Error processing stdin command: {e}")


# Update management

def kick() -> None:
    """Kick start an update cycle."""
    global update_delayed

    if not update_delayed:
        update_delayed = True
        # Schedule delayed update
        pygame.time.set_timer(pygame.USEREVENT + 4, 0)  # Immediate


def _do_delayed_update() -> None:
    """Perform delayed update."""
    global update_delayed

    update_delayed = False
    sim_update()


# View management coordination

def invalidate_maps() -> None:
    """Invalidate all map views."""
    if Sim:
        view = Sim.map
        while view:
            view.invalid = True  # Changed from 1 to True
            view.skip = 0
            _eventually_redraw_view(view)
            view = view.next


def invalidate_editors() -> None:
    """Invalidate all editor views."""
    if Sim:
        view = Sim.editor
        while view:
            view.invalid = True  # Changed from 1 to True
            view.skip = 0
            _eventually_redraw_view(view)
            view = view.next


def redraw_maps() -> None:
    """Redraw all map views."""
    if Sim:
        view = Sim.map
        while view:
            view.skip = 0
            _eventually_redraw_view(view)
            view = view.next


def redraw_editors() -> None:
    """Redraw all editor views."""
    if Sim:
        view = Sim.editor
        while view:
            view.skip = 0
            _eventually_redraw_view(view)
            view = view.next


def _eventually_redraw_view(view: SimView) -> None:
    """Schedule a view redraw."""
    # In pygame, we just mark for update - actual drawing happens in main loop
    view.needs_redraw = True


# Auto-scroll functionality (simplified)

def start_auto_scroll(view: SimView, x: int, y: int) -> None:
    """Start auto-scrolling for a view (simplified implementation)."""
    if view.tool_mode == 0:
        return

    # Check if cursor is near edge
    edge_triggered = (
        x < auto_scroll_edge or
        x > (view.w_width - auto_scroll_edge) or
        y < auto_scroll_edge or
        y > (view.w_height - auto_scroll_edge)
    )

    if edge_triggered:
        # Simplified auto-scroll - just trigger immediately
        _do_auto_scroll(view, x, y)


def stop_auto_scroll(view: SimView) -> None:
    """Stop auto-scrolling for a view (simplified - no-op)."""
    pass


def _do_auto_scroll(view: SimView, x: int, y: int) -> None:
    """Perform auto-scroll operation (simplified)."""
    # This is a placeholder for the auto-scroll logic
    # In a full implementation, this would pan the view based on cursor position
    pass


# Override the placeholder Eval function in types.py
def eval_override(cmd: str) -> None:
    """Override for types.Eval to use our command system."""
    eval_command(cmd)


# Initialize the override
TypesEval.__code__ = eval_override.__code__