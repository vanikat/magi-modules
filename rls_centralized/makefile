# for rCentral test.
all: rCentral.c 
	gcc -g -w -o test rCentral.c magiCLib/Agent.c magiCLib/Util.c magiCLib/Database.c magiCLib/AgentMessenger.c magiCLib/AgentTransport.c magiCLib/AgentRequest.c magiCLib/MAGIMessage.c magiCLib/logger.c  centralized/RLS_Auto.cpp centralized/rpoly.cpp centralized/PMU_src.cpp centralized/RLS_common.cpp -lstdc++ -larmadillo -lpthread -lboost_thread-mt -lboost_filesystem -lboost_program_options -lboost_system -L/usr/lib -I/usr/include/libmongoc-1.0 -I/usr/include/libbson-1.0 -lmongoc-1.0 -lbson-1.0 -lyaml
clean:
	rm -rf test
