#!/usr/bin/python

"""Diff compresed directories

This is primarily created to see the difference between 2 compressed
directories.
"""

from __future__ import print_function
import os, sys, argparse, textwrap
import uuid
import re
import utils
utils.setup_logging()

import logging
logger = logging.getLogger("differ.main")

__author__ = "Nodar Nutsubidze"

if __name__ == "__main__":
  def add_sp(sub_p, action, func=None, help=None):
    """Add an action to the main parser

    :param sub_p: The sub parser
    :param action: The action name
    :param func: The function to perform for this action
    :param help: The help to show for this action
    :rtype: The parser that is generated
    """
    p = sub_p.add_parser(action, help=help)
    if func:
      p.set_defaults(func=func)
    p.add_argument('-v', '--verbose', action='store_true',
             help='Show verbose logging')
    return p

  def ap_diff(args):
    """Run the differ

    :param args: The command line arguments
    """
    for path in [args.path1, args.path2]:
      if not os.path.exists(path):
        print("Path {} does not exist".format(path))
        sys.exit(1)
    differ = utils.Differ(args.path1, args.path2)
    differ.start()

  parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description = 'Differ of compressed tar files',
    epilog = textwrap.dedent('''\
      Examples:
      -----------------------
      {prg} diff before.tar.gz after.tar.gz
    '''.format(prg=sys.argv[0])))
  sub_p = parser.add_subparsers(title='Actions',
                                help='%(prog)s <action> -h for more info')
  p = add_sp(sub_p, "diff", func=ap_diff,
    help="Get the difference between 2 snapshots")
  p.add_argument("path1")
  p.add_argument("path2")

  args = parser.parse_args()
  if args.verbose:
    utils.setup_logging('DEBUG')

  args.func(args)
