from __future__ import print_function
import os, sys
import uuid
import re
import datetime
import textwrap

import utils
from plugins import PLUGINS

import logging
import logging.config
logger = logging.getLogger('differ.utils')

class Paths(object):
  def __init__(self, path):
    self.paths = []
    self.base = path
    if path:
      start = len(path) + 1
      for root, dirs, files in os.walk(path):
        for name in files:
          fname = os.path.join(root, name)
          logger.debug("base {} fname {}".format(self.base, fname))
          fpath = fname[start:]
          self.paths.append(fpath)

  def __repr__(self):
    return self.base

  def has(self, path):
    """Check whether a path exists in this object

    :param path: The path to check
    :return: True if path exists in the paths. False otherwise
    """
    return path in self.paths

  def get(self, path):
    """Get the full path of the path that is matched

    :param path: The path to look for
    :return: The full path that is matched against.
    """
    full = os.path.join(self.base, path)
    PLUGINS.strip_hook(path, full)
    return full

class Path(object):
  def __init__(self, path):
    self.path = path
    self.name = None
    self.valid = False
    if not path:
      logger.error("No path passed in")
      return
    if not os.path.exists(self.path):
      logger.error("Path {} does not exist".format(path))
      return
    self.name = os.path.basename(self.path)
    self.valid = True

  def extract_cmd(self, path):
    """Given a path extract the contents

    :param path: The path to extract
    :return: The command string to run
    """
    cmd = None
    exten_dict = {
      '.tar':     'tar xf',
      '.tar.gz':  'tar xzf',
      '.tgz':     'tar xzf',
      '.tar.bz2': 'tar xjf',
      '.tar.xz':  'tar xJf',
      '.zip':     'unzip'
    }
    if not path:
      return None
    for exten, prg in exten_dict.items():
      if path.endswith(exten):
        cmd = "{} {}".format(prg, path)
        logger.debug("path: {} cmd: {}".format(path, cmd))
        return cmd
    return None

  def extract_by_name(self, change_dir):
    """Extract the path name

    :param change_dir: The directory to change into before extracting
    :return: True on success. False otherwise
    """
    if self.path is None:
      logger.error("Path is None")
      return False

    full_path = self.name
    if change_dir:
      full_path = os.path.join(change_dir, self.name)

    # If the path name doesn't exist then there is nothing to do
    if not os.path.exists(full_path):
      logger.error("{} does not exist".format(full_path))
      return False

    # If this is a directory then nothing to extract
    if os.path.isdir(full_path):
      logger.debug("Nothing to extract for a directory {}".format(
        full_path))
      return True

    cmd = self.extract_cmd(self.name)
    if not cmd:
      logger.error("{}: No extraction command available".format(self.name))
      return False

    if change_dir is not None:
      cmd = "cd {}; {}".format(change_dir, cmd)
    logger.debug("{} cmd {}".format(self.name, cmd))
    ret = os.system(cmd)
    if ret != 0:
      logger.error("Failed to run {}".format(cmd))
      return False
    return True

  def copy(self, dest_dir):
    """Copy the path to the destination directory

    :param dest_dir: The destination directory
    :return: True on success, False otherwise
    """
    if not dest_dir:
      logger.error("No directory passed in")
      return False

    if not os.path.exists(dest_dir):
      logger.error("Dest directory {} does not exist".format(dest_dir))
      return False
    cmd = None
    if os.path.isfile(self.path):
      cmd = "cp {} {}".format(self.path, dest_dir)
    else:
      cmd = "cp -R {} {}".format(self.path, dest_dir)
    logger.debug("path {} name {} cmd {}".format(
      self.path,
      self.name,
      cmd))
    ret = os.system(cmd)
    if ret != 0:
      logger.error("Failed to copy {} to {}".format(
        self.path,
        dest_dir))
      return False
    return True

class Differ(object):
  def __init__(self, path1, path2, base="diff_output"):
    """Initilize the Differ class

    :param path1: The path to compare from
    :param path2: The path to compare against
    :param base: Where to store the output
    """
    self._valid = False
    self.path1 = Path(path1)
    self.path2 = Path(path2)
    if self.path1.valid and self.path2.valid:
      self._valid = True

    base_dir = os.getcwd()
    if base is not None:
      base_dir = base
    if not os.path.exists(base_dir):
      os.mkdir(base_dir)
    self.diff_dir = "diff.{}_{}.{}".format(
      self.path1.name,
      self.path2.name,
      datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    self.diff_dir = os.path.join(base_dir, self.diff_dir)
    self.path1_dir = os.path.join(self.diff_dir, "path1")
    self.path2_dir = os.path.join(self.diff_dir, "path2")
    self.changed_dir = os.path.join(self.diff_dir, "changed")
    self.added_dir = os.path.join(self.diff_dir, "added")
    self.removed_dir = os.path.join(self.diff_dir, "removed_dir")
    self.summary_path = os.path.join(self.diff_dir, "summary")

    self.add_list = []
    self.rm_list = []
    self.changed_list = []

  def __repr__(self):
    if self._valid:
      return "{} {}".format(self.path1.name, self.path2.name)
    else:
      return "NOT VALID: Path1 {} Path2: {}".format(self.path1.path, self.path2.path)

  def extract_path(self, path, path_dir, exclude_dir=None):
    """Extract a given path into the path directory

    :parma path: What to extract
    :param path_dir: Where to extract it
    :param exclude_dir: When moving items into the path_dir what directories
                        to exclude
    :return: True on success, False otherwise
    """
    if not path:
      logger.error("No path provided")
      return False
    if not path_dir:
      logger.error("No path directory provided")
      return False
    path.extract_by_name(self.diff_dir)

    for item in os.listdir(self.diff_dir):
      full_path = "{}/{}".format(self.diff_dir, item)
      if os.path.isdir(full_path):
        if exclude_dir and full_path == exclude_dir:
          continue
        os.system("mv {} {}".format(full_path, path_dir))
    return True

  def setup(self):
    """Setup the directories necessary"""
    # Create the directory that will be used
    os.mkdir(self.diff_dir)

    # Copy over the files
    self.path1.copy(self.diff_dir)
    self.path2.copy(self.diff_dir)

    # Extract paths
    self.extract_path(self.path1, self.path1_dir)
    self.extract_path(self.path2,
      self.path2_dir,
      exclude_dir=self.path1_dir)

  def start(self):
    """Start the differ"""
    self.setup()

    self.path1_obj = Paths(self.path1_dir)
    self.path2_obj = Paths(self.path2_dir)

    for path in self.path1_obj.paths:
      if not self.path2_obj.has(path):
        self.deleted(path)
      else:
        self.compare(path)

    for path in self.path2_obj.paths:
      if not self.path1_obj.has(path):
        self.added(path)

    self.summary()

  def summary(self):
    """Print the summary"""
    results = {
      'dir': self.diff_dir,
      'added': len(self.add_list),
      'removed': len(self.rm_list),
      'changed': len(self.changed_list)
    }
    with open(self.summary_path, "w") as fp:
      fp.write("=" * 40)
      fp.write(textwrap.dedent("""
        Output directory: {dir}

        # of files added {added}
        # of files removed {removed}
        # of files changed {changed}
        """.format(**results)))

    with open(self.summary_path, 'r') as fp:
      print(fp.read())

  def create_path(self, path):
    """Create the path specified

    :param path: The path to create
    """
    os.system("mkdir -p {}".format(os.path.dirname(path)))

  def deleted(self, path):
    """Mark the path that it was deleted in path2

    :param path: The path that was deleted
    """
    print("{} was removed".format(path))
    self.rm_list.append(path)
    item = self.path1_obj.get(path)
    result = os.path.join(self.removed_dir, path)
    self.create_path(result)
    os.system("cp {} {}".format(item, result))

  def added(self, path):
    """Mark the path that it was added in path2

    :param path: The path that was added
    """
    print("{} was added".format(path))
    self.add_list.append(path)
    item = self.path2_obj.get(path)
    result = os.path.join(self.added_dir, path)
    self.create_path(result)
    os.system("cp {} {}".format(item, result))

  def compare(self, path):
    """Compare the path and see if it changed

    :param path: The path to check
    """
    logger.debug("{} is being compared".format(path))
    p1 = self.path1_obj.get(path)
    p2 = self.path2_obj.get(path)
    ret = os.system("diff -Naur {} {} > /dev/null 2>&1".format(p1, p2))
    if not ret:
      return
    result = os.path.join(self.changed_dir, path)
    self.create_path(result)
    os.system("diff -Naur {} {} > {}.diff".format(p1, p2, result))
    os.system("diff -Naur {} {} > {}.diff".format(p1, p2, result))
    self.changed_list.append(path)

def setup_logging(level='INFO'):
  """Setup logging

  :param level: The level to set in the logging configuration
  """
  LOGGER_DEFAULT = {
    'level': level
  }
  LOG_CONFIG = {
    "version": 1,
   "formatters": {
     "default": {
       "format": "%(levelname)-8s %(module)s %(funcName)s - %(message)s",
       "datefmt": "%Y-%m-%d %H:%M:%S"
     },
    },
    "handlers": {
      "console": {
        "class": "logging.StreamHandler",
        "formatter": "default"
      },
    },
    "loggers": {
      "differ.main": LOGGER_DEFAULT,
      "differ.utils": LOGGER_DEFAULT,
      "differ.plugins": LOGGER_DEFAULT,
    },
    "root": {
      "handlers": ["console"],
    },
  }
  logging.config.dictConfig(LOG_CONFIG)
