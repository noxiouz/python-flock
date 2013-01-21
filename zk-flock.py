#! /usr/bin/env python

from distributedflock import Zookeeper as ZK

import subprocess
import sys
import os
import time
import atexit

from signal import SIGTERM

cfg = {
		"type"      :   "Zookeeper",
		"host"      :   ["cocaine-log01g.kit.yandex.net:2181","cocaine-log02f.kit.yandex.net:2181","cocaine-mongo03f.kit.yandex.net:2181"],
		"timeout"   :   5,
        "app_id"    :   "CMN",
        "name"      :   "TEST_LOCK"
}

#========================================================================================

class Daemon(object):

    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile

    def daemonize(self):
        """Double-fork magic"""
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError, err:
            sys.stderr.write("First fork failed: %d (%s)\n" % (err.errno, err.strerror))
            sys.exit(1)
        # decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # Second fork
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError, err:
            sys.stderr.write("Second fork failed: %d (%s)\n" % (err.errno, err.strerror))
            sys.exit(1)
            
        sys.stdout.flush()
        sys.stderr.flush()
        si = file(self.stdin, 'r')
        so = file(self.stdout, 'w')
        se = file(self.stderr, 'w')
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        #write PID file
        atexit.register(self.delpid)
        pid = str(os.getpid())
        file(self.pidfile,'w').write("%s\n" % pid)

    def delpid(self):
        try:
            os.remove(self.pidfile)
        except Exception, err:
            pass

    def start(self, *args):
        """
        Start  the daemon
        """

        try:
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if pid:
            msg = "pidfile %s has been already existed. Exit.\n"
            sys.stderr.write(msg % self.pidfile)
            sys.exit(1)

        self.daemonize()
        self.run(*args)

    def stop(self):
        """
        Stop daemon.
        """
        try:
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if not pid:
            msg = "pidfile %s doesnot exist. Exit.\n"
            sys.stderr.write(msg % self.pidfile)
            sys.exit(1)

        #Kill
        try:
            while True:
                os.kill(pid, SIGTERM)
                time.sleep(0.5)
        except OSError, err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print str(err)
                sys.exit(1)


    def restart(self, *args):
        self.stop()
        self.start(*args)

    def run(self, *args):
        pass

#===========================================================

def start_child(cmd):
    import shlex
    args = shlex.split(cmd)
    try:
        p = subprocess.Popen(args, close_fds=True)
    except OSError as err:
        print "OSError %s" % str(err)
    except ValueError as err:
        print "ValueError %s" % str(err)
    else:
        return p

def kill_child(prcs):
    prcs.kill()

def main(cmd_arg):
    z = ZK.ZKLockServer(**cfg)
    if not z.getlock():
        print "Error"
        return
    p = start_child(cmd_arg)
    while True:
        if p.poll() is not None:
            z.releaselock()
            z.destroy()
            return 
        if not z.checkLock():
            try:
                kill_child(p)
                if p.poll() is not None:
                    p.terminate()
                z.destroy()
            except Exception as err:
                print str(err)

#===============================================

if __name__ == "__main__":
    daemon = Daemon("TEST_PID")
    daemon.run = main
    if len(sys.argv) == 2:
        daemon.start(sys.argv[1])
    else:
        sys.exit(0)
