from __future__ import print_function
import os, sys
import uuid
import re
import datetime
import textwrap
import stat

from plugins import PLUGINS
from changes import Changes
from paths import Paths
from path import Path

import logging
import logging.config
logger = logging.getLogger('differ.utils')

class Differ(object):
  def __init__(self, path1, path2, base="diff_output"):
    """Initilize the Differ class

    :param path1: The path to compare from
    :param path2: The path to compare against
    :param base: Where to store the output
    """
    self._valid = False
    self.changes = Changes()
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

    self.path1.copy(self.diff_dir)
    self.extract_path(self.path1, self.path1_dir)

    self.path2.copy(self.diff_dir)
    self.extract_path(self.path2,
      self.path2_dir,
      exclude_dir=self.path1_dir)

    self.changed_dir = os.path.join(self.diff_dir, "changed")
    self.added_dir = os.path.join(self.diff_dir, "added")
    self.removed_dir = os.path.join(self.diff_dir, "removed_dir")
    self.stat_dir = os.path.join(self.diff_dir, "stat_changed")
    self.summary_path = os.path.join(self.diff_dir, "summary")

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
      'added': len(self.changes.get_added()),
      'removed': len(self.changes.get_removed()),
      'changed': len(self.changes.get_changed()),
      'changed_stat': len(self.changes.get_changed_stat()),
    }
    with open(self.summary_path, "w") as fp:
      fp.write("=" * 40)
      fp.write(textwrap.dedent("""
        Output directory: {dir}

        # of files added {added}
        # of files removed {removed}
        # of files changed {changed}
        # of files changed stat {changed_stat}
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
    self.changes.mark_deleted(path)
    item = self.path1_obj.get(path)
    result = os.path.join(self.removed_dir, path)
    self.create_path(result)
    os.system("cp {} {}".format(item, result))

  def added(self, path):
    """Mark the path that it was added in path2

    :param path: The path that was added
    """
    print("{} was added".format(path))
    self.changes.mark_added(path)
    item = self.path2_obj.get(path)
    result = os.path.join(self.added_dir, path)
    self.create_path(result)
    os.system("cp {} {}".format(item, result))

  def compare(self, path):
    """Compare the path and see if it changed

    :param path: The path to check
    """
    self.compare_stat(path)
    logger.debug("{} is being compared".format(path))
    p1 = self.path1_obj.get(path)
    p2 = self.path2_obj.get(path)

    # If either is a FIFO then don't try to do a diff
    for item in [p1, p2]:
      if get_file_type(item) == 'fifo':
        logger.debug("Skipping diff of {} because its a FIFO".format(item))
        return

    ret = os.system("diff -Naur {} {} > /dev/null 2>&1".format(p1, p2))
    if not ret:
      return
    result = os.path.join(self.changed_dir, path)
    self.create_path(result)
    os.system("diff -Naur {} {} > {}.diff".format(p1, p2, result))
    self.changes.mark_changed(path)
    self.changes.add_related(path, "{}.diff".format(result))

  def _compare_mode(self, path):
    """Compare the os.stat st_mode

    :param path: The path to check
    """
    logger.debug("{} is being compared for stat mode".format(path))
    p1 = self.path1_obj.get(path)
    p2 = self.path2_obj.get(path)

    p1_mode = os.stat(p1).st_mode
    p2_mode = os.stat(p2).st_mode
    logger.debug("{} p1 {} p2 {}".format(path, p1_mode, p2_mode))
    if p1_mode == p2_mode:
      return
    result = os.path.join(self.stat_dir, path)
    self.create_path(result)
    output = "{}.mode".format(result)

    self.changes.mark_changed_stat(path)
    self.changes.add_related(path, output)

    with open(output, 'w') as fp:
      p1_perms = oct(p1_mode & 0777)
      p2_perms = oct(p2_mode & 0777)
      if p1_perms != p2_perms:
        fp.write("Permissions {} => {}\n".format(
          p1_perms,
          p2_perms))

      p1_type = get_file_type(p1)
      p2_type = get_file_type(p2)
      if p1_type != p2_type:
        fp.write("File Type {} => {}\n".format(
          p1_type,
          p2_type))

  def _compare_size(self, path):
    """Compare the os.stat st_size

    :param path: The path to check
    """
    logger.debug("{} is being compared for stat size".format(path))
    p1 = self.path1_obj.get(path)
    p2 = self.path2_obj.get(path)

    p1_size = os.stat(p1).st_size
    p2_size = os.stat(p2).st_size
    if p1_size == p2_size:
      return
    result = os.path.join(self.stat_dir, path)
    self.create_path(result)
    output = "{}.size".format(result)

    with open(output, 'w') as fp:
      fp.write("Size {} => {}\n".format(
        p1_size,
        p2_size))

    self.changes.mark_changed_stat(path)
    self.changes.add_related(path, output)

  def compare_stat(self, path):
    """Check whether the path modes changed

    :param path: The path to check
    """
    self._compare_mode(path)
    self._compare_size(path)

def get_file_type(path):
  """Retrieve the file type of the path

  :param path: The path to get the file type for
  :return: The file type as a string or None on error
  """
  f_types = {
    'socket':           stat.S_IFSOCK,
    'regular':          stat.S_IFREG,
    'block':            stat.S_IFBLK,
    'directory':        stat.S_IFDIR,
    'character_device': stat.S_IFCHR,
    'fifo':             stat.S_IFIFO,
  }
  if not path or not os.path.exists(path):
    return None

  obj = os.stat(path).st_mode
  for key,val in f_types.items():
    if obj & val == val:
      return key

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
      "differ.changes": LOGGER_DEFAULT,
      "differ.main": LOGGER_DEFAULT,
      "differ.path": LOGGER_DEFAULT,
      "differ.paths": LOGGER_DEFAULT,
      "differ.plugins": LOGGER_DEFAULT,
      "differ.utils": LOGGER_DEFAULT,
    },
    "root": {
      "handlers": ["console"],
    },
  }
  logging.config.dictConfig(LOG_CONFIG)
