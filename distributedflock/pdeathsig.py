# -*- coding: utf-8 -*-
#
# Copyright (c) 2012-2014+ Tyurin Anton <noxiouz@yandex.ru>
#
# This file is part of python-flock.
#
# python-flock is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# python-flock is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import sys


# https://docs.python.org/2/library/sys.html#sys.platform
if sys.platform.startswith("linux"):
    import ctypes
    from ctypes.util import find_library

    libc = ctypes.CDLL(find_library('c'))

    PR_SET_PDEATHSIG = 1  # <sys/prctl.h>

    def set_pdeathsig(sig_num):
        libc.prctl(PR_SET_PDEATHSIG, sig_num, 0, 0, 0)

else:
    set_pdeathsig = None


def support_pdeathsig():
    return set_pdeathsig is not None
