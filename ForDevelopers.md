# The code files #

tftpgui.py  - which is the script that runs the application

tftp\_package/tftpcfg.py  - reads and writes to the config file

tftp\_package/gui\_stuff.py  - runs the GUI

tftp\_package/tftp\_engine.py  - runs the tftp server

tftp\_package/ipv4.py  - parses ip addresses


# tftpgui.py #

When tftpgui.py is run, it parses command line options, gets the scriptdirectory where it is located, and sets a default config file (or reads it from the command line).

It then calls functions in tftp\_package/tftpcfg.py to read the config file.

Two functions are available:

```
tftpcfg.getconfigstrict(scriptdirectory, configfile)
```

This is called if the option --nogui is given or if a config file is given on the command line.

It reads and parses the configfile strictly - raising an error if any items are missing.

If the program is to be run with a gui, and with the default config file, then the function:

```
tftpcfg.getconfig(scriptdirectory, configfile)
```

is run instead, this also reads the config file, but replaces any missing items with defaults, and even writes out a new one if no default config file exists.

Both these functions return a dictionary:

```
    cfgdict = { "anyclient": True,
                "clientipaddress": "192.168.0.0",
                "clientmask": 16,
                "listenport": 69,
                "listenipaddress": "0.0.0.0",
                "tftprootfolder": os.path.join(scriptdirectory,'tftproot'),
                "logfolder": os.path.join(scriptdirectory,'tftplogs')  }
```

The keys must all exist, but the values are read from the config file, those given above are the defaults. If you wish to incorporate parts of tftpgui in your own program, and don't want to use  tftpcfg.py - then generate the above dictionary some other way.

tftp\_package/tftp\_engine.py is imported and a server is defined:

```
server = tftp_engine.ServerState(**cfgdict)
```

This defines a 'server' but does not run it, to do that, an  event loop must be run.

Two event loops are available in tftp\_engine.py; loop(server) for use with a GUI and loop\_nogui(server) for without a GUI.  So if the --nogui option has been chosen:

```
result = tftp_engine.loop_nogui(server)
```

This then runs until the process is killed.  It returns 1 on error or 0 if terminated with CTRL-c.

If a gui is to be run, then the gui is run in the main thread, and the engine loop in a second thread using the tftp\_engine.loop(server) function:

```
thread.start_new_thread(tftp_engine.loop, (server,))
```

Then gui\_stuff is imported, and the gui started by

```
gui_stuff.create_gui(server)
```

This enters a gui event loop, when it exits (via the Exit button on the gui) the server thread is killed by calling

```
server.break_loop = True
# give a moment for server thread to stop
time.sleep(0.5)
sys.exit(0)
```

The tftp\_engine module does not import either gui\_stuff.py or tftpcfg.py, so it could be imported and used to run a tftp server loop on its own (but it does need ipv4.py), the programmer will just need the dictionary defined above to create the 'server'.  It does import ipv4.py, as this is used to work out if the calling client ip address is within the subnet of allowed client addresses.

The gui can change, and read attributes of the 'server' instance, which controls the server engine.

# Further Information #

[AboutTFTPgui](AboutTFTPgui.md) - introductory information

CommandlineOptions - gives more info on available options from the command line.

DistributionPackagers - gives info for anyone packaging TFTPgui for a Linux distribution.

FutureVersions - description of the SVN structure and future work