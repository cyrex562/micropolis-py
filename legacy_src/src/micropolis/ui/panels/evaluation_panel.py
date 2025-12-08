"""Evaluation panel implementation for the pygame UI stack."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from micropolis import evaluation as eval_module
from micropolis.context import AppContext
from micropolis.ui.event_bus import EventBus, get_default_event_bus
from micropolis.ui.timer_service import TimerEvent
from micropolis.ui.uipanel import UIPanel
from micropolis.ui.widgets import (
    Button,
    Checkbox,
    NullRenderer,
    RecordingRenderer,
    ScrollContainer,
    TextLabel,
    Theme,
    ThemeManager,
    UIEvent,
    UIWidget,
    WidgetRenderer,
)

try:  # Optional dependency for real rendering
    import pygame

    _HAVE_PYGAME = True
except Exception:  # pragma: no cover - pygame optional in tests
    pygame = None  # type: ignore
    _HAVE_PYGAME = False


# Problem names mapping from evaluation.py
PROBLEM_STRINGS = [
    "Crime",
    "Pollution",
    "Housing Costs",
    "Taxes",
    "Traffic",
    "Unemployment",
    "Fires",
]

# Evaluation categories for display
EVAL_CATEGORIES = [
    ("Population", "population"),
    ("Migration", "migration"),
    ("Assessed Value", "value"),
    ("City Class", "class"),
    ("Game Level", "level"),
    ("Overall Score", "score"),
]


@dataclass
class EvaluationPanelState:
    """Snapshot of the evaluation panel display for tests and diagnostics."""

    is_visible: bool = False
    city_score: int = 0
    score_delta: int = 0
    city_pop: int = 0
    pop_delta: int = 0
    city_class: str = "VILLAGE"
    game_level: str = "Easy"
    assessed_value: str = "$0"
    approval_yes: int = 0
    approval_no: int = 0
    top_problems: list[tuple[str, int]] | None = None
    auto_evaluation: bool = False

    def __post_init__(self):
        if self.top_problems is None:
            object.__setattr__(self, "top_problems", [])


class _PygameWidgetRenderer(WidgetRenderer):
    """Minimal pygame-backed renderer satisfying the widget protocol."""

    def __init__(self, surface: Any) -> None:
        if not _HAVE_PYGAME or surface is None:
            raise RuntimeError("pygame surface required")
        self._surface = surface
        self._font_cache: dict[tuple[str | None, int | None], Any] = {}

    def _color(self, color: tuple[int, int, int, int]) -> tuple[int, int, int]:
        r, g, b, _ = color
        return int(r), int(g), int(b)

    def _font(self, font: str | None, size: int | None) -> Any:
        key = (font, size)
        cached = self._font_cache.get(key)
        if cached is not None:
            return cached
        resolved = pygame.font.SysFont(font or "dejavusans", size or 16)
        self._font_cache[key] = resolved
        return resolved

    def draw_rect(
        self,
        rect: tuple[int, int, int, int],
        color: tuple[int, int, int, int],
        border: bool = False,
        border_color: tuple[int, int, int, int] | None = None,
        radius: int = 0,
    ) -> None:
        pg_rect = pygame.Rect(rect)
        pygame.draw.rect(
            self._surface,
            self._color(color),
            pg_rect,
            width=0 if not border else 0,
            border_radius=radius,
        )
        if border:
            pygame.draw.rect(
                self._surface,
                self._color(border_color or color),
                pg_rect,
                width=1,
                border_radius=radius,
            )

    def draw_text(
        self,
        text: str,
        position: tuple[int, int],
        color: tuple[int, int, int, int],
        font: str | None = None,
        size: int | None = None,
    ) -> None:
        font_obj = self._font(font, size)
        surface = font_obj.render(text, True, self._color(color))
        text_rect = surface.get_rect()
        text_rect.center = position
        self._surface.blit(surface, text_rect)

    def draw_line(
        self,
        start: tuple[int, int],
        end: tuple[int, int],
        color: tuple[int, int, int, int],
        width: int = 1,
    ) -> None:
        pygame.draw.line(self._surface, self._color(color), start, end, width)

    def draw_image(
        self,
        image_id: str,
        dest: tuple[int, int, int, int],
        tint: tuple[int, int, int, int] | None = None,
    ) -> None:  # pragma: no cover - images not yet used
        return None


class _EvaluationCategoryRow(UIWidget):
    """Single row showing a category name, value, and indicator bar."""

    def __init__(
        self,
        category: str,
        rect: tuple[int, int, int, int],
        theme: Theme,
    ) -> None:
        super().__init__(widget_id=f"eval-row-{category.lower()}", rect=rect)
        self._category = category
        self._value_text = ""
        self._bar_percent = 0.0  # 0.0 to 1.0
        self._bar_color = (100, 200, 100, 255)

        x, y, w, h = rect

        # Category label on the left
        self.category_label = TextLabel(
            category,
            widget_id=f"{category.lower()}-label",
        )
        self.category_label.set_rect((x, y, w // 3, h))
        self.add_child(self.category_label)

        # Value label in the middle
        self.value_label = TextLabel(
            "",
            widget_id=f"{category.lower()}-value",
        )
        self.value_label.set_rect((x + w // 3, y, w // 3, h))
        self.add_child(self.value_label)

        # Bar indicator on the right (rendered custom)
        self._bar_rect = (x + 2 * w // 3, y + h // 4, w // 3 - 8, h // 2)

    def set_value(self, text: str, bar_percent: float = 0.0, bar_color=None) -> None:
        """Update the displayed value and optional indicator bar."""
        self._value_text = text
        self._bar_percent = max(0.0, min(1.0, bar_percent))
        if bar_color:
            self._bar_color = bar_color
        self.value_label.set_text(text)
        self.invalidate()

    def on_render(self, renderer: WidgetRenderer) -> None:
        palette = self.theme.palette if self.theme else None
        if not palette:
            return

        # Draw bar background
        bx, by, bw, bh = self._bar_rect
        renderer.draw_rect(
            self._bar_rect,
            palette.surface_alt,  # Changed from disabled
            border=True,
            border_color=palette.border,
        )

        # Draw filled portion
        if self._bar_percent > 0:
            fill_w = int(bw * self._bar_percent)
            renderer.draw_rect(
                (bx, by, fill_w, bh),
                self._bar_color,
            )


class _ProblemListItem(UIWidget):
    """Display row for a single city problem with name and vote percentage."""

    def __init__(
        self,
        rect: tuple[int, int, int, int],
        theme: Theme,
    ) -> None:
        super().__init__(widget_id="problem-item", rect=rect)
        self._problem_name = ""
        self._vote_percent = 0

        x, y, w, h = rect

        self.name_label = TextLabel(
            "",
            widget_id="problem-name",
        )
        self.name_label.set_rect((x, y, w - 60, h))
        self.add_child(self.name_label)

        self.vote_label = TextLabel(
            "",
            widget_id="problem-vote",
        )
        self.vote_label.set_rect((x + w - 60, y, 60, h))
        self.add_child(self.vote_label)

    def set_problem(self, name: str, vote_percent: int) -> None:
        """Update the problem name and vote percentage."""
        self._problem_name = name
        self._vote_percent = vote_percent
        self.name_label.set_text(name)
        self.vote_label.set_text(f"{vote_percent}%")
        self.invalidate()

    def on_render(self, renderer: WidgetRenderer) -> None:
        palette = self.theme.palette if self.theme else None
        if palette:
            renderer.draw_rect(
                self.rect,
                palette.surface,
                border=True,
                border_color=palette.border,
            )


class _EvaluationDialogView(UIWidget):
    """Widget tree for the evaluation panel display."""

    def __init__(
        self,
        rect: tuple[int, int, int, int],
        theme: Theme,
        context: AppContext,
    ) -> None:
        super().__init__(widget_id="evaluation-dialog", rect=rect)
        self.context = context

        x, y, w, h = rect
        padding = 16
        row_height = 32

        # Title
        self.title_label = TextLabel(
            f"City Evaluation {self._get_current_year()}",
            widget_id="eval-title",
        )
        self.title_label.set_rect((x + padding, y + padding, w - padding * 2, 40))
        self.add_child(self.title_label)

        # Left column - scores and ratings
        left_x = x + padding
        left_w = (w - padding * 3) // 2
        info_y = y + 80

        # Score display
        self.score_label = TextLabel("Overall Score", widget_id="score-title")
        self.score_label.set_rect((left_x, info_y, left_w, 24))
        self.add_child(self.score_label)

        self.score_value = TextLabel("500", widget_id="score-value")
        self.score_value.set_rect((left_x, info_y + 28, left_w, 32))
        self.add_child(self.score_value)

        self.score_delta = TextLabel("(+0)", widget_id="score-delta")
        self.score_delta.set_rect((left_x, info_y + 64, left_w, 24))
        self.add_child(self.score_delta)

        # Approval rating
        approval_y = info_y + 120
        self.approval_label = TextLabel("Approval Rating", widget_id="approval-title")
        self.approval_label.set_rect((left_x, approval_y, left_w, 24))
        self.add_child(self.approval_label)

        self.approval_yes = TextLabel("50% Yes", widget_id="approval-yes")
        self.approval_yes.set_rect((left_x, approval_y + 28, left_w // 2, 24))
        self.add_child(self.approval_yes)

        self.approval_no = TextLabel("50% No", widget_id="approval-no")
        self.approval_no.set_rect(
            (left_x + left_w // 2, approval_y + 28, left_w // 2, 24)
        )
        self.add_child(self.approval_no)

        # Category rows
        category_y = approval_y + 80
        self._category_rows: dict[str, _EvaluationCategoryRow] = {}

        for i, (category, key) in enumerate(EVAL_CATEGORIES):
            row = _EvaluationCategoryRow(
                category,
                (left_x, category_y + i * row_height, left_w, row_height - 4),
                theme,
            )
            self._category_rows[key] = row
            self.add_child(row)

        # Right column - top problems
        right_x = x + padding * 2 + left_w
        right_w = left_w

        self.problems_label = TextLabel("Top City Problems", widget_id="problems-title")
        self.problems_label.set_rect((right_x, info_y, right_w, 32))
        self.add_child(self.problems_label)

        # Problem list (scrollable container - simplified without content_height)
        problems_y = info_y + 40
        problems_h = 200
        self.problems_scroll = ScrollContainer(
            widget_id="problems-scroll",
            rect=(right_x, problems_y, right_w, problems_h),
        )
        self.add_child(self.problems_scroll)

        # Create problem item widgets (up to 7)
        self._problem_items: list[_ProblemListItem] = []
        for i in range(7):
            item = _ProblemListItem(
                (0, i * 32, right_w - 20, 30),
                theme,
            )
            self._problem_items.append(item)
            self.problems_scroll.add_child(item)  # Changed from add_content_child

        # Recommendations section
        recommend_y = problems_y + problems_h + padding
        self.recommendations_label = TextLabel(
            "Recommendations", widget_id="recommendations-title"
        )
        self.recommendations_label.set_rect((right_x, recommend_y, right_w, 24))
        self.add_child(self.recommendations_label)

        self.recommendations_text = TextLabel(
            "Focus on addressing the top problems listed above.",
            widget_id="recommendations-text",
        )
        self.recommendations_text.set_rect((right_x, recommend_y + 28, right_w, 80))
        self.add_child(self.recommendations_text)

        # Bottom buttons
        button_y = y + h - 120
        button_w = 180
        button_h = 32
        button_spacing = 8
        center_x = x + w // 2

        self.run_eval_button = Button(
            "Run Evaluation",
            widget_id="run-eval-button",
            rect=(
                center_x - button_w - button_spacing // 2,
                button_y,
                button_w,
                button_h,
            ),
            on_click=lambda _: self._handle_run_evaluation(),
        )
        self.add_child(self.run_eval_button)

        self.view_budget_button = Button(
            "View Budget",
            widget_id="view-budget-button",
            rect=(
                center_x + button_spacing // 2,
                button_y,
                button_w,
                button_h,
            ),
            on_click=lambda _: self._handle_view_budget(),
        )
        self.add_child(self.view_budget_button)

        # Toggles
        toggle_y = button_y + button_h + padding
        self.auto_eval_checkbox = Checkbox(
            "Auto-Evaluation",
            widget_id="auto-eval-checkbox",
            rect=(center_x - button_w, toggle_y, button_w * 2, 28),
            on_toggle=lambda cb, val: self._handle_auto_eval_toggle(val),
        )
        self.add_child(self.auto_eval_checkbox)

        self.notifications_checkbox = Checkbox(
            "Show Notifications",
            widget_id="notifications-checkbox",
            rect=(center_x - button_w, toggle_y + 32, button_w * 2, 28),
            on_toggle=lambda cb, val: self._handle_notifications_toggle(val),
        )
        self.add_child(self.notifications_checkbox)

        self._on_run_evaluation = None
        self._on_view_budget = None

    def set_callbacks(self, on_run_evaluation, on_view_budget):
        self._on_run_evaluation = on_run_evaluation
        self._on_view_budget = on_view_budget

    def update_evaluation_data(
        self,
        score: int,
        score_delta: int,
        population: int,
        pop_delta: int,
        city_class: str,
        game_level: str,
        assessed_value: str,
        approval_yes: int,
        approval_no: int,
        top_problems: list[tuple[str, int]],
    ) -> None:
        """Update all evaluation display data."""
        # Update title with current year
        self.title_label.set_text(f"City Evaluation {self._get_current_year()}")

        # Update score
        self.score_value.set_text(str(score))
        delta_str = f"(+{score_delta})" if score_delta >= 0 else f"({score_delta})"
        self.score_delta.set_text(delta_str)

        # Update approval
        self.approval_yes.set_text(f"{approval_yes}% Yes")
        self.approval_no.set_text(f"{approval_no}% No")

        # Update category rows
        pop_str = f"{population:,}"
        pop_delta_str = f"(+{pop_delta:,})" if pop_delta >= 0 else f"({pop_delta:,})"
        self._category_rows["population"].set_value(pop_str, 0.0)
        self._category_rows["migration"].set_value(pop_delta_str, 0.0)
        self._category_rows["value"].set_value(assessed_value, 0.0)
        self._category_rows["class"].set_value(city_class, 0.0)
        self._category_rows["level"].set_value(game_level, 0.0)

        # Score indicator bar (0-1000 scale)
        score_percent = score / 1000.0
        score_color = self._get_score_color(score)
        self._category_rows["score"].set_value(str(score), score_percent, score_color)

        # Update problems list
        for i, item in enumerate(self._problem_items):
            if i < len(top_problems):
                name, vote_pct = top_problems[i]
                item.set_problem(name, vote_pct)
                item.show()  # Changed to use show/hide methods
            else:
                item.hide()  # Changed to use show/hide methods

        # Update recommendations based on top problem
        if top_problems:
            top_problem = top_problems[0][0]
            recommendation = self._get_recommendation(top_problem)
            self.recommendations_text.set_text(recommendation)
        else:
            self.recommendations_text.set_text("City is running smoothly!")

    def update_auto_evaluation(self, enabled: bool) -> None:
        """Update auto-evaluation checkbox state."""
        self.auto_eval_checkbox.set_toggled(enabled, fire=False)  # Changed

    def _get_current_year(self) -> int:
        """Get current game year from context."""
        return (self.context.city_time // 48) + self.context.starting_year

    def _get_score_color(self, score: int) -> tuple[int, int, int, int]:
        """Determine bar color based on score."""
        if score >= 700:
            return (50, 200, 50, 255)  # Green - excellent
        elif score >= 500:
            return (200, 200, 50, 255)  # Yellow - good
        elif score >= 300:
            return (200, 150, 50, 255)  # Orange - fair
        else:
            return (200, 50, 50, 255)  # Red - poor

    def _get_recommendation(self, problem: str) -> str:
        """Generate recommendation text based on top problem."""
        recommendations = {
            "Crime": "Increase police funding to reduce crime rates.",
            "Pollution": (
                "Add parks and reduce industrial zones near residential areas."
            ),
            "Housing Costs": ("Zone more residential areas and improve land values."),
            "Taxes": "Consider lowering tax rates to increase satisfaction.",
            "Traffic": "Build more roads and public transit to ease congestion.",
            "Unemployment": "Zone more commercial and industrial areas for jobs.",
            "Fires": "Increase fire department funding and coverage.",
        }
        return recommendations.get(problem, "Continue developing your city wisely.")

    def _handle_run_evaluation(self) -> None:
        if self._on_run_evaluation:
            self._on_run_evaluation()

    def _handle_view_budget(self) -> None:
        if self._on_view_budget:
            self._on_view_budget()

    def _handle_auto_eval_toggle(self, enabled: bool) -> None:
        self.context.auto_evaluation = enabled

    def _handle_notifications_toggle(self, enabled: bool) -> None:
        # Store notification preference in context
        self.context.eval_notifications = enabled

    def on_render(self, renderer: WidgetRenderer) -> None:
        palette = self.theme.palette if self.theme else None
        if palette:
            renderer.draw_rect(
                self.rect,
                palette.surface,
                border=True,
                border_color=palette.border,
                radius=8,
            )


class EvaluationPanel(UIPanel):
    """Evaluation panel displaying city scores and recommendations."""

    legacy_name = "EvaluationWindows"

    def __init__(self, manager, context: AppContext) -> None:
        super().__init__(manager, context)
        self.legacy_name = "EvaluationWindows"  # Restore after parent init
        self.visible = False  # Start hidden
        self._theme = ThemeManager().current
        self._event_bus: EventBus = (
            getattr(context, "event_bus", None) or get_default_event_bus()
        )
        self._state = EvaluationPanelState()
        self._renderer = RecordingRenderer()
        self._eval_subscription_id: str | None = None
        self._auto_eval_timer_id: str | None = None

        # Create dialog content
        dialog_rect = (100, 50, 824, 668)
        self._dialog_view = _EvaluationDialogView(dialog_rect, self._theme, context)
        self._dialog_view.set_callbacks(
            on_run_evaluation=self._handle_run_evaluation,
            on_view_budget=self._handle_view_budget,
        )

    # Lifecycle ------------------------------------------------------------
    def did_mount(self) -> None:
        self.set_rect((0, 0, 1024, 768))
        self._register_event_subscriptions()

        # Initialize auto-evaluation from context
        if hasattr(self.context, "auto_evaluation"):
            self._dialog_view.update_auto_evaluation(self.context.auto_evaluation)

    def did_unmount(self) -> None:
        self._unregister_event_subscriptions()
        self._stop_auto_eval_timer()

    # Public API -----------------------------------------------------------
    def open_evaluation(self) -> None:
        """Open the evaluation panel and refresh data."""
        if self._state.is_visible:
            return

        # Show the panel and refresh from the existing context. Do NOT
        # automatically run the full evaluation here: many tests construct a
        # pre-populated AppContext and expect the panel to reflect that
        # data rather than recomputing stochastic evaluation results.
        self.show()

        # Refresh display (state snapshot updated here)
        self.refresh_from_context()

        # Publish event
        self._event_bus.publish(
            "evaluation.opened",
            {},
            source="evaluation-panel",
            tags=("ui", "evaluation"),
            defer=True,
        )

        # Start auto-evaluation timer if enabled
        if self.context.auto_evaluation:
            self._start_auto_eval_timer()

    def close_evaluation(self) -> None:
        """Close the evaluation panel."""
        if not self._state.is_visible:
            return

        self.hide()
        self._stop_auto_eval_timer()

        self._state = EvaluationPanelState(is_visible=False)

        # Publish event
        self._event_bus.publish(
            "evaluation.closed",
            {},
            source="evaluation-panel",
            tags=("ui", "evaluation"),
            defer=True,
        )

    def toggle_evaluation(self) -> None:
        """Toggle evaluation panel visibility."""
        if self._state.is_visible:
            self.close_evaluation()
        else:
            self.open_evaluation()

    # Rendering ------------------------------------------------------------
    def draw(self, surface: Any) -> None:
        if not self.visible:
            return

        renderer: WidgetRenderer
        if isinstance(surface, WidgetRenderer):
            renderer = surface
        elif _HAVE_PYGAME and isinstance(surface, pygame.Surface):  # type: ignore
            renderer = _PygameWidgetRenderer(surface)
        else:
            renderer = self._renderer if surface is None else NullRenderer()

        # Draw semi-transparent background
        renderer.draw_rect(
            (0, 0, 1024, 768),
            (0, 0, 0, 180),
        )

        # Draw dialog
        self._dialog_view.render(renderer)

    # Event handling -------------------------------------------------------
    def handle_panel_event(self, event: Any) -> bool:
        if not self.visible:
            return False

        ui_event = self._convert_event(event)
        if ui_event is None:
            return False

        return self._dialog_view.handle_event(ui_event)

    def _convert_event(self, event: Any) -> UIEvent | None:
        if isinstance(event, UIEvent):
            return event
        if event is None:
            return None

        type_name = getattr(event, "type", None)
        if isinstance(type_name, int):
            # pygame event type
            if type_name == 4:  # MOUSEMOTION
                type_str = "mouse_move"
            elif type_name == 5:  # MOUSEBUTTONDOWN
                type_str = "mouse_down"
            elif type_name == 6:  # MOUSEBUTTONUP
                type_str = "mouse_up"
            elif type_name == 2:  # KEYDOWN
                type_str = "key_down"
            elif type_name == 3:  # KEYUP
                type_str = "key_up"
            else:
                return None
        elif isinstance(type_name, str):
            type_str = type_name.lower()
        else:
            return None

        pos = getattr(event, "pos", None) or getattr(event, "position", None)
        button = getattr(event, "button", None)
        key = getattr(event, "key", None)
        unicode_text = getattr(event, "unicode", None)

        return UIEvent(
            type=type_str,
            position=pos,
            button=button,
            key=key,
            unicode=unicode_text,
        )

    # Data updates ---------------------------------------------------------
    def refresh_from_context(self) -> None:
        """Refresh all display values from context."""
        ctx = self.context

        # Build top problems list
        top_problems = []
        for i in range(min(4, len(ctx.problem_order))):
            problem_idx = ctx.problem_order[i]
            if problem_idx < len(PROBLEM_STRINGS):
                problem_name = PROBLEM_STRINGS[problem_idx]
                vote_pct = (
                    ctx.problem_votes[problem_idx]
                    if problem_idx < len(ctx.problem_votes)
                    else 0
                )
                if vote_pct > 0:  # Only show problems with votes
                    top_problems.append((problem_name, vote_pct))

        # Get city class string
        city_class_names = [
            "VILLAGE",
            "TOWN",
            "CITY",
            "CAPITAL",
            "METROPOLIS",
            "MEGALOPOLIS",
        ]
        city_class = (
            city_class_names[ctx.city_class]
            if 0 <= ctx.city_class < len(city_class_names)
            else "VILLAGE"
        )

        # Get game level string
        level_names = ["Easy", "Medium", "Hard"]
        game_level = (
            level_names[ctx.game_level]
            if 0 <= ctx.game_level < len(level_names)
            else "Easy"
        )

        # Format assessed value
        assessed_value = f"${ctx.city_ass_value:,}"

        # Update dialog view
        self._dialog_view.update_evaluation_data(
            score=ctx.city_score,
            score_delta=ctx.delta_city_score,
            population=ctx.city_pop,
            pop_delta=ctx.delta_city_pop,
            city_class=city_class,
            game_level=game_level,
            assessed_value=assessed_value,
            approval_yes=ctx.city_yes,
            approval_no=ctx.city_no,
            top_problems=top_problems,
        )

        # Update state snapshot
        self._state = EvaluationPanelState(
            is_visible=self.visible,
            city_score=ctx.city_score,
            score_delta=ctx.delta_city_score,
            city_pop=ctx.city_pop,
            pop_delta=ctx.delta_city_pop,
            city_class=city_class,
            game_level=game_level,
            assessed_value=assessed_value,
            approval_yes=ctx.city_yes,
            approval_no=ctx.city_no,
            top_problems=top_problems,
            auto_evaluation=ctx.auto_evaluation
            if hasattr(ctx, "auto_evaluation")
            else False,
        )

    # Button handlers ------------------------------------------------------
    def _handle_run_evaluation(self) -> None:
        """Run city evaluation and refresh display."""
        eval_module.city_evaluation(self.context)
        self.refresh_from_context()

        self._event_bus.publish(
            "evaluation.run",
            {"score": self.context.city_score},
            source="evaluation-panel",
            tags=("evaluation", "run"),
            defer=True,
        )

    def _handle_view_budget(self) -> None:
        """Open budget panel."""
        self._event_bus.publish(
            "budget.open_requested",
            {},
            source="evaluation-panel",
            tags=("budget", "request"),
            defer=True,
        )

    # Auto-evaluation timer ------------------------------------------------
    def _start_auto_eval_timer(self) -> None:
        """Start periodic auto-evaluation (every game year)."""
        if self._auto_eval_timer_id:
            return

        # Run evaluation every simulated year (48 * 16 ticks ~ 768 ticks)
        # At normal speed, this is roughly every 30-60 seconds
        year_in_ms = 30000  # 30 seconds for demo purposes

        self._auto_eval_timer_id = self.manager.timer_service.call_every(
            year_in_ms,
            self._handle_auto_eval_tick,
            simulation_bound=True,
            tags=("simulation", "evaluation", "auto"),
        )

    def _stop_auto_eval_timer(self) -> None:
        """Stop auto-evaluation timer."""
        if self._auto_eval_timer_id and self.manager.timer_service.has_timer(
            self._auto_eval_timer_id
        ):
            self.manager.timer_service.cancel(self._auto_eval_timer_id)
        self._auto_eval_timer_id = None

    def _handle_auto_eval_tick(self, _: TimerEvent) -> None:
        """Handle auto-evaluation timer tick."""
        if not self.context.auto_evaluation:
            self._stop_auto_eval_timer()
            return

        eval_module.city_evaluation(self.context)

        # Only refresh if panel is visible
        if self.visible:
            self.refresh_from_context()

        # Optionally show notification
        if (
            hasattr(self.context, "eval_notifications")
            and self.context.eval_notifications  # type: ignore
        ):
            self._event_bus.publish(
                "message.post",
                {
                    "text": f"Annual evaluation: Score {self.context.city_score}",
                    "severity": "info",
                },
                source="evaluation-panel",
                tags=("message", "evaluation"),
                defer=True,
            )

    # Event subscriptions --------------------------------------------------
    def _register_event_subscriptions(self) -> None:
        """Subscribe to relevant events."""
        self._eval_subscription_id = self._event_bus.subscribe(
            "evaluation.open_requested",
            self._handle_evaluation_requested,
        )

    def _unregister_event_subscriptions(self) -> None:
        """Unsubscribe from events."""
        if self._eval_subscription_id:
            self._event_bus.unsubscribe(self._eval_subscription_id)
            self._eval_subscription_id = None

    def _handle_evaluation_requested(self, event) -> None:
        """Handle evaluation open request."""
        self.open_evaluation()

    # State snapshot -------------------------------------------------------
    def get_state(self) -> EvaluationPanelState:
        """Get current panel state for testing."""
        return self._state


__all__ = ["EvaluationPanel", "EvaluationPanelState"]
