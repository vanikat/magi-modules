# for rCentral test.
all: rCentral.c 
	gcc -g -w -o test rCentral.c centralized/RLS_Auto.cpp centralized/rpoly.cpp centralized/PMU_src.cpp centralized/RLS_common.cpp -lmagic -lyaml -lmongoc-1.0 -lbson-1.0 -lpthread -lstdc++ -larmadillo -lboost_thread-mt -lboost_filesystem -lboost_program_options -lboost_system -L/usr/lib -I/usr/include/libmagic -I/usr/include/libmongoc-1.0 -I/usr/include/libbson-1.0
clean:
	rm -rf test
