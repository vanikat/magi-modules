PORT=10500
BUFF=1024

import json
import socket
import thread
import threading
from threading import Thread
from threading import Semaphore

class ClientCommService:
    
    def __init__(self):
        self.isClient=0
        self.isServer=0
        self.threadMap={}
        self.valueOutMap={}
        self.slock={}
        self.running=1
    
    def initAsClient(self, address, clientID,replyHandler):
        self.isClient=1
        self.s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.connect((address,PORT))
        data=json.dumps({'id':clientID})
        self.s.send(data)
        nthread=Thread(name=clientID,target=self.ClientHandler,args=(clientID,self.s,replyHandler))
        nthread.start()
        
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
    
    def close(self):
        self.running=0
        for key,value in self.slock.iteritems():
            value.release()