#!/usr/bin/env python
#
# tftphq.py
#
# Version : 1.1
# Date : 20070228
#
# Author : Bernard Czenkusz
# Email  : bernie@skipole.co.uk

#
# tftphq.py - TFTP server engine, run as part of TFTPgui
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

"""Does the tftp work

This module provides the control mechanisms to turn on and
off the tftp server, to do the file transfers,
and reports file transfer progress back to tftpgui.py
"""

import socket
import asyncore
import ipv4_parse
import stopwatch
import os
import logging

# GLOBAL VARIABLES

# TTLtimer is an instance of stopwatch
TTLtimer=stopwatch.stopwatch()

# timed_out is usually 0 but is set to 1 after the first time out.
# data is then re-transmitted, and on another time out this flag is
# checked and if it is 1, initiates an error packet and end
# of session 
timed_out=0

# data is the string containing data recieved or sent
data=None

# old_data is the previous data sent, held in case it has to be re-transmitted
old_data=None

# transmitting is 1 when the server is a transmitting
# and 0 otherwise
transmitting=0

# tftpsession_flag is equal to 0 if no session is in progress
# or to 1, if a session is in progress
tftpsession_flag=0

# session_request is either RRQ Read Request or WRQ Write Request
# on receiving a successful request packet, or None if no valid
# request is received
session_request=None

# filename is the name of the file (not the full path) being transferred
filename=None

# tftpserver is an instance of the class tftp_server
# which listens on the tftp port
tftpserver=None

# blksize is the tftp block size, 512 bytes as default
blksize=512

# changebarinfo is:
# 0 if the barinfo is not to be changed
# 1 if the barinfo should be updated
changebarinfo=1

# barinfo is:
#  0 if the progress bar should be blank
#  1 to 100 if a percent should be shown
#  -1 if the bar should oscillate
barinfo=-1

# changetxtinfo is:
# 0 if the txtinfo is not to be changed
# 1 if the txtinfo should be updated
changetxtinfo=0

# txtinfo is the text to be displyed on the tftpgui window
txtinfo=None

# fp is the file pointer used to open and close files for
# reading and writing
fp=None

# lastpacket is normally 0, and is set to 1 to indicate this is the last packet
# to transmit, and the session is subsequently ended
# It is set to 2 if this is the last packet to transmit, plus wait for one
# received ack - if it doesn't come, send again
lastpacket=0

# blkcount is a list of two variables, the first is the integer value of the
# blockcount, and the second is the two byte hex value of the blockcount
blkcount=[0, "\x00\x00"]

# LogHandler is initially None, and is created when the tftp server is started
LogHandler=None
# rootLogger is set to log anything with level INFO and above, change this
# to DEBUG if you wish to log more detailed information
# or to ERROR if you only wish to log errors
rootLogger = logging.getLogger('')
rootLogger.setLevel(logging.INFO)



def reset_globals():
    """These global variables track the various states of
       the tftp session, this function re-sets them
       to zero or None"""
    global tftpsession_flag
    global session_request
    global filename
    global transmitting
    global timed_out
    global lastpacket
    global data
    global blkcount
    global fp
    global changebarinfo
    global barinfo
    tftpsession_flag=0
    session_request=None
    filename=None
    transmitting=0
    timed_out=0
    lastpacket=0
    data=None
    blkcount=[0, "\x00\x00"]
    if fp:
        fp.close()
        fp=None
    changebarinfo=1
    barinfo=-1
    
    
def startserver(setupdict):
    """Starts the server by creating a listenning socket"""
    global tftpserver
    tftpserver=None
    start_logging(setupdict)
    reset_globals()
    try:
        tftpserver=tftp_server(setupdict)
    except:
        logging.error("Unable to start server")
        stop_logging()
        if tftpserver :
            tftpserver.close()
            del tftpserver
        return 0
    return 1
    

def pollserver():
    """Check if anything is coming in or to be sent"""
    global tftpsession_flag
    global transmitting
    global data
    global old_data
    global TTLtimer
    global timed_out
    try:
        asyncore.poll()
    except:
        # If poll gives an error, end the session
        error_ocurred("Error - session aborted.")
        return
    if tftpsession_flag and (not transmitting):
        # that is - we are waiting for a responce
        # check timeout not expired
        if TTLtimer.time_it(): return
        else:
            if timed_out==0:
                # This is the first time out, so re-transmit
                logging.debug("Time out while waiting for a response - resending.")
                timed_out=1
                transmitting=1
                data=old_data
                return
            else:
                # This is the second time-out, so end the session
                logging.debug("Second time out - ending session.")
                send_error()
                return    

                
def stopserver():
    """Stops the server and closes all sockets"""
    global tftpserver
    global TTLtimer
    stop_logging()
    if tftpserver :
        tftpserver.close()
        del tftpserver
    reset_globals()
    TTLtimer.stop()

# class tftp_server defines the socket which is listenning for
# a tftp request, normally on port 69.
# it also defines the handle read and write functions

class tftp_server(asyncore.dispatcher):
    """Class for the tftp listenning socket"""
    def __init__(self, setupdict):
        asyncore.dispatcher.__init__(self)
        self.setupdict=setupdict
        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.bind(("", int(self.setupdict["port"])))
        self.addr=None
        global session_request
        global filename
        global changebarinfo
        global barinfo
        session_request=None
        filename=None
        changebarinfo=1
        barinfo=-1

    def handle_read(self):
        """Handle incoming data"""
        global tftpsession_flag
        global session_request
        global transmitting
        global lastpacket
        global blksize
        header_and_block=blksize+4
        rx_data, rx_addr = self.recvfrom(header_and_block)
        if tftpsession_flag:
            # To get to this point, a session is in progress
            if rx_addr != self.addr: return
            # Check if an error packet is received
            if rx_data[0] == "\x00" and rx_data[1] == "\x05" :
                # Its an error packet, drop the call
                error_ocurred("Error received, dropping session")
                return
            if transmitting: return           
            if session_request == "RRQ":
                recv_RRQ_data(rx_data)
            else:
                recv_WRQ_data(rx_data)
        else:
            # No session in progress, so check if a start session packet received
            recv_start_session_data(rx_data, rx_addr, self.setupdict)
            # return if the packet received is invalid
            if session_request == None : return
            # So now a session has started
            self.addr=rx_addr

    def handle_write(self):
        """If global variables transmitting and tftpsession_flag are 1
           and if the global variable data contains data, then send it"""
        global data
        global transmitting
        global tftpsession_flag
        global TTLtimer
        global lastpacket
        global old_data
        if not tftpsession_flag: return
        if not transmitting: return
        # So there is a session in progress, and transmitting is enabled
        if data:
            # Take a copy of data, in case it has to be re-transmitted
            old_data=data
            while data:
                i=self.sendto(data, self.addr)
                if i == -1:
                    # Problem has ocurred, drop the call
                    error_ocurred("Error : Unable to send data")
                    return
                data=data[i:]
            data=None
            # data has been sent, so enable receiver
            transmitting = 0
            if lastpacket != 1:
                TTLtimer.start()
        if lastpacket == 1:
            # This is the last packet, so end the session
            reset_globals()

    def handle_connect(self):
        pass
        
    def handle_error(self):
        logging.error("dispatcher error has occurred")
        


# The following functions dissect and create tftp packets

# opcode   operation
# 1         Read request    (RRQ)
# 2         Write request   (WRQ)
# 3         Data            (DATA)
# 4         Acknowledgement (ACK)
# 5         Error           (ERROR)



def recv_start_session_data(startdata, startaddr, setupdict):
    """dissect a session start packet, and set up global variable session_request
       with None if the packet is invalid, or RRQ or WRQ"""
    global txtinfo
    global data
    global blkcount
    global blksize
    global session_request
    global filename
    global tftpsession_flag
    global transmitting
    global changetxtinfo
    global txtinfo
    global changebarinfo
    global barinfo
    session_request=None
    filename=None
    # check if the caller is from an allowed address
    if setupdict["anysource"] == "0" :
        if not ipv4_parse.IsAddressInSubnet(startaddr[0], setupdict["ipaddress"],
                                            setupdict["mask"]):
            # The caller ip address is not within the subnet as defined by the
            # ipaddress and mask which are given in the setup dictionary
            # So just ignore it
            logging.debug("Caller not from allowed subnet.")
            return
    #
    # still to do : if from a broadcast address, must ignore
    #
    # check first two bytes of rx_data
    if startdata[0] != "\x00" : return
    if ((startdata[1] != "\x01") and (startdata[1] != "\x02")): return
    # So this packet is a RRQ or a WRQ
    # Now split the rest into filename and mode
    parts=startdata[2:].split("\x00")
    temp1_filename=parts[0]
    mode=parts[1].lower()
    # mode must be "netascii" or "octet"
    if ((mode != "netascii") and (mode != "octet")): return
    # filename must be at least one character, and at most 256 characters long
    if ((len(temp1_filename) < 1) or (len(temp1_filename)>256)): return
    # filename must not start with a . character
    if temp1_filename[0] == ".": return
    # if filename starts with a \ or a / - strip it off
    if temp1_filename[0] == "\\" or temp1_filename[0] == "/":
        if len(temp1_filename) == 1: return
        temp1_filename=temp1_filename[1:]
    # filename must not start with a . character
    if temp1_filename[0] == ".": return    
    # The filename should only contain the printable characters, A-Z a-z 0-9 -_ or .
    # Temporarily replace any instances of the ._- characters with "x"
    temp2_filename=temp1_filename.replace(".", "x")
    temp2_filename=temp2_filename.replace("-", "x")
    temp2_filename=temp2_filename.replace("_", "x")
    # Check all characters are alphanumeric
    if not temp2_filename.isalnum(): return
    # Open filename for reading or writing
    global fp
    filepath=os.path.join(setupdict["tftprootfolder"],temp1_filename)
    try:
        if startdata[1] == "\x01" and mode == "octet":
            fp=open(filepath, "rb")
        if startdata[1] == "\x01" and mode == "netascii":
            fp=open(filepath, "r")
        if startdata[1] == "\x02" and mode == "octet":
            fp=open(filepath, "wb")
        if startdata[1] == "\x02" and mode == "netascii":
            fp=open(filepath, "w")
    except IOError:
        fp=None
        logging.error("Unable to open file %s" % filepath)
        return
    # so all tests passed, this is a successful session start
    filename=temp1_filename
    tftpsession_flag=1
    transmitting=1
    changetxtinfo=1
    txtinfo="File transfer requested by :\n%s\n\n" % startaddr[0]
    changebarinfo=1
    barinfo=1
    blkcount=[0, "\x00\x00"]
    if startdata[1] == "\x01" :
        # Client is Reading a file from the server
        session_request = "RRQ"
        logging.debug("RRQ received, mode %s" % mode)
        txtinfo=txtinfo + "Sending file :\n%s" % filename
        # Make the first packet
        blkcount=increment_blockcount(blkcount)
        data="\x00\x03"+blkcount[1]+fp.read(blksize)
        logging.info("%s requested by %s" % (filename, startaddr[0]))
    if startdata[1] == "\x02" :
        # Client is Writing a file to the server
        session_request = "WRQ"
        logging.debug("WRQ received, mode %s" % mode)
        txtinfo=txtinfo + "Receiving file :\n%s" % filename
        # Make an acknowledgement packet
        data="\x00\x04"+blkcount[1]
        logging.info("%s to be sent by %s" % (filename, startaddr[0]))
    return


def recv_RRQ_data(rx_data):
    """ Received a RRQ ack packet, check its block count
        and if ok, send the next block of data"""
    global fp
    global data
    global TTLtimer
    global changetxtinfo
    global txtinfo
    global tftpsession_flag
    global session_request
    global filename
    global transmitting
    global timed_out
    global lastpacket
    global changebarinfo
    global barinfo
    global blkcount
    # is packet ok
    # Check opcode is 4
    rx_opcode=rx_data[:2]
    if rx_opcode != "\x00\x04" : return
    # Check blockcount is ok
    rx_blkcount=rx_data[2:4]
    if blkcount[1] != rx_blkcount : return
    # Received ack packet ok
    TTLtimer.stop()
    # Either this was the last packet, or another data
    # packet needs to be made
    # First check - is this the last packet?
    if lastpacket==2:
        # It is, so end the session
        changetxtinfo=1
        txtinfo="Transfer of file :\n\n%s\n\ncompleted." % filename
        logging.info("Transfer of file %s completed." % filename)
        reset_globals()
        return
    # Its not the last packet - so make a data packet
    blkcount=increment_blockcount(blkcount)
    payload=fp.read(blksize)
    if len(payload) < blksize:
        # End of session
        fp.close()
        fp=None
        lastpacket=2
    else:
        changebarinfo=1
        barinfo += 1
        if barinfo >= 100:
            barinfo=1
    if payload == "":
        data="\x00\x03"+blkcount[1]
    else:
        data="\x00\x03"+blkcount[1]+payload
    transmitting=1
    timed_out=0
    return
      
def recv_WRQ_data(rx_data):
    """ Received a WRQ data packet, check its block count
        and save contents to file"""
    global fp
    global data
    global TTLtimer
    global changetxtinfo
    global txtinfo
    global tftpsession_flag
    global session_request
    global filename
    global transmitting
    global timed_out
    global lastpacket
    global changebarinfo
    global barinfo
    global blkcount
    # is packet ok
    # Check opcode is 3
    rx_opcode=rx_data[:2]
    if rx_opcode != "\x00\x03" : return
    # Check blockcount has incremented
    new_blkcount=increment_blockcount(blkcount)
    rx_blkcount=rx_data[2:4]
    if new_blkcount[1] != rx_blkcount : return
    blkcount=new_blkcount
    payload=rx_data[4:]
    # Received packet ok so make an acknowledgement packet
    TTLtimer.stop()
    data="\x00\x04"+blkcount[1]
    # flag this is to be transmitted, and set timed_out flag to zero
    transmitting=1
    timed_out=0
    if (len(payload)<blksize):
        # End the session, but set lastpacket to 1 , allowing the last
        # acknowledgement to be transmitted
        if len(payload)>0:
            fp.write(payload)
        changetxtinfo=1
        txtinfo="Transfer of file :\n\n%s\n\ncompleted." % filename
        fp.close()
        fp=None
        logging.info("Transfer of file %s completed." % filename)
        lastpacket=1
        return
    # Write the received data to file
    fp.write(payload)
    # and set the status bar
    changebarinfo=1
    barinfo += 1
    if barinfo >= 100:
        barinfo=1
    return

def send_error():
    """ create an error packet to send"""
    global fp
    global data
    global TTLtimer
    global changetxtinfo
    global txtinfo
    global tftpsession_flag
    global transmitting
    global timed_out
    global lastpacket
    changetxtinfo=1
    txtinfo="ERROR: Transfer Aborted."
    logging.error("Transfer Aborted")
    if fp:
        fp.close()
        fp=None
    lastpacket=1
    timed_out=0
    transmitting=1
    # set data to be an error value
    data="\x00\x05\x00\x00Terminated due to timeout\x00"
    
    
def error_ocurred(errortext):
    """Error ocurred, drop the call and set error text"""
    global changetxtinfo
    global txtinfo
    changetxtinfo=1
    txtinfo=errortext
    logging.error(errortext)
    reset_globals()
    return


def increment_blockcount(blkcount):
    """blkcount is a list, index 0 is blkcount_int holding
       the integer value of the blockcount and index 1 is the
       two byte string holding the hex value of the blockcount.
       This function increments both, taking care to rollover,
       and returns the new blkcount list."""
    blkcount_int=blkcount[0]+1
    if blkcount_int>65535: blkcount_int=0
    blkcount_hex=chr(blkcount_int/256) + chr(blkcount_int%256)
    new_blkcount=[blkcount_int, blkcount_hex]
    return new_blkcount

def start_logging(setupdict):
    """Set up and start the logging"""
    global rootLogger
    global LogHandler
    # set a format
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    # create a FileHandler
    logfile=os.path.join(setupdict["logfolder"],"tftplog")    
    LogHandler = logging.FileHandler(logfile, "a")
    # tell the handler to use the format
    LogHandler.setFormatter(formatter)
    # add the handler to the root logger
    rootLogger.addHandler(LogHandler)
    logging.info("TFTP server started on port %s" % setupdict["port"])
    
def stop_logging():
    """Stop the logging"""
    global rootLogger
    global LogHandler
    logging.info("TFTP server stopped")
    rootLogger.removeHandler(LogHandler)
    