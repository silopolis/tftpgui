TFTPgui

Version : 1.1
Date : 20070301



This program is a TFTP server, it requires Python 2.4 or later.
It is intended to run as a user initiated program, rather than
a service daemon, and displays a gui interface allowing the user
to stop and start the tftp server.

It provides a simple tftp server for engineers to download
configuration files from equipment such as routers and switches.

It has been tested on Windows XP and Linux platforms.


It consists of the files:

tftpgui.py     The main program - when run, it starts the gui

(For windows users, it may be called tftpgui.pyw)

The following files are in the same folder, and are called by tftpgui.py:

ipv4_parse.py  Used to parse IP addresses
stopwatch.py   Used to time packets
tftpcfg.py     Used to parse and save configuration values
tftphq.py      Implements the tftp protocol

When tftpgui.py is run, it creates the file tftpgui.cfg to hold
configuration data.

It also requires two directories, one to hold logs, which are created
during file transfers, and one to act as the root folder to which files
are put, and from which files are pulled.

As default, these are the folders tftplogs and tftproot which are under
the folder where the above files are held.

These two folders can be set to other folders of your choice from
within the gui.



USAGE ------------------------------------------------------------------

Running tftpgui.py (typically using the "python tftpgui.py" command
under Linux, or "tftpgui.pyw" under Windows - if the .pyw extension is
associated with pythonw.exe),the program presents you with a graphical
window, with start, stop, setup and exit buttons.

Start - will start the server, which will then listen for file transfers
from remote tftp clients.

Stop - will stop the server.

Setup - will open a window giving various options described below.

Exit - will close the program.



SETUP OPTIONS ---------------------------------------------------------

TFTP ROOT Folder:  set the folder where files will be sent and received

TFTP LOGS Folder:  During transmission, the program writes log entries,
                   these are held in this folder, which you can set.

Allow access from any remote IP Address, or just a specified subnet:

If any remote address is allowed, then any client can call this server.

If a subnet is specified, then you may input the subnet and mask,
and the server will only accept calls from clients within this
subnet.  If you wish to limit remote access from a single device, set
the subnet to the remote device IP address, and the mask to 32.

PORT: The port which the tftp server listens on, as standard this is 69

It should be noted that on Linux, to set up a server listening on any
port below 1000 requires root permission, therefore you will need to be
root (or use sudo) to run this program on port 69.

APPLY   - Save and implement the options.
CANCEL  - Discard any option changes you have done.
DEFAULT - Set options to the initial defaults.



LICENSE ---------------------------------------------------------------

Author : Bernard Czenkusz
Email  : bernie@skipole.co.uk

TFTPgui - A GUI TFTP Server
Copyright (c) 2007 Bernard Czenkusz

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

