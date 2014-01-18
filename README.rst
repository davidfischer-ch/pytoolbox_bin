.. _github: https://github.com
.. _pytoolbox: https://github.com/davidfischer-ch/pytoolbox
.. _youtube: https://youtube.com

=============
Pytoolbox Bin
=============

.. image:: https://secure.travis-ci.org/davidfischer-ch/pytoolbox_bin.png
    :target: http://travis-ci.org/davidfischer-ch/pytoolbox_bin

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
    sudo apt-get install git-core python-dev python-pip python-pyexiv2

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

----

2013 - David Fischer
