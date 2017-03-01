import os
import logging
logger = logging.getLogger('differ.path')

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
      cmd = "cp -a {} {}".format(self.path, dest_dir)
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
