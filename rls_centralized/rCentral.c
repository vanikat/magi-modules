#include "centralized/PMU_src.h"
#include "centralized/RLS_Auto.h"

#include "Agent.h"
#include "AgentRequest.h"
#include "Database.h"
#include "MAGIMessage.h"
#include "Logger.h"
#include "Util.h"

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

extern Logger* logger;

pthread_t rlsPid;
pthread_t pmuPid;

struct argsRLS {
	char  pmuCount[100];
	char  dataPort[100];
	char  initialsFile[100];
};

struct argsPMU {
	char  rlsHost[100];
	char  rlsPort[100];
	char  sourceFile[100];
};  

void startRLS(char* pmuCount, char* dataPort, char* initialsFile);
void *tempStartRLS(void* arg);
void returnWhenRLSDone();
void startPMU(char* rlsHost, char* rlsPort, char* sourceFile);
void *tempStartPMU(void* arg);


void startRLS(char* pmuCount, char* dataPort, char* initialsFile) {
	log_info(logger,"entering startRLS");
	struct argsRLS *rlsArgs = (struct argsRLS*) malloc(sizeof(struct argsRLS));
	strcpy(rlsArgs->pmuCount, pmuCount);
	strcpy(rlsArgs->dataPort, dataPort);
	strcpy(rlsArgs->initialsFile, initialsFile);
	log_info(logger,"pmuCount: %s, dataPort: %s, initialsFile: %s",
			rlsArgs->pmuCount, rlsArgs->dataPort, rlsArgs->initialsFile);
	pthread_create(&rlsPid, NULL, tempStartRLS, rlsArgs);
	log_info(logger,"exiting startRLS");
}

void *tempStartRLS(void* arg) {
	log_info(logger,"entering tempStartRLS");
	struct argsRLS* rlsArgs;
	rlsArgs = (struct argsRLS*) arg;
	log_info(logger,"tempStartRLS: pmuCount: %s, dataPort: %s, initialsFile: %s",
			rlsArgs->pmuCount, rlsArgs->dataPort, rlsArgs->initialsFile);
	int retTemp = RLS(rlsArgs->pmuCount, rlsArgs->dataPort, rlsArgs->initialsFile);
	log_info(logger,"exiting tempStartRLS");
	return NULL;
}

void returnWhenRLSDone() {
	log_info(logger,"entering returnWhenRLSDone");
	pthread_join(rlsPid, NULL);
	log_info(logger,"exiting returnWhenRLSDone");
}

void startPMU(char* rlsHost, char* rlsPort, char* sourceFile) {
	log_info(logger,"entering startPMU");
	struct argsPMU* pmuArgs = (struct argsPMU*) malloc(sizeof(struct argsPMU));
	strcpy(pmuArgs->rlsHost, rlsHost);
	strcpy(pmuArgs->rlsPort, rlsPort);
	strcpy(pmuArgs->sourceFile, sourceFile);
	log_info(logger,"rlsHost: %s, rlsPort: %s, sourceFile: %s", pmuArgs->rlsHost, pmuArgs->rlsPort, pmuArgs->sourceFile);
	pthread_create(&pmuPid, NULL, tempStartPMU, pmuArgs);
	log_info(logger,"exiting startPMU function");
}

void *tempStartPMU(void* arg) {
	log_info(logger,"entering tempStartPMU");
	struct argsPMU* pmuArgs;
	pmuArgs = (struct argsPMU*) arg;
	log_info(logger,"tempPMU: rlsHost: %s, rlsPort: %s, sourceFile: %s", pmuArgs->rlsHost, pmuArgs->rlsPort, pmuArgs->sourceFile);
	int retTemp = PMU(pmuArgs->rlsHost, pmuArgs->rlsPort, pmuArgs->sourceFile);
	return NULL;
}

int main(int argc, char **argv) {
	registerFunction("startRLS", "void", &startRLS, 3, "char*" ,"char*", "char*");
	registerFunction("startPMU", "void", &startPMU, 3, "char*" ,"char*", "char*");
	registerFunction("returnWhenRLSDone", "void", &returnWhenRLSDone, 0, NULL);
	agentStart(argc,argv);
}
