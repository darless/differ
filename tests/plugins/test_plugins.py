from context import differ

def test_plugins():
  plugins = differ.plugins.Plugins()
  assert not plugins.get(None)
