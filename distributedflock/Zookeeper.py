# -*- coding: utf-8 -*-
#
# Copyright (c) 2012 Tyurin Anton noxiouz@yandex-team.ru
#
# This file is part of Distributed-flock.
#
# Distributed-flock is free software; you can redistribute it and/or modify
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


from ZKeeperAPI import zkapi as ZK
from socket import gethostname
import uuid

import logging

class ZKLockServer():
    """Zookeeper based lockserver. """
    def __init__(self, **config):
        try:
            self.log = logging.getLogger(config.get('logger_name','combaine'))
            self.zkclient = ZK.ZKeeperClient(**config)
            self.id = config['app_id']
            res = self.zkclient.write('/'+self.id,"Rootnode")
            if (res != ZK.zookeeper.NODEEXISTS) and (res < 0):
                if res == ZK.DEFAULT_ERRNO:
                    self.log.error("Unexpectable error")
                    raise Exception("Unexpectable error. See Zookeeper logs for details")
                else:
                    msg = "Zookeeper error number %d: %s" % (res, ZK.zookeeper.zerror(res))
                    self.log.error(msg)
                    raise Exception(msg)
            self.lock = config['name']
            self.lockpath = '/'+self.id+'/'+self.lock
            self.locked = False
            self.lock_content = gethostname() + str(uuid.uuid4())
        except Exception as err:
            self.log.error('Failed to init ZKLockServer: '+str(err))
            raise
        else:
            self.log.debug('ZK create')

    def getlock(self):
        if self.zkclient.write(self.lockpath, self.lock_content,1) == 0:
            self.log.info('Lock: success')
            self.locked = True
            return True
        else:
            self.log.info('Lock: fail')
            return False

    def setLockName(self, name):
        self.lock = name
        self.lockpath = '/'+self.id+'/'+self.lock

    def releaselock(self):
        if self.zkclient.delete(self.lockpath) ==0:
            self.log.info('Unlock: success')
            self.locked = False
            return True
        else:
            self.log.debug('Unlock: fail')
            return False

    def checkLock(self):
        try:
            isMyLock = self.zkclient.read(self.lockpath)
            if isMyLock[0] != self.lock_content:
                return False
            else:
                return True
        except Exception as err:
            self.log.debug("lock isn't mine")
            return False
        else:
            return True#isMyLock

    def set_async_checkLock(self, callback):
        if not self.locked:
            return False
        if not callable(callback):
            return False
        def callback_wrapper():
            callback()
            if self.checkLock:
                self.zkclient.aget(self.lockpath, callback_wrapper)

        if self.zkclient.aget(self.lockpath, callback_wrapper) == 0:
            return True

    def destroy(self):
        if self.zkclient.disconnect() == 0:
            self.log.info('Successfully disconnect from LS')
            return True
        else:
            self.log.debug('Cannot disconnect from LS')
            return False
