import os
import logging
logger = logging.getLogger('differ.paths')

from plugins import PLUGINS

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
