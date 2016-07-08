from magi.util.agent import DispatchAgent, agentmethod
from magi.util.processAgent import initializeProcessAgent
from shutil import copyfile
from random import randint

# FileCreator agent implementation, derived from DispatchAgent.
class FileCreator(DispatchAgent):
    def __init__(self):
        DispatchAgent.__init__(self)
        self.sourceFile = ''
        self.destinationFile = ''

    # Method that creates destinationFile based on sourceFile.
    # The @agentmethod() decorator not required, but encouraged. Does nothing of substance now, but may in future.
    @agentmethod()
    def createFile(self, msg):
        with open(self.destinationFile, "a") as destination:
            with open(self.sourceFile, "r") as source:
                currentop = 1
                randa = randint(1, 100)
                randb = randint(1, 100)
                for line in source:
                    if "a:" in line:
                        print >>destination, "          a: %d" % randa
                    elif "b:" in line:
                        print >>destination, "          b: %d" % randb
                    elif "retVal:" in line:
                        if currentop == 1:
                            print >>destination, line[0:line.find("retVal")] + "retVal: " + str(randa + randb) + "} ]"
                        elif currentop == 2:
                            print >>destination, line[0:line.find("retVal")] + "retVal: " + str(randa - randb) + "} ]"
                        elif currentop == 3:
                            print >>destination, line[0:line.find("retVal")] + "retVal: " + str(randa * randb) + "} ]"
                        elif currentop == 4:
                            # truncate the resulting double and cast as int to match the return of simpleAgent.c
                            print >>destination, line[0:line.find("retVal")] + "retVal: " + str(randa / randb) + "} ]"
                        #currenttop += 1
                        #randa = randint(1, 100)
                        #randb = randint(1, 100)
                    else:
                        destination.write(line)

# getAgent() method must be defined somewhere for all agents.
# Magi daemon invokes method to get reference to agent. Uses reference to run and interact with agent instance.
def getAgent(**kwargs):
    agent = FileCreator()
    agent.setConfiguration(None, **kwargs)
    return agent

# In case agent run as separate process, need to create instance of agent, initialize required
# parameters based on received arguments, and call run method defined in DispatchAgent.
if __name__ == "__main__":
    agent = FileCreator()
    initializeProcessAgent(agent, sys.argv)
    agent.run()
