#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2012-2014+ Tyurin Anton <noxiouz@yandex.ru>
#
# This file is part of Combaine.
#
# Combaine is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# Combaine is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from setuptools import setup

__author__ = 'Anton Tiurin'
__copyright__ = 'Copyright 2012-2014+'
__credits__ = []
__license__ = 'LGPLv3+'
__version__ = '0.1.4.1'
__maintainer__ = 'Anton Tiurin'
__email__ = 'noxiouz@yandex.ru'
__status__ = 'Production'
__title__ = 'zk-flock'
__url__ = 'https://github.com/noxiouz/python-flock'
__description__ = 'Utility to launch process under distributed Zookeeper lock'
d = 'https://github.com/noxiouz/python-flock/archive/master.zip'


setup(
    name=__title__,
    version=__version__,
    author=__author__,
    author_email=__email__,
    maintainer=__maintainer__,
    maintainer_email=__email__,
    url=__url__,
    description=__description__,
    download_url=d,
    long_description=open('./README.md').read(),
    scripts=[
        'zk-flock'
    ],
    classifiers=['Development Status :: 4 - Beta',
                 'Intended Audience :: Developers',
                 'Programming Language :: Python',
                 'Programming Language :: Python :: 2.6',
                 'Programming Language :: Python :: 2.7',
                 # 'Programming Language :: Python :: 3.2',
                 # 'Programming Language :: Python :: 3.3',
                 # 'Programming Language :: Python :: 3.4',
                 'Programming Language :: Python :: Implementation :: CPython',
                 'Operating System :: OS Independent',
                 'Topic :: Utilities',
                 'License :: OSI Approved :: GNU Lesser General Public '
                 'License v3 or later (LGPLv3+)'],
    platforms=['Independent'],
    license=open('./LICENSE').read(),
    zip_safe=False,
    packages=[
        "distributedflock",
        "distributedflock.ZKeeperAPI"
    ],
    install_requires=open('./requirements.txt').read(),
    tests_require=open('./tests/requirements.txt').read(),
    test_suite='nose.collector'
)
