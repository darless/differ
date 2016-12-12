How to use Differ
=================

This page will describe how to use the differ program.

.. toctree::
  :maxdepth: 2

Below is the basic syntax to use:

.. code-block:: bash

    ./differ.py diff <PATH1> <PATH2>

For a more specific example. Let's say there are 2 tar files with
configuration data from yesterday and one from today and you would
like to compare the 2 tar files and the content withint it.

.. code-block:: bash

    ./differ.py diff yesterday.tgz today.tgz

This will create a folder in *diff_output* which will contain a directory
of files that were added between yesterday and today. A directory of files
that were present yesterday but not today. The last directory will contain a
list of files with the extension .diff which changed between yesterday and
today.

Differ functions
++++++++++++++++
.. autoclass:: differ.utils.Differ
  :members:
