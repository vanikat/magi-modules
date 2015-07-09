#!/usr/bin/env python

from magi.util.agent import DispatchAgent, agentmethod
from magi.util.processAgent import initializeProcessAgent
from magi.testbed import testbed
from subprocess import Popen, PIPE
import logging
import sys

log = logging.getLogger()
#logging.basicConfig(filename='/users/vaidyars/dtn.log',level=log.info)

from magi.util import database, config

import time

# The DTN_send_recv agent implementation, derived from DispatchAgent.
class DTN_send_recv(DispatchAgent):
    def __init__(self):
        DispatchAgent.__init__(self)
        self.process_s_dtnd = None
        self.process_c_dtnd = None
        self.process_dtncpd = None
        self.process_dtncp = None
	self.collection = database.getCollection(self.name)
    
    def setup_server(self, msg):
        
        configFile = "/proj/montage/exp/casestudy1/servernode_dtn.conf" #it is better to take it as an argument
        logFile = "/home/user/dtn/dtnd.log"
        
        log.info("Setting up server")
        
        # this initialized the database required for the DTN
        log.info("Initializing the database")
        process = Popen(["sudo", "dtnd", "-c", configFile, "--init-db"], stdout=PIPE, stderr=PIPE)
        returncode = process.wait()
        stdout, stderr = process.communicate()
        if returncode == 0:
            log.info(stdout)
            log.info("Database initialized")
        else:
            log.error(stderr)
            log.error("Error initializing database. Returncode %d" %(returncode))
        
        # this starts the DTN daemon
        log.info("Starting daemon")
        self.process_s_dtnd = Popen(["sudo",  "dtnd", "-c", configFile, "-o", logFile], stdout=PIPE, stderr=PIPE)
        log.info("Daemon started")
        
        return True    

    def setup_client(self, msg):
        # this copies the dtn.conf file later has to be changed to settig up a conf file on its own
        
        configFile = "/proj/montage/exp/casestudy1/clientnode_dtn.conf"
        logFile = "/home/user/dtn/dtnd.log"
        
        log.info("Setting up client")
#         return True
        
        # this initialized the database required for the DTN
        log.info("Initializing the database")
        process = Popen(["sudo", "dtnd", "-c", configFile, "--init-db"], stdout=PIPE, stderr=PIPE)
        returncode = process.wait()
        stdout, stderr = process.communicate()
        if returncode == 0:
            log.info(stdout)
            log.info("Database initialized")
        else:
            log.error(stderr)
            log.error("Error initializing database. Returncode %d" %(returncode))
        
        # this starts the DTN daemon
        log.info("Starting daemon")
        self.process_c_dtnd = Popen(["sudo",  "dtnd", "-c", configFile, "-o", logFile], stdout=PIPE, stderr=PIPE)
        log.info("Client daemon started")
        
        return True    

    def start_recv(self, msg):
        log.info("Starting receive process")
        self.process_dtncpd = Popen(["sudo", "dtncpd", "/home/user/dtn/incoming"], stdout=PIPE, stderr=PIPE)
        log.info("Started receiving")
        return True    

    def random_send(self, msg, no_of_files, final_dest):
        for i in range(0, no_of_files):
            filename = '/tmp/' + testbed.nodename + str(i) + '.txt'
            Popen(["sudo", "touch", filename])
            self.start_send(filename, final_dest)
            #time.sleep(0.5)
        return True  
    
    def start_send(self, filename, dest_dtn_eid):
        log.info("Trying to send file %s to %s" %(filename, dest_dtn_eid))
        process = Popen(["sudo", "dtncp", filename, dest_dtn_eid], stdout=PIPE, stderr=PIPE)
        returncode = process.wait()
	t = time.time()
        out, err = process.communicate()
        if returncode == 0:
	    self.collection.insert({"filename" : filename, 
                                    "send_time" : t})
            log.info(out)
            log.info("File: %s sent at time: %s " %(filename, str(t)))
        else:
            log.error(err)
            log.error("Error sending file: %s sent at time: %s " %(filename, str(time.time())))
           
        return True    


    def stop_server(self, msg):
        log.info("Terminating the server")
        time.sleep(2)
        if self.process_s_dtnd:
            self.process_s_dtnd.terminate()
            out, err = self.process_s_dtnd.communicate()
            returncode = self.process_s_dtnd.poll()
            if returncode == 0:
                log.info(out)
                log.info("Server terminated")
            else:
                log.error("Error terminating server. Returncode: %d" %(returncode))
                log.error(err)
        else:
            log.info("No server process running")
        return True 

    def stop_client(self, msg):
        log.info("Terminating the client")
        time.sleep(2)
        if self.process_c_dtnd:
            self.process_c_dtnd.terminate()
            out, err = self.process_c_dtnd.communicate()
            returncode = self.process_c_dtnd.poll()
            if returncode == 0:
                log.info(out)
                log.info("Client terminated")
            else:
                log.error("Error terminating client. Returncode: %d" %(returncode))
                log.error(err)
        else:
            log.info("No client process running")
        return True    

    def parse_output_to_database(self, out):
	# format of output: "%ld,%ld,%s,%s,%d\n", recv_count, current, host, filename,(int) st.st_size
	list_out = out.split( );
	for s in list_out:
		srno, time, source, filename, size = s.split(',')       # split up line around comma characters
		self.collection.insert({"srno" : srno,
					"recv_time" : time, 
					"source" : source, 
					"filename" : filename, 
					"size" : size})
    	return True;


    def stop_recv(self, msg):
        log.info("Stopping to receive")
        time.sleep(2)
        if self.process_dtncpd:
            self.process_dtncpd.terminate()
            out, err = self.process_dtncpd.communicate()
            returncode = self.process_dtncpd.poll()
            if returncode == 143:#this is actually a returncode when the process is terminated using SIGTERM (it is infinaite loop program)
                log.info("Receive process terminated")
                log.info("Received Files:")
                log.info(out)
		self.parse_output_to_database(out)
            else:
                log.error("Error terminating receive process. Returncode: %d" %(returncode))
                log.error(err)
            	log.info(out)
        else:
            log.info("No receive process running")
        log.info("All done!")
        return True

    
    def close_log(self, msg):
        log.info("cleanup done")
    #    logging.shutdown()
        return True  
        

# the getAgent() method must be defined somewhere for all agents.
# The Magi daemon invokes this method to get a reference to an
# agent. It uses this reference to run and interact with an agent
# instance.
def getAgent():
    agent = DTN_send_recv()
    return agent

# In case the agent is run as a separate process, we need to
# create an instance of the agent, initialize the required
# parameters based on the received arguments, and then call the
# run method defined in DispatchAgent.
if __name__ == "__main__":
    agent = DTN_send_recv()
    kwargs = initializeProcessAgent(agent, sys.argv)
    agent.setConfiguration(None, **kwargs)
    agent.run()
