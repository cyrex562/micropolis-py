#!/usr/bin/env python3
"""
Script to automate the retirement of Tcl/Tk scripts once pygame replacements reach parity.

This script implements the workflow described in §8.1 of docs/pygame_ui_port_checklist.md.

Usage:
    uv run python scripts/retire_tcl_script.py check <script_name>
    uv run python scripts/retire_tcl_script.py retire <script_name> [--force]
    uv run python scripts/retire_tcl_script.py list [--status <status>]
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
DOCS_DIR = PROJECT_ROOT / "docs"
TESTS_DIR = PROJECT_ROOT / "tests"
TRACKER_FILE = DOCS_DIR / "TCL_MIGRATION_TRACKER.md"


class TclScriptRetirement:
    """Handles the retirement process for Tcl/Tk scripts."""

    # Script metadata mapping
    SCRIPT_METADATA = {
        "micropolis.tcl": {
            "pygame_module": "src/micropolis/ui/app.py",
            "tests": ["tests/ui/test_app.py"],
            "description": "Root launcher with panel orchestration",
            "category": "core",
        },
        "whead.tcl": {
            "pygame_module": "src/micropolis/ui/panels/head_panel.py",
            "tests": ["tests/ui/test_head_panel.py"],
            "description": "Head/status panel",
            "category": "core",
        },
        "weditor.tcl": {
            "pygame_module": "src/micropolis/ui/panels/editor_panel.py",
            "tests": ["tests/ui/test_editor_panel.py"],
            "description": "Editor canvas + tool palette",
            "category": "core",
        },
        "wmap.tcl": {
            "pygame_module": "src/micropolis/ui/panels/map_panel.py",
            "tests": ["tests/ui/test_map_panel.py"],
            "description": "Overview/minimap panel",
            "category": "core",
        },
        "wgraph.tcl": {
            "pygame_module": "src/micropolis/ui/panels/graph_panel.py",
            "tests": ["tests/ui/test_graph_panel.py"],
            "description": "Graph panel",
            "category": "core",
        },
        "wbudget.tcl": {
            "pygame_module": "src/micropolis/ui/panels/budget_panel.py",
            "tests": ["tests/ui/test_budget_panel.py"],
            "description": "Budget dialog",
            "category": "core",
        },
        "weval.tcl": {
            "pygame_module": "src/micropolis/ui/panels/evaluation_panel.py",
            "tests": ["tests/ui/test_evaluation_panel.py"],
            "description": "Evaluation panel",
            "category": "core",
        },
        "wnotice.tcl": {
            "pygame_module": "src/micropolis/ui/panels/notice_panel.py",
            "tests": ["tests/ui/test_notice_panel.py"],
            "description": "Notice/message panel",
            "category": "core",
        },
        "wplayer.tcl": {
            "pygame_module": "src/micropolis/ui/panels/player_panel.py",
            "tests": ["tests/ui/test_player_panel.py"],
            "description": "Player/chat panel",
            "category": "core",
        },
        "whelp.tcl": {
            "pygame_module": "src/micropolis/ui/panels/help_panel.py",
            "tests": ["tests/ui/test_help_panel.py"],
            "description": "Help browser",
            "category": "core",
        },
        "wfile.tcl": {
            "pygame_module": "src/micropolis/ui/dialogs/file_dialog.py",
            "tests": ["tests/ui/test_file_dialog.py"],
            "description": "File dialog",
            "category": "core",
        },
        "wask.tcl": {
            "pygame_module": "src/micropolis/ui/dialogs/ask_dialog.py",
            "tests": ["tests/ui/test_ask_dialog.py"],
            "description": "Confirmation dialog",
            "category": "core",
        },
        "wfrob.tcl": {
            "pygame_module": "src/micropolis/ui/panels/debug_panel.py",
            "tests": ["tests/ui/test_debug_panel.py"],
            "description": "Debug/frob controls",
            "category": "core",
        },
        "wscen.tcl": {
            "pygame_module": "src/micropolis/ui/scenes/scenario_scene.py",
            "tests": ["tests/ui/test_scenario_scene.py"],
            "description": "Scenario picker",
            "category": "core",
        },
        "wsplash.tcl": {
            "pygame_module": "src/micropolis/ui/scenes/splash_scene.py",
            "tests": ["tests/ui/test_splash_scene.py"],
            "description": "Splash screen",
            "category": "core",
        },
        "button.tcl": {
            "pygame_module": "src/micropolis/ui/widgets/button.py",
            "tests": ["tests/ui/widgets/test_button.py"],
            "description": "Button widget",
            "category": "widget",
        },
        "menu.tcl": {
            "pygame_module": "src/micropolis/ui/widgets/menu.py",
            "tests": ["tests/ui/widgets/test_menu.py"],
            "description": "Menu widget",
            "category": "widget",
        },
        "listbox.tcl": {
            "pygame_module": "src/micropolis/ui/widgets/listbox.py",
            "tests": ["tests/ui/widgets/test_listbox.py"],
            "description": "Listbox widget",
            "category": "widget",
        },
        "entry.tcl": {
            "pygame_module": "src/micropolis/ui/widgets/entry.py",
            "tests": ["tests/ui/widgets/test_entry.py"],
            "description": "Entry widget",
            "category": "widget",
        },
        "text.tcl": {
            "pygame_module": "src/micropolis/ui/widgets/text.py",
            "tests": ["tests/ui/widgets/test_text.py"],
            "description": "Text widget",
            "category": "widget",
        },
        "help.tcl": {
            "pygame_module": "src/micropolis/ui/help_system.py",
            "tests": ["tests/ui/test_help_system.py"],
            "description": "Help system",
            "category": "widget",
        },
        "sound.tcl": {
            "pygame_module": "src/micropolis/audio.py",
            "tests": ["tests/test_audio.py"],
            "description": "Sound system",
            "category": "widget",
        },
    }

    def __init__(self, script_name: str):
        self.script_name = script_name
        self.script_path = ASSETS_DIR / script_name
        self.metadata = self.SCRIPT_METADATA.get(script_name)

    def check_parity(self) -> Dict[str, bool]:
        """
        Check if pygame replacement meets parity requirements.

        Returns:
            Dict with check results: tests_pass, pygame_exists, docs_updated
        """
        results = {
            "tests_pass": False,
            "pygame_exists": False,
            "docs_updated": False,
            "script_exists": self.script_path.exists(),
        }

        if not self.metadata:
            print(f"⚠️  No metadata found for {self.script_name}")
            return results

        # Check if pygame replacement exists
        pygame_path = PROJECT_ROOT / self.metadata["pygame_module"]
        results["pygame_exists"] = pygame_path.exists()

        if results["pygame_exists"]:
            print(f"✅ Pygame replacement exists: {self.metadata['pygame_module']}")
        else:
            print(f"❌ Pygame replacement missing: {self.metadata['pygame_module']}")

        # Check if tests exist and pass
        tests_exist = all(
            (PROJECT_ROOT / test).exists() for test in self.metadata["tests"]
        )

        if tests_exist:
            print(f"✅ Test files exist: {', '.join(self.metadata['tests'])}")
            # Run tests
            try:
                for test_file in self.metadata["tests"]:
                    result = subprocess.run(
                        ["uv", "run", "pytest", test_file, "-v"],
                        cwd=PROJECT_ROOT,
                        capture_output=True,
                        text=True,
                    )
                    if result.returncode == 0:
                        print(f"✅ Tests pass: {test_file}")
                        results["tests_pass"] = True
                    else:
                        print(f"❌ Tests fail: {test_file}")
                        print(result.stdout)
                        results["tests_pass"] = False
                        break
            except Exception as e:
                print(f"⚠️  Could not run tests: {e}")
        else:
            print(f"❌ Test files missing")

        # Check if tracker doc is updated
        if TRACKER_FILE.exists():
            content = TRACKER_FILE.read_text()
            if self.script_name in content:
                results["docs_updated"] = True
                print(f"✅ Tracker doc includes {self.script_name}")
            else:
                print(f"⚠️  Tracker doc missing {self.script_name}")

        return results

    def create_git_tag(self) -> bool:
        """Create a git tag before retiring the script."""
        script_basename = self.script_name.replace(".tcl", "")
        tag_name = f"tcl-{script_basename}-final"
        tag_message = f"Last version of {self.script_name} before pygame migration"

        try:
            # Check if tag already exists
            result = subprocess.run(
                ["git", "tag", "-l", tag_name],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
            )

            if result.stdout.strip():
                print(f"⚠️  Tag {tag_name} already exists")
                return True

            # Create tag
            subprocess.run(
                ["git", "tag", "-a", tag_name, "-m", tag_message],
                cwd=PROJECT_ROOT,
                check=True,
            )
            print(f"✅ Created git tag: {tag_name}")

            # Push tag (optional, may fail if no remote)
            try:
                subprocess.run(
                    ["git", "push", "origin", tag_name],
                    cwd=PROJECT_ROOT,
                    check=True,
                    capture_output=True,
                )
                print(f"✅ Pushed tag to remote: {tag_name}")
            except subprocess.CalledProcessError:
                print(f"⚠️  Could not push tag (no remote or not configured)")

            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create git tag: {e}")
            return False

    def update_tracker_doc(self, retired_date: str) -> bool:
        """Update the migration tracker document."""
        if not TRACKER_FILE.exists():
            print(f"❌ Tracker file not found: {TRACKER_FILE}")
            return False

        content = TRACKER_FILE.read_text()

        # Update status to RETIRED and add date
        # Look for the script in the table and update its status
        lines = content.split("\n")
        updated_lines = []
        for line in lines:
            if self.script_name in line and "🟢 READY" in line:
                line = line.replace("🟢 READY", "✅ RETIRED")
                line = line.replace("| - |", f"| {retired_date} |")
                print(f"✅ Updated tracker: {self.script_name} marked as RETIRED")
            updated_lines.append(line)

        TRACKER_FILE.write_text("\n".join(updated_lines))
        return True

    def retire(self, force: bool = False) -> bool:
        """
        Retire the Tcl script after all checks pass.

        Args:
            force: Skip parity checks if True

        Returns:
            True if retirement successful
        """
        if not self.script_path.exists():
            print(f"❌ Script not found: {self.script_path}")
            return False

        # Run parity checks unless forced
        if not force:
            print(f"\n🔍 Checking parity for {self.script_name}...\n")
            results = self.check_parity()

            if not all([results["pygame_exists"], results["tests_pass"]]):
                print(f"\n❌ Parity checks failed. Use --force to override.")
                return False

            print(f"\n✅ All parity checks passed!\n")

        # Create git tag for archival
        print(f"📦 Creating archival git tag...")
        if not self.create_git_tag():
            print(f"⚠️  Could not create git tag, but continuing...")

        # Update tracker document
        retired_date = datetime.now().strftime("%Y-%m-%d")
        print(f"📝 Updating tracker document...")
        self.update_tracker_doc(retired_date)

        # Remove the script
        print(f"🗑️  Removing {self.script_path}...")
        try:
            subprocess.run(
                ["git", "rm", str(self.script_path)],
                cwd=PROJECT_ROOT,
                check=True,
            )
            print(f"✅ Removed {self.script_name}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to remove script: {e}")
            print(f"   You may need to manually remove: {self.script_path}")
            return False

        # Commit the changes
        print(f"💾 Committing retirement...")
        commit_message = f"Retire {self.script_name} - pygame replacement complete"
        try:
            subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=PROJECT_ROOT,
                check=True,
            )
            print(f"✅ Committed retirement of {self.script_name}")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Could not commit changes: {e}")
            print(f"   You may want to commit manually.")

        print(f"\n🎉 Successfully retired {self.script_name}!")
        print(f"   Pygame replacement: {self.metadata['pygame_module']}")
        print(f"   Retired date: {retired_date}")

        return True


def list_scripts(status_filter: Optional[str] = None):
    """List all Tcl scripts and their status."""
    print("\n📋 Tcl/Tk Script Status\n")

    for script_name, metadata in TclScriptRetirement.SCRIPT_METADATA.items():
        script_path = ASSETS_DIR / script_name
        exists = script_path.exists()

        if exists:
            status = "🟢 READY" if metadata.get("pygame_module") else "🔴 NOT STARTED"
        else:
            status = "✅ RETIRED"

        if status_filter:
            if status_filter.lower() == "retired" and status != "✅ RETIRED":
                continue
            elif status_filter.lower() == "ready" and status != "🟢 READY":
                continue
            elif status_filter.lower() == "pending" and status == "✅ RETIRED":
                continue

        print(f"{status} {script_name:25} → {metadata.get('pygame_module', 'N/A')}")


def main():
    parser = argparse.ArgumentParser(
        description="Manage retirement of Tcl/Tk scripts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check if script is ready to retire
  uv run python scripts/retire_tcl_script.py check whead.tcl
  
  # Retire a script (runs checks first)
  uv run python scripts/retire_tcl_script.py retire whead.tcl
  
  # Force retire without checks (use with caution)
  uv run python scripts/retire_tcl_script.py retire whead.tcl --force
  
  # List all scripts
  uv run python scripts/retire_tcl_script.py list
  
  # List only retired scripts
  uv run python scripts/retire_tcl_script.py list --status retired
""",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Check command
    check_parser = subparsers.add_parser("check", help="Check if script meets parity")
    check_parser.add_argument("script_name", help="Tcl script name (e.g., whead.tcl)")

    # Retire command
    retire_parser = subparsers.add_parser("retire", help="Retire a Tcl script")
    retire_parser.add_argument("script_name", help="Tcl script name (e.g., whead.tcl)")
    retire_parser.add_argument(
        "--force", action="store_true", help="Skip parity checks"
    )

    # List command
    list_parser = subparsers.add_parser("list", help="List all Tcl scripts")
    list_parser.add_argument(
        "--status",
        choices=["retired", "ready", "pending"],
        help="Filter by status",
    )

    args = parser.parse_args()

    if args.command == "check":
        retirement = TclScriptRetirement(args.script_name)
        results = retirement.check_parity()
        sys.exit(0 if all(results.values()) else 1)

    elif args.command == "retire":
        retirement = TclScriptRetirement(args.script_name)
        success = retirement.retire(force=args.force)
        sys.exit(0 if success else 1)

    elif args.command == "list":
        list_scripts(status_filter=args.status)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
