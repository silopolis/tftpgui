#!/usr/bin/env python
#
# tftpcfg.py
#
# Version : 1.0
# Date : 20070221
#
# Author : Bernard Czenkusz
# Email  : bernie@skipole.co.uk

#
# tftpcfg.py - Parse and store config values for TFTPgui
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

"""This module provides functions to parse and store
config information for the TFTPgui program

It stores setup values in the file tftpgui.cfg, and
via function getconfig() it returns a dictionary of
the setup values, these being:

 tftprootfolder  - path to a folder
 logfolder       - path to a folder
 anysource       - 1 if any source can call, 0 if only from a specific subnet
 ipaddress       - specific subnet ip address
 mask            - specific subnet mask
 port            - tftp port used
"""

import ConfigParser
import os
import ipv4_parse
import sys

# Default global variables
SCRIPTDIRECTORY=os.path.abspath(os.path.dirname(sys.argv[0]))
CONFIGFILE=os.path.join(SCRIPTDIRECTORY,'tftpgui.cfg')
TFTPROOTFOLDER=os.path.join(SCRIPTDIRECTORY,'tftproot')
LOGFOLDER=os.path.join(SCRIPTDIRECTORY,'tftplogs')

def setdefaults():
    cfgdefault={}
    cfgdefault["tftprootfolder"]=TFTPROOTFOLDER
    cfgdefault["logfolder"]=LOGFOLDER
    cfgdefault["anysource"]="1"
    cfgdefault["ipaddress"]="192.168.0.0"
    cfgdefault["mask"]="16"
    cfgdefault["port"]="69"
    return cfgdefault

def parse_tftprootfolder(folderpath):
    # returns 1 if ok, 0 if not
    # Does path exist, is it readable and writeable
    if not os.path.exists(folderpath):
        # it doesn't exist
        return 0
    if not os.path.isdir(folderpath):
        # its not a directory
        return 0
    if not os.access(folderpath, os.R_OK | os.W_OK):
        # Don't have read and write permissions
        return 0
    return 1
    
def parse_logfolder(folderpath):
    # returns 1 if ok, 0 if not
    # Does path exist, is it writeable
    if not os.path.exists(folderpath):
        # it doesn't exist
        return 0
    if not os.path.isdir(folderpath):
        # its not a directory
        return 0
    if not os.access(folderpath, os.W_OK):
        # Don't have write permissions
        return 0
    return 1

def parse_anysource(IsAny):
    if IsAny == "0" or IsAny == "1":
        return 1
    return 0
    
def parse_ip(ipvalue, mask):
    if not ipv4_parse.parse(ipvalue, mask): return 0
    return 1
    
def parse_port(udp_port):
    if not udp_port.isdigit(): return 0
    int_port=int(udp_port)
    if int_port<0 or int_port>65535: return 0 
    return 1
        
def parse_all(newcfg):
    # Given a new dictionary of setup values,
    # parse each value
    # returns 1 if ok, 0 if not
    if not parse_tftprootfolder(newcfg["tftprootfolder"]): return 0
    if not parse_logfolder(newcfg["logfolder"]): return 0    
    if not parse_anysource(newcfg["anysource"]): return 0
    if not parse_ip(newcfg["ipaddress"],newcfg["mask"]): return 0
    if not parse_port(newcfg["port"]): return 0
    return 1

def correctconfig(newcfg):
    # Given a dictionary of setup values
    # put them in better shape
    # If there's an error, don't do anything, just return the original
    if not parse_all(newcfg): return newcfg
    tempcfg=newcfg
    # convert the ip address to a proper subnet if it is not already one.
    if newcfg["mask"] != "32":
        IP=ipv4_parse.IPAddressMask(newcfg["ipaddress"],newcfg["mask"])
        tempcfg["ipaddress"]=IP.NetworkString
    # Correct \ / mess introduced by browsing for a folder
    # and make sure folders are absolute path names
    tempcfg["tftprootfolder"]=os.path.abspath(newcfg["tftprootfolder"])
    tempcfg["logfolder"]=os.path.abspath(newcfg["logfolder"])
    return tempcfg
    
def writeconfigtofile(cfg):
    fp=open(CONFIGFILE, "w")
    cfg.write(fp)
    fp.close()

def setconfig(newcfg):
    # Given a new dictionary of setup values,
    # parse each value, then save them to tftpgui.cfg
    # returns 1 if ok, 0 if not
    cfg=ConfigParser.ConfigParser()
    cfg.add_section("Folders")
    cfg.add_section("IPsetup")
    if not parse_all(newcfg): return 0
    cfg.set("Folders", "tftprootfolder", newcfg["tftprootfolder"])
    cfg.set("Folders", "logfolder", newcfg["logfolder"])
    cfg.set("IPsetup", "anysource", newcfg["anysource"])
    cfg.set("IPsetup", "ipaddress", newcfg["ipaddress"])
    cfg.set("IPsetup", "mask", newcfg["mask"])
    cfg.set("IPsetup", "port", newcfg["port"])
    writeconfigtofile(cfg)
    return 1

def getconfig():
    """Return a dictionary of setup values for tftpgui.py
    
       Read the tftpgui.cfg config file, and if it does
       not exist, or parts do not exist, substitute 
       defaults instead, and then return a dictionary
       of the setup values"""
    # First create a dictionary of default config values
    cfgdict={}
    cfgdict=setdefaults()
    # Now create a ConfigParser object, to read and write
    # to the config file
    cfg=ConfigParser.ConfigParser()
    if os.path.exists(CONFIGFILE):
        # read it
        cfg.read(CONFIGFILE)
    # make sure cfg has the two sections Folders and IPsetup
    if not cfg.has_section("Folders"):
        cfg.add_section("Folders")
    if not cfg.has_section("IPsetup"):
        cfg.add_section("IPsetup")
    # Read each parameter in turn, and if it doesnt
    # exist, make sure the defaults are inserted into cfg instead
    if cfg.has_option("Folders", "tftprootfolder"):
        cfgdict["tftprootfolder"]=cfg.get("Folders", "tftprootfolder")
    else:
        cfg.set("Folders", "tftprootfolder", cfgdict["tftprootfolder"])
    if cfg.has_option("Folders", "logfolder"):
        cfgdict["logfolder"]=cfg.get("Folders", "logfolder")
    else:
        cfg.set("Folders", "logfolder", cfgdict["logfolder"])
    if cfg.has_option("IPsetup", "anysource"):
        cfgdict["anysource"]=cfg.get("IPsetup", "anysource")
    else:
        cfg.set("IPsetup", "anysource", cfgdict["anysource"])
    if cfg.has_option("IPsetup", "ipaddress"):
        cfgdict["ipaddress"]=cfg.get("IPsetup", "ipaddress")
    else:
        cfg.set("IPsetup", "ipaddress", cfgdict["ipaddress"])
    if cfg.has_option("IPsetup", "mask"):
        cfgdict["mask"]=cfg.get("IPsetup", "mask")
    else:
        cfg.set("IPsetup", "mask", cfgdict["mask"])
    if cfg.has_option("IPsetup", "port"):
        cfgdict["port"]=cfg.get("IPsetup", "port")
    else:
        cfg.set("IPsetup", "port", cfgdict["port"])
    # So cfg and dictionary cfgdict are now matched
    # write out the config file and return the dictionary    
    writeconfigtofile(cfg)
    return cfgdict
