zk-flock  [![Build Status](https://travis-ci.org/noxiouz/python-flock.svg?branch=master)](https://travis-ci.org/noxiouz/python-flock)
========

You can use `zk-flock` to run programs in a cluster under a distributed lock to limit overall amount of instances.

Configuration
=============

You have to write the configuration file **/etc/distributed-flock.json** with the following content:
```js
{
    "host": ["hostname1:2181","hostname2:2181","hostname3:2181"],
    "timeout": 5,
    "app_id": "my_application_namespace",
    "sleep": "ON",    //ON or OFF - Default OFF
    "maxla": 30,      // If >=0 -> max loadaverage for work. Default -1
    "logger": {
            "path": "/tmp/zkflock.log",
            "level": "INFO",
            "zklevel": "ERROR"
    },
    "auth": {
        "scheme": "digest",
        "data": "noxiouz:password"
    }
}
```
 * **host** - list of Zookeeper nodes
 * **timeout** - timeout for zookeper connection (sec)
 * **app_id** - namespace for your application in Zookeeper. This means that the lock will be stored
                in Zookeeper with path likes **/app_id/your_lock_name**
 * **sleep** - Sleep before work. Default: "OFF". Switch "ON" by -s (--sleep).
 * **maxla** - Maximal load average. Use if >=0. Default: -1. Set by -m (--maxla).

Logging
=======

* **path** - path to log file (default: /dev/null)
* **level** - logging level of zk-flock (default: INFO)
* **zklevel** - logging level of Zookeeper Client (default: WARN)

Both loglevels are one of values: ERROR, WARN, INFO, DEBUG

Usage
=====

To run the application under the supervision of the zk-flock use the command:
```bash
zk-flock <pidname> <application command>
```

If your application requires command-line arguments enclose it in double quotes:
```bash
zk-flock my_test_lock "bash /home/user/test.sh arg1 arg2 arg3"
```

For attempting to lock lasted for a specific time, use the **-w** option (**--wait**) setting the time in seconds.
Add key **-d** or **--daemonize** to starts this appliction as daemon.

If need set minimum time in seconds for lock use the **-l** option (**--minlocktime**) - default 5 sec

Use **-p** or **--pdeathsig** to specify a signal that will be sent if the master process died. By default the signal is **SIGTERM**.

Non Linux usage warning
=======================

If you kill zk-flock application with **kill -9**, the lock will be released, but this will not stop your application.
