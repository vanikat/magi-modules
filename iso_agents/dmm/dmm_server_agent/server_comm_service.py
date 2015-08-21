PORT=10500
BUFF=1024

import json
import socket
import thread
import threading
from threading import Thread
from threading import Semaphore

class ServerCommService:
    
    def __init__(self):
        self.isClient=0
        self.isServer=0
        self.threadMap={}
        self.valueOutMap={}
        self.slock={}
        self.running=1
    
    def ServerHandler(self,clientID,clientsock,addr,replyHandler):
        #Now block thread until dispatched with new output level
        t = threading.currentThread()
        while self.running:
            self.slock[clientID].acquire()
            if self.running == 0:
                break
            data=json.dumps({'id' : clientID, 'dispatch':self.valueOutMap[clientID]})
            #print 'Sending data ' + data
            clientsock.send(data)
            #print 'Waiting to RX...'
            data=clientsock.recv(BUFF)
            jdata = json.loads(data.strip())
            #print 'RX data ' + str(jdata["utility"])
            replyHandler(clientID,jdata["utility"])
        #Cleanup
        clientsock.close()
        
        
    def serverSendValue(self,clientID,dispatch):
        if clientID in self.slock:
            self.valueOutMap[clientID]=dispatch
            self.slock[clientID].release()
        else:
            pass
            #print 'Client ' + clientID + ' Not Registered'
        pass
        
    def initAsServer(self,replyHandler):
        thread = Thread(target=self.thread_initAsServer,args=(replyHandler,))
        thread.start()
        return thread
    
    #Blocking, never returns
    def thread_initAsServer(self,replyHandler):
        self.isServer=1
        self.s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind(('',PORT))
        self.s.listen(5)
        while self.running:
            clientsock, addr = self.s.accept()
            data = clientsock.recv(BUFF)
            jdata = json.loads(data.strip())
            clientID = jdata["id"]
            nthread=Thread(name=clientID,target=self.ServerHandler,args=(clientID,clientsock,addr,replyHandler))
            self.threadMap[clientID]=nthread
            self.valueOutMap[clientID]=0
            self.slock[clientID]=Semaphore(0)
            nthread.start()
            print 'Client ' + clientID + ' registered.'
        self.s.close()
        
    def close(self):
        self.running=0
        for key,value in self.slock.iteritems():
            value.release()
        