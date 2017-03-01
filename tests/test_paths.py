import os
import sys
import pytest

from context import differ

def test_utils_paths():
  # No paths specified should cause paths to be empty
  paths = differ.utils.Paths(None)
  assert not paths.paths

  # A non-existant path should cause paths to be empty
  paths = differ.utils.Paths("/does/not/exist")
  assert not paths.paths
