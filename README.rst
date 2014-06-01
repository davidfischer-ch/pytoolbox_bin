.. _github: https://github.com
.. _pygal: http://pygal.org/
.. _pytoolbox: https://github.com/davidfischer-ch/pytoolbox
.. _tespeed: https://github.com/davidfischer-ch/tespeed
.. _youtube: https://youtube.com

=============
Pytoolbox Bin
=============

.. image:: https://badge.fury.io/py/pytoolbox_bin.png
    :target: http://badge.fury.io/py/pytoolbox_bin

.. image:: https://pypip.in/d/pytoolbox_bin/badge.png
    :target: https://crate.io/packages/pytoolbox_bin/

.. image:: https://secure.travis-ci.org/davidfischer-ch/pytoolbox_bin.png
    :target: http://travis-ci.org/davidfischer-ch/pytoolbox_bin

.. image:: https://landscape.io/github/davidfischer-ch/pytoolbox_bin/master/landscape.png
   :target: https://landscape.io/github/davidfischer-ch/pytoolbox_bin/master

Afraid of red status ? Please click on the link, sometimes this is not my fault ;-)

Personal utility scripts based on pytoolbox_ and other goodies.

------------------------------------
What the release number stands for ?
------------------------------------

I do my best to follow this interesting recommendation : `Semantic Versioning 2.0.0 <http://semver.org/>`_

--------------------------------
How to install it (Python 2.7) ?
--------------------------------

Install some packages that are not handled by pip::

    sudo apt-get -y build-dep python-imaging
    sudo apt-get install git-core libffi-dev python-dev python-pip python-pyexiv2

Make sure that pip is up-to-date (PIPception)::

    sudo pip-2.7 install --upgrade pip

Then, you only need to run ``setup.py``::

    python2 setup.py test
    sudo python2 setup.py install

--------------------------------
How to install it (Python 3.3) ?
--------------------------------

Install some packages that are not handled by pip::

    sudo apt-get -y build-dep python3-imaging
    sudo apt-get install git-core python3-dev python3-pip python-pyexiv2

Make sure that pip is up-to-date (PIPception)::

    sudo pip-3.3 install --upgrade pip

Then, you only need to run ``setup.py``::

    python3 setup.py test
    sudo python3 setup.py install

-----------------------
How to check coverage ?
-----------------------

::

    python setup.py test
    xdg-open tests/cover/index.html

---------------
How to use it ?
---------------

Here is list of the functionalities available through the command line (see all files called ``bin.py``).

:github-clone-starred: Clone the repositories your starred on GitHub_.
:youtube-download-likes: Download the video you liked on YouTube_, can also convert them to AAC (songs).
:socket-fec-generator: Create SMPTE 2022-1 FEC streams from a sniffed source stream. Socket-based implementation.
:twisted-fec-generator: Create SMPTE 2022-1 FEC streams from a sniffed source stream. Twisted-based implementation.
:isp-benchmark: Benchmark your Internet connection and graph the speed over the time, based on tespeed_ and pygal_.

----

2014 - David Fischer
