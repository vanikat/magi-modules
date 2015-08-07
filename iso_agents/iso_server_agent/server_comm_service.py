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

class ServerCommService:
    
    def __init__(self):
        self.threadMap={}
        self.valueOutMap={}
        self.slock={}
        self.running=1
    
    def serverSendValue(self, clientID, dispatch):
        #Unblock the client thread waiting to send
        if clientID in self.slock:
            self.valueOutMap[clientID] = dispatch
            self.slock[clientID].release()
        else:
            print 'ERROR CLIENT NOT REGISTERED'
            raise Exception, 'Client ' + clientID + ' Not Registered'
            pass
        pass
        
    def initAsServer(self,replyHandler):
        thread = Thread(target=self.thread_initAsServer,args=(replyHandler,))
        thread.start()
        return thread
    
    #Blocking, never returns
    def thread_initAsServer(self, replyHandler):
        self.s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.settimeout(TXTIMEOUT)
        self.s.bind(('',PORT))
        self.s.listen(5)
        while self.running:
            log.info("%s Running thread_initAsServer on" % threading.currentThread().name)
            try:
                clientsock, addr = self.s.accept()
                rxdata = clientsock.recv(BUFF)
            except socket.timeout:
                log.info("Thread_initAsServer, socket timed out")
                continue

            try:
                jdata = json.loads(rxdata.strip())
            except json.JSONDecodeError:
                log.info("Exception in thread_initAsServer while trying to parse JSON %s" % repr(rxdata))
                continue

            clientID = jdata["id"]
            nthread = Thread(name=clientID + "Handler", target=self.ServerHandler, args=(clientID,clientsock,addr,replyHandler))
            self.threadMap[clientID] = nthread
            self.valueOutMap[clientID] = 123456789 #sentinel value
            self.slock[clientID] = Semaphore(0)
            nthread.start()
            log.info('Client ' + clientID + ' connected.')
        log.info("%s Leaving thread__initAsServer" % threading.currentThread().name)
        self.s.close()
        
    #One thread is run per client on the servers's side
    def ServerHandler(self, clientID, clientsock, addr, replyHandler):
        #Now block thread until dispatched with new output level
        # t = threading.currentThread()
        clientsock.settimeout(TXTIMEOUT);
        while self.running:
            log.info("ServerHandler Running -- %s" % threading.currentThread().name)
            try:
                rxdata = clientsock.recv(BUFF)
            except socket.timeout:
                #If there's nothing to send, then keep waiting
                log.info('Server RX Timeout, Checking Lock')
                if self.slock[clientID].acquire(blocking=FALSE):
                    #Process a pending dispatch send
                    data = json.dumps({
                        'id' : clientID, 
                        'dispatch':self.valueOutMap[clientID]
                    })
                    #print 'Sending data ' + data
                    clientsock.send(data)
                continue
            
            #Handle rxdata, should be json with "commandData" field
            try:
                jdata = json.loads(rxdata.strip())
            except :
                log.info("Exception in ServerHandler while trying to parse JSON string: %s" % repr(rxdata))
                continue

            log.info('ServerHandler RX data: %s' % repr(jdata["returnData"]))
            replyHandler(clientID, jdata["returnData"])

        #Cleanup
        clientsock.close()
        log.info("%s Leaving ServerHandler" % threading.currentThread().name)

    def close(self):
        self.running=0
        for key,value in self.slock.iteritems():
            value.release()
        
    def stop(self):
        self.close()
        