#include <stdarg.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "Agent.h"
#include "AgentRequest.h"
#include "Database.h"
#include "MAGIMessage.h"
#include "Logger.h"
#include "Util.h"

dList_t* list;

extern Logger* logger;

char* testChar(char* a, char* b){
	entrylog(logger, __func__, __FILE__, __LINE__);
	log_debug(logger, "a: %s", a);
	log_debug(logger, "b: %s", b);
	char* result = malloc(strlen(a) + strlen(b) + 1);
	strcpy(result, a);
	strcat(result, b);
	log_debug(logger, "result: %s", result);
	exitlog(logger, __func__, __FILE__, __LINE__);
	return result;
}

int* testInt(int a, int b){
	entrylog(logger, __func__, __FILE__, __LINE__);
	log_debug(logger, "a: %d", a);
	log_debug(logger, "b: %d", b);
	int* result = (int*) malloc(sizeof(int));
	*result = a + b;
	log_debug(logger, "result: %d", *result);
	exitlog(logger, __func__, __FILE__, __LINE__);
	return result;
}

void testVoid() {
	entrylog(logger, __func__, __FILE__, __LINE__);
	keyValueNode_t node1 = (keyValueNode_t) malloc(sizeof(struct keyValueNode));
	node1->key = "function";
	node1->value = "testVoid";
	node1->type = STRING_TYPE;
	node1->next = NULL;
	mongoDBExecute(OPER_INSERT, node1);
	free(node1);
	exitlog(logger, __func__, __FILE__, __LINE__);
}

int* addInteger(int a, int b) {
	entrylog(logger, __func__, __FILE__, __LINE__);
	int* result1 = (int*) malloc(sizeof(int));
	*result1 = a + b;
	keyValueNode_t node1 = (keyValueNode_t) malloc(sizeof(struct keyValueNode));
	node1->key = "addResult";
	node1->value = (void*) *result1;
	node1->type = INT_TYPE;
	node1->next = NULL;
	mongoDBExecute(OPER_INSERT, node1);
	free(node1);
	exitlog(logger, __func__, __FILE__, __LINE__);
	return result1;
}

int* subtractInteger(int a, int b) {
	entrylog(logger, __func__, __FILE__, __LINE__);
	int* result2 = (int*) malloc(sizeof(int));
	*result2 = a - b;
	keyValueNode_t node1 = (keyValueNode_t) malloc(sizeof(struct keyValueNode));
	node1->key = "subResult";
	node1->value = (void*) *result2;
	node1->type = INT_TYPE;
	node1->next = NULL;
	mongoDBExecute(OPER_INSERT, node1);
	free(node1);
	exitlog(logger, __func__, __FILE__, __LINE__);
	return result2;
}
int* multiplyInteger(int a, int b) {
	entrylog(logger, __func__, __FILE__, __LINE__);
	int* result3 = (int*) malloc(sizeof(int));
	*result3 = a * b;
	keyValueNode_t node1 = (keyValueNode_t) malloc(sizeof(struct keyValueNode));
	node1->key = "multResult";
	node1->value = (void*) *result3;
	node1->type = INT_TYPE;
	node1->next = NULL;
	mongoDBExecute(OPER_INSERT, node1);
	free(node1);
	exitlog(logger, __func__, __FILE__, __LINE__);
	return result3;
}
int* divideInteger(int a, int b) {
	entrylog(logger, __func__, __FILE__, __LINE__);
	int* result4 = (int*) malloc(sizeof(int));
	*result4 = a / b;
	keyValueNode_t node1 = (keyValueNode_t) malloc(sizeof(struct keyValueNode));
	node1->key = "divResult";
	node1->value = (void*) *result4;
	node1->type = INT_TYPE;
	node1->next = NULL;
	mongoDBExecute(OPER_INSERT, node1);
	free(node1);
	exitlog(logger, __func__, __FILE__, __LINE__);
	return result4;
}
int main(int argc, char **argv) {
	registerFunction("testChar", "char*", &testChar, 2, "char*", "char*");
	registerFunction("testInt", "int*", &testInt, 2, "int", "int");
	registerFunction("testVoid", "void", &testVoid, 0);
	registerFunction("addInteger", "int*", &addInteger, 2, "int", "int");
	registerFunction("subtractInteger", "int*", &subtractInteger, 2, "int", "int");
	registerFunction("multiplyInteger"), "int*", &multiplyInteger, 2, "int", "int");
	registerFunction("divideInteger"), "int*", &divideInteger, 2, "int", "int");
	//list = ArgParser(argc, argv);
	agentStart(argc, argv);
	log_debug(logger, "Going out of the main\n");
}
      
        
        


