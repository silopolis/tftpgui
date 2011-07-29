TFTPgui Version : 3.0
Date 20110726

This program is a TFTP server.

It is intended to run as a user initiated program, rather than a service daemon,
and displays a gui interface allowing the user to stop and start the tftp server.

It provides a simple tftp server for engineers to download and upload
configuration files from equipment such as routers and switches.

Download the tar file tftpgui_3_0.tar : Untar it into a directory of your
choice, and running "python tftpgui.py" will run the program.

Or if using Windows: download tftpgui_3_0.zip, unzip it and run python tftpgui.pyw

Using the option --help on the command line will give further usage options.

Windows users may need to replace the 'python' with the path to their Python
interpreter, i.e. C:\Python32\python tftpgui.pyw

It would also be possible to associate the .pyw extension with the python
interpreter, in which case merely double clicking on the tftpgui.pyw file
will run the program.

tftpgui_3_0 requires python 3.2 and later to be installed, and also the
python tk modules.

On Ubuntu/Debian this is package python-tk, on Widows it is built into
Python and does not need to be separately installed.

Note, this version does not work under python 2, please choose tftpgui_2_x.tar
for a version that does.

Usage

The program presents you with a graphical window, with start, stop,
setup and exit buttons.

Start - will start the server, which will then listen for file
        transfers from remote tftp clients.

Stop - will stop the server.

Setup - will open a window giving various options described below.

Exit - will close the program.

Setup Options

TFTP ROOT Folder: set the folder where files will be sent and received

TFTP LOGS Folder: During transmission, the program writes log entries,
these are held in this folder, which you can set.

Allow access from any remote IP Address, or just a specified subnet:

If any remote address is allowed, then any client can call this server.

If a subnet is specified, then you may input the subnet and mask, and
the server will only accept calls from clients within this subnet.
If you wish to limit remote access from a single device, set the subnet
to the remote device IP address, and the mask to 32.

PORT: The port which the tftp server listens on, as standard this is 69

It should be noted that on Linux, to set up a server listening on any
port below 1000 requires root permission, therefore you will need
to be root (or use sudo) to run this program on port 69.

APPLY - Save and implement the options.

CANCEL - Discard any option changes you have done.

DEFAULT - Set options to the initial defaults.

Configuration file

Under normal use, the file tftpgui.cfg is changed whenever the user
sets changes on the graphical interface. The file is read on startup,
so the users changes are persistent. Most users need never look at,
or edit the file.

New in version 2 and 3:

Using the --nogui option on the command line allows the server to be
run without a graphical environment, in which case the configuration
file is the only form of controlling the server. In this case, a
configuration file location can be set on the command line.

Try:
python tftpgui.py --help
For a description of options

The configuration file has one option not set via the GUI. This
is 'listenipaddress' which is normally set to 0.0.0.0 - meaning
the server will listen on any ip address. If however you have a
machine with multiple IP addresses and you want the tftp service
to only listen on one, you can set the IP address here. 
