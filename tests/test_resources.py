"""
test_resources.py - Test suite for resources.py module
"""

import os
import tempfile
import unittest
from unittest.mock import patch, mock_open
from typing import List

# Import the module to test
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from micropolis import resources


class TestResources(unittest.TestCase):
    """Test cases for resources.py module"""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Clear any cached resources
        resources.clear_resource_cache()

        # Create a temporary directory for test resources
        self.test_dir = tempfile.mkdtemp()
        resources.ResourceDir = self.test_dir

        # Create test resource files
        self.create_test_resources()

    def tearDown(self):
        """Clean up test fixtures after each test method."""
        # Clear cache
        resources.clear_resource_cache()

        # Reset global variables
        resources.ResourceDir = ""
        resources.HomeDir = ""

        # Clean up test files
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def create_test_resources(self):
        """Create test resource files for testing."""
        # Create test resource file: test.1
        test_file_path = os.path.join(self.test_dir, "test.1")
        with open(test_file_path, 'wb') as f:
            f.write(b"Hello, World!")

        # Create string table resource: stri.100
        stri_file_path = os.path.join(self.test_dir, "stri.100")
        with open(stri_file_path, 'w') as f:
            f.write("First string\nSecond string\nThird string\n")

        # Create another resource: abcd.42
        abcd_file_path = os.path.join(self.test_dir, "abcd.42")
        with open(abcd_file_path, 'wb') as f:
            f.write(b"Test data for ABCD")

    def test_get_resource_basic(self):
        """Test basic resource loading functionality."""
        # Test loading a resource
        handle = resources.get_resource("test", 1)
        self.assertIsNotNone(handle)
        self.assertEqual(handle, b"Hello, World!")

        # Test that resource is cached (second call returns same handle)
        handle2 = resources.get_resource("test", 1)
        self.assertEqual(handle, handle2)

    def test_get_resource_not_found(self):
        """Test loading a non-existent resource."""
        handle = resources.get_resource("nonexistent", 999)
        self.assertIsNone(handle)

    def test_get_resource_different_ids(self):
        """Test loading resources with same name but different IDs."""
        # Create another test resource
        test2_path = os.path.join(self.test_dir, "test.2")
        with open(test2_path, 'wb') as f:
            f.write(b"Different content")

        handle1 = resources.get_resource("test", 1)
        handle2 = resources.get_resource("test", 2)

        self.assertIsNotNone(handle1)
        self.assertIsNotNone(handle2)
        self.assertNotEqual(handle1, handle2)
        self.assertEqual(handle1, b"Hello, World!")
        self.assertEqual(handle2, b"Different content")

    def test_resource_size(self):
        """Test ResourceSize function."""
        handle = resources.get_resource("test", 1)
        self.assertIsNotNone(handle)

        size = resources.resource_size(handle)
        self.assertEqual(size, 13)  # "Hello, World!" is 13 bytes

        # Test with invalid handle
        size_invalid = resources.resource_size(None)
        self.assertEqual(size_invalid, 0)

    def test_resource_name(self):
        """Test ResourceName function."""
        handle = resources.get_resource("test", 1)
        self.assertIsNotNone(handle)

        name = resources.resource_name(handle)
        self.assertEqual(name, "test")

        # Test with invalid handle
        name_invalid = resources.resource_name(None)
        self.assertEqual(name_invalid, "")

    def test_resource_id(self):
        """Test ResourceID function."""
        handle = resources.get_resource("test", 1)
        self.assertIsNotNone(handle)

        id_val = resources.resource_id(handle)
        self.assertEqual(id_val, 1)

        # Test with invalid handle
        id_invalid = resources.resource_id(None)
        self.assertEqual(id_invalid, 0)

    def test_get_ind_string_basic(self):
        """Test GetIndString function with basic string table."""
        str_buffer: List[str] = [""]

        # Test getting first string (1-based indexing)
        resources.get_ind_string(str_buffer, 100, 1)
        self.assertEqual(str_buffer[0], "First string")

        # Test getting second string
        resources.get_ind_string(str_buffer, 100, 2)
        self.assertEqual(str_buffer[0], "Second string")

        # Test getting third string
        resources.get_ind_string(str_buffer, 100, 3)
        self.assertEqual(str_buffer[0], "Third string")

    def test_get_ind_string_caching(self):
        """Test that string tables are cached properly."""
        str_buffer: List[str] = [""]

        # Load string table once
        resources.get_ind_string(str_buffer, 100, 1)
        self.assertEqual(str_buffer[0], "First string")

        # Modify the cached string table to verify caching
        table = resources.StringTables
        self.assertIsNotNone(table)
        self.assertEqual(table.id, 100)
        table.strings[0] = "Modified string"

        # Get the same string again - should return modified version
        resources.get_ind_string(str_buffer, 100, 1)
        self.assertEqual(str_buffer[0], "Modified string")

    def test_get_ind_string_out_of_range(self):
        """Test GetIndString with out-of-range indices."""
        str_buffer: List[str] = [""]

        # Test index 0 (should be out of range)
        resources.get_ind_string(str_buffer, 100, 0)
        self.assertEqual(str_buffer[0], "Well I'll be a monkey's uncle!")

        # Test index beyond table size
        resources.get_ind_string(str_buffer, 100, 10)
        self.assertEqual(str_buffer[0], "Well I'll be a monkey's uncle!")

    def test_get_ind_string_missing_table(self):
        """Test GetIndString with non-existent string table."""
        str_buffer: List[str] = [""]

        # Try to load non-existent string table
        resources.get_ind_string(str_buffer, 999, 1)
        self.assertEqual(str_buffer[0], "Well I'll be a monkey's uncle!")

    def test_release_resource(self):
        """Test ReleaseResource function (currently a stub)."""
        handle = resources.get_resource("test", 1)
        self.assertIsNotNone(handle)

        # Release should not crash (currently a no-op)
        resources.release_resource(handle)

        # Resource should still be accessible (cached)
        handle2 = resources.get_resource("test", 1)
        self.assertEqual(handle, handle2)

    def test_initialize_resource_paths(self):
        """Test initialize_resource_paths function."""
        # Reset paths
        resources.ResourceDir = ""
        resources.HomeDir = ""

        # Create a mock res directory
        res_dir = os.path.join(self.test_dir, "res")
        os.makedirs(res_dir)

        # Change to test directory and initialize
        old_cwd = os.getcwd()
        try:
            os.chdir(self.test_dir)
            resources.initialize_resource_paths()

            # Should find the res directory
            self.assertTrue(resources.ResourceDir.endswith("res"))
            self.assertTrue(os.path.exists(resources.ResourceDir))

            # Home directory should be set
            self.assertNotEqual(resources.HomeDir, "")

        finally:
            os.chdir(old_cwd)

    def test_clear_resource_cache(self):
        """Test clear_resource_cache function."""
        # Load some resources
        handle1 = resources.get_resource("test", 1)
        handle2 = resources.get_resource("abcd", 42)

        self.assertIsNotNone(handle1)
        self.assertIsNotNone(handle2)

        # Verify resources are in cache
        self.assertIsNotNone(resources.Resources)

        # Clear cache
        resources.clear_resource_cache()

        # Cache should be empty
        self.assertIsNone(resources.Resources)
        self.assertIsNone(resources.StringTables)

    def test_tcl_commands_getresource(self):
        """Test TCL getresource command."""
        result = resources.ResourcesCommand.handle_command("getresource", "test", "1")
        self.assertEqual(result, "1")  # Should succeed

        result = resources.ResourcesCommand.handle_command("getresource", "nonexistent", "999")
        self.assertEqual(result, "0")  # Should fail

    def test_tcl_commands_resourceloaded(self):
        """Test TCL resourceloaded command."""
        # Load a resource first
        resources.get_resource("test", 1)

        result = resources.ResourcesCommand.handle_command("resourceloaded", "test", "1")
        self.assertEqual(result, "1")  # Should be loaded

        result = resources.ResourcesCommand.handle_command("resourceloaded", "test", "2")
        self.assertEqual(result, "0")  # Should not be loaded

    def test_tcl_commands_getindstring(self):
        """Test TCL getindstring command."""
        result = resources.ResourcesCommand.handle_command("getindstring", "100", "1")
        self.assertEqual(result, "First string")

        result = resources.ResourcesCommand.handle_command("getindstring", "100", "2")
        self.assertEqual(result, "Second string")

    def test_tcl_commands_setresourcedir(self):
        """Test TCL setresourcedir command."""
        test_path = "/test/path"
        result = resources.ResourcesCommand.handle_command("setresourcedir", test_path)
        self.assertEqual(result, "")
        self.assertEqual(resources.ResourceDir, test_path)

    def test_tcl_commands_getresourcedir(self):
        """Test TCL getresourcedir command."""
        resources.ResourceDir = "/test/path"
        result = resources.ResourcesCommand.handle_command("getresourcedir")
        self.assertEqual(result, "/test/path")

    def test_tcl_commands_invalid(self):
        """Test TCL command error handling."""
        with self.assertRaises(ValueError):
            resources.ResourcesCommand.handle_command("invalidcommand")

        with self.assertRaises(ValueError):
            resources.ResourcesCommand.handle_command("getresource", "onlyonearg")

        with self.assertRaises(ValueError):
            resources.ResourcesCommand.handle_command("getresource", "name", "notanumber")


if __name__ == '__main__':
    unittest.main()