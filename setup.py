import py2exe

from distutils.core import setup
setup( windows=[{"script": "bp_collector_win_qt_thread.py"}],
        options={"py2exe": {"includes": ["sip"]}})