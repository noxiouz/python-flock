try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
        name = "zk-flock",
        version = "0.1.0",
        author = "Anton Tyurin",
        author_email = "noxiouz@yandex.ru",
        description = "Some descrip",
        url = "https://github.com/noxiouz/python-flock",
        license = "GPL3",
        packages = [
            "distributedflock",
            "distributedflock.ZKeeperAPI"
        ],
        data_files = [
            ('/usr/bin/',['zk-flock']),
        ],
        requires = [
            "zookeeper"
        ],
        test_suite="tests"
)
