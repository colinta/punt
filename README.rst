====
punt
====

I saw kicker_ the other day and thought: I could write that in a minute!

So I did.

------------
INSTALLATION
------------

::

    $ uv tool install punt

-----
USAGE
-----

::

    $ punt 'du -sh'                   # list file sizes, update the list when a file in cwd changes
    $ punt -w tests/ -w lib/ py.test  # run py.test when any file in tests/ or lib/ changes
    $ punt -w info.yml py.test        # run py.test when info.yml changes
    $ punt -l make                    # only monitor "local" files (don't observe subdirectories)
    $ punt --info -w src make         # show info like command status
    $ punt --help
    $ punt --version

----
INFO
----

``punt`` is a tiny tool, just one ``__init__.py`` file.  It uses watchdog_ to
monitor file changes, and docopt_ to parse command line arguments.

-------
LICENSE
-------

:Author: Colin Thomas-Arnold
:Copyright: 2012 Colin Thomas-Arnold <http://colinta.com/>

Copyright (c) 2012, Colin Thomas-Arnold
All rights reserved.

See LICENSE_ for more details (it's a simplified BSD license).

.. _kicker:    https://github.com/alloy/kicker
.. _watchdog:  http://github.com/gorakhargosh/watchdog
.. _docopt:    http://github.com/docopt/docopt
.. _LICENSE:   https://github.com/colinta/punt/blob/master/LICENSE
