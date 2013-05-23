# -*- coding: utf-8 -*-
#
# Copyright (c) 2012 Tyurin Anton noxiouz@yandex.ru
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

import threading
import time
import logging
from functools import partial

import zookeeper

ZK_ACL = {"perms":0x1f, "scheme":"world", "id":"anyone"}

zookeeper.set_log_stream(open('/dev/null','w'))

DEFAULT_ERRNO = -9999

# JFYI
LOG_LEVELS = {  "DEBUG" : zookeeper.LOG_LEVEL_DEBUG,
                "INFO"  : zookeeper.LOG_LEVEL_INFO,
                "WARN"  : zookeeper.LOG_LEVEL_WARN,
                "ERROR" : zookeeper.LOG_LEVEL_ERROR,
}


class Null(object):
    """This class does nothing as logger"""

    def __init__(self, *args, **kwargs): pass
    def __call__(self, *args, **kwargs): return self
    def __getattribute__(self, name): return self
    def __setattribute__(self, name, value): pass
    def __delattribute__(self, name): pass

def handling_error(zkfunc, logger=Null()):
    def wrapper(*args, **kwargs):
        ret = None
        errno = DEFAULT_ERRNO
        try:
            ret = zkfunc(*args, **kwargs)
        except zookeeper.ConnectionLossException as err:
            logger.error("ConectionLossException: %s" % str(err))
            errno = zookeeper.CONNECTIONLOSS
        except zookeeper.NodeExistsException as err:
            logger.debug("Node exists: %s" % str(err))
            errno = zookeeper.NODEEXISTS
        except zookeeper.OperationTimeoutException as err:
            logger.error("Operation timeout: %s" % str(err))
            errno = zookeeper.OPERATIONTIMEOUT
        except zookeeper.zookeeper.RuntimeInconsistencyException as err:
            logger.error("RuntimeInconsistency: %s" % str(err))
            errno = zookeeper.RUNTIMEINCONSISTENCY
        except zookeeper.MarshallingErrorException as err:
            logger.error(str(err))
            errno = zookeeper.MARSHALLINGERROR
        except zookeeper.ZooKeeperException as err:
            logger.error("ZookeperException %s" % str(err))
        except Exception as err:
            logger.exception("Unknown exception %s" % str(err))
        else:
            errno = 0
        finally:
            return ret, errno
    return wrapper

class ZKeeperClient():
    def __init__(self, **config):
        if config.has_key('logger_name'):
            self.logger = logging.getLogger(config['logger_name'])
        else:
            self.logger = Null()

        # zookeeper client log
        try:
            zklogfile_path, zklog_level = config.get("ZookeeperLog", ("/dev/stderr", "WARN"))
            _f = open(zklogfile_path,'a')
        except Exception as err:
            self.logger.error("In init ZKeeperClient: %s" % str(err))
        else:
            zookeeper.set_log_stream(_f)
            zookeeper.set_debug_level(LOG_LEVELS.get(zklog_level, zookeeper.LOG_LEVEL_WARN))

        try:
            self.connection_timeout = config['timeout']
            self.zkhosts = config['host']
        except KeyError as err:
            self.logger.exception("Cann't init ZKeeperClient: %s" % str(err))

        self.connected = False
        self.zkhandle = None
        if self.connect():
            self.logger.info('Connected to Zookeeper succesfully')

    def connect(self):
        self.cv = threading.Condition()
        self.connected = False
        def connect_watcher(handle, type, state, path ):
            """ Callback for connect()"""
            self.cv.acquire()
            self.connected = True
            self.cv.notify()
            self.cv.release()

        self.cv.acquire()
        zkserver = ','.join(self.zkhosts)
        try:
            self.zkhandle = handling_error(zookeeper.init, self.logger)(zkserver, connect_watcher)[0]
        except Exception as err:
            self.logger.exception("In ZKeeperClient.connect(): %s" % str(err))
        else:
            self.cv.wait(self.connection_timeout)
        finally:
            self.cv.release()
        return self.connected

    def disconnect(self):
        return handling_error(zookeeper.close, self.logger)(self.zkhandle)[1]

    def write(self, absname, value, typeofnode=0, acl=ZK_ACL):
        return handling_error(zookeeper.create, self.logger)(self.zkhandle,\
                                                        absname,\
                                                        value,\
                                                        [acl],\
                                                        typeofnode)[1];

    def read(self, absname):
        _res = handling_error(zookeeper.get, self.logger)(self.zkhandle, absname)
        res = (_res[0][0], _res[1])
        return res

    def list(self, absname):
        res = handling_error(zookeeper.get_children, self.logger)(self.zkhandle, absname)
        return res

    def modify(self, absname, value):
        return handling_error(zookeeper.set, self.logger)(self.zkhandle, absname, value)[1]

    def delete(self, absname):
        return handling_error(zookeeper.delete, self.logger)(self.zkhandle, absname)[1]

    # Async API
    def aget(self, node, callback):
        if not callable(callback):
            return None
        def watcher(self, zh, event, state, path):
            self.logger.info("Node state has been changed")
            #print "event", event
            if event == zookeeper.CHANGED_EVENT:
                self.logger.debug("Node %s has been modified" % str(path))
            elif event == zookeeper.CREATED_EVENT:
                self.logger.debug("Node %s has been created" % str(path))
            elif event == zookeeper.DELETED_EVENT:
                self.logger.warning("Node %s has been deleted" % str(path))

            if state == zookeeper.EXPIRED_SESSION_STATE:
                self.logger.error("Session expired")
            callback()
        return zookeeper.aget(self.zkhandle, node, partial(watcher, self), self.handler)

    def handler(self, zh, rc, data, stat):
        if zookeeper.OK == rc:
            self.logger.debug("Callback was  attached succesfully")
        else:
           if zookeeper.NONODE == rc:
                self.logger.error("Watched node doesn't exists")
