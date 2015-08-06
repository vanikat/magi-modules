#!/usr/bin/env python

# Copyright (C) 2013 University of Southern California.
# This software is licensed under the GPLv3 license, included in
# ./GPLv3-LICENSE.txt in the source distribution

import BaseHTTPServer
import CGIHTTPServer
import cgitb; cgitb.enable()  ## This line enables CGI error reporting
import logging
import sys
import threading
import os

from magi.util.agent import SharedServer
from magi.util.processAgent import initializeProcessAgent


log = logging.getLogger(__name__)

class HttpServer(SharedServer):
    """
		The wget http generator controls a set of wget clients that make HTTP requests to a set HTTP servers.
		Also look at TrafficClientAgent
	"""
    def __init__(self):
        SharedServer.__init__(self)
        self.port = 80
        self.httpd = None
        
    def runserver(self):
        """ subclass implementation """
        server = BaseHTTPServer.HTTPServer
        handler = CGIHTTPServer.CGIHTTPRequestHandler
        server_address = ("", self.port)
        handler.cgi_directories = ["/"]
        
        # Changing working directory to agent's directory
        os.chdir(os.path.dirname(os.path.realpath(__file__)))
        
        server.allow_reuse_address = True
        self.httpd = server(server_address, handler)
        
        serverThread = threading.Thread(target=self.httpd.serve_forever)
        serverThread.start()
        
        log.info('Server started.')
        return True

    def terminateserver(self):
        """ subclass implementation """
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
        log.info('Server stopped.')
        return True
    
def getAgent(**kwargs):
    agent = HttpServer()
    agent.setConfiguration(None, **kwargs)
    return agent

if __name__ == "__main__":
    agent = HttpServer()
    kwargs = initializeProcessAgent(agent, sys.argv)
    agent.setConfiguration(None, **kwargs)
    agent.run()

            