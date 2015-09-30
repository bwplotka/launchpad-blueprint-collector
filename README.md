### Launchpad Blueprint Collector

App with GUI which collects all valid blueprints from existing project on launchpad via https://api.launchpad.net/devel/
Output for this app is the .csv file which is ready to be opened by Excel.

Tested on Windows 8.1 x64

## App details:
 - exe is compiled for Windows 8.1 x64
 - implementation in Python 3.4 x64, PyQt4 and urllib3
 - .exe file is available in 'dist' directory.
 
 
## Building exe:
 - Install python 3.4 and py2exe  [instructions](http://www.anthonydebarros.com/2014/02/16/setting-up-python-in-windows-8-1/)
 - Using pip install
	- urllib3
	- PySide
	- py2exe
 - Download PyQt4 binaries for Python3.4 and windows x64
 - Modify bp_collector_win_qt_thread.py
 - In console:  python setup.py py2exe --includes sip
 - Now you have fresh .exe in 'dist' directory

 
 
 
 