# Program Structure #

The version 2 branch of the code requires python 2.5 to 2.7 and imports the Tkinter module, therefore on Ubuntu/Debian systems it needs python-tk.

The version 3 branch requires python 3.2 or later, and depends on python3-tk.

The license is GPL v3

The applications structure is:

tftpgui.py - the script that runs the program

Directories:

tftp\_package - contains pure python modules that run the application

tftproot - a folder where the user will get and put files

tftplogs - a folder where logs are created, (note the application rotates and limits log file sizes itself)

The user can choose from the gui where tftproot and tftplogs directories will be sited.

The file .tftpgui.cfg in the users home directory is created on first startup, and holds parameters set by the user via the GUI, so these changes are persistent.

The initial default tftproot and tftplogs directories are set in the function:

tftp\_package.tftpcfg.get\_defaults()


# Further Information #

[AboutTFTPgui](AboutTFTPgui.md) - introductory information

CommandlineOptions - gives more info on available options from the command line.

ForDevelopers - more detailed program information

FutureVersions - description of the SVN structure and future work