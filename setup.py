try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
        name = "zk-flock",
        version = "0.1.0",
        author = "Anton Tyurin",
        author_email = "noxiouz@yandex.ru",
        url = "https://github.com/noxiouz/python-flock",
        license = "GPL3",
        packages = [
            "distributedflock",
            "distributedflock.ZKeeperAPI"
        ],
        scripts = [
            'zk-flock'
        ],
        requires = [
            "zookeeper"
        ],
        test_suite="tests"
)
