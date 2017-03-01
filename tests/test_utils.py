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
    differ.utils.setup_logging('DEBUG')

  def test_utils_differ(self):
    """Test the basic functionality of differ.utils.Differ"""
    differ.utils.Differ(None, None)
    assert not differ.utils.Differ("FAIL", "FAIL")._valid
    obj = differ.utils.Differ(".", "FAIL")
    assert not obj._valid
    assert "NOT VALID" in repr(obj)
    assert not obj.extract_path(None, None)
    assert not obj.extract_path("Something", None)

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

    # Test with the different files
    before_items = [
      # TAR
      'before.tar',
      # TAR GZIP
      'before.tar.gz',
      'before.tgz',
      # TAR BZIP2
      'before.tar.bz2',
      # TAR LZMA
      'before.tar.xz',
      # ZIP
      'before.zip',
      # Directory
      'before',
    ]
    for f_name in before_items:
      obj = differ.utils.Differ(
        "tests/files/{}".format(f_name),
        "tests/files/after.tgz",
        base=self.base)
      assert obj._valid
      obj.start()
      assert len(obj.add_list) == 1
      assert len(obj.rm_list) == 1
      assert len(obj.changed_list) == 2
      assert os.path.exists(obj.summary_path)
      with open(obj.summary_path) as fp:
        summary = fp.read()
        assert "added 1" in summary
        assert "removed 1" in summary
        assert "changed 2" in summary

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

class TestPath():
  base = "/tmp/differ/"

  @pytest.fixture(scope='function', autouse=True)
  def setup(self):
    """This function will be run before every test function in this class"""
    print("Running setup function")
    if os.path.exists(self.base):
      os.system("rm -rf {}".format(self.base))
    os.mkdir(self.base)
    differ.utils.setup_logging('DEBUG')

  def test_extract_cmd(self):
    obj = differ.utils.Path(None)

    # Passing in None should return None
    assert obj.extract_cmd(None) == None

    # Passing in a path which doesn't match a valid
    # extension should also return None
    assert obj.extract_cmd("fail") == None

    # TAR
    assert 'tar xf' in obj.extract_cmd("test.tar")

    # TAR GZIP
    assert 'tar xzf' in obj.extract_cmd("test.tgz")
    assert 'tar xzf' in obj.extract_cmd("test.tar.gz")

    # BZIP2
    assert 'tar xjf' in obj.extract_cmd("test.tar.bz2")

    # LZMA
    assert 'tar xJf' in obj.extract_cmd("test.tar.xz")

    # ZIP
    assert 'unzip' in obj.extract_cmd("test.zip")

  def test_copy(self):
    dest_dir = os.path.join(self.base, "dest_dir")
    os.mkdir(dest_dir)

    # Passing in no dest_dir should fail
    obj = differ.utils.Path(None)
    assert not obj.copy(None)

    # Passing in a destination path which doesn't exist
    # should fail. Also if the base path doesn't exist the
    # copy should fail.
    dir_path = os.path.join(self.base, "does-not-exist")
    obj = differ.utils.Path(dir_path)
    assert not obj.copy(dir_path)
    assert not obj.copy(dest_dir)

    # Test a successful copy
    dir_path = os.path.join(self.base, "test_dir")
    os.mkdir(dir_path)
    obj = differ.utils.Path(dir_path)
    assert obj.copy(dest_dir)

  def test_extract_by_name(self):
    # Test against a path that doesn't exist
    obj = differ.utils.Path(None)
    assert not obj.extract_by_name(None)

    dir_path = os.path.join(self.base, "test_dir")
    os.mkdir(dir_path)
    obj = differ.utils.Path(dir_path)
    assert not obj.extract_by_name(dir_path)

    # Testing against a valid directory should return True
    # since there is nothing to extract
    obj = differ.utils.Path(dir_path)
    assert obj.extract_by_name(self.base)

    # Test against a file that is not extractable
    path = os.path.join(self.base, "name.noexten")
    with open(path, 'w') as fp:
      pass
    obj = differ.utils.Path(path)
    assert not obj.extract_by_name(self.base)

    # Test against an empty file with a valid extension
    path = os.path.join(self.base, "name.tgz")
    with open(path, 'w') as fp:
      pass
    obj = differ.utils.Path(path)
    assert not obj.extract_by_name(self.base)
