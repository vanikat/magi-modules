#include <arpa/inet.h>
#include <errno.h>
#include <netdb.h>
#include <netinet/in.h>
#include <signal.h>
#include <stdarg.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <unistd.h>

#include "magiCLib/Agent.h"
#include "magiCLib/AgentRequest.h"
#include "magiCLib/Database.h"
#include "magiCLib/MAGIMessage.h"
#include "magiCLib/logger.h"
#include "magiCLib/Util.h"

dList_t* list;

extern Logger* logger;

char* testChar(char* a, char* b){
	log_debug(logger, "ENTRY testChar\n");
	log_debug(logger, "a: %s", a);
	log_debug(logger, "b: %s", b);
	char* result = malloc(strlen(a) + strlen(b) + 1);
	strcpy(result, a);
	strcat(result, b);
	log_debug(logger, "result: %s", result);
	log_debug(logger, "EXIT testChar\n");
	return result;
}

int* testInt(int a, int b){
	log_debug(logger, "ENTRY testInt\n");
	log_debug(logger, "a: %d", a);
	log_debug(logger, "b: %d", b);
	int* result = (int*) malloc(sizeof(int));
	*result = a + b;
	log_debug(logger, "result: %d", result);
	log_debug(logger, "EXIT testInt\n");
	return result;
}

void testVoid() {
	log_debug(logger, "ENTRY testVoid\n");
	keyValueNode_t node1 = (keyValueNode_t) malloc(sizeof(struct keyValueNode));
	node1->key = "function";
	node1->value = "testVoid";
	node1->type = STRING_TYPE;
	node1->next = NULL;
	mongoDBExecute(OPER_INSERT, node1);
	free(node1);
	log_debug(logger, "EXIT testVoid\n");
}

int* addInteger(int a, int b) {
	int* result1 = (int*) malloc(sizeof(int));
	log_debug(logger, "Inside addInteger\n");
	*result1 = a + b;
	keyValueNode_t node1 = (keyValueNode_t) malloc(sizeof(struct keyValueNode));
	node1->key = "addResult";
	node1->value = (void*) *result1;
	node1->type = INT_TYPE;
	node1->next = NULL;
	mongoDBExecute(OPER_INSERT, node1);
	free(node1);
	log_debug(logger, "Going out of the addInterger function\n");
	return result1;
}

int* subtractInteger(int a, int b) {
	log_debug(logger, "Inside subtractInteger\n");
	int* result2 = (int*) malloc(sizeof(int));
	*result2 = a - b;
	keyValueNode_t node1 = (keyValueNode_t) malloc(sizeof(struct keyValueNode));
	node1->key = "subResult";
	node1->value = (void*) *result2;
	node1->type = INT_TYPE;
	node1->next = NULL;
	mongoDBExecute(OPER_INSERT, node1);
	free(node1);
	log_debug(logger,
			"Going out of the subtractInterger function with value %d\n",
			*result2);
	return result2;
}

int main(int argc, char **argv) {
	registerFunction("testChar", "char*", &testChar, 2, "char*", "char*");
	registerFunction("testInt", "int*", &testInt, 2, "int", "int");
	registerFunction("testVoid", "void", &testVoid, 0);
	registerFunction("addInteger", "int*", &addInteger, 2, "int", "int");
	registerFunction("subtractInteger", "int*", &subtractInteger, 2, "int", "int");
	list = ArgParser(argc, argv);
	agentStart(argc, argv);
	log_debug(logger, "Going out of the main\n");
}
