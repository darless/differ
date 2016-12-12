import os
import re

class IptablesStrip(object):
  def strip_hook(self, path):
    """Run the stripper on the path provided

    :param path: The path to strip
    """

    print("Stripping for iptables {}".format(path))

    matches = [
      " *pkts *bytes",
      " *[0-9]*  *[0-9]*",
    ]

    # Save the original
    os.system("cp {} {}.orig".format(path, path))
    with open(path, "r") as fp:
      lines = fp.readlines()
    with open(path, "w") as fp:
      for line in lines:
        line = line.rstrip()
        found = False
        for match in matches:
          obj = re.match(match, line)
          if obj:
            if match:
              fp.write(line[len(obj.group(0)) + 1:] + '\n')
              found = True
              break
        if found:
          continue
        fp.write(line + '\n')
