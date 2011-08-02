####### TFTPgui #######
#
# tftp_engine.py  - runs the tftp server for TFTPgui
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
tftp_engine.py - runs the TFTP server for TFTPgui

Normally imported by tftpgui.py which creates an instance
of the ServerState class defined here, and then calls the
function engine_loop - which loops continuously running
the server.

The ServerState class is called with argument 'serving',
followed by a dictionary of configuration values taken
from the configuration file.

The instance 'serving' attribute is initially set to the
serving argument given (which is True or False), the attribute
can then be set at anytime to turn listenning on or off.

The engine loop is then called with arguments:
engine_loop(server, nogui)
server being the instance of the ServerState class created, and nogui
should be True if no GUI is being run, or False if a GUI is run.

Call the shutdown() method of the ServerState instance to completely
shut down the server and exit the loop.

The remaining classes are only used within this module.
"""

import os, time, asyncore, socket, logging, logging.handlers, string

from tftp_package import ipv4_parse

# CONNECTIONS is a dictionary of current connections
# the keys are address tuples, the values are connection objects
# start off with an empty dictionary 
CONNECTIONS = {}

def add_connection(connection):
    "Adds the given connection to the connection dictionary"
    global CONNECTIONS
    if connection.rx_addr not in CONNECTIONS:
        CONNECTIONS[connection.rx_addr] = connection

def del_connection(connection):
    """Deletes the given connection from the connection dictionary"""
    global CONNECTIONS
    if connection.rx_addr not in CONNECTIONS:
        return
    del CONNECTIONS[connection.rx_addr]


class DropPacket(Exception):
    """Raised to flag the packet should be dropped"""
    pass


class ServerState(object):
    """Defines a class which records the current server state
       and produces logs, and a text attribute for a gui"""

    def __init__(self, cfgdict, serving=False):
        """Creates a class which defines the state of the server
           serving = True if the server is to start up listenning
           Subsequently setting the serving attribute turns on
           and off the server.
           cfgdict is a dictionary read from the config file
             tftprootfolder  - path to a folder
             logfolder       - path to a folder
             anyclient       - 1 if any client can call, 0 if only from a specific subnet
             clientipaddress - specific subnet ip address of the client
             clientmask      - specific subnet mask of the client
             listenport      - tftp port to listen on
             listenipaddress - address to listen on"""
        # set attributes from the dictionary, use assert to ensure
        # all attributes are present
        assert self.set_from_config_dict(cfgdict)

        self.serving = serving
        self.engine_available = True

        # The attribute self.text is read by the gui at regular intervals
        # and displayed to give server status messages
        self.text = """TFTPgui - a free tftp Server

Version\t:  TFTPgui 3.0
Author\t:  Bernard Czenkusz
Web site\t:  www.skipole.co.uk
License\t:  GPLv3

"""
        if serving:
            self.text += "Press Stop to disable the tftp server"
        else:
            self.text += "Press Start to enable the tftp server"

        # create logger
        self.logging_enabled = True
        try:
            # Dont want a logging failure to stop the server
            self.rootLogger = logging.getLogger('')
            self.rootLogger.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
            logfile=os.path.join(self.logfolder,"tftplog")
            self.loghandler = logging.handlers.RotatingFileHandler(logfile,
                                                    maxBytes=20000, backupCount=5)
            self.loghandler.setFormatter(formatter)
            self.rootLogger.addHandler(self.loghandler)
        except Exception:
            self.logging_enabled = False

    def log_exception(self, e):
        "Used to log exceptions"
        if self.logging_enabled:
            try:
                logging.exception(e)
            except Exception:
                self.log_disable()

    def log_disable(self):
        "close the logger"
        if self.logging_enabled:
            try:
                self.rootLogger.removeHandler(self.loghandler)
            except Exception:
                pass
        self.logging_enabled = False

    def add_text(self, text_line, clear=False):
        """Adds text_line to the log, and also to self.text,
           which is used by the gui interface - adds the line to
           the text, keeping a maximum of 12 lines.
           If clear is True, deletes previous lines, making text
           equal to this text_line only"""

        if len(text_line)>100:
            # limit to 100 characters
            text_line = text_line[:100]
        # strip non-printable characters, as this is to be displayed on screen
        text_line = ''.join([char for char in text_line if char in string.printable])

        if self.logging_enabled:
            try:
                logging.info(text_line)
            except Exception:
                self.log_disable()

        if clear:
            self.text = text_line
            return
        text_list = self.text.splitlines()
        if not text_list:
            self.text = text_line
            return
        if len(text_list) > 12:
            # remove first line
            text_list.pop(0)
        text_list.append(text_line)
        self.text = "\n".join(text_list)

    def get_connections(self):
        """If connections are needed, they are available via this method
           CONNECTIONS is a dictionary of current connections
           the keys are address tuples, the values are connection objects"""
        return CONNECTIONS

    def get_config_dict(self):
        "Returns a dictionary of the config attributes"
        cfgdict = { "tftprootfolder":self.tftprootfolder,
                    "logfolder":self.logfolder,
                    "anyclient":self.anyclient,
                    "clientipaddress":self.clientipaddress,
                    "clientmask":self.clientmask,
                    "listenport":self.listenport,
                    "listenipaddress":self.listenipaddress}
        return cfgdict

    def set_from_config_dict(self, cfgdict):
        """Sets attributes from a given dictionary
           Returns True if all attributes supplied, or False if not"""
        all_attributes = True
        if "logfolder" in cfgdict:
            self.logfolder = cfgdict["logfolder"]
        else:
            all_attributes = False
        if "tftprootfolder" in cfgdict:
            self.tftprootfolder = cfgdict["tftprootfolder"]
        else:
            all_attributes = False
        if "anyclient" in cfgdict:
            self.anyclient = cfgdict["anyclient"]
        else:
            all_attributes = False
        if "clientipaddress" in cfgdict:
            self.clientipaddress = cfgdict["clientipaddress"]
        else:
            all_attributes = False
        if "clientmask" in cfgdict:
            self.clientmask = cfgdict["clientmask"]
        else:
            all_attributes = False
        if "listenport" in cfgdict:
            self.listenport = cfgdict["listenport"]
        if "listenipaddress" in cfgdict:
            if cfgdict["listenipaddress"] == "0.0.0.0":
                self.listenipaddress = ""
            else:
                self.listenipaddress = cfgdict["listenipaddress"]
        else:
            all_attributes = False
        return all_attributes

    def shutdown(self):
        "Shuts down the server"
        global CONNECTIONS
        # remove all connections from CONNECTIONS
        for connection in CONNECTIONS.values():
            connection.shutdown()
        CONNECTIONS = {}
        self.serving = False
        self.engine_available = False
        self.add_text("TFTPgui application stopped")
        self.log_disable()     


class STOPWATCH_ERROR(Exception):
    """time_it should only be called if start has been called first."""
    pass

class Stopwatch(object):
    """stopwatch class calculates the TTL - the time to live in seconds
    
    The start() method should be called, each time a packet is transmitted
    which expects a reply, and then the time_it() method should be called
    periodically while waiting for the reply.
    If  time_it() returns True, then the time is still within the TTL - 
    so carry on waiting.
    If time_it() returns False, then the TTL has expired and the calling
    program needs to do something about it.
    When a packet is received, the calling program should call the
    stop() method - this then calculates the average round trip
    time (aveRTT), and a TTL of three times the aveRTT.
    TTL is  a minimum of 0.5 secs, and a maximum of 5 seconds.
    Methods: 
      start() to start  the stopwatch
      stop() to stop the stopwatch, and update aveRTT and TTL
      time_it() return True if the time between start and time_it is less than TTL
      return False if it is greater
    Exceptions:
        STOPWATCH_ERROR is raised by time_it() if is called without
        start() being called first - as the stopwatch must be running
        for the time_it measurement to have any validity
      """
      
    def __init__(self):
        # initial starting values
        self.RTTcount=1
        self.TotalRTT=0.5
        self.aveRTT=0.5
        self.TTL=1.5
        self.rightnow=0.0
        self.started=False
       
    def start(self):
        self.rightnow=time.time()
        self.started=True
        
    def stop(self):
        if not self.started: return
        # Calculate Round Trip Time (RTT)            
        RTT=time.time()-self.rightnow
        if RTT == 0.0 :
            # Perhaps the time() function on this platform is not
            # working, or only times to whole seconds. If this is the case
            # assume an RTT of 0.5 seconds
            RTT=0.5
        # Avoid extreme values
        RTT=min(3.0, RTT)
        RTT=max(0.01, RTT)
        # Calculate average Round Trip time
        self.TotalRTT += RTT
        self.RTTcount += 1
        self.aveRTT=self.TotalRTT/self.RTTcount
        # Don't let TotalRTT and RTTcount increase indefinetly
        # after twenty measurements, reset TotalRTT to five times
        # the aveRTT
        if self.RTTcount > 20:
            self.TotalRTT = 5.0*self.aveRTT
            self.RTTcount=5
        # Also limit aveRTT from increasing too much 
        if self.aveRTT>2.0:
            self.TotalRTT=10.0
            self.RTTcount=5
            self.aveRTT=2.0
        # And make Time To Live (TTL) = 3 * average RTT
        # with a maximum of 5 seconds, and a minimum of 0.5 seconds
        self.TTL=3.0*self.aveRTT
        self.TTL=min(5.0, self.TTL)
        self.TTL=max(0.5, self.TTL)
        # and finally flag that the stopwatch has been stopped
        self.started=False
    
    def time_it(self):
        """Called to check time is within TTL, if it is, return True
           If not, started attribute is set to False, and returns False"""
        if not self.started: raise STOPWATCH_ERROR
        deltatime=time.time()-self.rightnow
        if deltatime<=self.TTL :
            return True
        # increase the TTL in case the timeout was due to
        # excessive network delay
        self.aveRTT += 0.5
        self.aveRTT=min(2.0, self.aveRTT)
        self.TotalRTT = 5.0*self.aveRTT
        self.RTTcount=5
        self.TTL=3.0*self.aveRTT
        self.TTL=min(5.0, self.TTL)
        self.TTL=max(0.5, self.TTL)
        # Also a timeout will stop the stopwatch
        self.started=False
        return False


class NoService(Exception):
    """Raised to flag the service is unavailable"""
    pass

class TFTPserver(asyncore.dispatcher):
    """Class for binding the tftp listenning socket
       asyncore.poll will call the handle_read method whenever data is
       available to be read, and handle_write to see if data is to be transmitted"""
    def __init__(self, server):
        """Bind the tftp listener to the address given in server.listenipaddress
           and port given in server.listenport"""
        asyncore.dispatcher.__init__(self)
        self.server = server
        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
        # list of connections to test for sending data
        self.connection_list = []
        # current connection sending data
        self.connection = None
        try:
            self.bind((server.listenipaddress, server.listenport))
        except Exception as e:
            server.log_exception(e)
            if server.listenipaddress:
                server.text = """Failed to bind to %s : %s
Possible reasons:
Check this IP address exists on this server.
(Try with 0.0.0.0 set as the 'listenipaddress'
in the configuration file which binds to any
server address.)"""  % (server.listenipaddress, server.listenport)
            else:
                server.text = "Failed to bind to port %s." % server.listenport
            
            server.text += """
Check you do not have another service listenning on
this port (you may have a tftp daemon already running).
Also check your user permissions allow you to open a
socket on this port."""
            if os.name == "posix" and server.listenport<1000 and os.geteuid() != 0:
                server.text += "\n(Ports below 1000 may need root or administrator privileges.)"
            server.text += "\nFurther error details will be given in the logs file."
            raise NoService

    def handle_read(self):
        """Handle incoming data - Checks if this is an existing connection,
           if not, creates a new connection object and adds it to global
           CONNECTIONS dictionary.
           If it is, then calls the connection object incoming_data method
           for that object to handle it"""
        global CONNECTIONS
        # buffer size of 4100 is given, when negotiating block size, only sizes
        # less than 4100 will be accepted
        rx_data, rx_addr = self.recvfrom(4100)
        # rx_data is a bytes sequence
        if len(rx_data)>4100:
            raise DropPacket
        try:
            if rx_addr not in CONNECTIONS:
                # This is not an existing connection, so must be
                # a new first packet from a client.
                # check first two bytes of rx_data
                # should be 0001 or 0002
                if rx_data[0] != 0:
                    raise DropPacket
                if rx_data[1] == 1 :
                    # Client is reading a file from the server
                    # create a SendData connection object and add it to
                    # the global CONNECTIONS dictionary
                    connection = SendData(self.server, rx_data, rx_addr)
                    add_connection(connection)
                elif rx_data[1] == 2 :
                    # Client is sending a file to the server
                    # create a ReceiveData connection object and add it to
                    # the global CONNECTIONS dictionary
                    connection = ReceiveData(self.server, rx_data, rx_addr)
                    add_connection(connection)
                else:
                    # connection not recognised, just drop it
                    raise DropPacket
            else:
                # This is an existing connection
                # let the appropriate connection class handle it
                # via its incoming_data method
                CONNECTIONS[rx_addr].incoming_data(rx_data)
        except DropPacket:
            # packet invalid in some way, drop it
            pass

    def handle_write(self):
        """Check connections, if one has data to send, send it
           keep sending until no more on that connection, then on next call to
           this function, try the next connection"""
        global CONNECTIONS
        # self.connection is the current connection sending data
        # self.connection_list is a list of the connections,
        # test each in turn, popping the connection from the list
        # until none are left, then renew self.connection_list from
        # CONNECTIONS - this is done to ensure each connection is
        # handled in turn, and if CONNECTIONS is updated while one
        # is being dealt with, any new connections are tested after
        # the current ones in the list.
        if not self.connection:
            # get the next connection in the list
            if not self.connection_list:
                # but if no list, renew it now
                self.connection_list = list(CONNECTIONS.values())
            if not self.connection_list:
                # no available connections, just return
                return
            # so one or more connections exist in the list
            # get a connection, and remove it from the list
            self.connection = self.connection_list.pop()
        if self.connection.expired or not self.connection.tx_data:
            self.connection = None
            return
        # so current connection has data to send, send it
        self.connection.send_data(self.sendto)
        # And if all data sent, or connection shutdown
        if self.connection.expired or not self.connection.tx_data:
            self.connection = None
            return


    def handle_connect(self):
        pass
        
    def handle_error(self):
        pass


# opcode   operation
# 1         Read request           (RRQ)
# 2         Write request          (WRQ)
# 3         Data                   (DATA)
# 4         Acknowledgement        (ACK)
# 5         Error                  (ERROR)
# 6         Option Acknowledgement (OACK)

class Connection(object):
    """Stores details of a connection, acts as a parent to
       SendData and ReceiveData classes"""

    def __init__(self, server, rx_data, rx_addr):
        "New connection, check header"
        # check if the caller is from an allowed address
        if not server.anyclient :
            if not ipv4_parse.IsAddressInSubnet(rx_addr[0],
                                                server.clientipaddress,
                                                server.clientmask):
                # The caller ip address is not within the subnet as defined by the
                # clientipaddress and clientmask
                raise DropPacket
        if len(rx_data)>512:
            raise DropPacket
        # Check header
        if rx_data[0] != 0:
            raise DropPacket
        if (rx_data[1] != 1) and (rx_data[1] != 2):
            raise DropPacket
        ### parse the filename received from the client ###
        # split the remaining rx_data into filename and mode
        parts=rx_data[2:].split(b"\x00")
        if len(parts) < 2:
            raise DropPacket
        self.filename=str(parts[0], encoding='ascii')
        self.mode=parts[1].lower()
        # mode must be "netascii" or "octet"
        if ((self.mode != b"netascii") and (self.mode != b"octet")):
            raise DropPacket
        # filename must be at least one character, and at most 256 characters long
        if (len(self.filename) < 1) or (len(self.filename)>256):
            raise DropPacket
         # filename must not start with a . character
        if self.filename[0] == ".":
            raise DropPacket
        # if filename starts with a \ or a / - strip it off
        if self.filename[0] == "\\" or self.filename[0] == "/":
            if len(self.filename) == 1:
                raise DropPacket
            self.filename=self.filename[1:]
        # filename must not start with a . character
        if self.filename[0] == ".":
            raise DropPacket    
        # The filename should only contain the printable characters, A-Z a-z 0-9 -_ or .
        # Temporarily replace any instances of the ._- characters with "x"
        temp_filename=self.filename.replace(".", "x")
        temp_filename=temp_filename.replace("-", "x")
        temp_filename=temp_filename.replace("_", "x")
        # Check all characters are alphanumeric
        if not temp_filename.isalnum():
            raise DropPacket
        # Check this filename is not being altered by a ReceiveData connection
        for conn in CONNECTIONS.values():
            if self.filename == conn.filename and isinstance(conn, ReceiveData):
                raise DropPacket
        # so self.filename is the file to be acted upon, set the filepath
        self.filepath=os.path.join(server.tftprootfolder,self.filename)
        # check header for options
        self.request_options = {}
        self.options = {}
        self.tx_data = None

        # Set block size
        self.blksize = 512

        try:
            # Get any tftp options
            if not parts[-1]:
                # last of parts will be an empty string, remove it
                parts.pop(-1)
            if len(parts)>3 and not (len(parts) % 2):
                # options exist, and the number of parts is even
                # set the transmit packet to acknowledge the handled options
                self.tx_data = b"\x00\x06"
                option_parts = parts[2:]
                # option_parts should be option, value, option, value etc..
                # put these into the self.request_options dictionary
                for index, opt in enumerate(option_parts):
                    if not (index % 2):
                        str_option = str(opt, encoding='ascii')
                        str_value = str(option_parts[index+1], encoding='ascii')
                        # add to dictionary
                        self.request_options[str_option.lower()] = str_value.lower()
                # self.request_options dictionary is now a dictionary of options requested
                # from the client, make another dictionary, self.options of those options
                # that this server will support
                # check if blksize is in there
                if "blksize" in self.request_options:
                    blksize = int(self.request_options["blksize"])
                    if blksize > 4096:
                        blksize = 4096
                    if blksize>7:
                        # This server only allows blocksizes up to 4096
                        self.blksize = blksize
                        self.tx_data += b"blksize\x00" + bytes(str(blksize),encoding="ascii") + b"\x00"
                        self.options["blksize"] = str(blksize)
                # elif "nextoption" in self.options:
                    # for each further option to be implemented, use an elif chain here
                    # and add the option name and value to tx_data
                if not self.options:
                    # No options recognised
                    self.tx_data = None
        except Exception:
            # On any failure, ignore all options
            self.blksize = 512
            self.options = {}
            self.tx_data = None
 
        # This connection_time is updated to current time every time a packet is
        # sent or received, if it goes over 30 seconds, something is wrong
        # and so the connection is terminated
        self.connection_time=time.time()
        # The second value in this blockcount is incremented for each packet
        self.blkcount=[0, b"\x00\x00", 0]
        # fp is the file pointer used to read/write to disc
        self.fp = None
        self.server = server
        self.rx_addr = rx_addr
        self.rx_data = rx_data
        # expired is a flag to indicate to the engine loop that this
        # connection should be removed from the CONNECTIONS list
        self.expired = False
        # tx_data is the data to be transmitted
        # and re_tx_data is a copy in case a re-transmission is needed
        self.re_tx_data = self.tx_data
        # This timer is used to measure if a packet has timed out, it
        # increases as the round trip time increases
        self.timer = Stopwatch()
        self.timeouts = 0
        self.last_packet = False


    def increment_blockcount(self):
        """blkcount is a list, index 0 is blkcount_int holding
           the integer value of the blockcount which rolls over at 65535
           index 1 is the two byte string holding the hex value of blkcount_int.
           index 2 is blkcount_total which holds total number of blocks
           This function increments them all."""
        blkcount_total=self.blkcount[2]+1
        blkcount_int=self.blkcount[0]+1
        if blkcount_int>65535: blkcount_int=0
        blkcount_hex=bytes([blkcount_int//256, blkcount_int%256])
        self.blkcount=[blkcount_int, blkcount_hex, blkcount_total]


    def send_data(self, tftp_server_sendto):
        "send any data in self.tx_data, using dispatchers sendto method"
        if self.expired or not self.tx_data:
            return
        # about to send data
        # re-set connection time to current time
        self.connection_time=time.time()
        # send the data
        sent=tftp_server_sendto(self.tx_data, self.rx_addr)
        if sent == -1:
            # Problem has ocurred, drop the connection
            self.shutdown()
            return
        self.tx_data=self.tx_data[sent:]
        if not self.tx_data:
            # All data has been sent
            # if this is the last packet to be sent, shutdown the connection
            if self.last_packet:
                self.shutdown()
            else:
                # expecting a reply, so start TTL timer
                self.timer.start()


    def poll(self):
        """Polled by the main loop.
           Checks connection is no longer than 30 seconds between packets.
           Checks TTL timer, resend on timeouts, or if too many timeouts
           send an error packet and flag last_packet as True"""
        if time.time()-self.connection_time > 30.0:
            # connection time has been greater than 30 seconds
            # without a packet sent or received, something is wrong
            self.server.add_text("Connection from %s:%s timed out" % self.rx_addr)
            self.shutdown()
            return
        if self.expired:
            return
        if self.tx_data or not self.timer.started:
            # Must be sending data, so nothing to check
            return
        # no tx data and timer has started, so waiting for a packet
        if self.timer.time_it():
            # if True, still within TTL, so ok
            return
        # Outside of TTL, timeout has occurred, send an error
        # if too many have occurred or re-send last packet
        self.timeouts += 1
        if self.timeouts <= 3:
            # send a re-try
            self.tx_data=self.re_tx_data
            return
        # Tried four times, give up and set data to be an error value
        self.tx_data=b"\x00\x05\x00\x00Terminated due to timeout\x00"
        self.server.add_text("Connection to %s:%s terminated due to timeout" % self.rx_addr)
        # send and shutdown, don't wait for anything further
        self.last_packet = True


    def shutdown(self):
        """Shuts down the connection by closing the file pointer and
           setting the expired flag to True.
           The engine loop will then remove this instance from the CONNECTIONS
           list and it will be garbage collected."""            
        if self.fp:
            self.fp.close()
        self.expired = True
        self.tx_data=""

    def __str__(self):
        "String value of connection, for diagnostic purposes"
        str_list = "%s %s" % (self.rx_addr, self.blkcount[2])
        return str_list



class SendData(Connection):
    """A connection which handles file sending
       the client is reading a file, the connection is of type RRQ"""
    def __init__(self, server, rx_data, rx_addr):
        Connection.__init__(self, server, rx_data, rx_addr)
        if rx_data[1] != 1 :
            raise DropPacket
        if not os.path.exists(self.filepath) or os.path.isdir(self.filepath):
            server.add_text("%s requested %s: file not found" % (rx_addr[0], self.filename))
            # Send an error value
            self.tx_data=b"\x00\x05\x00\x01File not found\x00"
            # send and shutdown, don't wait for anything further
            self.last_packet = True
            return
        # Open file for reading
        try:
            if self.mode == b"octet":
                self.fp=open(self.filepath, "rb")
            elif self.mode == b"netascii":
                self.fp=open(self.filepath, "r")
            else:
                raise DropPacket
        except IOError as e:
            server.add_text("%s requested %s: unable to open file" % (rx_addr[0], self.filename))
            # Send an error value
            self.tx_data=b"\x00\x05\x00\x02Unable to open file\x00"
            # send and shutdown, don't wait for anything further
            self.last_packet = True
            return
        server.add_text("Sending %s to %s" % (self.filename, rx_addr[0]))
        # If True this flag indicates shutdown on the next received packet 
        self.last_receive = False
        # If self.tx_data has contents, this will be because the parent Connections
        # class is acknowledging an option
        # If there is nothing in self.tx_data, get the first payload
        if not self.tx_data:
            # Make the first packet, call get_payload to put the data into tx_data
            self.get_payload()


    def get_payload(self):
        """Read file, a block of self.blksize bytes at a time which is put
           into re_tx_data and tx_data."""
        assert not self.last_receive
        payload=self.fp.read(self.blksize)
        if len(payload) < self.blksize:
            # The file is read, and no further data is available
            self.fp.close()
            self.fp = None
            bytes_sent = self.blksize*self.blkcount[2] + len(payload)
            self.server.add_text("%s bytes of %s sent to %s" % (bytes_sent, self.filename, self.rx_addr[0]))
            # shutdown on receiving the next ack
            self.last_receive = True
        self.increment_blockcount()
        self.re_tx_data=b"\x00\x03"+self.blkcount[1]+payload
        self.tx_data=self.re_tx_data


    def incoming_data(self, rx_data):
        """Handles incoming data - these should be acks from the client
           for each data packet sent"""
        if self.expired:
            return
        # if timer hasn't started, we may be in the process of sending
        if self.tx_data or not self.timer.started:
            return
        if rx_data[0] != 0:
            # All packets should start 00, so ignore it
            return
        # This should be either an ack, or an error
        # Check if an error packet is received
        if rx_data[1] == 5 :
            # Its an error packet, log it and drop the connection
            try:
                if len(rx_data[4:]) > 1  and len(rx_data[4:]) < 255:
                    # Error text available
                    error_text = str(rx_data[4:-1], encoding="ascii")
                    self.server.add_text("Error from %s:%s code %s : %s" % (self.rx_addr[0],
                                                                       self.rx_addr[1],
                                                                       rx_data[3],
                                                                       error_text))
                else:
                    # No error text
                    self.server.add_text("Error from %s:%s code %s" % (self.rx_addr[0],
                                                                  self.rx_addr[1],
                                                                  rx_data[3]))
            except Exception:
                # If error trying to read error type, just ignore
                pass
            self.shutdown()
            return
        if rx_data[1] != 4 :
            # Should be 04, if not ignore it
            return
        # So this is an ack
        # Check blockcount is ok
        rx_blkcount=rx_data[2:4]
        if self.blkcount[1] != rx_blkcount:
            # wrong blockcount, ignore it
            return
        # Received ack packet ok
        # re-set connection time to current time
        self.connection_time=time.time()
        # re-set any timouts
        self.timeouts = 0
        self.timer.stop()
        if self.last_receive:
            # file is fully read and sent, so shutdown
            self.shutdown()
            return
        # Must create another packet to send
        self.get_payload()
        

class ReceiveData(Connection):
    """A connection which handles file receiving
       the client is sending a file, the connection is of type WRQ"""
    def __init__(self, server, rx_data, rx_addr):
        Connection.__init__(self, server, rx_data, rx_addr)
        if rx_data[1] != 2 :
            raise DropPacket
        if os.path.exists(self.filepath):
            server.add_text("%s trying to send %s: file already exists" % (rx_addr[0], self.filename))
            # Send an error value
            self.tx_data=b"\x00\x05\x00\x06File already exists\x00"
            # send and shutdown, don't wait for anything further
            self.last_packet = True
            return
        # Open filename for writing
        try:
            if self.mode == b"octet":
                self.fp=open(self.filepath, "wb")
            elif self.mode == b"netascii":
                self.fp=open(self.filepath, "w")
            else:
                raise DropPacket
        except IOError as e:
            server.add_text("%s trying to send %s: unable to open file" % (rx_addr[0], self.filename))
            # Send an error value
            self.tx_data=b"\x00\x05\x00\x02Unable to open file\x00"
            # send and shutdown, don't wait for anything further
            self.last_packet = True
            return
        server.add_text("Receiving %s from %s" % (self.filename, rx_addr[0]))
        # Create next packet
        # If self.tx_data has contents, this will be because the parent Connections
        # class is acknowledging an option
        # If there is nothing in self.tx_data, create an acknowledgement
        if not self.tx_data:
            self.re_tx_data=b"\x00\x04"+self.blkcount[1]
            self.tx_data=self.re_tx_data


    def incoming_data(self, rx_data):
        """Handles incoming data, these should contain the data to be saved to a file"""
        if self.expired:
            return
        # if timer hasn't started, we may be in the process of sending
        if self.tx_data or not self.timer.started:
            return
        if rx_data[0] != 0:
            # All packets should start 00, so ignore it
            return
        # This should be either data, or an error
        # Check if an error packet is received
        if rx_data[1] == 5:
            # Its an error packet, log it and drop the connection
            try:
                if len(rx_data[4:]) > 1  and len(rx_data[4:]) < 255:
                    # Error text available
                    error_text = str(rx_data[4:-1], encoding="ascii")
                    self.server.add_text("Error from %s:%s code %s : %s" % (self.rx_addr[0],
                                                                       self.rx_addr[1],
                                                                       rx_data[3],
                                                                       error_text))
                else:
                    # No error text
                    self.server.add_text("Error from %s:%s code %s" % (self.rx_addr[0],
                                                                  self.rx_addr[1],
                                                                  rx_data[3]))
            except Exception:
                # If error trying to read error type, just ignore
                pass
            self.shutdown()
            return
        if rx_data[1] != 3:
            # Should be 03, if not ignore it
            return
        # Check blockcount has incremented
        old_blockcount = self.blkcount
        self.increment_blockcount()
        rx_blkcount=rx_data[2:4]
        if self.blkcount[1] != rx_blkcount:
            # Blockcount mismatch, ignore it
            self.blkcount = old_blockcount
            return
        # re-set any timouts
        self.timeouts = 0
        self.timer.stop()
        if len(rx_data) > self.blksize+4:
            # received data too long
            self.tx_data=b"\x00\x05\x00\x04Block size too long\x00"
            # send and shutdown, don't wait for anything further
            self.last_packet = True
            return
        payload=rx_data[4:]
        # Received packet ok
        # Make an acknowledgement packet
        self.re_tx_data=b"\x00\x04"+self.blkcount[1]
        self.tx_data=self.re_tx_data
        # Write the received data to file
        if len(payload)>0:
            self.fp.write(payload)
        if len(payload)<self.blksize:
            # flag all data is written and this ack is the last packet
            self.last_packet = True
            self.fp.close()
            self.fp=None
            bytes_sent = self.blksize*old_blockcount[2] + len(payload)
            self.server.add_text("%s bytes of %s received from %s" % (bytes_sent, self.filename, self.rx_addr[0]))


#### The engine loop ####

def engine_loop(server, nogui):
    """This loop runs while server.engine_available is True.
       If the server is in listenning mode (server.serving True),
       it creates the TFTPserver instance which is an
       asyncore.dispatcher object.
       This TFTPserver creates connections and stores them in the
       global CONNECTIONS dictionary as new calls come in.
       This engine then loops - each time calling asyncore.poll() and for each
       connection object in CONNECTIONS it calls its poll() method,
       which checks the connection timers.
       It also checks for expired connections and removes them from CONNECTIONS.
       If server.serving becomes False, it calls close on the TFTPserver, clears
       the CONNECTIONS dictionary and then goes into a sleep loop, until
       server.serving becomes True again.
       """
    global CONNECTIONS
    CONNECTIONS = {}
    tftp_server = None
    try:
        while server.engine_available:
            if server.serving:
                # start server
                try:
                    tftp_server = TFTPserver(server)
                except NoService:
                    # Failed to start the server
                    server.serving = False
                    if nogui:
                        # Stop the service with an error message
                        print(server.text)
                        raise
                else:
                    # The tftp server is now listenning
                    if server.listenipaddress:
                        server.add_text(("Listenning on %s:%s" % (server.listenipaddress, server.listenport)), clear=True)
                    else:
                        server.add_text(("Listenning on port %s" % server.listenport), clear=True)
            # engine loop continues while the engine is available
            while server.engine_available and server.serving:
                # This loop runs while the engine is serving
                asyncore.poll()
                # Poll each connection to see if it is ready to send anything
                connection_list = list(CONNECTIONS.values())
                for connection in connection_list:
                    connection.poll()
                    asyncore.poll()
                # If any connection has expired, remove it from CONNECTIONS
                for connection in connection_list:
                    if connection.expired:
                        del_connection(connection)
                # make sure no reference is kept to old connections,
                # so they can be garbage collected
                connection_list = None
            # server no longer running, stop listening
            if tftp_server != None:
                tftp_server.close()
                tftp_server = None
                server.add_text("Server stopped")
            # remove all connections from connection list
            for connection in CONNECTIONS.values():
                connection.shutdown()
            CONNECTIONS = {}
            while server.engine_available and not server.serving:
                # This loop runs while the engine is not serving
                time.sleep(0.25)
    except Exception as e:
        # log the exception and exit the main loop
        server.log_exception(e)
        return 1
    except KeyboardInterrupt:
        # The loop has been manually stopped, exit the program
        return 0
    finally:
        # shutdown the server
        server.shutdown()   
    return 0
