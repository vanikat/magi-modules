from magi.util.agent import DispatchAgent, agentmethod
from magi.util.processAgent import initializeProcessAgent
from shutil import copyfile

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
                for testln in source:
                    line = testln.readline()
                    destination.write(line + "\n")
                    
                    '''if line.find("a:"):
                        destination.write("          a: " + str(random.random() * 100) + "\n") 
                    elif line.find("b:"):
                        destination.write("          b: " + str(random.random() * 100) + "\n") 
                    else:
                        destination.write(line + "\n")'''

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
