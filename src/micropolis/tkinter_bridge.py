"""
tkinter_bridge.py - TK integration replacement with pygame event loop

This module replaces the TCL/TK integration from w_tk.c with pygame-based
event loop management. It provides timer management, command processing,
UI callbacks, and coordinates between the simulation engine and pygame UI.

Adapted from w_tk.c for pygame compatibility while maintaining Sugar
activity integration through stdin/stdout communication.
"""

import select
import sys
import threading
from collections.abc import Callable

import pygame

from .audio import make_sound
from .constants import SIM_TIMER_EVENT, EARTHQUAKE_TIMER_EVENT, UPDATE_EVENT
from .context import AppContext
from .disasters import do_earth_quake
from .engine import sim_loop, sim_update
from .sim_view import SimView


def _current_sim(context: AppContext):
    """Return the active simulation object, allowing tests to inject one."""
    return context.sim


class TkTimer:
    """Simplified timer class to replace TK timers."""

    def __init__(self, delay_ms: int, callback: Callable, data=None):
        self.delay_ms = delay_ms
        self.callback = callback
        self.data = data
        self.active = False
        self.timer_id: int | None = None

    def start(self):
        """Start the timer."""
        if not self.active:
            self.active = True
            self.timer_id = pygame.USEREVENT + 1
            pygame.time.set_timer(self.timer_id, self.delay_ms)

    def stop(self):
        """Stop the timer."""
        if self.active:
            self.active = False
            if self.timer_id is not None:
                pygame.time.set_timer(self.timer_id, 0)
                self.timer_id = None

    def trigger(self):
        """Manually trigger the callback."""
        if self.callback:
            self.callback(self.data)


def tk_main_init(context: AppContext, screen: pygame.Surface) -> None:
    """
    Initialize the TK bridge system.

    Args:
        screen: Pygame screen surface to use as main window
        :param context:
    """
    # global main_window, tk_main_interp, running

    context.main_window = screen
    context.tk_main_interp = {}  # Simplified command registry
    context.running = True

    # Register core commands
    register_command(context, "UIEarthQuake", lambda: do_earth_quake(context))
    register_command(context, "UISaveCityAs", lambda: None)  # Placeholder
    register_command(context, "UIDidLoadCity", lambda: None)  # Placeholder
    register_command(context, "UIDidSaveCity", lambda: None)  # Placeholder

    # Start stdin processing thread for Sugar integration
    start_stdin_processing(context)


def tk_main_loop(context: AppContext) -> None:
    """Main event loop - replaces TK's Tk_MainLoop().
    :param context:
    """
    # global running

    clock = pygame.time.Clock()

    while context.running:
        # Handle pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                context.running = False
                break
            elif event.type == pygame.USEREVENT + 1:
                # Timer event - handled by individual timers
                pass
            elif event.type == SIM_TIMER_EVENT:
                _sim_timer_callback(context)
            elif event.type == EARTHQUAKE_TIMER_EVENT:
                _earthquake_timer_callback(context)
            elif event.type == UPDATE_EVENT and context.update_delayed:
                _do_delayed_update(context)
            # Additional event handling can be added here

        # Process stdin commands
        _process_stdin_commands(context)

        # Update display if needed
        if context.update_delayed:
            _do_delayed_update(context)

        # Maintain frame rate
        clock.tick(60)  # Target 60 FPS

    # Cleanup
    stop_stdin_processing(context)


def tk_main_cleanup(context: AppContext) -> None:
    """Clean up TK bridge resources.
    :param context:
    """
    # global running, update_delayed

    context.running = False

    stop_micropolis_timer(context)
    stop_earthquake(context)
    pygame.time.set_timer(UPDATE_EVENT, 0)
    context.update_delayed = False

    stop_stdin_processing(context)


def register_command(context: AppContext, name: str, callback: Callable) -> None:
    """
    Register a command callback.

    Args:
        name: Command name
        callback: Function to call when command is executed
        :param context:
    """
    context.command_callbacks[name] = callback


def eval_command(context: AppContext, cmd: str) -> int:
    """
    Evaluate a command string.

    Args:
        cmd: Command string to evaluate

    Returns:
        0 on success, non-zero on error
        :param context:
    """
    try:
        # Parse command (simplified - assumes single command per call)
        parts = cmd.strip().split()
        if not parts:
            return 0

        command_name = parts[0]
        args = parts[1:]

        if command_name in context.command_callbacks:
            callback = context.command_callbacks[command_name]
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


def start_micropolis_timer(context: AppContext) -> None:
    """Start the simulation timer."""
    # global sim_timer_token, sim_timer_idle, sim_timer_set

    context.sim_timer_idle = False
    delay = max(1, _calculate_sim_delay(context))
    pygame.time.set_timer(SIM_TIMER_EVENT, delay)
    context.sim_timer_token = SIM_TIMER_EVENT
    context.sim_timer_set = True


def stop_micropolis_timer(context: AppContext) -> None:
    """Stop the simulation timer.
    :param context:
    """
    # global sim_timer_token, sim_timer_idle, sim_timer_set

    if context.sim_timer_set:
        pygame.time.set_timer(SIM_TIMER_EVENT, 0)
        context.sim_timer_set = False
    context.sim_timer_token = None
    context.sim_timer_idle = False


def fix_micropolis_timer(context: AppContext) -> None:
    """Restart simulation timer if it was set."""
    # global sim_timer_set

    if context.sim_timer_set:
        start_micropolis_timer(context)


def _calculate_sim_delay(context: AppContext) -> int:
    """Calculate simulation delay based on current state.
    :param context:
    """
    delay = context.sim_delay

    # Adjust for special conditions (earthquake, etc.)
    if context.shake_now or context.need_rest > 0:
        delay = max(delay, 50000)

    # Convert to milliseconds, ensuring at least 1
    return max(1, delay // 1000)


def _sim_timer_callback(context: AppContext) -> None:
    """Simulation timer callback.
    :param context:
    """
    # global sim_timer_token, sim_timer_set

    context.sim_timer_token = None
    context.sim_timer_set = False

    if context.need_rest > 0:
        context.need_rest -= 1

    if context.sim_speed:
        sim_loop(context, True)  # Changed from 1 to True
        start_micropolis_timer(context)
    else:
        stop_micropolis_timer(context)


def really_start_micropolis_timer(context: AppContext) -> None:
    """Actually start the simulation timer (called from idle handler)."""
    # global sim_timer_idle

    context.sim_timer_idle = False
    stop_micropolis_timer(context)
    start_micropolis_timer(context)


def do_earthquake(context: AppContext) -> None:
    """Trigger earthquake effect.
    :param context:
    """
    # global earthquake_timer_token, earthquake_timer_set

    make_sound(context, "city", "Explosion-Low")
    eval_command(context, "UIEarthQuake")
    context.shake_now = 1

    # Start earthquake timer
    pygame.time.set_timer(EARTHQUAKE_TIMER_EVENT, context.earthquake_delay)
    context.earthquake_timer_token = EARTHQUAKE_TIMER_EVENT
    context.earthquake_timer_set = True


def stop_earthquake(context: AppContext) -> None:
    """Stop earthquake effect.
    :param context:
    """
    # global earthquake_timer_set, earthquake_timer_token

    context.shake_now = 0
    pygame.time.set_timer(EARTHQUAKE_TIMER_EVENT, 0)
    context.earthquake_timer_set = False
    context.earthquake_timer_token = None


def _earthquake_timer_callback(context: AppContext) -> None:
    """Earthquake timer callback."""
    stop_earthquake(context)


# Stdin processing for Sugar integration


def start_stdin_processing(context: AppContext) -> None:
    """Start stdin processing thread for Sugar integration.
    :param context:
    """
    # global stdin_thread

    if context.stdin_thread is None:
        stdin_thread = threading.Thread(target=_stdin_reader_thread, daemon=True)
        stdin_thread.start()


def stop_stdin_processing(context: AppContext) -> None:
    """Stop stdin processing."""
    # global stdin_thread

    if context.stdin_thread:
        context.stdin_thread.join(timeout=1.0)
        context.stdin_thread = None


def _stdin_reader_thread(context: AppContext) -> None:
    """Thread function to read from stdin."""
    try:
        while context.running:
            # Use select to check if stdin has data
            if sys.stdin in select.select([sys.stdin], [], [], 0.1)[0]:
                line = sys.stdin.readline()
                if not line:  # EOF
                    break
                line = line.strip()
                if line:
                    context.stdin_queue.put(line)
    except Exception as e:
        print(f"Stdin reader error: {e}")


def _process_stdin_commands(context: AppContext) -> None:
    """Process commands from stdin queue."""
    while not context.stdin_queue.empty():
        try:
            cmd = context.stdin_queue.get_nowait()
            eval_command(context, cmd)
        except Exception as e:
            print(f"Error processing stdin command: {e}")


# Update management


def kick(context: AppContext) -> None:
    """Kick start an update cycle."""
    # global update_delayed

    if not context.update_delayed:
        context.update_delayed = True
        # Schedule delayed update
        pygame.time.set_timer(UPDATE_EVENT, 1)


def _do_delayed_update(context: AppContext) -> None:
    """Perform delayed update."""
    # global update_delayed

    context.update_delayed = False
    pygame.time.set_timer(UPDATE_EVENT, 0)
    sim_update(context)


# View management coordination


def invalidate_maps(context: AppContext) -> None:
    """Invalidate all map views."""
    sim_obj = _current_sim(context)
    if sim_obj:
        view = sim_obj.map
        while view:
            view.invalid = True
            view.skip = 0
            _eventually_redraw_view(view)
            view = view.next


def invalidate_editors(context: AppContext) -> None:
    """Invalidate all editor views."""
    sim_obj = _current_sim(context)
    if sim_obj:
        view = sim_obj.editor
        while view:
            view.invalid = True
            view.skip = 0
            _eventually_redraw_view(view)
            view = view.next


def redraw_maps(context: AppContext) -> None:
    """Redraw all map views."""
    sim_obj = _current_sim(context)
    if sim_obj:
        view = sim_obj.map
        while view:
            view.skip = 0
            _eventually_redraw_view(view)
            view = view.next


def redraw_editors(context: AppContext) -> None:
    """Redraw all editor views."""
    sim_obj = _current_sim(context)
    if sim_obj:
        view = sim_obj.editor
        while view:
            view.skip = 0
            _eventually_redraw_view(view)
            view = view.next


def _eventually_redraw_view(view: SimView) -> None:
    """Schedule a view redraw."""
    # In pygame, we just mark for update - actual drawing happens in main loop
    view.needs_redraw = True


# Auto-scroll functionality (simplified)


def start_auto_scroll(context: AppContext, view: SimView, x: int, y: int) -> None:
    """Start auto-scrolling for a view (simplified implementation)."""
    if view.tool_mode == 0:
        return

    # Check if cursor is near edge
    edge_triggered = (
            x < context.auto_scroll_edge
            or x > (view.w_width - context.auto_scroll_edge)
            or y < context.auto_scroll_edge
            or y > (view.w_height - context.auto_scroll_edge)
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
def eval_override(context: AppContext, cmd: str) -> None:
    """Override for types.Eval to use our command system."""
    eval_command(context, cmd)
