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

import zookeeper
import threading

from functools import partial

ZK_ACL = {"perms":0x1f, "scheme":"world", "id":"anyone"}

ZK_NODE_EXISTS=-2;


zookeeper.set_log_stream( open('/dev/null','w'))

def handling_error(zkfunc):
    def wrapper(*args, **kwargs):
        ret = None
        errno = -1
        try:
            ret = zkfunc(*args, **kwargs)
        except zookeeper.ConnectionLossException, err:
            pass
        except zookeeper.NodeExistsException, err:
            #print str(err)
            errno = ZK_NODE_EXISTS
        #except zookeeper.NoNodeExistsException, err:
        #    print 'dsdsds' + str(err)
        except zookeeper.MarshallingErrorException, err:
            #print err
            pass
        #=====================================
        except  zookeeper.ZooKeeperException, errmsg:
            #print 'Unknown zookeeper error: '+ str(errmsg)
            raise
        except Exception, errmsg:
            #print 'Unknown: '+str(errmsg)
            raise
        else:
            errno = 0
        finally:
            return ret, errno
    return wrapper

class ZKeeperClient():
    def __init__(self, **config):
        try:
            self.connection_timeout =5#config['timeout']
            self.zkhosts = config['host']
        except Exception, errmsg:
            #print "Cannot init: "+str(errmsg)
            pass
        self.connected = False
        self.zkhandle = None
        self.connect()

    def connect(self):
        self.cv = threading.Condition()
        self.connected = False
        def connect_watcher(handle, type, state, path ):
            """ Callback for connect()"""
            self.cv.acquire()
            self.connected = True
            self.cv.notify()
            self.cv.release()

        for zkserver in self.zkhosts:
            self.cv.acquire()
            try:
                self.zkhandle = handling_error(zookeeper.init)(zkserver, connect_watcher)[0]
            except Exception, err:
                pass
            else:
                self.cv.wait(self.connection_timeout)
            finally:
                self.cv.release()
            if self.connected:
                break
        return self.connected

    def disconnect(self):
        return handling_error(zookeeper.close)(self.zkhandle)[1]

    def write(self, absname, value, typeofnode=0, acl=ZK_ACL):
        return handling_error(zookeeper.create)(self.zkhandle,\
                                                        absname,\
                                                        value,\
                                                        [acl],\
                                                        typeofnode)[1];

    def read(self, absname):
        _res = handling_error(zookeeper.get)(self.zkhandle, absname)
        res = (_res[0][0], _res[1] )
        return res

    def list(self, absname):
        res = handling_error(zookeeper.get_children)(self.zkhandle, absname)
        return res

    def modify(self, absname, value):
        return handling_error(zookeeper.set)(self.zkhandle, absname, value)[1]

    def delete(self, absname):
        return handling_error(zookeeper.delete)(self.zkhandle, absname)[1]
#========================
    def aget(self, node, callback):
        if not callable(callback):
            return None
        def watcher(self, zh, event, state, path):
            callback()
        return zookeeper.aget(self.zkhandle, node, partial(watcher, self), self.handler)

    def handler(self, zh, rc, data, stat):
        if zookeeper.OK == rc:
            print "WORK"
        else:
           if zookeeper.NONODE == rc:
               print "No node"
