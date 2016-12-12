Plugins
=======

A plugin for differ allows to change how the differ works. By default the
differ will look at each path and see how it has changed. Depending on what
the user is comparing this could give false postives because if a file
contains counters then it will be quite likely that the files look like
they changed when the important content did not change.

Due to this we have a default plugin for iptables to provide an example.

.. literalinclude:: ../differ/plugins/strip_iptables_counters.py

plugins
+++++++
.. autoclass:: differ.plugins.Plugins
  :members:
