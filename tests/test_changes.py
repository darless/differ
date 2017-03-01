import os
import sys
import pytest

from context import differ

def test_change():
  change = differ.changes.Change('path')
  print(change)
  assert change.state == differ.changes.CHANGE_STATE.NONE
