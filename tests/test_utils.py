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

def test_logging():
  """Test the logging function"""
  differ.utils.setup_logging('INFO')
  differ.utils.setup_logging('DEBUG')
  differ.utils.setup_logging('ERROR')

class TestDiffer():
  base = "/tmp/differ/"

  @pytest.fixture(scope='function', autouse=True)
  def setup(self):
    """This function will be run before every test function in this class"""
    print("Running setup function")
    if os.path.exists(self.base):
      os.system("rm -rf {}".format(self.base))

  def test_utils_differ(self):
    """Test the basic functionality of differ.utils.Differ"""
    differ.utils.Differ(None, None)
    assert not differ.utils.Differ("FAIL", "FAIL")._valid
    obj = differ.utils.Differ(".", "FAIL")
    assert not obj._valid
    assert "NOT VALID" in repr(obj)

    # Test with the same tar files
    obj = differ.utils.Differ(
      "tests/files/before.tgz",
      "tests/files/before.tgz",
      base=self.base)
    assert obj._valid
def test_utils_paths():
  # No paths specified should cause paths to be empty
  paths = differ.utils.Paths(None)
  assert not paths.paths

  # A non-existant path should cause paths to be empty
  paths = differ.utils.Paths("/does/not/exist")
  assert not paths.paths

def test_logging():
  """Test the logging function"""
  differ.utils.setup_logging('INFO')
  differ.utils.setup_logging('DEBUG')
  differ.utils.setup_logging('ERROR')

class TestDiffer():
  base = "/tmp/differ/"

  @pytest.fixture(scope='function', autouse=True)
  def setup(self):
    """This function will be run before every test function in this class"""
    print("Running setup function")
    if os.path.exists(self.base):
      os.system("rm -rf {}".format(self.base))

  def test_utils_differ(self):
    """Test the basic functionality of differ.utils.Differ"""
    differ.utils.Differ(None, None)
    assert not differ.utils.Differ("FAIL", "FAIL")._valid
    obj = differ.utils.Differ(".", "FAIL")
    assert not obj._valid
    assert "NOT VALID" in repr(obj)

    # Test with the same tar files
    obj = differ.utils.Differ(
      "tests/files/before.tgz",
      "tests/files/before.tgz",
      base=self.base)
    assert obj._valid
    assert "NOT VALID" not in repr(obj)
    obj.start()
    print(obj.path1_obj)
    assert not obj.add_list
    assert not obj.rm_list
    assert not obj.changed_list

    # Test with the differnt tar files
    obj = differ.utils.Differ(
      "tests/files/before.tgz",
      "tests/files/after.tgz",
      base=self.base)
    assert obj._valid
    obj.start()
    assert len(obj.add_list) == 1
    assert len(obj.rm_list) == 1
    assert len(obj.changed_list) == 2

  def test_plugin_iptables_strip(self):
    """Test the plugin iptables stripper"""
    obj = differ.utils.Differ(
      "tests/files/plugins/iptables/before.tgz",
      "tests/files/plugins/iptables/after.tgz",
      base=self.base)
    assert obj._valid
    obj.start()
    assert len(obj.add_list) == 0
    assert len(obj.rm_list) == 0
    assert len(obj.changed_list) == 1
    assert os.path.exists(obj.diff_dir)
    changed_path = os.path.join(
      obj.changed_dir,
      "my_iptables_mangle.diff")
    with open(changed_path, "r") as fp:
      changed_content = fp.read()
    assert "-DIFFER-TEST-3" in changed_content
    assert "+DIFFER-TEST-4" in changed_content
