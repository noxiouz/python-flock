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

from __future__ import with_statement

from functools import partial
import logging
import threading

import zookeeper

ZK_ACL = {"perms": 0x1f,
          "scheme": "world",
          "id": "anyone"}

zookeeper.set_log_stream(open('/dev/null', 'w'))

DEFAULT_ERRNO = -9999

# JFYI
LOG_LEVELS = {"DEBUG": zookeeper.LOG_LEVEL_DEBUG,
              "INFO": zookeeper.LOG_LEVEL_INFO,
              "WARN": zookeeper.LOG_LEVEL_WARN,
              "ERROR": zookeeper.LOG_LEVEL_ERROR}


class Null(object):
    """This class does nothing as logger"""

    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return self

    def __getattribute__(self, name):
        return self

    def __setattribute__(self, name, value):
        pass

    def __delattribute__(self, name):
        pass


def handling_error(zkfunc, logger=Null()):
    def wrapper(*args, **kwargs):
        ret = None
        errno = DEFAULT_ERRNO
        try:
            ret = zkfunc(*args, **kwargs)
        except zookeeper.ConnectionLossException as err:
            logger.error("ConectionLossException: %s", str(err))
            errno = zookeeper.CONNECTIONLOSS
        except zookeeper.NodeExistsException as err:
            logger.debug("Node exists: %s", str(err))
            errno = zookeeper.NODEEXISTS
        except zookeeper.OperationTimeoutException as err:
            logger.error("Operation timeout: %s", str(err))
            errno = zookeeper.OPERATIONTIMEOUT
        except zookeeper.RuntimeInconsistencyException as err:
            logger.error("RuntimeInconsistency: %s", str(err))
            errno = zookeeper.RUNTIMEINCONSISTENCY
        except zookeeper.MarshallingErrorException as err:
            logger.error(str(err))
            errno = zookeeper.MARSHALLINGERROR
        except zookeeper.ZooKeeperException as err:
            logger.error("ZookeperException %s", str(err))
        except Exception as err:
            logger.exception("Unknown exception %s", str(err))
        else:
            errno = 0
        finally:
            return ret, errno
    return wrapper


class ZKeeperClient(object):
    def __init__(self, **config):
        logger_name = config.get('logger_name')
        self.logger = logging.getLogger(logger_name) if logger_name else Null()
        self.zkhandle = None
        self.auth = None
        self.cv = threading.Condition()

        try:
            auth_config = config.get("auth")
            if auth_config is not None:
                auth_scheme = auth_config["scheme"]
                auth_data = auth_config["data"]
                self.auth = (auth_scheme, auth_data)
            zklogfile_path, zklog_level = config.get("ZookeeperLog",
                                                     ("/dev/stderr", "WARN"))
            self.connection_timeout = config['timeout']
            self.zkhosts = ','.join(config['host'])
        except KeyError as err:
            self.logger.exception("Missing configuration option: %s", err)
            raise
        except Exception as err:
            self.logger.exception("Unknown configuration error: %s", err)
            raise

        try:
            _f = open(zklogfile_path, 'a')
        except IOError as err:
            self.logger.error("Unable to open logfile %s %s",
                              zklogfile_path, err)
        else:
            zookeeper.set_log_stream(_f)
            zookeeper.set_debug_level(LOG_LEVELS.get(zklog_level.upper(),
                                                     zookeeper.LOG_LEVEL_WARN))

        self.connect()
        if zookeeper.state(self.zkhandle) == zookeeper.CONNECTED_STATE:
            self.logger.info('Connected to Zookeeper successfully')
        else:
            raise zookeeper.ZooKeeperException('Unable to connect '
                                               'to Zookeeper')

        def on_auth_callback(state, result):
            with self.cv:
                if result == zookeeper.AUTHFAILED:
                    self.logger.error(zookeeper.zerror(zookeeper.AUTHFAILED))
                self.logger.info("on_auth: state %s, result %s",
                                 state, result)
                self.cv.notify()

        if self.auth:
            self.logger.info("Auth using %s", self.auth[0])
            with self.cv:
                res = zookeeper.add_auth(self.zkhandle, self.auth[0],
                                         self.auth[1], on_auth_callback)
                if res != zookeeper.OK:
                    self.logger.error("Invalid status %d",
                                      zookeeper.zerror(res))
                    raise Exception("Invalid status")
                self.cv.wait(self.connection_timeout)

            if zookeeper.state(self.zkhandle) == zookeeper.AUTH_FAILED_STATE:
                raise zookeeper.ZooKeeperException('authentication failed')

    def connect(self):
        def connect_watcher(handle, w_type, state, path):
            """Callback for connect()"""
            with self.cv:
                if state == zookeeper.CONNECTED_STATE:
                    self.logger.debug("connect_watcher: CONNECTED_STATE")
                else:
                    self.logger.debug("connect_watcher: state %d", state)
                self.cv.notify()

        with self.cv:
            try:
                # zookeeper.init accepts timeout in ms
                recv_timeout = int(self.connection_timeout * 1e3)
                self.zkhandle = zookeeper.init(self.zkhosts, connect_watcher,
                                               recv_timeout)
            except Exception as err:
                self.logger.exception("Unable to init zookeeper: %s", err)
                raise err
            else:
                while True:
                    self.logger.debug("Connecting to Zookeeper... Wait %d",
                                      self.connection_timeout)
                    self.cv.wait(self.connection_timeout)
                    if zookeeper.state(self.zkhandle) != zookeeper.CONNECTING_STATE:
                        break

    @property
    def connected(self):
        return self.zkhandle and\
            zookeeper.state(self.zkhandle) == zookeeper.CONNECTED_STATE

    def disconnect(self):
        return zookeeper.close(self.zkhandle)

    def write(self, absname, value, typeofnode=0, acl=ZK_ACL):
        return handling_error(zookeeper.create, self.logger)(self.zkhandle,
                                                             absname,
                                                             value,
                                                             [acl],
                                                             typeofnode)[1]

    def read(self, absname):
        res = zookeeper.get(self.zkhandle, absname)
        return res[0]

    def list(self, absname):
        return zookeeper.get_children(self.zkhandle, absname)

    def modify(self, absname, value):
        return zookeeper.set(self.zkhandle, absname, value)

    def delete(self, absname):
        return zookeeper.delete(self.zkhandle, absname)

    # Async API
    def aget(self, node, callback, rccallback=None):
        # callback is invoked when the watcher triggers
        # rccallback is invoked when the result of attaching
        # becomes available (OK, NONODE and so on)
        assert callable(callback), "callback must be callable"
        if rccallback is not None:
            assert callable(rccallback), "rccallback must be callable"

        def watcher(self, zh, event, state, path):
            self.logger.info("Node state has been changed")
            if event == zookeeper.CHANGED_EVENT:
                self.logger.debug("Node %s has been modified", path)
            elif event == zookeeper.CREATED_EVENT:
                self.logger.debug("Node %s has been created", path)
            elif event == zookeeper.DELETED_EVENT:
                self.logger.warning("Node %s has been deleted", path)

            if state == zookeeper.EXPIRED_SESSION_STATE:
                self.logger.error("Session has expired")
            callback(event, state, path)

        def rc_handler(self, zh, rc, data, stat):
            if zookeeper.OK == rc:
                self.logger.debug("Callback has been attached succesfully")
            elif zookeeper.NONODE == rc:
                self.logger.warning("Watched node doesn't exists")
            if rccallback is not None:
                rccallback(rc)

        res = zookeeper.aget(self.zkhandle, node,
                             partial(watcher, self),
                             partial(rc_handler, self))
        return res == zookeeper.OK
