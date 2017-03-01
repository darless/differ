import os
import sys
import pytest

from context import differ

def test_logging():
  """Test the logging function"""
  differ.utils.setup_logging('INFO')
  differ.utils.setup_logging('DEBUG')
  differ.utils.setup_logging('ERROR')

def test_get_file_type():
  """Test get_file_type"""
  assert differ.utils.get_file_type(None) == None
  assert differ.utils.get_file_type("Doesn't exist") == None
