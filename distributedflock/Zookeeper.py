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


import logging
import socket
import uuid

from ZKeeperAPI import zkapi


class ZKLockServer(object):
    def __init__(self, **config):
        try:
            self.log = logging.getLogger(config.get('logger_name', 'combaine'))
            self.zkclient = zkapi.ZKeeperClient(**config)
            self.id = config['app_id']
            res = self.zkclient.write('/%s' % self.id, "Rootnode")
            if (res != zkapi.zookeeper.NODEEXISTS) and (res < 0):
                if res == zkapi.DEFAULT_ERRNO:
                    self.log.error("Unexpectable error")
                    raise Exception("Unexpectable error. See Zookeeper logs")
                else:
                    msg = "Zookeeper error: %s" % zkapi.zookeeper.zerror(res)
                    self.log.error(msg)
                    raise Exception(msg)

            self.lock = config['name']
            self.lockpath = '/%s/%s' % (self.id, self.lock)
            self.locked = False
            self.lock_content = socket.gethostname() + str(uuid.uuid4())
        except Exception as err:
            self.log.error('Failed to init ZKLockServer: %s', err)
            raise
        else:
            self.log.debug('ZKeeperClient has been created')

    def getlock(self):
        if self.locked:
            return True
        if self.zkclient.write(self.lockpath, self.lock_content, 1) == 0:
            self.log.info('Lock: success')
            self.locked = True
            return True
        else:
            self.log.info('Lock: fail')
            return False

    def set_lock_name(self, name):
        self.lock = name
        self.lockpath = '/%s/%s' % (self.id, self.lock)

    def releaselock(self):
        try:
            self.zkclient.delete(self.lockpath)
            self.log.info('Unlocked successfully')
            self.locked = False
            return True
        except Exception as err:
            self.log.error('Unlocking failed %s', err)
        return False

    def check_lock(self):
        try:
            content = self.zkclient.read(self.lockpath)
            return content == self.lock_content
        except Exception as err:
            self.log.error("Unable to check lock %s", repr(err))
        return False

    def set_async_check_lock(self, callback):
        assert callable(callback), "callback must be callable"
        if not self.locked:
            return False

        def callback_wrapper(*args):
            callback()
            if self.check_lock():
                self.zkclient.aget(self.lockpath, callback_wrapper)

        return self.zkclient.aget(self.lockpath, callback_wrapper)

    def set_node_deleting_watcher(self, path, callback):
        assert callable(callback), "callback must be callable"

        def callback_wrapper(event, state, path):
            if event == 2:  # zookeeper.DELETE_EVENT
                callback()

        def callback_rc_wrapper(rc):
            if rc == -101:  # zookeeper.NONODE
                callback()

        return self.zkclient.aget(path, callback_wrapper, callback_rc_wrapper)

    def destroy(self):
        try:
            self.zkclient.disconnect()
            self.log.info('Disconnected successfully')
            return True
        except Exception as err:
            self.log.error('Disconnection error %s', err)
        return False
