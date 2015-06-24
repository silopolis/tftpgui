# TFTPgui Introduction #

This program is a TFTP server.

It is intended to run as a user initiated program, rather than a service daemon, and displays a gui interface allowing the user to stop and start the tftp server.

It provides a simple tftp server for engineers to download and upload configuration files from equipment such as routers and switches.

If using Windows, download tftpgui\_2\_1\_py25\_installer.exe and run it to install, this will give an application icon, which will run the program.

Alternatively, if you are a Python user, and have Python version 2.5 to 2.7 installed, you can download just the Python source files in tftpgui\_2\_2.zip, unzip it and run 'python tftpgui.pyw'.  You may need to replace the 'python' with the path to the Python interpreter, i.e. C:\Python27\python tftpgui.pyw

If you have Python 3.2 or later installed, download tftpgui\_3\_1.zip instead.

It would also be possible to associate the .pyw extension with the python interpreter, in which case merely double clicking on the tftpgui.pyw file will run the program.

If you are a Linux user:

Download the tar file tftpgui\_2\_2.tar : Untar it into a directory of your choice, and running "python tftpgui.py" will run the program.  Or you could make tftpgui.py executable, and run it directly.

Use tftpgui\_3\_1.tar if you have Python 3.2 or later installed.

TFTPgui requires the python tkinter package. On Ubuntu/Debian this is package python-tk, (for default Python 2) or python3-tk (for Python 3), on Windows it is built into Python and does not need to be separately installed.

# Usage #

Try:

python tftpgui.py --help

For a description of options.

The program presents you with a graphical window, with start, stop, setup and exit buttons.

Start - will start the server, which will then listen for file transfers from remote tftp clients.

Stop - will stop the server.

Setup - will open a window giving various options described below.

Exit - will close the program.


# Setup Options #

TFTP ROOT Folder:  set the folder where files will be sent and received

TFTP LOGS Folder:  During transmission, the program writes log entries, these are held in this folder, which you can set.

Allow access from any remote IP Address, or just a specified subnet:

If any remote address is allowed, then any client can call this server.

If a subnet is specified, then you may input the subnet and mask, and the server will only accept calls from clients within this subnet.  If you wish to limit remote access from a single device, set the subnet to the remote device IP address, and the mask to 32.

PORT: The port which the tftp server listens on, as standard this is 69

It should be noted that on Linux, to set up a server listening on any port below 1000 requires root permission, therefore you will need to be root (or use sudo) to run this program on port 69.

APPLY   - Save and implement the options.

CANCEL  - Discard any option changes you have done.

DEFAULT - Set options to the initial defaults.

# Configuration file #

Under normal use, the hidden file .tftpgui.cfg is initially created in the users home directory, or under Windows - in the per-user application directory.  The file is changed whenever the user sets changes on the graphical interface. The file is subsequently read on startup, so the users changes are persistent.  Most users need never look at, or edit the file.

Using the --nogui option on the command line allows the server to be run without a graphical environment, in which case the configuration file is the only form of controlling the server. In this case, a configuration file location can be set on the command line.

Typical contents of configuration file

```
---------------------------------------------------
[IPsetup]
clientmask = 16
listenport = 69
anyclient = 1
listenipaddress = 0.0.0.0
clientipaddress = 192.168.0.0

[Folders]
tftprootfolder = /home/bernie/tftpgui3/tftproot
logfolder = /home/bernie/tftpgui3/tftplogs
----------------------------------------------------
```

The value 'anyclient' is set to 1 to indicate any client can contact the server, or zero if only a client with an ip address in the given subnet will be accepted.

The folder locations will be set to appropriate locations on your own PC the first time you run the program.

The configuration file has one option not set via the GUI. This is 'listenipaddress' which is normally set to 0.0.0.0 - meaning the server will listen on all ip addresses configured on the PC. If however you have a machine with multiple IP addresses and you want the tftp service to only listen on one, you can set the IP address here.

# Further Information #

CommandlineOptions - gives more info on available options from the command line.

DistributionPackagers - gives info for anyone packaging TFTPgui for a Linux distribution.

ForDevelopers - more detailed program information

FutureVersions - description of the SVN structure and future work