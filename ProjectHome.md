This program is a TFTP server.

http://www.skipole.plus.com/skipole/images/TFTPgui_main.PNG  http://www.skipole.plus.com/skipole/images/TFTPgui_setup.PNG

It is intended to run as a user initiated program, rather than a service daemon, and displays a gui interface allowing the user to stop and start the tftp server.

It provides a simple tftp server for engineers to download and upload configuration files from equipment such as routers and switches.

Written in Python to be multi-platform

Easy to install (standard library, pure python, no dependencies, put it anywhere and run)

Easy to uninstall – delete directory and files

To run: move to the directory where you have un-tarred the source, and type:

`python tftpgui.py`

or, if using Linux, and you want to listen on port 69:

`sudo python tftpgui.py`

Notes;

The tftpgui\_2\_1\_py25\_install.exe for Windows includes an embedded Python interpreter, download and run it to fully install TFTPgui.

The version 2 source file installs requires Python 2.5 to 2.7, and the Python tkinter package to be installed, called python-tk on Debian/Ubuntu (already included on Windows if you have Python installed).

The version 3 source file installs requires Python 3.2 or later, and the Python tkinter package to be installed, called python3-tk on Debian/Ubuntu (already included on Windows if you have Python installed).

You should download the latest version 3 source file if you have the latest version3 Python installed on your computer. Unarchive the file, and read the README.TXT file.

Features:

Multiple simultaneous transfers

Can be run from the command line, without a GUI

Blocksize negotiation


New - in version 2.2 and 3.1:

Some code refactoring.

The config file is now created in the users home directory as a hidden file, allowing different users on a machine to maintain their own persistent setup options.