""" TBot """
from setuptools import setup, find_packages

setup(
    name="tbot",
    version="0.3.0",
    packages=find_packages(),
    install_requires=["paramiko", "enforce"],
    entry_points={
        "console_scripts": ["tbot = tbot.main:main", "tbot-mgr = tbot.mgr:main"]
    },
    package_data={"tbot": ["builtin/*.py", "builtin/**/*.py"]},
)
