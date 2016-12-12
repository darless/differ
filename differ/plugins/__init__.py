import os
import sys
import inspect
import imp
import pkgutil
import re

import logging
logger = logging.getLogger("differ.plugins")

class Plugins(object):
  def __init__(self):
    self.plugins = {}
    self.paths = {}

  def get_plugins(self):
    """Retrieve all the available plugins in the plugins directory"""
    dir_path = os.path.dirname(inspect.getfile(inspect.currentframe()))
    for root, dirs, files in os.walk(dir_path):
      for fname in files:
        path = os.path.join(root, fname)
        if fname == "__init__.py":
          continue
        exten = os.path.splitext(fname)[1]
        if exten == ".py":
          module = imp.load_source('plugin', path)
          for item in dir(module):
            obj = getattr(module, item)
            if inspect.isclass(obj):
              self.add(obj())

  def add(self, plugin):
    """Add the plugin to the dictionary of plugins"""
    name = plugin.__class__.__name__
    self.plugins[name] = plugin

  def add_parsers(self, parsers):
    """Update the parser dictionary

    :param parsers: A passed in dictionary of parsers
    :ptype parsers: dict
    """
    self.paths.update(parsers)

  def get(self, name):
    """Retrieve a plugin by its name

    :return: A plugin object or None if not found
    """
    item = self.plugins.get(name)
    if not item:
      print("No such plugin by name {}".format(name))
      return None
    return item

  def strip_hook(self, path, full_path):
    """Hook to strip the path passed in

    This will perform stripping on the file only if the path
    matches any of the plugins and if the plugin has the strip_hook
    functionality.

    :param path: The path to check
    :param full_path: The full path of the file to strip
    """
    for path_regex, plugin in self.paths.items():
      if re.match(path_regex, path):
        # Run the strip_hook if it exists
        if getattr(plugin, "strip_hook"):
          plugin.strip_hook(full_path)

PLUGINS = Plugins()
PLUGINS.get_plugins()

# Define default paths
PLUGINS.add_parsers({
  '.*iptables.*': PLUGINS.get("IptablesStrip"),
})
