#!/usr/bin/env python 

# Copyright (C) 2012 University of Southern California 
# This software is licensed under the GPLv3 license, included in
# ./GPLv3-LICENSE.txt in the source distribution

from magi.util.agent import agentmethod, ReportingDispatchAgent
from magi.util.processAgent import initializeProcessAgent
from magi.util.recording import DBase, Record, RecordingSession
from sqlalchemy import Column, String, Float, Integer
import logging
import subprocess
import sys
import time


log = logging.getLogger(__name__)

if 'CurlReport' not in locals():
    class CurlReport(DBase, Record):
        dest = Column(String)
        tcp_connected = Column(Float)
        start_transfer = Column(Float)
        total_time = Column(Float)
        bandwidth = Column(Float)
        topology = Column(String)
        sut = Column(String)
        proto = Column(String)
        size = Column(Integer)

class CurlReporter(ReportingDispatchAgent):
    """
    Agent which uses curl to check latency and bandwidth and record to the magi database.

    """
    table_class = CurlReport

    def __init__(self, *args, **kwargs):
        ReportingDispatchAgent.__init__(self, *args, **kwargs)
        self.active = False
        # configurable
        self.dests = []       # which machine to use as endpoints in latency measurements.
        self.interval = 10
        self.url = '%s://%s/getsize.py?length=%d'
        self.sizes = [1, 8192, 16384, 65536, 1048576]
        self.useSocks = False
        self.socksVersion = 4
        self.socksServer = 'localhost'
        self.socksPort = 5010
        self.protocol = 'http'

        # These are "pass through" testbed/experiment configuration passed from the AAL
        # and inserted to tag each measurement. This may be wasteful and there may be a 
        # better way to get the same effect.
        self.topology = ''
        self.sut = ''

        # how long to wait between each host during each iteration
        self.wait = 0
        # whether to truncate the db table
        self.truncate = False

    def confirmConfiguration(self):
        try:
            self.socksVersion = int(self.socksVersion)
            self.socksPort = int(self.socksPort)
            self.interval= int(self.interval)
        
            if len(self.sizes):
                self.sizes = [int(x) for x in self.sizes]

        except ValueError, e:
            log.error('socks version or socks port or interval is not an int.')
            return False

        if self.useSocks and self.socksVersion != 4 and self.socksVersion !=5:
            log.error('We only supports SOCKS 4 or SOCKS 5')
            return False

        return True    


    def periodic(self, now):
        if self.active:
            # iterate over the given sizes. 
            size = self.sizes[0]
            self.sizes.insert(len(self.sizes)-1, self.sizes.pop(0))
            for dst in self.dests:
                url = self.url % (self.protocol, dst, size)
                cmd = []
                cmd.extend(['curl', '-S', '-s', '-o', '/dev/null', '-w', '%{time_connect},%{time_starttransfer},%{time_total},%{speed_download}\\n', url])

                if self.useSocks:
                    cmd.extend(['--proxy', 'socks%d://%s:%d' % (self.socksVersion, self.socksServer, self.socksPort)])

                if self.protocol == 'https':
                    cmd.extend(['--insecure'])    # the cert is self-signed, don't bother checking it

                log.debug(cmd)
                try:
                    # GTL - check_output is in python 2.7 and we have a few 2.6 images in use.
                    # GTL - Popen().communicate()[0] is python 2.6+
                    # sample output: 0.026,266565.000,
                    # o = subprocess.check_output(cmd)
                    o = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0]
                    log.debug('curl out:%s', o)
                    ttc, tts, tt, bw = o.split(',')
                    ttc = float(ttc)
                    tts = float(tts)
                    tt = float(tt)
                    bw = float(bw)
                except subprocess.CalledProcessError, e:
                    log.error('called process error in curl execution: %s', str(e))
                    lat, bw = 0, 0
                except OSError, e:
                    log.error('OS error in curl execution: %s', str(e))
                    lat, bw = 0, 0

                self.session.add(self.table_class(timestamp=time.time(), dest=dst, tcp_connected=ttc, start_transfer=tts, total_time=tt, bandwidth=bw, topology=self.topology, sut=self.sut, proto=self.protocol, size=size))
                time.sleep(self.wait)
            self.session.commit()

        ret=int(self.interval) + now - time.time()
        return ret if ret > 0 else 0
            
    @agentmethod()
    def startCollection(self, msg):
        if not self.active:
            self.active = True
            self.session = RecordingSession()
            if self.truncate:
                log.info('dropping and recreating DB table ' + self.table_class.__name__)
                self.table_class.metadata.drop_all(self.session.bind, tables=[self.table_class.__table__])
            self.table_class.metadata.create_all(self.session.bind)
            log.info('data collection started')
        else:
            log.warning('start collection requested, but collection is already active')
        # return True so that any defined trigger gets sent back to the orchestrator
        return True

    @agentmethod()
    def stopCollection(self, msg):
        self.active = False
        self.session.close()
        log.info('data collection stopped')
        # return True so that any defined trigger gets sent back to the orchestrator
        return True
    
def getAgent():
    agent = CurlReporter()
    return agent

if __name__ == "__main__":
    agent = CurlReporter()
    initializeProcessAgent(agent, sys.argv)
    agent.run()
