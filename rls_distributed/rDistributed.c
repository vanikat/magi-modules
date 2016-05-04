#include "distributed/PMU_src.h"

#include "Agent.h"
#include "AgentRequest.h"
#include "Database.h"
#include "MAGIMessage.h"
#include "Logger.h"
#include "Util.h"
#include "AgentMessenger.h"

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


dList_t* list;

FILE* agentFile;
Logger* agentLogger;
pthread_t pidADMMServer;
pthread_t pidPMU;
pthread_t pidPronyClient;

struct argsADMMServer
{
   char  agentArg1[100];
   char  agentArg2[100];
};

struct argsPMU
{
   char  agentArg1[100];
   char  agentArg2[100];
   char  agentArg3[100];
};  

struct argsPronyClient 
{
   char  agentArg1[100];
   char  agentArg2[100];
   char  agentArg3[100];
   char  agentArg4[100];
   char  agentArg5[100];
   char  agentArg6[100];
   char  agentArg7[100];
   char  agentArg8[100];
   char  agentArg9[100];
   char  agentArg10[100];
   char  agentArg11[100];
   char  agentArg12[100];
   char  agentArg13[100];
   char  agentArg14[100];
};

void *tempStartServer(void* arg) {
  log_info(agentLogger, "entering tempStartServer \n");
  struct argsADMMServer* agent1;
  agent1 = (struct argsADMMServer*)arg;
  log_info(agentLogger, "arg1 %s arg2 %s\n", agent1->agentArg1, agent1->agentArg2);
  int retTemp = ADMMServer(agent1->agentArg1, agent1->agentArg2);
  log_info(agentLogger, "exiting tempStartServer \n");
  return NULL;
}

void startADDMServer(char* a, char* b)
{
  log_info(agentLogger, "entering startServer \n");
  struct argsADMMServer *agent = (struct argsADMMServer *)malloc(sizeof(struct argsADMMServer));
  strcpy(agent->agentArg1, a);
  strcpy(agent->agentArg2, b);
  log_info(agentLogger, "arg1 %s arg2 %s\n", agent->agentArg1, agent->agentArg2);
  pthread_create(&pidADMMServer, NULL, tempStartServer, agent);
  log_info(agentLogger, "exiting startServer \n");
}

void returnWhenServerDone()
{
  log_info(agentLogger, "entering returnWhenServerDone \n");
  pthread_join(pidADMMServer, NULL);
  log_info(agentLogger, "exiting returnWhenServerDone \n");
}

void *tempStartPMU(void* arg) {
  log_info(agentLogger, "entering tempStartPMU \n");
  struct argsPMU* agent1;
  agent1 = (struct argsPMU*)arg;
  log_info(agentLogger, "tempPMU: arg1 %s arg2 %s arg3 %s\n", agent1->agentArg1, agent1->agentArg2, agent1->agentArg3);
  int retTemp = PMU(agent1->agentArg1, agent1->agentArg2, agent1->agentArg3);
  log_info(agentLogger, "exiting tempStartPMU \n");
  return NULL;
}

void startPMU(char* a, char* b, char* c)
{
  log_info(agentLogger, "entering startPMU \n");
  struct argsPMU* agent = (struct argsPMU *)malloc(sizeof(struct argsPMU));
  strcpy(agent->agentArg1, a);
  strcpy(agent->agentArg2, b);
  strcpy(agent->agentArg3, c);
  log_info(agentLogger, "PMU: arg1 %s arg2 %s arg3 %s \n", agent->agentArg1, agent->agentArg2, agent->agentArg3);
  pthread_create(&pidPMU, NULL, tempStartPMU, agent);
  log_info(agentLogger,"exiting startPMU function\n");
}

void *tempStartPronyClient(void* arg) {
  log_info(agentLogger, "entering tempStartPronyClient\n");
  struct argsPronyClient* agent1;
  agent1 = (struct argsPronyClient*)arg;
  int retTemp = PronyADMMClient(agent1->agentArg1, agent1->agentArg2, agent1->agentArg3, agent1->agentArg4,
                                agent1->agentArg5, agent1->agentArg6, agent1->agentArg7, agent1->agentArg8,
                                agent1->agentArg9, agent1->agentArg10, agent1->agentArg11, agent1->agentArg12,
                                agent1->agentArg13, agent1->agentArg14);
  log_info(agentLogger, "exiting tempStartPronyClient\n");
  return NULL;
}

int* startADDMClient(char* b, char* c)
{
  int* result = (int*)malloc(sizeof(int));
  log_info(agentLogger, "entering startPronyClient\n");
  struct argsPronyClient *agent = (struct argsPronyClient *)malloc(sizeof(struct argsPronyClient));
  strcpy(agent->agentArg1, "node-0-link0");
  strcpy(agent->agentArg2, "65000");
  strcpy(agent->agentArg3, "65002");
  strcpy(agent->agentArg4, "1");
  strcpy(agent->agentArg5, "node-1-link1");
  strcpy(agent->agentArg6, "65001");
  strcpy(agent->agentArg7, "node-2-link2");
  strcpy(agent->agentArg8, "65001");
  strcpy(agent->agentArg9, "node-3-link3");
  strcpy(agent->agentArg10, "65001");
  strcpy(agent->agentArg11, "node-4-link4b");
  strcpy(agent->agentArg12, "65001");
  strcpy(agent->agentArg13, "1");
  strcpy(agent->agentArg14, "4");
  pthread_create(&pidPronyClient, NULL, tempStartPronyClient, agent);
  log_info(agentLogger, "exiting startPronyClient \n");
  *result = 20;
  return result;
}


int main(int argc, char **argv)
{
  agentFile = fopen("/tmp/cagent.log","a");
  agentLogger = Logger_create(agentFile,0);
  log_info(agentLogger,"Main function called\n");
  addFunc("startADDMServer", "void", &startADDMServer, 2, "char*" ,"char*");
  addFunc("startPMU", "void", &startPMU, 3, "char*" ,"char*", "char*");
  addFunc("startADDMClient", "int*", &startADDMClient, 2, "char*" ,"char*");
  addFunc("returnWhenServerDone", "void", &returnWhenServerDone, 0, NULL);
  list = ArgParser(argc,argv);
  agentStart(argc,argv);
  fclose(agentFile);
}
