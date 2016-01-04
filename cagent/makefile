all: simpleAgent.c 
	gcc -g -w -o test simpleAgent.c magiCLib/Agent.c magiCLib/AgentMessenger.c magiCLib/AgentTransport.c magiCLib/AgentRequest.c magiCLib/MAGIMessage.c magiCLib/Logger.c magiCLib/Database.c magiCLib/Util.c -lpthread -lyaml -L/usr/lib -I/usr/include/libmongoc-1.0 -I/usr/include/libbson-1.0 -lmongoc-1.0 -lbson-1.0
clean:
	rm -rf test
