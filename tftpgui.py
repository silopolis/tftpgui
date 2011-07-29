#!/usr/bin/env python

####### TFTPgui #######
#
# tftpgui.py  - a TFTP server
#
# Version : 3.0
# Date : 20110725
#
# Author : Bernard Czenkusz
# Email  : bernie@skipole.co.uk
#
#
# Copyright (c) 2007,2008,2009,2010,2011 Bernard Czenkusz
#
# This file is part of TFTPgui.
#
#    TFTPgui is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    TFTPgui is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with VATStuff.  If not, see <http://www.gnu.org/licenses/>.
#

"""
tftpgui.py  - a TFTP server.

This script parses command line options, reads the configuration file
and starts a GUI loop in the main thread and the tftp service in a
second thread. It is intended to be run with the simplest installation;
by placing the files in a directory and running the script from there.

The program is run with:

python tftpgui.py [options] <configuration-file>

The command line options are:

--nogui : in which case the tftp server is run, but no GUI is created.
--version : prints the version number and exits
--help : prints a usage message and exits

<configuration-file> : The location of the configuration file.

If no  configuration file is given on the command line, a config file
tftpgui.cfg in the same directory as this script will be looked for.

The configuration file holds the options available via the GUI 'Setup'
button and as these are changed in the GUI, they are changed in the
config file.

With one exception:  The config file also has the option 'listenipaddress'
which by default is set to '0.0.0.0' - meaning listen on any address.

If 'listenipaddress' is set to a specific IP address of the computer
(only applicable for a computer with multiple ip addresses), then it will
only listen on the address given.

If run with the --nogui option then the program has no dependencies other
than standard Python (version 3.2 and above).  If run with a GUI then the
script imports the Tkinter module, and some Gnu/Linux distributions may
require this installing (package python-tk in Debian).

Note: If set to listen on port 69 (the default tftp server port), then
under Gnu/Linux the program must be run with administrator pivileges
(ie using sudo) - as the OS requires this.
"""

import os, sys, thread, time, argparse

from tftp_package import tftpcfg, tftp_engine

# Check the python version
if not sys.version_info[0] == 3 and sys.version_info[1] >= 2:
    print("Sorry, your python version is not compatable")
    print("This program requires python 3.2 or later")
    print("Program exiting")
    sys.exit(1)

# get the directory this script is in
scriptdirectory=os.path.abspath(os.path.dirname(sys.argv[0]))

# set the default location of the config file
default_configfile=os.path.join(scriptdirectory,'tftpgui.cfg')


parser = argparse.ArgumentParser(description='A TFTP gui server', epilog='''
Without any options the program runs with a GUI.
If no configuration file is specified, the program will look
for tftpgui.cfg in the same directory as the %(prog)s script.''')

parser.add_argument("-n", "--nogui", action="store_true", dest="nogui", default=False,
                  help="program runs without GUI, serving immediately")

parser.add_argument('--version', action='version', version='%(prog)s 3.0')

parser.add_argument('configfile', dest="configfile", default=default_configfile,
                  help="path to configuration file")

args = parser.parse_args()

nogui = args.nogui
configfile = args.configfile

# read configuration values
error_text = ""

if nogui or configfile != default_configfile:
    # Read config file, and exit if any errors
    try:
        cfgdict = tftpcfg.getconfigstrict(scriptdirectory, configfile)
    except tftpcfg.ConfigError, e:
        print "Error in config file:"
        print e
        sys.exit(1)
else:
    # Gui option and default config, so can be more relaxed
    # Try to repair config file
    try:
        cfgdict = tftpcfg.getconfig(scriptdirectory, configfile)
    except tftpcfg.ConfigError, e:
        # On error fall back to defaults, but warn the user
        cfgdict = tftpcfg.get_defaults()
        error_text = "Error in config file:\n" + str(e) + "\nso using defaults"

if nogui:
    # Create a server without a gui
    # this class records the server state, start with the server running
    server = tftp_engine.ServerState(cfgdict, serving=True)
    if server.listenipaddress :
        print "TFTP server listening on %s:%s\nSee logs at:\n%s" % (server.listenipaddress,
                                                                    server.listenport,
                                                                    server.logfolder)
    else:
        print "TFTP server listening on port %s\nSee logs at:\n%s" % (server.listenport,server.logfolder)
    print "Press CTRL-c to stop"
    # This runs the server engine, returns 0 if terminated with CTRL-c
    # or 1 if an error occurs.
    result = tftp_engine.engine_loop(server, nogui)
    sys.exit(result)

# Create a server with a gui
try:
    # Check tkinter can be imported
    import tkinter
except Exception, e:
    print """\
Failed to import tkinter - required to run the GUI.
Check the tKinter Python module has been installed on this machine.
Alternatively, run with the --nogui option to operate without a GUI"""
    sys.exit(1)

# this class records the server state, start with the server not running
server = tftp_engine.ServerState(cfgdict, serving=False)

# If an error occurred reading the config file, show it
if error_text:
    server.text = error_text +"\n\nPress Start to enable the tftp server"

# create a thread which runs the tftp engine
thread.start_new_thread(tftp_engine.engine_loop, (server, nogui))

# create the gui
from tftp_package import gui_stuff
gui_stuff.create_gui(server)


# when mainloop of gui ends, stop the server
server.shutdown()

# give a moment for server thread to stop
time.sleep(0.5)

sys.exit(0)


