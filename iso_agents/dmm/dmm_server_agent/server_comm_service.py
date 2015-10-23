PORT=10500
BUFF=1024
FALSE=0
TXTIMEOUT=1
HOST=''

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
        self.threadMap = {}
        self.valueOutMap = {}
        self.slock = {}
        self.running = 1
    
    def sendValue(self, clientID, dispatch):
        #Unblock the client thread waiting to send
        if clientID in self.slock:
            self.valueOutMap[clientID] = dispatch
            self.slock[clientID].release()
        else:
            print 'ERROR CLIENT NOT REGISTERED'
            raise Exception, 'Client ' + clientID + ' Not Registered'
            pass
        pass
        
    def startServer(self, replyHandler):
        self.s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.settimeout(TXTIMEOUT)
        self.s.bind((HOST,PORT))
        self.s.listen(5)

        serverThread = Thread(target=self.listenForConnections,args=(replyHandler,))
        serverThread.start()

        return serverThread
    
    #Blocking, only returns if self.running set to False/0
    def listenForConnections(self, replyHandler):
        threadName = threading.currentThread().name
        while self.running:
            log.info("Thread: %s listenForConnections()" % threadName)
            try:
                clientsock, addr = self.s.accept()
                rxdata = clientsock.recv(BUFF)
            except socket.timeout:
                log.info("Thread: %s No connections received before time out" % threadName)
                continue

            try:
                # receive registration message
                jdata = json.loads(rxdata.strip())
            except json.JSONDecodeError:
                log.info("Thread %s: Did not receive expected message from client, ignoring" % threadName)
                continue

            clientID = jdata["id"]
            newThread = Thread(
                name = "serverCommThread for " + clientID, 
                target = self.serverCommThread, 
                args = (clientID, clientsock, addr, replyHandler)
            )
            self.threadMap[clientID] = newThread
            self.valueOutMap[clientID] = 123456789 #sentinel value
            self.slock[clientID] = Semaphore(0)
            
            newThread.start()
            
            log.info('Client ' + clientID + ' connected.')

        log.info("%s Leaving listenForConnections" % threadName)
        self.s.close()
    
    # # for reference...
    # def ServerHandler(self,clientID,clientsock,addr,replyHandler):
    #     #Now block thread until dispatched with new output level
    #     t = threading.currentThread()
    #     while self.running:
    #         self.slock[clientID].acquire()
    #         if self.running == 0:
    #             break
    #         data=json.dumps({'id' : clientID, 'dispatch':self.valueOutMap[clientID]})
    #         #print 'Sending data ' + data
    #         clientsock.send(data)
    #         #print 'Waiting to RX...'
    #         data=clientsock.recv(BUFF)
    #         jdata = json.loads(data.strip())
    #         #print 'RX data ' + str(jdata["utility"])
    #         replyHandler(clientID,jdata["utility"])
    #     #Cleanup
    #     clientsock.close()

    # One thread is run per client on the servers's side
    def serverCommThread(self, clientID, clientsock, addr, replyHandler):
        threadName = threading.currentThread().name
        # Now block thread until dispatched with new output level
        clientsock.settimeout(TXTIMEOUT);
        while self.running:
            log.info("serverCommThread Running -- %s" % threadName)
            
            # when would their be contention for this lock?
            self.slock[clientID].acquire()
            if not self.running:
                break
            
            data = json.dumps({
                'type' : 'dispatch', 
                'payload': self.valueOutMap[clientID]
            })
            clientsock.send(data)
            
            try:
                rxdata = clientsock.recv(BUFF)
            except socket.timeout:
                continue
            
            try:
                jdata = json.loads(rxdata.strip())
            except :
                log.info("Exception in serverCommThread while trying to parse JSON string: %s" % repr(rxdata))
                continue

            log.info('serverCommThread RX data: %s' % repr(jdata["utility"]))
            replyHandler(clientID, jdata["utility"])

        #Cleanup
        clientsock.close()
        log.info("%s Leaving serverCommThread" % threadName)

    def close(self):
        self.running = 0
        for key,value in self.slock.iteritems():
            value.release()
        
    def stop(self):
        self.close()