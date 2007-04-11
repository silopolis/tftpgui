#!/usr/bin/env python
#
# stopwatch.py
#
# Version : 1.0
# Date : 20070119
#
# Author : Bernard Czenkusz
# Email  : bernie@skipole.co.uk

#
# stopwatch.py - Module to calculate and time TTL values
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

"""Calculates the TTL - the time to live in seconds

This module contains the single stopwatch() class, which is used 
to time the RTT (Round trip time) between sending and receiving
a data packet, it then calculates an average RTT
and assumes a TTL of three times the average RTT

The exception STOPWATCH_ERROR will be raised if the method time_it is
called before the method start."""

import time

class STOPWATCH_ERROR(Exception):
    """time_it should only be called if start has been called first."""
    pass

class stopwatch:
    """stopwatch class calculates the TTL - the time to live in seconds
    
    The start() method should be called, each time a packet is transmitted
    which expects a reply, and then the time_it() method should be called
    periodically while waiting for the reply.
    If  time_it() returns 1, then the time is still within the TTL - 
    so carry on waiting.
    If time_it() returns 0, then the TTL has expired and the calling
    program needs to do something about it.
    When a packet is received, the calling program should call the
    stop() method - this then calculates the average round trip
    time (aveRTT), and a TTL of three times the aveRTT.
    TTL is  a minimum of 0.5 secs, and a maximum of 5 seconds.
    Methods: 
      start() to start  the stopwatch
      stop() to stop the stopwatch, and update aveRTT and TTL
      time_it() return 1 if the time between start and time_it is less than TTL
      return 0 if it is greater
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
        self.started=0
       
    def start(self):
        self.rightnow=time.time()
        self.started=1
        
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
        self.started=0
    
    def time_it(self):
        if(not self.started): raise STOPWATCH_ERROR
        deltatime=time.time()-self.rightnow
        if deltatime>self.TTL :
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
            self.started=0
            return 0
        return 1

