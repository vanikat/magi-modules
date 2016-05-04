all: simpleAgent.c 
	gcc -g -w -o test simpleAgent.c -lmagic -lyaml -lmongoc-1.0 -lbson-1.0 -lpthread -L/usr/local/lib -L/usr/lib -I/usr/include/libmagic -I/usr/include/libmongoc-1.0 -I/usr/include/libbson-1.0
clean:
	rm -rf test
