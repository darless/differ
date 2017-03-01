import os
import sys
import pytest

from context import differ

class TestPath():
  base = "/tmp/differ/"

  @pytest.fixture(scope='function', autouse=True)
  def setup(self):
    """This function will be run before every test function in this class"""
    print("Running setup function")
    if os.path.exists(self.base):
      os.system("rm -rf {}".format(self.base))
    os.mkdir(self.base)

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
