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
        # open and immediately close the file to create it.
        # open(self.filename, 'w').close()
        
        # Copy the AAL File
        # copyfile(self.sourceFile, self.destinationFile)
        
        # Aaron code test
        with open(self.destinationFile, "a") as destination:
            with open(self.sourceFile, "r") as source:
                for line in source:
                    # line = testln.readline()
                    # destination.write(line + "\n")
                    
                    if "a:" in line:
                        # stringa = "          a: %d" % (random.randint(1, 100))
                        # destination.write(stringa)
                        
                        destination.writelines("teststring")
                        destination.close()
                        open(self.destinationFile, "a") as destination
                    elif "b:" in line:
                        destination.write("          b: %d" % (random.randint(1, 100)))
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
