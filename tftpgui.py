#!/usr/bin/env python
#
# tftpgui.py
#
# Version : 1.1
# Date : 20070301
#
# Author : Bernard Czenkusz
# Email  : bernie@skipole.co.uk

#
# tftpgui.py - TFTP server, run as a gui program
# Copyright (c) 2007 Bernard Czenkusz
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#

"""This program is a gui to initiate or stop a tftp service

It uses Tkinter as its graphical environment, and should therefore
work on both Windows and Linux

Associated files :
    tftpcfg.py      -       Parses and stores configuration values
    ipv4_parse.py   -       Parses IP address and mask values
    tftpgui.cfg     -       Holds configuration data
    tftphq.py       -       Runs the tftp communications
    stopwatch.py    -       Timer functions, for adaptive timeouts
"""

import Tkinter
import tkMessageBox, tkFileDialog
import socket
import sys
import tftpcfg
import tftphq
import os


class TftpGui(Tkinter.Frame):
    def __init__(self, master):
        Tkinter.Frame.__init__(self, master)

        # Create the buttons
        ButtonFrame=Tkinter.Frame(self)
        ButtonFrame.pack(side=Tkinter.TOP, expand=Tkinter.YES, fill=Tkinter.X)
        # create four buttons
        # START
        self.StartButton=Tkinter.Button(ButtonFrame)
        self.StartButton["text"]="Start"
        self.StartButton["command"]=self.StartServer
        self.StartButton.pack(side=Tkinter.LEFT, expand=Tkinter.YES, fill=Tkinter.X)
        # STOP
        self.StopButton=Tkinter.Button(ButtonFrame)
        self.StopButton["text"]="Stop"
        self.StopButton["command"]=self.StopServer
        self.StopButton.pack(side=Tkinter.LEFT, expand=Tkinter.YES, fill=Tkinter.X)
        # SETUP
        self.SetupButton=Tkinter.Button(ButtonFrame)
        self.SetupButton["text"]="Setup"
        self.SetupButton["command"]=self.SetupServer
        self.SetupButton.pack(side=Tkinter.LEFT, expand=Tkinter.YES, fill=Tkinter.X)
        # EXIT
        self.ExitButton=Tkinter.Button(ButtonFrame)
        self.ExitButton["text"]="Exit"
        self.ExitButton["command"]=self.ExitApp
        self.ExitButton.pack(side=Tkinter.LEFT, expand=Tkinter.YES, fill=Tkinter.X)

        # Create a label area, showing tftp progress
        self.Progress=Tkinter.Label(self, width=40, height=12, relief=Tkinter.SUNKEN,
                                    background="white", borderwidth=2,
                                    anchor=Tkinter.NW, justify=Tkinter.LEFT)
        self.Progress.pack(side=Tkinter.TOP, padx=10, pady=10)

        # Create a Progress Bar
        BarFrame=Tkinter.Frame(self)
        BarFrame.pack(side=Tkinter.TOP, expand=Tkinter.YES, fill=Tkinter.X)
        self.Bar=ProgressBar(BarFrame)

        # Create a status label showing current ip address of this PC
        self.textAddress=socket.gethostbyname(socket.gethostname())
        # But only show it, if it doesn't start with "127."
        if self.textAddress[0:4] != "127.":
            Tkinter.Label(self, text="This PC :  " + self.textAddress).pack(side=Tkinter.TOP, pady=5)

        # Call StartApp to set initial button state and screen message
        self.StartApp("TFTPgui - a free tftp Server\n\n"+\
                      "Version\t:  TFTPgui 1.1\n"+\
                      "Author\t:  Bernard Czenkusz\n"+\
                      "Web site\t:  www.skipole.co.uk\n"+\
                      "License\t:  GPL\n\n"+\
                      "Press Start to enable the tftp server")

        # Pack and display the frame
        self.pack()

        # Check Config is ok
        global setupdict
        if not tftpcfg.parse_all(setupdict):
            self.StartButton["state"]=Tkinter.DISABLED
            tkMessageBox.showwarning("WARNING", "There is an error in the configuration. Choose Setup to correct it.")
            self.Progress["text"]="There is an error in the configuration.\nChoose Setup to correct it."
        # If this is a posix system, and user is not su and port is less
        # than 1000, then user does not have permission to run a server
        if os.name == "posix":
            if int(setupdict["port"])<1000 and os.geteuid() != 0:
                self.StartButton["state"]=Tkinter.DISABLED
                tkMessageBox.showwarning("WARNING", "Need to be su to run a server with a port less than 1000.")
                self.Progress["text"]="There is an error in the configuration.\nChoose Setup to correct it."    
            
            
    def StartApp(self, startuptext):
        self.Progress["text"]=startuptext
        self.StartButton["state"]=Tkinter.NORMAL
        self.StopButton["state"]=Tkinter.DISABLED
        self.SetupButton["state"]=Tkinter.NORMAL
        self.ExitButton["state"]=Tkinter.NORMAL
        global StatusVar
        StatusVar=0

    def StartServer(self):
        global setupdict
        global StatusVar
        # create the tftp server
        if tftphq.startserver(setupdict):
            StatusVar=1
            self.StartButton["state"]=Tkinter.DISABLED
            self.StopButton["state"]=Tkinter.NORMAL
            self.SetupButton["state"]=Tkinter.DISABLED
            # After x msec, poll the server by calling function pollsocket
            # pollsocket then continues to poll while the server is running
            MainWindow.after(100, pollsocket)
            self.Progress["text"]="tftp server started"
        else:
            # Server has not started
            StatusVar=2
            self.StopButton["state"]=Tkinter.DISABLED
            self.StartButton["state"]=Tkinter.NORMAL
            self.SetupButton["state"]=Tkinter.NORMAL
            self.Progress["text"]="Unable to start tftp server"
            self.Bar.Clear()
 
    def StopServer(self):
        global StatusVar
        StatusVar=2
        self.StopButton["state"]=Tkinter.DISABLED
        self.StartButton["state"]=Tkinter.NORMAL
        self.SetupButton["state"]=Tkinter.NORMAL
        tftphq.stopserver()
        self.Progress["text"]="tftp server stopped"
        self.Bar.Clear()

    def SetupServer(self):
        # quitting this mainloop - so main program can
        # show the SetupGui
        global StatusVar
        StatusVar=3
        self.quit()

    def ExitApp(self):
        global StatusVar
        StatusVar=4
        self.quit()



class SetupGui(Tkinter.Frame):
    def __init__(self, master=None):
        Tkinter.Frame.__init__(self, master)
        # Create and set the widgit variables from the global setupdict
        global setupdict
        self.tftprootfolder=Tkinter.StringVar()
        self.tftprootfolder.set(setupdict["tftprootfolder"])
        self.logfolder=Tkinter.StringVar()
        self.logfolder.set(setupdict["logfolder"])
        self.anysource=Tkinter.StringVar()
        self.anysource.set(setupdict["anysource"])
        self.ipaddress=Tkinter.StringVar()
        self.ipaddress.set(setupdict["ipaddress"])
        self.mask=Tkinter.StringVar()
        self.mask.set(setupdict["mask"])
        self.port=Tkinter.StringVar()
        self.port.set(setupdict["port"])

        # Create the tfp root directory entry widget
        BigTftprootFrame=Tkinter.Frame(self)
        BigTftprootFrame.pack(side=Tkinter.TOP, expand=Tkinter.YES, fill=Tkinter.X, pady=5)
        # Create the text label for the entry
        Tkinter.Label(BigTftprootFrame, text="Tftp root folder for GET and PUT files").pack(side=Tkinter.TOP, anchor=Tkinter.W)
        TftprootFrame=Tkinter.Frame(BigTftprootFrame)
        TftprootFrame.pack(side=Tkinter.TOP, expand=Tkinter.YES, fill=Tkinter.X)
        # Create the entry field
        Tkinter.Entry(TftprootFrame, textvariable=self.tftprootfolder, width=30).pack(side=Tkinter.LEFT)
        # Create the browse button
        self.RootBrowseButton=Tkinter.Button(TftprootFrame)
        self.RootBrowseButton["text"]="Browse"
        self.RootBrowseButton["width"]=8
        self.RootBrowseButton["command"]=self.BrowseRootFolder
        self.RootBrowseButton["state"]=Tkinter.NORMAL
        self.RootBrowseButton.pack(side=Tkinter.LEFT,padx=5)

        # Create the log directory entry widget
        BigLogFrame=Tkinter.Frame(self)
        BigLogFrame.pack(side=Tkinter.TOP, expand=Tkinter.YES, fill=Tkinter.X, pady=5)
        # Create the text label for the entry
        Tkinter.Label(BigLogFrame, text="Folder for Log files").pack(side=Tkinter.TOP, anchor=Tkinter.W)
        LogFrame=Tkinter.Frame(BigLogFrame)
        LogFrame.pack(side=Tkinter.TOP, expand=Tkinter.YES, fill=Tkinter.X)
        # Create the entry field
        Tkinter.Entry(LogFrame, textvariable=self.logfolder, width=30).pack(side=Tkinter.LEFT)
        # Create the browse button
        self.LogBrowseButton=Tkinter.Button(LogFrame)
        self.LogBrowseButton["text"]="Browse"
        self.LogBrowseButton["width"]=8
        self.LogBrowseButton["command"]=self.BrowseLogFolder
        self.LogBrowseButton["state"]=Tkinter.NORMAL
        self.LogBrowseButton.pack(side=Tkinter.LEFT,padx=5)

        # Create the input client ip address radio buttons
        ClientFrame=Tkinter.Frame(self)
        ClientFrame.pack(side=Tkinter.TOP, expand=Tkinter.YES, fill=Tkinter.X, pady=5)
        # Create the text label for the entry
        Tkinter.Label(ClientFrame, text="Allow TFTP from :").pack(side=Tkinter.LEFT)
        # Create the buttons
        self.RadioAny=Tkinter.Radiobutton(ClientFrame, text="Any", variable=self.anysource, value="1")
        self.RadioAny.pack(side=Tkinter.LEFT, padx=10)
        self.RadioAny["command"]=self.ToggleRadio
        self.RadioSubnet=Tkinter.Radiobutton(ClientFrame, text="Subnet", variable=self.anysource, value="0")
        self.RadioSubnet.pack(side=Tkinter.LEFT, padx=10)
        self.RadioSubnet["command"]=self.ToggleRadio

        # Create the entry ip address and mask fields
        AddressFrame=Tkinter.Frame(self)
        AddressFrame.pack(side=Tkinter.TOP, expand=Tkinter.YES, fill=Tkinter.X)
        Tkinter.Label(AddressFrame, text="IP :").pack(side=Tkinter.LEFT)
        self.IPEntry=Tkinter.Entry(AddressFrame, textvariable=self.ipaddress, width=17)
        self.IPEntry.pack(side=Tkinter.LEFT)
        Tkinter.Label(AddressFrame, text="   MASK :").pack(side=Tkinter.LEFT)
        self.MASKEntry=Tkinter.Entry(AddressFrame, textvariable=self.mask, width=3)
        self.MASKEntry.pack(side=Tkinter.LEFT)
        # Set field enabled or disabled depending on Any or Subnet radio buttons
        self.ToggleRadio()

        # Set udp port
        PortFrame=Tkinter.Frame(self)
        PortFrame.pack(side=Tkinter.TOP, expand=Tkinter.YES, fill=Tkinter.X, pady=15)
        Tkinter.Label(PortFrame, text="UDP port :").pack(side=Tkinter.LEFT)
        self.PortEntry=Tkinter.Entry(PortFrame, textvariable=self.port, width=6)
        self.PortEntry.pack(side=Tkinter.LEFT)
        Tkinter.Label(PortFrame, text="(Default 69)").pack(side=Tkinter.LEFT, padx=10)

        # Create the Apply and Cancel buttons
        ButtonFrame=Tkinter.Frame(self)
        ButtonFrame.pack(side=Tkinter.TOP, expand=Tkinter.YES, fill=Tkinter.X, pady=10)
        # create two buttons - Apply Cancel
        self.ApplyButton=Tkinter.Button(ButtonFrame)
        self.ApplyButton["text"]="Apply"
        self.ApplyButton["width"]=8
        self.ApplyButton["command"]=self.ApplySetup
        self.ApplyButton["state"]=Tkinter.NORMAL
        self.ApplyButton.pack(side=Tkinter.LEFT, padx=10)
        self.CancelButton=Tkinter.Button(ButtonFrame)
        self.CancelButton["text"]="Cancel"
        self.CancelButton["width"]=8
        self.CancelButton["command"]=self.CancelSetup
        self.CancelButton["state"]=Tkinter.NORMAL
        self.CancelButton.pack(side=Tkinter.LEFT, padx=10)
        self.DefaultButton=Tkinter.Button(ButtonFrame)
        self.DefaultButton["text"]="Default"
        self.DefaultButton["width"]=8
        self.DefaultButton["command"]=self.DefaultSetup
        self.DefaultButton["state"]=Tkinter.NORMAL
        self.DefaultButton.pack(side=Tkinter.LEFT, padx=10)
        global StatusVar
        StatusVar=0

    def BrowseRootFolder(self):
        dirname = tkFileDialog.askdirectory(parent=self, mustexist=1, initialdir=self.tftprootfolder.get())
        if dirname=="": return 0
        self.tftprootfolder.set(dirname)

    def BrowseLogFolder(self):
        dirname = tkFileDialog.askdirectory(parent=self, mustexist=1, initialdir=self.logfolder.get())
        if dirname=="": return 0
        self.logfolder.set(dirname)

    def check_tftprootfolder(self):
        if not tftpcfg.parse_tftprootfolder(self.tftprootfolder.get()):
            # tftprootfolder failed parse test
            tkMessageBox.showerror("Error", "The tftp root folder must exist,\nwith read and write permissions.")
            return 0
        return 1

    def check_logfolder(self):
        if not tftpcfg.parse_logfolder(self.logfolder.get()):
            # logfolder failed parse test
            tkMessageBox.showerror("Error", "The log folder must exist,\nwith write permissions.")
            return 0
        return 1

    def check_ip(self):
        if not tftpcfg.parse_ip(self.ipaddress.get(), self.mask.get()):
            # IP address and mask failed parse test
            tkMessageBox.showerror("Error", "The ip subnet is incorrect.")
            return 0
        return 1

    def check_port(self):
        if not tftpcfg.parse_port(self.port.get()):
            # udp port failed parse test
            tkMessageBox.showerror("Error", "The UDP port is incorrect.")
            return 0
        # If this is a posix system, and user is not su and port is less
        # than 1000, then user does not have permission to run a server
        if os.name == "posix":
            if int(self.port.get())<1000 and os.geteuid() != 0:
                tkMessageBox.showerror("Error", "Need to be su to run a server with a port less than 1000.")
                return 0        
        return 1

    def ApplySetup(self):
        # put setup values into the dictionary
        global setupdict
        global StatusVar
        if not self.check_tftprootfolder(): return 0
        if not self.check_logfolder(): return 0
        if not self.check_ip(): return 0
        if not self.check_port(): return 0
        setupdict["tftprootfolder"]=self.tftprootfolder.get()
        setupdict["logfolder"]=self.logfolder.get()
        setupdict["anysource"]=self.anysource.get()
        setupdict["ipaddress"]=self.ipaddress.get()
        setupdict["mask"]=self.mask.get()
        setupdict["port"]=self.port.get()
        setupdict=tftpcfg.correctconfig(setupdict)
        self.AssignDictToValues(setupdict)
        # save the dictionary to the config file
        if not tftpcfg.setconfig(setupdict):
            # An error has occurred
            # restore setupdict from config file
            setupdict=tftpcfg.getconfig()
            tkMessageBox.showerror("Error", "There is an error in the config\nsettings have not been applied")
            return 0
        StatusVar=5
        self.quit()

    def CancelSetup(self):
        # Return option values to as they were
        global setupdict
        global StatusVar
        self.AssignDictToValues(setupdict)
        if not tftpcfg.parse_all(setupdict):
            tkMessageBox.showerror("Error", "There is an error in the config\nsettings have not been applied")
            return 0
        StatusVar=6
        self.quit()

    def DefaultSetup(self):
        # Return option values to Default
        self.AssignDictToValues(tftpcfg.setdefaults())

    def AssignDictToValues(self, tempdict):
        # Assigns a setup dictionary to the field values
        self.tftprootfolder.set(tempdict["tftprootfolder"])
        self.logfolder.set(tempdict["logfolder"])
        self.anysource.set(tempdict["anysource"])
        self.ipaddress.set(tempdict["ipaddress"])
        self.mask.set(tempdict["mask"])
        self.port.set(tempdict["port"])
        self.ToggleRadio()

    def ToggleRadio(self):
        if self.anysource.get() == "1":
            self.IPEntry["state"]=Tkinter.DISABLED
            self.MASKEntry["state"]=Tkinter.DISABLED
        else:
            self.IPEntry["state"]=Tkinter.NORMAL
            self.MASKEntry["state"]=Tkinter.NORMAL


class ProgressBar:
    def __init__(self, Parent, Height=10, Width=200, ForegroundColor=None,
                 BackgroundColor=None):
        self.Height=Height
        self.Width=Width
        # shaker is a variable used to show an oscillating dot on the bar
        self.shaker=1
        self.Progress=0
        self.BarCanvas=Tkinter.Canvas(Parent, width=Width, height=Height,
                                      borderwidth=1, relief=Tkinter.SUNKEN)
        if (BackgroundColor==None): BackgroundColor="white"
        self.BarCanvas["background"]=BackgroundColor
        self.BarCanvas.pack(padx=5, pady=2)
        self.RectangleID=self.BarCanvas.create_rectangle(0, 0, 0, Height)
        if (ForegroundColor==None): ForegroundColor="red"
        self.BarCanvas.itemconfigure(self.RectangleID, fill=ForegroundColor)
        self.Clear()
        
    def SetProgressPercent(self, NewLevel):
        self.Progress=NewLevel
        self.Progress=min(100, self.Progress)
        self.Progress=max(0, self.Progress)
        ProgressPixel=(self.Progress/100.0)*self.Width
        self.BarCanvas.coords(self.RectangleID, 0, 0, ProgressPixel, self.Height)
        
    def Clear(self):
        self.SetProgressPercent(0)
        
    def ShowProgress(self, barinfo):
        """This is the main function of the class, and is called
           with input variable barinfo set to:
           0 if the progress bar should be blank
           1 to 100 if a percent should be shown
           -1 if the bar should oscilate"""
        if barinfo >= 0:
            self.SetProgressPercent(barinfo)
            return 1
        # So if barinfo is less than 0, draw oscillating bar
        if (self.Progress>98):
            self.shaker = -1
        if (self.Progress<4):
            self.shaker=1
        self.Progress=self.Progress+self.shaker
        ProgressPixel=(self.Progress/100.0)*self.Width
        self.BarCanvas.coords(self.RectangleID, ProgressPixel-2, 0, ProgressPixel, self.Height)


# Start the main program

# Get initial setup values via tftpcfg module and place them in
# the global dictionary setupdict
setupdict={}
setupdict=tftpcfg.getconfig()

# get the name of the logfile
logfile=os.path.join(setupdict["logfolder"],"tftplog")

# Each time the program is started, a new logfile will be created, and the
# existing one will be saved as tftplog.old - any previous tftplog.old will
# be deleted

if os.path.exists(logfile):
    # if an existing log file exists, rename it to tftplog.old
    # but first check if an old logfile exists
    old_logfile=os.path.join(setupdict["logfolder"],"tftplog.old")
    try:
        if os.path.exists(old_logfile):
            # An old logfile exists, so delete it
            os.remove(old_logfile)
        # now ok to rename the logfile
        os.rename(logfile, old_logfile)
    except:
        # An error has occurred, possibly two instances are running
        # and the logfile is locked, so just continue without
        # trying to rename the logfile
        pass
        
# The global variable StatusVar is a flag showing
# what point the program has reached

StatusVar=0

# Two frames are created;
# ServerFrame which shows the running server
# with buttons to stop or start it, and a progress bar.
# SetupFrame which gives options to input the tftp root folder
# to place transferred files, where to place log files, what
# client addresses to allow, and what udp port to use

MainWindow=Tkinter.Tk()
MainWindow.title("TFTPgui")
MainWindow.minsize(width=250, height=300)
MainWindow.resizable(Tkinter.NO, Tkinter.NO)

ServerFrame=TftpGui(MainWindow)
SetupFrame=SetupGui(MainWindow)

def pollsocket():
    if StatusVar==1 :
        # Tftp server is running
        # The module tftphq does the communications control
        # pollserver checks if anything is coming in or to be sent
        tftphq.pollserver()
        if tftphq.changebarinfo:
            # variable tftphq.barinfo is
            #  0 if the progress bar should be blank
            #  1 to 100 if a percent should be shown
            #  -1 if the bar should oscilate
            ServerFrame.Bar.ShowProgress(tftphq.barinfo)
        if tftphq.changetxtinfo:
            # variable tftphq.txtinfo is
            # the text to be displayed in the main informational window
            ServerFrame.Progress["text"]=tftphq.txtinfo
            tftphq.changetxtinfo=0

        # and call this function again, in another 10 msec
        MainWindow.after(10, pollsocket)



while (StatusVar==0):
    ServerFrame.mainloop()
    if (StatusVar!=3):
        # Shutdown the application
        break

    # If StatusVar = 3, then the user
    # has requested the setup frame , so hide
    # the ServerFrame and show the alternate
    # SetupFrame, and re-start the main loop
    StatusVar=0
    geom=MainWindow.geometry()
    ServerFrame.pack_forget()
    SetupFrame.pack()
    MainWindow.geometry(geom)
    SetupFrame.mainloop()
    if (StatusVar==0):
        # The windows decorator X must have been pressed
        # shutdown the application
        break

    # SetupFrame finished, so go back to ServerFrame
    SetupFrame.pack_forget()
    StatusVar=0
    ServerFrame.StartApp("Press Start to enable the tftp server")
    ServerFrame.pack()


# Gui application has shut down
# clear up and exit

sys.exit(0)


