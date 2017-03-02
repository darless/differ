import os
import sys
import pytest

from context import differ

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
    assert not obj.changes.get_added()
    assert not obj.changes.get_removed()
    assert not obj.changes.get_removed()

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
      assert len(obj.changes.get_added()) == 1
      assert len(obj.changes.get_removed()) == 1
      assert len(obj.changes.get_changed()) == 2
      assert os.path.exists(obj.summary_path)
      with open(obj.summary_path) as fp:
        summary = fp.read()
        assert "added 1" in summary
        assert "removed 1" in summary
        assert "changed 2" in summary

  def test_differ_stat_changes(self):
    """Test differ where there are mode changes"""
    obj = differ.utils.Differ(
      "tests/files/stat_changes/before",
      "tests/files/stat_changes/after",
      base=self.base)
    assert obj._valid
    obj.start()
    assert len(obj.changes.get_added()) == 0
    assert len(obj.changes.get_removed()) == 0
    assert len(obj.changes.get_changed()) == 1
    assert len(obj.changes.get_changed_stat()) == 2
    assert os.path.exists(obj.summary_path)
    with open(obj.summary_path) as fp:
      summary = fp.read()
      assert "added 0" in summary
      assert "removed 0" in summary
      assert "changed 1" in summary
      assert "changed stat 2" in summary

  def test_differ_fifo(self):
    """Test differ where there are fifo files"""

    # Create 2 directories
    before = os.path.join(self.base, "before_tmp")
    after = os.path.join(self.base, "after_tmp")
    os.makedirs(before)
    os.makedirs(after)

    os.system("mkfifo {}/test_file".format(before))
    os.system("touch {}/test_file".format(after))

    obj = differ.utils.Differ(
      before,
      after,
      base=self.base)
    assert obj._valid
    obj.start()
    assert len(obj.changes.get_added()) == 0
    assert len(obj.changes.get_removed()) == 0
    assert len(obj.changes.get_changed()) == 0
    assert len(obj.changes.get_changed_stat()) == 1
    assert os.path.exists(obj.summary_path)
    with open(obj.summary_path) as fp:
      summary = fp.read()
      assert "added 0" in summary
      assert "removed 0" in summary
      assert "changed 0" in summary
      assert "changed stat 1" in summary

    changed_path = obj.changes.get_changed_stat()[0]
    change = obj.changes.changes.get(changed_path)
    assert change.related
    with open(change.related[0], 'r') as fp:
      mode = fp.read()
      assert 'fifo => regular' in mode

  def test_plugin_iptables_strip(self):
    """Test the plugin iptables stripper"""
    obj = differ.utils.Differ(
      "tests/files/plugins/iptables/before.tgz",
      "tests/files/plugins/iptables/after.tgz",
      base=self.base)
    assert obj._valid
    obj.start()
    assert len(obj.changes.get_added()) == 0
    assert len(obj.changes.get_removed()) == 0
    assert len(obj.changes.get_changed()) == 1
    assert os.path.exists(obj.diff_dir)

    changed_path = os.path.join(
      obj.changed_dir,
      "my_iptables_mangle.diff")
    with open(changed_path, "r") as fp:
      changed_content = fp.read()
    assert "-DIFFER-TEST-3" in changed_content
    assert "+DIFFER-TEST-4" in changed_content
