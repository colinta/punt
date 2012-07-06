====
punt
====

I saw kicker_ the other day and thought: I could write that in a minute!

So I did.

------------
INSTALLATION
------------

::

    $ pip install punt

-----
USAGE
-----

::

    $ punt 'du -sh'  # list file sizes, update the list when a file changes
    $ punt --help
    $ punt --version
    $ punt -w tests 'py.test'  # run py.test when any file in tests/ changes
    $ punt --watch ~ --local 'ls -la'  # options
    $ punt -w ~ -l 'ls -la'            # same, but short names


-------
LICENSE
-------

:Author: Colin Thomas-Arnold
:Copyright: 2012 Colin Thomas-Arnold <http://colinta.com/>

Copyright (c) 2012, Colin Thomas-Arnold
All rights reserved.

See LICENSE_ for more details (it's a simplified BSD license).

.. _kicker:       https://github.com/alloy/kicker
.. _LICENSE:      https://github.com/colinta/punt/blob/master/LICENSE
