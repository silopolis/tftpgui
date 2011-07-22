#!/usr/bin/env python
#
# ipv4_parse.py
#
# Version : 2.0
# Date : 20061231
#
# Author : Bernard Czenkusz
# Email  : bernie@skipole.co.uk

#
# ipv4_parse.py - Module to parse IP V4 addresses
# Copyright (c) 2006 Bernard Czenkusz
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

"""Check format of an IP4 address and mask.

This module is typically used to check the format of an IP
address and mask input by a user, via a web site or other form.
It provides the calling program with the ip and mask in different formats.
The module defines the class IPAddressMask
which is called with two arguments :
An address such as a string 192.168.2.3 or list [192,168,2,3]
and a mask, which can be:
either an integer or string such as the number 24,
or a string such as 255.255.255.0
or a list such as [255,255,255,0]
The class initiater checks the arguments and raises the exception
class IP_FORMAT_ERROR if it is not a valid ip address and mask.
Attributes of the class are :
    AddressSlashMaskString which is a string such as 192.168.2.3/24
    AddressString which is the string 192.168.2.3
    AddressList is the list of integers [192, 168, 2, 3]
    MaskBits which is the integer value of the mask 24
    MaskList is the list of integers [255, 255, 255, 0]
    MaskString is the string 255.255.255.0
    NetworkList is the list of integers [192, 168, 2, 0]
    NetworkString is the string 192.168.2.0
    BroadcastList is the list of integers [192, 168, 2, 255]
    BroadcastString is the string 192.168.2.255
Methods of the class are :
    IsBroadcast()
    IsNetwork()
    IsHost()
which are true if the address is a broadcast, network or host
address within the subnet respectively.
If the mask is 32 bits - therefore not giving any network
information, IsBroadcast and IsNetwork will return false
and IsHost will return true.
The addresses 255.255.255.255/32 and 0.0.0.0/32
will both raise an IP_FORMAT_ERROR error.

The class overloads the == and !=
operators so they can be used with class instances.

Functions defined in the module, and are used by the class,
but not normally by external programs, are :

IsAddressListOK(AddressList)
IsAddressStringOK(AddressString)
IsMaskListOK(MaskList)
IsMaskStringOK(MaskString)
IsAddressSlashMaskStringOK(AddressSlashMaskString)
MaskBitsToList(Bits)
MaskStringToList(MaskString)
MaskListToBits(MaskList)
MaskStringToBits(MaskString)
AnyMaskToBits(Mask)
MaskListToString(MaskList)
MaskBitsToString(Bits)
AddressStringToList(AddressString)
AddressListToString(AddressList)

Functions defined in the module, and intended to
be used by external programs, are :

AddressSlashMaskStringSplit(AddressSlashMaskString)
 This converts a string of format "192.168.2.3/24" into a
 list such as ["192.168.2.3",24]
 It raises the exception IP_FORMAT_ERROR if AddressSlashMaskString
 is not a valid ip address and mask

AreTwoHostsOnSameSubnet(IPAddressMask1, IPAddressMask2)
 This requires the two arguments to be
 instances of class IPAddressMask and raises the exception
 class NOT_IPADDRESSMASKCLASS_ERROR if they are not
 (This is a sub-class of IP_FORMAT_ERROR)
 It returns 1 if
    the two addresses are in the same subnet and with the same masks
    and the two addresses are not broadcast or network addresses
    and the two addresses are not equal to each other
    otherwise return 0

IsAddressInSubnet(address, subnet, mask)
  Checks if the address is within the given subnet and mask
  returns 1 if it is, 0 if it isn't
    
parse(address, mask)
  This takes two arguments:
  an IP address string, such as 192.168.2.3
  and a subnet mask, such as 24 or 255.255.255.0
  It checks the address and mask format, and returns an exit code of :
  0 if the address or mask are invalid, or any other error
  1 if the address is a broadcast address
  2 if the address is a network address
  3 if the address is a host (not a broadcast or network address)
  4 if the address is a valid address, but the mask is 32
  

IF RUN DIRECTLY - NOT AS A MODULE

The program will take two arguments, an ipaddress and mask, and run them through
parse(address, mask) returning the output as above.
"""

import sys
# contains sys.argv - the list of arguments passed to this program
# sys.argv[0] is the program name
# sys.argv[1] is the first argument - the IP address
# sys.argv[2] is the second argument - the subnet mask
# contains sys.exit - used to return error codes

import types
# Used to check string and integer types

# Create classes used for Exception Errors

class IP_FORMAT_ERROR(Exception):
    """Base class for IP Format Error in this module."""
    pass

class NOT_IPADDRESSMASKCLASS_ERROR(IP_FORMAT_ERROR):
    """Variable is not an instance of IPAddressMask Class"""
    pass

# class IPAddressMask
# Called with two arguments, an address and a subnet mask
# The address can be a string "192.168.2.1" or a list [192,168,2,1]
# The mask can be in one of the formats :
# 24 or "24" or [255,255,255,0] or "255.255.255.0"

class IPAddressMask:
    """ Class provides IP address and Mask in multiple formats

        Given two arguments - an ip address and mask, this class has
        attributes
        AddressSlashMaskString which is a string such as 192.168.2.3/24
        AddressString which is the string 192.168.2.3
        AddressList is the list of integers [192, 168, 2, 3]
        MaskBits which is the integer value of the mask 24
        MaskList is the list of integers [255, 255, 255, 0]
        MaskString is the string 255.255.255.0
        NetworkList is the list of integers [192, 168, 2, 0]
        NetworkString is the string 192.168.2.0
        BroadcastList is the list of integers [192, 168, 2, 255]
        BroadcastString is the string 192.168.2.255
        If the input is not of the right format, then the class
        initiator will raise an exception class IP_FORMAT_ERROR
        The class also provides methods:
        IsBroadcast()
        IsNetwork()
        IsHost() which are true if the address is a broadcast,
        network or host address within the subnet.
        If the mask is 32 bits - therefore not giving any network
        information, IsBroadcast and IsNetwork will return false
        and IsHost will return true.
        The addresses 255.255.255.255/32 and 0.0.0.0/32
        will both raise an IP_FORMAT_ERROR error.
        The class overloads the == and !=
        operators so they can be used with class instances"""
    def __init__(self,Address,Mask):
        """Check address and mask format, create attributes"""
        # Check the Address format is ok
        if (type(Address)==types.ListType):
            # The address is a list, check it is ok
            if(not IsAddressListOK(Address)): raise IP_FORMAT_ERROR
            self.AddressList=Address
            self.AddressString="%s.%s.%s.%s" % (self.AddressList[0],self.AddressList[1],self.AddressList[2],self.AddressList[3])
        else:
            # It's not a list, so it must be a string
            if(not IsAddressStringOK(Address)): raise IP_FORMAT_ERROR
            self.AddressString=Address
            self.AddressList=AddressStringToList(self.AddressString)
        #Get the mask in bits, for example self.MaskBits=24
        self.MaskBits=AnyMaskToBits(Mask)
        # Raise an error for either of the cases
        # 255.255.255.255/32
        # 0.0.0.0/32
        if ((self.AddressString == "0.0.0.0") and (self.MaskBits == 32)): raise IP_FORMAT_ERROR
        if ((self.AddressString == "255.255.255.255") and (self.MaskBits == 32)): raise IP_FORMAT_ERROR
        # get the address and mask - example self.AddressSlashMaskString="192.168.1.2/24"
        self.AddressSlashMaskString=self.AddressString+'/'+str(self.MaskBits)
        # get the mask as a list - example self.MaskList=[255, 255, 255, 0]
        self.MaskList=MaskBitsToList(self.MaskBits)
        # get the mask as a string - example self.MaskString="255.255.255.0"
        self.MaskString=MaskListToString(self.MaskList)
        # get the address as a list - example self.NetworkList=[192, 168, 1, 0]
        self.NetworkList=_GetNetworkList(self.AddressList, self.MaskList)
        # get the address as a string - example self.NetworkString="192.168.1.0"
        self.NetworkString="%s.%s.%s.%s" % (self.NetworkList[0],self.NetworkList[1],self.NetworkList[2],self.NetworkList[3])
        # get the broadcast address as a list - example self.BroadcastList=[192, 168, 1, 255]
        self.BroadcastList=_GetBroadcastList(self.AddressList, self.MaskList)
        # get the broadcast address as a string - example self.BroadcastString="192.168.1.255"
        self.BroadcastString="%s.%s.%s.%s" % (self.BroadcastList[0],self.BroadcastList[1],self.BroadcastList[2],self.BroadcastList[3])
    #Define methods
    def IsBroadcast(self):
        """Returns 1 if the instance of IPAddressMask is a broadcast address"""
        if(self.MaskBits == 32):return 0
        if(self.AddressString == self.BroadcastString):return 1
        return 0
    def IsNetwork(self):
        """Returns 1 if the instance of IPAddressMask is a network address"""
        if(self.MaskBits == 32):return 0
        if(self.AddressString == self.NetworkString):return 1
        return 0
    def IsHost(self):
        """Returns 1 if the instance of IPAddressMask is a host
        that is - it is not a network or broadcast address"""
        if(self.MaskBits == 32):return 1
        if(self.IsBroadcast() or self.IsNetwork()):return 0
        return 1
    def __eq__(self,other):
        """Allows == operator to work with instances of IPAddressMask"""
        if(self.AddressSlashMaskString == other.AddressSlashMaskString):
            return 1
        return 0
    def __ne__(self,other):
        """Allows != operator to work with instances of IPAddressMask"""
        if(self.AddressSlashMaskString != other.AddressSlashMaskString):
            return 1
        return 0


################################################################################
# The following two functions currently have no error checking and are normally
# only called by the class initiator
################################################################################


# GetNetworkList(AddressList, MaskList)
# Get the network address, given correct Address and Mask lists

def _GetNetworkList(AddressList, MaskList):
    """ Given an address as a list of four integers
    and a subnet mask as a list of four integers
    return the network address, as a list of four integers"""
    NetworkList=[0,0,0,0]
    NetworkList[0]=AddressList[0] & MaskList[0]
    NetworkList[1]=AddressList[1] & MaskList[1]
    NetworkList[2]=AddressList[2] & MaskList[2]
    NetworkList[3]=AddressList[3] & MaskList[3]
    return NetworkList


# GetBroadcastList(AddressList, MaskList)
# Get the broadcast address, given correct Address and Mask lists

def _GetBroadcastList(AddressList, MaskList):
    """ Given an address as a list of four integers
    and a subnet mask as a list of four integers
    return the broadcast address, as a list of four integers"""
    # Get the inverse of the subnet mask
    InvMask=[0,0,0,0]
    InvMask[0]=255 ^ MaskList[0]
    InvMask[1]=255 ^ MaskList[1]
    InvMask[2]=255 ^ MaskList[2]
    InvMask[3]=255 ^ MaskList[3]
    BroadcastList=[0,0,0,0]
    BroadcastList[0]=AddressList[0] | InvMask[0]
    BroadcastList[1]=AddressList[1] | InvMask[1]
    BroadcastList[2]=AddressList[2] | InvMask[2]
    BroadcastList[3]=AddressList[3] | InvMask[3]
    return BroadcastList


###########################################################################
# Testing functions :
#    IsAddressListOK(AddressList)
#    IsAddressStringOK(AddressString)
#    IsMaskListOK(MaskList)
#    IsMaskStringOK(MaskString)
#    IsAddressSlashMaskStringOK(AddressSlashMaskString)
#
# These functions test if the given format is ok
# and return 0 if not, 1 if ok.
###########################################################################


# IsAddressListOK(AddressList)
# Test if the address list is ok

def IsAddressListOK(AddressList):
    """Test if the address list is ok.

    Given an IP address list such as [192,168,1,2]
    check this is of the correct format and return one if it is a valid
    and zero if it is invalid"""
    # Check a list has been passed
    if (type(AddressList)!=types.ListType): return 0
    if (len(AddressList)!=4): return 0
    for number in AddressList:
        if (type(number)!=types.IntType): return 0
        if (number>255): return 0
        if (number<0): return 0
    return 1


# IsAddressStringOK(AddressString)
# Test if the address string is ok

def IsAddressStringOK(AddressString):
    """Test if the address string is ok.

    Given an IP address string with a format such as 192.168.1.2,
    check this is of the correct format and return one if it is a valid
    and zero if it is invalid"""
    # Check a string has been passed
    if (type(AddressString)!=types.StringType): return 0
    # check length
    if (len(AddressString)>15): return 0
    if (len(AddressString)<7): return 0
    if (AddressString.count('.')!=3): return 0
    SplitAddress=list()
    SplitAddress=AddressString.split('.')
    if (len(SplitAddress)!=4): return 0
    # So SplitAddress is a list of four items
    # that should be the four digits of the ip address
    # so test each element in turn
    for digit in SplitAddress:
        if (len(digit)>3): return 0
        if (not digit.isdigit()): return 0
        Number=int(digit)
        if (Number>255): return 0
        if (Number<0): return 0
    return 1


# IsMaskListOK(MaskList)
# Test if the mask list is ok

def IsMaskListOK(MaskList):
    """Test if the mask list is ok.

    Given a subnet mask as a list of integers with a format such as [255,255,255,0]
    check this is of the correct format and return one if it is valid
    and zero if it is invalid.
    This test considers [0,0,0,0] and [255,255,255,255] to be both valid
    but considers [255,254,255,0] to be invalid."""
    # Check a list has been passed
    if (type(MaskList)!=types.ListType): return 0
    # check length
    if (len(MaskList)!=4): return 0
    # So MaskList is a list of four items
    # that should be the four digits of the subnet mask
    # so test each element in turn
    # Each of these integers can only take the value of one of
    # 0, 128, 192, 224, 240, 248, 252, 254, 255
    AllowedValues=(0, 128, 192, 224, 240, 248, 252, 254, 255)
    for number in MaskList:
        if (type(number)!=types.IntType): return 0
        if (number>255): return 0
        if (number<0): return 0
        # Initially assume not ok, and set to ok if number is one
        # of the allowed values
        IsOK=0
        for allowedDigit in AllowedValues:
            if (number == allowedDigit): IsOK=1
        if (IsOK==0): return 0
    # So all MaskList items have AllowedValues
    # Now check the four together make a vaild mask
    if (MaskList[0]<255):
        if (MaskList[1]!=0): return 0
        if (MaskList[2]!=0): return 0
        if (MaskList[3]!=0): return 0
        return 1
    # So the first digit is 255
    if (MaskList[1]<255):
        if (MaskList[2]!=0): return 0
        if (MaskList[3]!=0): return 0
        return 1
    # So the second digit is 255
    if (MaskList[2]<255):
        if (MaskList[3]!=0): return 0
    return 1


# IsMaskStringOK(MaskString)
# Test if the Mask String is ok
# Depends on :
# ISMaskListOK

def IsMaskStringOK(MaskString):
    """Test if the Mask String is ok.

    Given a subnet mask with a format such as 255.255.255.0,
    check this is of the correct format and return one if it is valid
    and zero if it is invalid.
    This test considers 0.0.0.0 and 255.255.255.255 to be both valid
    but considers 255.254.255.0 to be invalid."""
    # Check a string has been passed
    if (type(MaskString)!=types.StringType): return 0
    # check length
    if (len(MaskString)>15): return 0
    if (len(MaskString)<7): return 0
    if (MaskString.count('.')!=3): return 0
    SplitMask=list()
    SplitMask=MaskString.split('.')
    if (len(SplitMask)!=4): return 0
    # So SplitMask is a list of four items
    # that should be the four digits of the subnet mask
    # so test each element in turn
    for digit in SplitMask:
        if (len(digit)>3): return 0
        if (not digit.isdigit()): return 0
        Number=int(digit)
        if (Number>255): return 0
        if (Number<0): return 0
    # So each SplitMask is correctly formatted as
    # a number between 0 and 255
    MaskList=list()
    MaskList=[int(SplitMask[0]),int(SplitMask[1]),int(SplitMask[2]),int(SplitMask[3])]
    # can use IsMaskListOK to further check the validity of the mask
    return IsMaskListOK(MaskList)


# IsAddressSlashMaskStringOK(AddressSlashMaskString)
# Test if the Address/Mask String is ok
# Depends on :
# IsAddressStringOK

def IsAddressSlashMaskStringOK(AddressSlashMaskString):
    """Test if the Address/Mask String is ok.

    Given an IP address and Mask with format such
    as 192.168.1.2/24, check this is of the correct format
    and return one if it is a valid and zero if it is invalid"""
    # Check a string has been passed
    if (type(AddressSlashMaskString)!=types.StringType): return 0
    if (AddressSlashMaskString.count('/')!=1): return 0
    SplitAddress=AddressSlashMaskString.split('/')
    if (len(SplitAddress)!=2): return 0
    # So SplitAddress is a list of two items
    # the first being the ip address, and the second
    # being the subnet mask test each element in turn
    if (not IsAddressStringOK(SplitAddress[0])): return 0
    Mask=SplitAddress[1]
    if (not Mask.isdigit()): return 0
    Number=int(Mask)
    if (Number>32): return 0
    if (Number<0): return 0
    if ((SplitAddress[0] == "0.0.0.0") and (Number == 32)): return 0
    if ((SplitAddress[0] == "255.255.255.255") and (Number == 32)): return 0
    return 1


#############################################################################
# The functions:
#    MaskBitsToList(Bits)             i.e. 24 to [255,255,255,0]
#    MaskStringToList(MaskString)     i.e. "255.255.255.0" to [255,255,255,0]
#
# Convert mask formats to lists. They use the previously defined test
# functions and raise an IP_FORMAT_ERROR if they encounter a format error
#############################################################################


# MaskBitsToList(Bits)
# Converts a mask integer representation of bits, to a list

def MaskBitsToList(Bits):
    """Converts a mask integer representation of bits, to a list.

    Given the number of mask bits, such as a number like 16
    Returns a list of the subnet mask, such as [255, 255, 0, 0]
    Raises IP_FORMAT_ERROR if the number supplied is less than
    zero, or greater than 32."""
    # Check an integer has been passed
    if (type(Bits)!=types.IntType): raise IP_FORMAT_ERROR
    if ((Bits<0) or (Bits>32)): raise IP_FORMAT_ERROR
    MaskList=[0,0,0,0]
    SumOfBits=(0,128,192,224,240,248,252,254,255)
    if (Bits<9):
        MaskList[0]=SumOfBits[Bits]
        return MaskList
    MaskList[0]=255
    if (Bits<17):
        MaskList[1]=SumOfBits[Bits-8]
        return MaskList
    MaskList[1]=255
    if (Bits<25):
        MaskList[2]=SumOfBits[Bits-16]
        return MaskList
    MaskList[2]=255
    MaskList[3]=SumOfBits[Bits-24]
    return MaskList


# MaskStringToList(MaskString)
# Converts a mask string to a list of integers
# Depends on :
# IsMaskStringOK

def MaskStringToList(MaskString):
    """Converts a mask string to a list of integers.

    Given a subnet mask with a format such as 255.255.255.0,
    check this is of the correct format and raise an exception
    IP_FORMAT_ERROR if not,
    then convert it to List of integers such as [255,255,255,0]"""
    if(not IsMaskStringOK(MaskString)): raise IP_FORMAT_ERROR
    SplitMask=list()
    SplitMask=MaskString.split('.')
    MaskList=list()
    MaskList=[int(SplitMask[0]),int(SplitMask[1]),int(SplitMask[2]),int(SplitMask[3])]
    # So MaskList is a list of the four subnet mask integers
    return MaskList



#########################################################################
# The functions:
#    MaskListToBits(MaskList)     i.e. [255,255,255,0] to 24
#    MaskStringToBits(MaskString) i.e. "255.255.255.0" to 24
#    AnyMaskToBits(Mask)          i.e. 24 or "24" or [255,255,255,0]
#                                      or "255.255.255.0" to 24
#
# Convert mask formats to bits. They use the previously defined test
# functions and raise an IP_FORMAT_ERROR if they encounter a format error
#########################################################################


# MaskListToBits(MaskList)
# Converts a mask list to an integer representation of mask bits
# Depends on :
# IsMaskListOK

def MaskListToBits(MaskList):
    """Converts a mask list to an integer representation of mask bits.

    Given a subnet mask as a list of integers with a format
    such as [255,255,255,0], check this is of the correct
    format and raise an exception
    IP_FORMAT_ERROR if not,
    then convert it to bits, and return the bits as an
    integer between 0 and 32 inclusive."""
    if(not IsMaskListOK(MaskList)): raise IP_FORMAT_ERROR
    # So MaskList is a list of the four subnet mask integers
    # Each of these integers can only take the value of one of
    # 0, 128, 192, 224, 240, 248, 252, 254, 255
    SumOfBits=0
    for digit in MaskList:
        if(digit==0): return SumOfBits
        if(digit==128): return SumOfBits+1
        if(digit==192): return SumOfBits+2
        if(digit==224): return SumOfBits+3
        if(digit==240): return SumOfBits+4
        if(digit==248): return SumOfBits+5
        if(digit==252): return SumOfBits+6
        if(digit==254): return SumOfBits+7
        if(digit==255): SumOfBits=SumOfBits+8
    return SumOfBits


# MaskStringToBits(MaskString)
# Converts a mask string to an integer representation of mask bits
# Depends on :
# MaskStringToList
# MaskListToBits

def MaskStringToBits(MaskString):
    """Converts a mask string to an integer representation of mask bits.

    Given a subnet mask with a format such as 255.255.255.0,
    check this is of the correct format and raise an exception
    IP_FORMAT_ERROR if not,
    then convert it to bits, and return the bits as an
    integer between 0 and 32 inclusive."""
    MaskList=MaskStringToList(MaskString)
    return MaskListToBits(MaskList)


# AnyMaskToBits(Mask)
# Converts an input mask of format either :
# 24 or "24" or [255,255,255,0] or "255.255.255.0" to an integer
# representation of the number of mask bits, such as 24
# Depends on :
# MaskListToBits
# MaskStringToBits

def AnyMaskToBits(Mask):
    """Converts a mask of any format to an integer representation of mask bits.

    Given a subnet mask with a format such as 255.255.255.0,
    or a format such as string or integer 24
    or a format as a list of integers such as [255,255,255,0]
    check this is a correct subnet mask and raise an exception
    IP_FORMAT_ERROR if not,
    then convert it to bits, and return the bits as an
    integer between 0 and 32 inclusive."""
    # First check if the mask is given as an integer number
    if (type(Mask)==types.IntType):
        if ((Mask<0) or (Mask>32)): raise IP_FORMAT_ERROR
        else: return Mask
    # Next check if it given as a list of integers such as [255,255,255,0]
    if (type(Mask)==types.ListType): return MaskListToBits(Mask)
    # So presumably its a string, if its anything else,
    # raise an exception
    if (type(Mask)!=types.StringType): raise IP_FORMAT_ERROR
    # So its a string, check if its a string representation of
    # an integer number of bits
    if (len(Mask)<3):
        # So it must be a string value such as 24
        if (not Mask.isdigit()): raise IP_FORMAT_ERROR
        number=int(Mask)
        if ((number<0) or (number>32)): raise IP_FORMAT_ERROR
        else: return number
    # So its a string such as 255.255.255.0
    return MaskStringToBits(Mask)


#############################################################################
# The functions:
#    MaskListToString(MaskList) i.e. [255,255,255,0] to "255.255.255.0"
#    MaskBitsToString(Bits)     i.e. 24 to "255.255.255.0"
#
# Convert mask formats to strings. They use the previously defined test
# functions and raise an IP_FORMAT_ERROR if they encounter a format error
#############################################################################


# MaskListToString(MaskList)
# Converts a mask list to a string
# Depends on :
# IsMaskListOK

def MaskListToString(MaskList):
    """Converts a mask list to a string.

    Given a subnet mask as a list of integers with a format
    such as [255,255,255,0], check this is of the correct
    format and raise an exception
    IP_FORMAT_ERROR if not,
    then convert it to a string such as 255.255.255.0"""
    # Check a correct List has been passed
    if(not IsMaskListOK(MaskList)): raise IP_FORMAT_ERROR
    MaskString="%s.%s.%s.%s" % (MaskList[0],MaskList[1],MaskList[2],MaskList[3])
    return MaskString


# MaskBitsToString(Bits)
# Converts an integer representation of the number of mask bits
# to a mask string
# Depends on :
# MaskbitsToList

def MaskBitsToString(Bits):
    """Converts an integer of the number of mask bits to a mask string.

    Given the number of mask bits, such as a number like 16
    Returns a string of the subnet mask, such as 255.255.0.0
    It first calls MaskBitsToList - which will raise IP_FORMAT_ERROR
    if the number supplied is less than zero, or greater than 32
    and then it converts the resultant list to a string."""
    # First convert to a list
    MaskList=MaskBitsToList(Bits)
    # Then to a string
    MaskString="%s.%s.%s.%s" % (MaskList[0],MaskList[1],MaskList[2],MaskList[3])
    # Then return the string
    return MaskString


#############################################################################
# The functions:
#    AddressStringToList(AddressString) i.e. "192.168.2.1" to [192,168,2,1]
#    AddressListToString(AddressList)   i.e. [192,168,2,1] to "192.168.2.1"
#
# Converts address formats, raising an IP_FORMAT_ERROR if they
# encounter a format error.
#############################################################################


# AddressStringToList(AddressString)
# Converts an address string to a list of integers
# Depends on :
# IsAddressStringOK

def AddressStringToList(AddressString):
    """Converts an address string to a list of integers.

    Given an address string with a format such as 192.168.2.1,
    check this is of the correct format and raise an exception
    IP_FORMAT_ERROR if not,
    then convert it to list of integers such as [192,168,2,1]"""
    if(not IsAddressStringOK(AddressString)): raise IP_FORMAT_ERROR
    SplitAddress=list()
    SplitAddress=AddressString.split('.')
    AddressList=list()
    AddressList=[int(SplitAddress[0]),int(SplitAddress[1]),int(SplitAddress[2]),int(SplitAddress[3])]
    # So AddressList is a list of the four address integers
    return AddressList

# AddressListToString(AddressList)
# Converts an address list of integers to a string
# Depends on :
# IsAddressListOK

def AddressListToString(AddressList):
    """Converts an address list of integers to a string.

    Given an address list of integers such as [192,168,2,1],
    check this is of the correct format and raise an exception
    IP_FORMAT_ERROR if not,
    then convert it to a string such as 192.168.2.1"""
    if(not IsAddressListOK(AddressList)): raise IP_FORMAT_ERROR
    AddressString="%s.%s.%s.%s" % (AddressList[0],AddressList[1],AddressList[2],AddressList[3])
    return AddressString


#############################################################################
# UTILITY FUNCTIONS:
#
# AddressSlashMaskStringSplit(AddressSlashMaskString)
#    This converts a string of format "192.168.2.3/24" into a
#    list such as ["192.168.2.3",24]
#
# AreTwoHostsOnSameSubnet(IPAddressMask1, IPAddressMask2)
#    Given two instances of class IPAddressMask, return 1 if
#    they are two different valid hosts on the same subnet
#    otherwise return 0
#
# parse(address, mask) takes two arguments:
#    an IP address string, such as 192.168.2.3
#    and a subnet mask, such as 24 or 255.255.255.0
#    It checks the address and mask format, and returns an exit code of :
#    0 if the address or mask are invalid, or any other error
#    1 if the address is a broadcast address
#    2 if the address is a network address
#    3 if the address is a valid host address (not a broadcast or network address) within a subnet
#    4 if the address is a valid address, but the mask is 32, so no subnet information is given
#  
##############################################################################


# AddressSlashMaskStringSplit(AddressSlashMaskString)
# This converts a string of format "192.168.2.3/24" into a
# list such as ["192.168.2.3",24]
# Depends on :
# IsAddressSlashMaskStringOK

def AddressSlashMaskStringSplit(AddressSlashMaskString):
    """Converts an address/mask string to a list [address,mask].

    Given an IP address and Mask with format such
    as 192.168.1.2/24, return a list of two items, the first
    being the address string 192.168.1.2, and the second
    being the integer 24
    raise the exception IP_FORMAT_ERROR if AddressSlashMaskString
    is not a valid ip address and mask"""
    # Check a string has been passed
    if(not IsAddressSlashMaskStringOK(AddressSlashMaskString)): raise IP_FORMAT_ERROR
    SplitAddress=list()
    SplitAddress=AddressSlashMaskString.split('/')
    SplitAddress[1]=int(SplitAddress[1])
    return SplitAddress


# AreTwoHostsOnSameSubnet(IPAddressMask1, IPAddressMask2)
# Given two instances of class IPAddressMask, return 1 if
# they are two different valid hosts on the same subnet
# otherwise return 0

def AreTwoHostsOnSameSubnet(IPAddressMask1, IPAddressMask2):
    """Check if two hosts are on the same subnet.

    Given two instances of class IPAddressMask, return 1 if
    the two addresses are in the same subnet and with the same masks
    and the two addresses are not broadcast or network addresses
    and the two addresses are not equal to each other
    i.e. they are two valid hosts on the same subnet
    otherwise return 0
    If subnet masks are 32, return 0 as this does not give
    sufficient network information for the test.
    If the addresses are not instances of IPAddressMask,
    this function will raise the exception class
    NOT_IPADDRESSMASKCLASS_ERROR
    which is a subclass of IP_FORMAT_ERROR"""
    if(not isinstance(IPAddressMask1,IPAddressMask)): raise NOT_IPADDRESSMASKCLASS_ERROR
    if(not isinstance(IPAddressMask2,IPAddressMask)): raise NOT_IPADDRESSMASKCLASS_ERROR
    #Must both be hosts, i.e. not network or broadcast addresses
    if(not IPAddressMask1.IsHost()): return 0
    if(not IPAddressMask2.IsHost()): return 0
    #Must have the same number of subnet bits
    if(IPAddressMask1.MaskBits != IPAddressMask2.MaskBits): return 0
    #And the subnet bits must not equal 32
    if(IPAddressMask1.MaskBits == 32): return 0
    #If they are equal, they are the same address which is not wanted
    if(IPAddressMask1 == IPAddressMask2): return 0
    #And they must have the same network strings
    if(IPAddressMask1.NetworkString != IPAddressMask2.NetworkString): return 0
    return 1

    
# IsAddressInSubnet(address, subnet, mask)
# Checks if the address is within the given subnet and mask
# returns 1 if it is, 0 if it isn't
    
def IsAddressInSubnet(address, subnet, mask):
    """Checks if the address is within the given subnet and mask
    
    If it is, return 1
    If it is not, or any other error is found, return 0"""
    # are the address, subnet and mask valid values
    if not parse(address, mask): return 0
    if not parse(subnet, mask): return 0
    # if the mask is 32, then address and subnet are one and the
    # same thing
    if mask == 32:
        if address == subnet :
            return 1
        else:
            return 0  
    # Create two instances of the class IPAddressMask
    try:
        InputSubnet=IPAddressMask(subnet, mask)
    except IP_FORMAT_ERROR:
        return 0
    try:
        InputAddress=IPAddressMask(address, mask)
    except IP_FORMAT_ERROR:
        return 0
    # if they both have the same network address and broadcast
    # address, then they are both within the same subnet and
    # it is fair to say address is within subnet
    if InputSubnet.NetworkString != InputAddress.NetworkString:
        return 0
    if InputSubnet.BroadcastString != InputAddress.BroadcastString:
        return 0
    return 1
        
   
# parse(address, mask)
# Checks the address and mask, returns 0 if they are invalid,
# or a return of 1 to 4 if valid

def parse(address, mask):
    """Checks the address and mask

    Check the address and mask format, and return :
    0 if the address or mask are invalid, or any other error
    1 if the address is a broadcast address
    2 if the address is a network address
    3 if the address is a valid host address (not a broadcast or network address) within a subnet
    4 if the address is a valid address, but the mask is 32, so no subnet information is given"""

    # Create an instance of the class IPAddressMask
    try:
        InputAddress=IPAddressMask(address, mask)
    except IP_FORMAT_ERROR:
        return 0
    # Return 0 if the address is 255.255.255.255
    if (InputAddress.AddressString == "255.255.255.255"): return 0
    # Return 4 if the mask is 32
    if (InputAddress.MaskBits == 32): return 4
    # Return 1 if it is a broadcast address
    if(InputAddress.IsBroadcast()): return 1
    # Return 2 if it is a network address
    if(InputAddress.IsNetwork()): return 2
    # Return 3 if it is a host address
    if(InputAddress.IsHost()): return 3
    # all done, - should never reach this point since it must
    # be either a Broadcast, Network or Host address.
    # So if this point is reached, it is likely to be a program error
    # somewhere - return 0 to shown an error has occurred
    return 0
    

#############################################################################
# MAIN
# Called if this module is run directly.
#############################################################################


if (__name__=="__main__"):
    # Get the arguments  -  two arguments should be given,
    # sys.argv should be of length three
    # since the first argument will be the script name.
    if (len(sys.argv) != 3):
        print"""Check format of an IP4 address and mask.

This can be run as a module, giving several IP parsing and
checking functions, - see the module source code.
If run directly, the program takes two arguments:
  an IP address string, such as 192.168.2.3
  and a subnet mask, such as 24 or 255.255.255.0

So typically it would be run as :

  python ipv4_parse.py 192.168.2.3 255.255.255.0

Or

  python ipv4_parse.py 192.168.2.3 24

It checks the address and mask format, and returns an exit code of :

  0 if the address or mask are invalid, or any other error
  1 if the address is a broadcast address
  2 if the address is a network address
  3 if the address is a valid host address (not a broadcast or network address) within a subnet
  4 if the address is a valid address, but the mask is 32, so no subnet information is given"""
        sys.exit(0)

    # Make sure the arguments have no trailing spaces or newlines
    InputIP=sys.argv[1].strip()
    InputMask=sys.argv[2].strip()

    sys.exit(parse(InputIP, InputMask))





