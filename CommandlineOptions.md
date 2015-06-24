# Introduction #

This is the header documentation of the startup script tftpgui.py


# Script Header #

tftpgui.py  - a TFTP server.

This script parses command line options, reads the configuration file
and starts a GUI loop in the main thread and the tftp service in a
second thread. It is intended to be run with the simplest installation;
by placing the files in a directory and running the script from there.

The program is run with:

```
python tftpgui.py [options] <configuration-file>

The command line options are:

--nogui : in which case the tftp server is run, but no GUI is created
--version : prints the version number and exits
--help : prints a usage message and exits

<configuration-file> : The optional location of a configuration file.
```

Normally a hidden file .tftpgui.cfg in the users home directory will
be created with default values.

The configuration file holds the options available via the GUI 'Setup'
button and as these are changed in the GUI, they are changed in the
config file.

With one exception:  The config file also has the option 'listenipaddress'
which by default is set to '0.0.0.0' - meaning listen on any address.

If 'listenipaddress' is set to a specific IP address of the computer
(only applicable for a computer with multiple ip addresses), then it will
only listen on the address given.

If run with the --nogui option then the program has no dependencies other
than standard Python.  If run with a GUI then the
script imports the Tkinter module, and some Gnu/Linux distributions may
require this installing (package python-tk in Debian).

Note: If set to listen on port 69 (the default tftp server port), then
under Gnu/Linux the program must be run with administrator pivileges
(ie using sudo) - as the OS requires this.

# Further Information #

[AboutTFTPgui](AboutTFTPgui.md) - introductory information

DistributionPackagers - gives info for anyone packaging TFTPgui for a Linux distribution.

ForDevelopers - more detailed program information

FutureVersions - description of the SVN structure and future work