#include "distributed/PronyADMM_Server.h"
#include "distributed/PronyADMM_Client.h"
#include "distributed/PMU_prony.h"

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

pthread_t pidADMMServer;
pthread_t pidPronyClient;
pthread_t pidPMU;

struct argsADMMServer
{
	char  pmuNum[100];
	char  portNum[100];
};

struct argsPronyClient 
{
	char  serverHost[100];
	char  serverPort[100];
	char  dataPort[100];
	char  strategy[100];
	char  bkpServerHost1[100];
	char  bkpServerHost2[100];
	char  bkpServerHost3[100];
	char  bkpServerHost4[100];
	char  bkpServerPort[100];
	char  numAttacks[100];
	char  numPdcs[100];
};

struct argsPMU {
	char  hostName[100];
	char  portNum[100];
	char  inFile[100];
};

void startServer(char* a, char* b);
void *tempStartServer(void* arg);
void returnWhenServerDone();
void startPronyClient(char* server_host, char* strategy,
		              char* backupserver1_host, char* backupserver2_host,
					  char* backupserver3_host, char* backupserver4_host,
					  char* num_of_attack, char* num_of_pdcs);
void *tempStartPronyClient(void* arg);
void startPMU(char* a, char* b, char* c);
void *tempStartPMU(void* arg);

void startServer(char* pmuNum, char* portNum) {
	log_info(logger, "entering startServer");
	struct argsADMMServer *serverArgs = (struct argsADMMServer*) malloc(sizeof(struct argsADMMServer));
	strcpy(serverArgs->pmuNum, pmuNum);
	strcpy(serverArgs->portNum, portNum);
	log_info(logger, "pmuNum: %s, portNum: %s", serverArgs->pmuNum, serverArgs->portNum);
	pthread_create(&pidADMMServer, NULL, tempStartServer, serverArgs);
	log_info(logger, "exiting startServer");
}

void *tempStartServer(void* arg) {
	log_info(logger, "entering tempStartServer");
	struct argsADMMServer* serverArgs;
	serverArgs = (struct argsADMMServer*) arg;
	log_info(logger, "tempStartServer: pmuNum: %s, portNum: %s", serverArgs->pmuNum, serverArgs->portNum);
	int retTemp = ADMMServer(serverArgs->pmuNum, serverArgs->portNum);
	log_info(logger, "exiting tempStartServer");
	return NULL;
}

void returnWhenServerDone() {
	log_info(logger, "entering returnWhenServerDone");
	pthread_join(pidADMMServer, NULL);
	log_info(logger, "exiting returnWhenServerDone");
}

void returnWhenServerStarted(char* name) {
	log_info(logger, "entering returnWhenServerStarted");
	//TODO: Should wait for back server to start and return once it is up
	log_info(logger, "exiting returnWhenServerStarted");
}

void startPronyClient(char* server_host, char* strategy,
		              char* backupserver1_host, char* backupserver2_host,
					  char* backupserver3_host, char* backupserver4_host,
					  char* num_of_attack, char* num_of_pdcs) {
	log_info(logger, "entering startPronyClient");
	struct argsPronyClient *clientArgs = (struct argsPronyClient*) malloc(sizeof(struct argsPronyClient));
	strcpy(clientArgs->serverHost, server_host);
	strcpy(clientArgs->serverPort, "65000");
	strcpy(clientArgs->dataPort, "65002");
	strcpy(clientArgs->strategy, strategy);
	strcpy(clientArgs->bkpServerHost1, backupserver1_host);
	strcpy(clientArgs->bkpServerHost2, backupserver2_host);
	strcpy(clientArgs->bkpServerHost3, backupserver3_host);
	strcpy(clientArgs->bkpServerHost4, backupserver4_host);
	strcpy(clientArgs->bkpServerPort, "65001");
	strcpy(clientArgs->numAttacks, num_of_attack);
	strcpy(clientArgs->numPdcs, num_of_pdcs);
	pthread_create(&pidPronyClient, NULL, tempStartPronyClient, clientArgs);
	log_info(logger, "exiting startPronyClient");
}

void *tempStartPronyClient(void* arg) {
	log_info(logger, "entering tempStartPronyClient");
	struct argsPronyClient* clientArgs;
	clientArgs = (struct argsPronyClient*)arg;
	int retTemp = PronyADMMClient(clientArgs->serverHost, clientArgs->serverPort,
			clientArgs->dataPort, clientArgs->strategy,
			clientArgs->bkpServerHost1, clientArgs->bkpServerHost2,
			clientArgs->bkpServerHost3, clientArgs->bkpServerHost4,
			clientArgs->bkpServerPort,
			clientArgs->numAttacks, clientArgs->numPdcs);
	log_info(logger, "exiting tempStartPronyClient");
	return NULL;
}

void returnWhenPronyClientDone() {
	log_info(logger, "entering returnWhenPronyClientDone");
	pthread_join(pidPronyClient, NULL);
	log_info(logger, "exiting returnWhenPronyClientDone");
}

void startPMU(char* hostName, char* portNum, char* inFile) {
	log_info(logger, "entering startPMU");
	struct argsPMU* pmuArgs = (struct argsPMU*) malloc(sizeof(struct argsPMU));
	strcpy(pmuArgs->hostName, hostName);
	strcpy(pmuArgs->portNum, portNum);
	strcpy(pmuArgs->inFile, inFile);
	log_info(logger, "hostName: %s, portNum: %s, inFile: %s", pmuArgs->hostName, pmuArgs->portNum, pmuArgs->inFile);
	pthread_create(&pidPMU, NULL, tempStartPMU, pmuArgs);
	log_info(logger,"exiting startPMU");
}

void *tempStartPMU(void* arg) {
	log_info(logger, "entering tempStartPMU");
	struct argsPMU* pmuArgs;
	pmuArgs = (struct argsPronyClient*) arg;
	log_info(logger, "tempStartPMU: hostName: %s, portNum: %s, inFile: %s", pmuArgs->hostName, pmuArgs->portNum, pmuArgs->inFile);
	int retTemp = PMU(pmuArgs->hostName, pmuArgs->portNum, pmuArgs->inFile);
	log_info(logger, "exiting tempStartPMU");
	return NULL;
}

int main(int argc, char **argv) {
	registerFunction("startServer", "void", &startServer, 2, "char*" ,"char*");
	registerFunction("returnWhenServerDone", "void", &returnWhenServerDone, 0, NULL);
	registerFunction("returnWhenServerStarted", "void", &returnWhenServerStarted, 1, "char*");
	registerFunction("startPronyClient", "void", &startPronyClient, 8,
			"char*" ,"char*", "char*" ,"char*", "char*" ,"char*", "char*" ,"char*");
	registerFunction("returnWhenPronyClientDone", "void", &returnWhenPronyClientDone, 0, NULL);
	registerFunction("startPMU", "void", &startPMU, 3, "char*" ,"char*", "char*");
	agentStart(argc, argv);
}
