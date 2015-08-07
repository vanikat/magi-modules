"""

This class defines both client and server communication
    for sending and receiving data encoded in JSON format
    
Usage Guide:
Client:
call initAsClient(address, ID, replyHandler)
handle data from the server as replyHandler(clientID,dispatch)
    Must return a reply value
initiate data sending to the server as clientSendValue(clientID,command)
    Reply value will come as dispatch, this is a one-way communication structure
"""

PORT=10500
BUFF=1024
FALSE=0
TXTIMEOUT=1

import json
import socket
import thread
import threading
from threading import Thread
from threading import Semaphore

import logging
log = logging.getLogger(__name__)

class ClientCommService:
    
    def __init__(self):
        self.valueOutMap = {}
        self.running = 1
        self.connected = False
        self.registered = False
    
    def clientSendValue(self, command):
        self.valueOutMap = command;
        self.slock.release();
    
    def initAsClient(self, address, clientID, replyHandler):
        log.info("In initAsCLient")
        
        self.slock = Semaphore(0);
        self.valueOutMap = 0;
        
        self.s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        retries = 0
        while not self.connected and retries <= 4:
            log.info("Trying to connect to server, attempt #%d..." % (retries+1))
            try:
                self.s.connect((address,PORT))
                self.connected = True
            except socket.timeout as e:
                log.info("Socket timed out, exception: %s" % repr(e))
                retries += 1

        # if self.connected is False:
        #     log.info("ERROR: Client could not connect to server")
        #     raise Exception, "ERROR: Client could not connect to server"

        data = json.dumps({'id':clientID})
        self.s.send(data)
        nthread = Thread(name=clientID + "ClientComms", target=self.ClientHandler, args=(clientID, self.s, replyHandler))
        nthread.start()
        return nthread
    
    def ClientHandler(self, clientID, sock, replyHandler):
        t = threading.currentThread()
        sock.settimeout(TXTIMEOUT)
        while self.running:
            log.info("%s ClientHandler Running"  % t.name)
            #blocks on recv, but may timeout
            try:
                rxdata = sock.recv(BUFF)
            except socket.timeout:
                log.info("ClientHandler socket timed out")
                #Possible to handle some faults here
                #Otherwise see if client has anything to send
                if self.slock.acquire(blocking=FALSE):
                    log.info("valueOutMap = %s" % repr(self.valueOutMap))
                    if isinstance(self.valueOutMap, dict) and self.valueOutMap.get('type') == 'register':
                        self.registered = True

                    #Process output command
                    cdata = json.dumps({
                        'id': clientID,
                        'returnData': self.valueOutMap
                    });
                    sock.send(cdata);
                continue

            try:
                jdata = json.loads(rxdata.strip())
            except json.JSONDecodeError:
                log.info("ClientHandler could not parse JSON string: %s" % repr(rxdata))
                continue
            
            # dispatch = jdata["dispatch"]

            log.info('Client RX jdata: ' + repr(jdata))
            replyHandler(clientID, jdata['dispatch'])
            # returnData = replyHandler(clientID,dispatch)
            # rdata=json.dumps({'id':clientID,'returnData':returnData})
            #sock.send(rdata)
            ######

        #cleanup
        sock.close()
        log.info("%s Leaving ClientHandler" % threading.currentThread().name)
                
    def close(self):
        self.running = 0
        self.slock.release()
        
    def stop(self):
        self.close()