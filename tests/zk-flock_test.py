#! /usr/bin/env python

import os
import shlex
import subprocess
import time
import unittest


def check_pid(pid):
    if pid < 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True


class firsttest(unittest.TestCase):

    def setUp(self):
        args = shlex.split("python zk-flock ffffff \"sleep 3600\" -d")
        self.p = subprocess.Popen(args)
        time.sleep(2)
        x = subprocess.Popen("ps aux | grep \"zk-flock\" | grep sleep"
                             "| grep -v grep | awk '{print $2}'",
                             shell=True, stdout=subprocess.PIPE)
        output = x.stdout.read()
        self.PID = int(output)
        x = subprocess.Popen("ps aux | grep sleep | grep -v grep"
                             "| grep -v python | awk '{print $2}'",
                             shell=True, stdout=subprocess.PIPE)
        self.CHILD_PID = int(x.stdout.read())

    def test_kill_him(self):
        os.kill(self.PID, 15)
        time.sleep(2)
        self.assertFalse(check_pid(self.PID))

    def test_kill_child(self):
        os.kill(self.CHILD_PID, 15)
        time.sleep(5)
        self.assertFalse(check_pid(self.PID))


class exitcodetest(unittest.TestCase):
    def test_exit_code(self):
        args = shlex.split("python zk-flock ffffff \"bash -c 'exit 123'\"")
        p = subprocess.Popen(args)
        exit_code = p.wait()
        self.assertEquals(exit_code, 123)


if __name__ == "__main__":
    unittest.main()
