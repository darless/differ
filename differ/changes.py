import logging
logger = logging.getLogger('differ.changes')

class CHANGE_STATE():
  NONE =         0
  ADD =          1 << 0
  REMOVED =      1 << 1
  CHANGED =      1 << 2
  CHANGED_STAT = 1 << 3

class Change(object):
  def __init__(self, path):
    self.path = path
    self.state = CHANGE_STATE.NONE
    self.related = []

  def __repr__(self):
    return ("path={} state={} num_related={}".format(
      self.path,
      self.state,
      len(self.related)))

class Changes(object):
  def __init__(self):
    self.changes = {}

  def get_list_by_state(self, state):
    """Get a list of changes by state

    :param state: The state to look up
    :return: List of changes that match the state
    """
    items = []
    for item in self.changes.values():
      if (item.state & state) == state:
        items.append(item.path)
    print("Result {}".format(items))
    return items

  def get_added(self):
    return self.get_list_by_state(CHANGE_STATE.ADD)

  def get_removed(self):
    return self.get_list_by_state(CHANGE_STATE.REMOVED)

  def get_changed(self):
    return self.get_list_by_state(CHANGE_STATE.CHANGED)

  def get_changed_stat(self):
    return self.get_list_by_state(CHANGE_STATE.CHANGED_STAT)

  def get_or_add(self, path):
    """Get or add a change

    :param path: Path associated to the change
    :return: The change object which was either looked up or added
    """
    obj = self.changes.get(path)
    if obj:
      return obj
    self.changes[path] = Change(path)
    return self.changes[path]

  def set_state(self, path, state):
    """Set a state to the change associated to a path

    :param path: The path associated to the change
    :param state: The state of the change
    """
    obj = self.get_or_add(path)
    obj.state |= state
    logger.debug("path={} state={} updated state={}".format(
      path,
      state,
      obj.state))

  def mark_added(self, path):
    self.set_state(path, CHANGE_STATE.ADD)

  def mark_deleted(self, path):
    self.set_state(path, CHANGE_STATE.REMOVED)

  def mark_changed(self, path):
    self.set_state(path, CHANGE_STATE.CHANGED)

  def mark_changed_stat(self, path):
    self.set_state(path, CHANGE_STATE.CHANGED_STAT)

  def add_related(self, path, related_path):
    """Add a related path to the change

    :param path: The path associated to the change
    :param related_path: The related path to the change
    """
    obj = self.get_or_add(path)
    obj.related.append(related_path)
