PORT=10500
BUFF=1024
FALSE=0
TXTIMEOUT=1

import random
import json
import socket
import thread
import threading
from threading import Thread
from threading import Semaphore
import time

import logging
log = logging.getLogger(__name__)

class ClientCommService:
    
    def __init__(self):
        self.valueOutMap = {}
        self.running = 1
        self.connected = False
    
    def startClient(self, address, clientID, replyHandler):
        threadName = threading.currentThread().name
        log.info("Thread %s: In startClient" % threadName)
        
        self.slock = Semaphore(0);
        self.valueOutMap = 0;
        
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        retries = 0        
        while not self.connected:
            log.info("Trying to connect to server, attempt #%d..." % (retries+1))
            try:
                self.s.connect((address,PORT))
                self.connected = True
            except socket.error as e:
                retries += 1
                log.info("Socket timed out, exception: %s" % repr(e))
                time.sleep(0.1 + (random.random()*0.3))

        # basic registration
        data = json.dumps({'id':clientID})
        self.s.send(data)
        #
        
        commThread = Thread(
            name = clientID + "ClientComms",
            target = self.serverConnectionThread,
            args = (clientID, self.s, replyHandler)
        )
        commThread.start()
        return commThread
    
    # for reference..
    def ClientHandler(self,clientID,sock,replyHandler):
        t=threading.currentThread()
        sock.settimeout(2)
        while self.running:
            #blocks on recv, but may timeout
            try:
                rxdata=sock.recv(1024)
            except socket.timeout:
                continue
            jdata = json.loads(rxdata)
            dispatch=jdata["dispatch"]
            #print 'Client RX Dispatch ' + str(dispatch)
            returnData=replyHandler(clientID,dispatch)
            rdata=json.dumps({'id':clientID,'utility':returnData})
            sock.send(rdata)
        #cleanup
        sock.close()

    def serverConnectionThread(self, clientID, sock, replyHandler):
        t = threading.currentThread()
        sock.settimeout(TXTIMEOUT)
        while self.running:
            log.info("%s serverConnectionThread Running"  % t.name)
            
            #blocks on recv, but may timeout
            try:
                rxdata = sock.recv(BUFF)
            except socket.timeout:
                log.info("serverConnectionThread socket timed out")

                if self.slock.acquire(blocking=FALSE):
                    log.info("valueOutMap = %s" % repr(self.valueOutMap))

                    #Process output command
                    cdata = json.dumps({
                        'id': clientID,
                        'returnData': self.valueOutMap
                    });
                    sock.send(cdata);

                    if isinstance(cdata['returnData'], dict) and cdata['returnData'].get('type') == 'register':
                        self.registered = True

                        # clear valueOutMap so doesn't send register again
                        self.valueOutMap = {}

                continue

            try:
                jdata = json.loads(rxdata.strip())
            except json.JSONDecodeError:
                log.info("serverConnectionThread could not parse JSON string: %s" % repr(rxdata))
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
        log.info("%s Leaving serverConnectionThread" % threading.currentThread().name)
                
    def sendValue(self, msg):
        self.valueOutMap = msg;
        self.slock.release();
    
    def close(self):
        self.running = 0
        self.slock.release()
        
    def stop(self):
        self.close()