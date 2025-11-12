"""
resources.py - Resource management for Micropolis Python port
"""

import os
from dataclasses import dataclass, field
from typing import Any

from src.micropolis.context import AppContext

# ============================================================================
# Type Definitions
# ============================================================================

QUAD = int  # Equivalent to C QUAD (int/long)
Handle = Any  # Equivalent to C Handle (char **)


# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class Resource:
    """
    Resource structure equivalent to C struct Resource.

    Represents a loaded resource with its data, metadata, and linked list pointer.
    """
    buf: bytes | None = None      # Resource data buffer
    size: QUAD = 0                   # Size of resource data
    name: str = ""                   # Resource name (4 characters)
    id: QUAD = 0                     # Resource ID
    next: "Resource | None" = None  # Next resource in linked list

@dataclass
class StringTable:
    """
    String table structure for localized strings.

    Equivalent to C struct StringTable.
    """
    id: QUAD = 0                           # String table ID
    lines: int = 0                         # Number of strings in table
    strings: list[str] = field(default_factory=list)            # Array of strings
    next: "StringTable | None" = None   # Next string table in linked list

    def __post_init__(self):
        if self.strings is None:
            self.strings = []


# ============================================================================
# Global Variables
# ============================================================================

# Directory paths
HomeDir: str = ""
ResourceDir: str = ""
KeyDir: str = ""
HostName: str = ""

# Resource management
Resources: "Resource | None" = None  # Head of resource linked list
StringTables: "StringTable | None" = None  # Head of string table linked list


# ============================================================================
# Resource Management Functions
# ============================================================================

def get_resource(context: AppContext, name: str, id: QUAD) -> "Handle | None":
    """
    Get a resource by name and ID, loading it from file if necessary.

    Ported from GetResource() in w_resrc.c.
    Loads resources from files with pattern: {ResourceDir}/{name[0]}{name[1]}{name[2]}{name[3]}.{id}

    Args:
        name: Resource name (4 characters)
        id: Resource ID

    Returns:
        Handle to resource data, or None if not found/failed to load
    """
    # global Resources

    # Check if resource is already loaded
    current = context.Resources
    while current is not None:
        if (current.id == id and
            len(current.name) >= 4 and len(name) >= 4 and
            current.name[:4] == name[:4]):
            # Return handle to existing resource
            return current.buf
        current = current.next

    # Resource not loaded, create new resource entry
    resource = Resource()
    resource.name = name[:4] if len(name) >= 4 else name.ljust(4)
    resource.id = id

    # Construct filename
    if os.name == 'nt':  # Windows
        filename = f"{ResourceDir}\\{resource.name[0]}{resource.name[1]}{resource.name[2]}{resource.name[3]}.{resource.id}"
        perm_mode = 'rb'
    else:  # Unix-like systems
        filename = f"{ResourceDir}/{resource.name[0]}{resource.name[1]}{resource.name[2]}{resource.name[3]}.{resource.id}"
        perm_mode = 'r'

    # Try to load the file
    try:
        file_size = os.path.getsize(filename)
        if file_size == 0:
            print(f"Warning: Resource file '{filename}' is empty")
            return None

        resource.size = file_size

        with open(filename, perm_mode) as f:
            if perm_mode == 'rb':
                resource.buf = f.read()
            else:
                # For text mode, read as bytes anyway for consistency
                resource.buf = f.read().encode('latin-1')

        # Add to linked list
        resource.next = Resources
        Resources = resource

        return resource.buf

    except (OSError, IOError) as e:
        print(f"Can't find resource file '{filename}': {e}")
        return None


def release_resource(handle: Handle) -> None:
    """
    Release a resource.

    Ported from ReleaseResource() in w_resrc.c.
    Currently a stub implementation - resources are kept in memory.

    Args:
        handle: Handle to resource to release
    """
    # In the original C code, this was a stub too
    # Resources are kept cached in memory for performance
    pass


def resource_size(handle: Handle) -> QUAD:
    """
    Get the size of a resource.

    Ported from ResourceSize() in w_resrc.c.

    Args:
        handle: Handle to resource

    Returns:
        Size of resource in bytes, or 0 if handle is invalid
    """
    if handle is None:
        return 0

    # Find the resource in the linked list
    current = Resources
    while current is not None:
        if current.buf is handle:
            return current.size
        current = current.next

    return 0


def resource_name(handle: Handle) -> str:
    """
    Get the name of a resource.

    Ported from ResourceName() in w_resrc.c.

    Args:
        handle: Handle to resource

    Returns:
        Resource name, or empty string if handle is invalid
    """
    if handle is None:
        return ""

    # Find the resource in the linked list
    current = Resources
    while current is not None:
        if current.buf is handle:
            return current.name
        current = current.next

    return ""


def resource_id(handle: Handle) -> QUAD:
    """
    Get the ID of a resource.

    Ported from ResourceID() in w_resrc.c.

    Args:
        handle: Handle to resource

    Returns:
        Resource ID, or 0 if handle is invalid
    """
    if handle is None:
        return 0

    # Find the resource in the linked list
    current = Resources
    while current is not None:
        if current.buf is handle:
            return current.id
        current = current.next

    return 0


def get_ind_string(context: AppContext, str_buffer: list[str], id: int, num: int) -> None:
    """
    Get a string from a string table resource.

    Ported from GetIndString() in w_resrc.c.
    Loads string table resources and extracts individual strings.

    Args:
        str_buffer: Output buffer to store the string (modified in place)
        id: String table resource ID
        num: String index (1-based)
    """
    # global StringTables

    # Find existing string table
    table_ptr = context.StringTables
    while table_ptr is not None:
        if table_ptr.id == id:
            break
        table_ptr = table_ptr.next

    # If not found, load the string table resource
    if table_ptr is None:
        table = StringTable()
        table.id = id

        # Load the string table resource
        handle = get_resource(context, "stri", id)
        if handle is None:
            str_buffer[0] = "Well I'll be a monkey's uncle!"
            return

        size = resource_size(handle)
        if size == 0:
            str_buffer[0] = "Well I'll be a monkey's uncle!"
            return

        # Convert bytes to string and split on newlines
        try:
            content = handle.decode('latin-1') if isinstance(handle, bytes) else str(handle)
        except UnicodeDecodeError:
            content = str(handle)

        # Replace newlines with null terminators and count lines
        lines = []
        current_line = ""
        for char in content:
            if char == '\n':
                if current_line:  # Don't add empty lines
                    # Strip carriage returns and whitespace
                    clean_line = current_line.rstrip('\r')
                    lines.append(clean_line)
                current_line = ""
            else:
                current_line += char

        # Add the last line if it exists
        if current_line:
            clean_line = current_line.rstrip('\r')
            lines.append(clean_line)

        table.lines = len(lines)
        table.strings = lines

        # Add to linked list
        table.next = StringTables
        StringTables = table
        table_ptr = table

    # Get the requested string
    if num < 1 or num > table_ptr.lines:
        print(f"Out of range string index: {num}")
        str_buffer[0] = "Well I'll be a monkey's uncle!"
    else:
        str_buffer[0] = table_ptr.strings[num - 1]  # Convert to 0-based indexing


# ============================================================================
# TCL Command Interface
# ============================================================================

class ResourcesCommand:
    """
    TCL command interface for resource management functions.
    """

    @staticmethod
    def handle_command(context: AppContext, command : str, *args: str) -> str:
        """
        Handle TCL resource commands.

        Args:
            command: TCL command name
            *args: Command arguments

        Returns:
            TCL command result
        """
        if command == "getresource":
            if len(args) != 2:
                raise ValueError("Usage: getresource <name> <id>")
            name = args[0]
            try:
                id_val = int(args[1])
            except ValueError:
                raise ValueError("Resource ID must be an integer")
            handle = get_resource(name, id_val)
            return "1" if handle is not None else "0"

        elif command == "resourceloaded":
            if len(args) != 2:
                raise ValueError("Usage: resourceloaded <name> <id>")
            name = args[0]
            try:
                id_val = int(args[1])
            except ValueError:
                raise ValueError("Resource ID must be an integer")

            # Check if resource exists in cache
            current = Resources
            while current is not None:
                if (current.id == id_val and
                    len(current.name) >= 4 and len(name) >= 4 and
                    current.name[:4] == name[:4]):
                    return "1"
                current = current.next
            return "0"

        elif command == "getindstring":
            if len(args) != 2:
                raise ValueError("Usage: getindstring <id> <index>")
            try:
                id_val = int(args[0])
                index = int(args[1])
            except ValueError:
                raise ValueError("ID and index must be integers")

            str_buffer = [""]
            get_ind_string(str_buffer, id_val, index)
            return str_buffer[0]

        elif command == "setresourcedir":
            if len(args) != 1:
                raise ValueError("Usage: setresourcedir <path>")
            # global ResourceDir
            context.ResourceDir = args[0]
            return ""

        elif command == "getresourcedir":
            if len(args) != 0:
                raise ValueError("Usage: getresourcedir")
            return context.ResourceDir

        else:
            raise ValueError(f"Unknown resources command: {command}")


# ============================================================================
# Utility Functions
# ============================================================================

def initialize_resource_paths(context: AppContext) -> None:
    """
    Initialize resource directory paths.

    Sets up default paths for resource loading.
    """
    # global ResourceDir, HomeDir

    # Set default resource directory
    if not context.ResourceDir:
        # Try to find resources relative to the script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        potential_dirs = [
            os.path.join(script_dir, "..", "..", "assets"),  # From src/micropolis/
            os.path.join(script_dir, "..", "assets"),        # From src/
            "assets",                                        # From project root
        ]

        for res_dir in potential_dirs:
            if os.path.exists(res_dir):
                context.ResourceDir = os.path.abspath(res_dir)
                break

    # Set home directory
    if not context.HomeDir:
        context.HomeDir = os.path.expanduser("~")


def clear_resource_cache(context: AppContext) -> None:
    """
    Clear all cached resources.

    Frees memory by clearing the resource linked list.
    """
    # global Resources, StringTables
    context.Resources = None
    context.StringTables = None
