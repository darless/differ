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

class Differ(object):
  def __init__(self, path1, path2, base="diff_output"):
    """Initilize the Differ class

    :param path1: The path to compare from
    :param path2: The path to compare against
    :param base: Where to store the output
    """
    self.path1 = path1
    self.path2 = path2
    self._valid = False
    if not path1 or not path2:
      logger.error("Both path1 and path2 must be specified")
      return
    if not os.path.exists(self.path1):
      logger.error("Path1 {} does not exist".format(self.path1))
      return
    if not os.path.exists(self.path2):
      logger.error("Path2 {} does not exist".format(self.path2))
      return
    self._valid = True

    self.path1_name = os.path.basename(self.path1)
    self.path2_name = os.path.basename(self.path2)
    base_dir = os.getcwd()
    if base is not None:
      base_dir = base
    if not os.path.exists(base_dir):
      os.mkdir(base_dir)
    self.diff_dir = "diff.{}_{}.{}".format(
      self.path1_name,
      self.path2_name,
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
      return "{} {}".format(self.path1_name, self.path2_name)
    else:
      return "NOT VALID: Path1 {} Path2: {}".format(self.path1, self.path2)

  def extract_cmd(self, path):
    """Given a path extract the contents

    :param path: The path to extract
    :return: The command string to run
    """
    cmd = None
    if not path:
      logger.error("No path provided")
      return None

    exten_dict = {
      '.tar':     'tar xf',
      '.tar.gz':  'tar xzf',
      '.tgz':     'tar xzf',
      '.tar.bz2': 'tar xjf',
      '.tar.xz':  'tar xJf',
      '.zip':     'unzip'
    }
    for exten, prg in exten_dict.items():
      if path.endswith(exten):
        cmd = "{} {}".format(prg, path)
        logger.debug("path: {} cmd: {}".format(path, cmd))
        return cmd
    return None

  def setup(self):
    """Setup the directories necessary"""
    # Create the directory that will be used
    os.mkdir(self.diff_dir)

    # Copy over the files
    os.system("cp {} {}".format(self.path1, self.diff_dir))
    os.system("cp {} {}".format(self.path2, self.diff_dir))
    os.system("cd {}; {}".format(
      self.diff_dir,
      self.extract_cmd(self.path1_name)))
    for item in os.listdir(self.diff_dir):
      path = "{}/{}".format(self.diff_dir, item)
      if os.path.isdir(path):
        os.system("mv {} {}".format(path, self.path1_dir))
    os.system("cd {}; {}".format(
      self.diff_dir,
      self.extract_cmd(self.path2_name)))
    for item in os.listdir(self.diff_dir):
      path = "{}/{}".format(self.diff_dir, item)
      if os.path.isdir(path) and path != self.path1_dir:
        os.system("mv {} {}".format(path, self.path2_dir))

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
