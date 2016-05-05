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

struct agentArgs
{
	char  agentArg1[100];
	char  agentArg2[100];
	char  agentArg3[100];
};  

void *tempStartRLS(void* arg) {
	log_info(logger,"entering tempStartRLS");
	struct agentArgs* agent1;
	agent1=(struct agentArgs*)arg;
	log_info(logger,"arg1 %s arg2 %s arg3 %s", agent1->agentArg1, agent1->agentArg2, agent1->agentArg3);
	int retTemp = RLS(agent1->agentArg1, agent1->agentArg2, agent1->agentArg3);
	log_info(logger,"exiting tempStartRLS");
	return NULL;
}

void startRLS(char* a, char* b, char* c)
{
	log_info(logger,"entering startRLS");
	struct agentArgs *agent = (struct agentArgs *)malloc(sizeof(struct agentArgs));
	strcpy(agent->agentArg1, a);
	strcpy(agent->agentArg2, b);
	strcpy(agent->agentArg3, c);
	log_info(logger,"arg1 %s arg2 %s arg3 %s", agent->agentArg1, agent->agentArg2, agent->agentArg3);
	pthread_create(&rlsPid, NULL, tempStartRLS, agent);
	log_info(logger,"exiting startRLS");
}

void returnWhenRLSDone()
{
	log_info(logger,"entering returnWhenRLSDone");
	pthread_join(rlsPid, NULL);
	log_info(logger,"exiting returnWhenRLSDone");
}

void *tempStartPMU(void* arg) {
	log_info(logger,"entering tempStartPMU");
	struct agentArgs* agent1;
	agent1=(struct agentArgs*)arg;
	log_info(logger,"tempPMU: arg1 %s arg2 %s arg3 %s", agent1->agentArg1, agent1->agentArg2, agent1->agentArg3);
	int retTemp = PMU(agent1->agentArg1, agent1->agentArg2, agent1->agentArg3);
	return NULL;
}

void startPMU(char* a, char* b, char* c)
{
	log_info(logger,"entering startPMU");
	struct agentArgs* agent = (struct agentArgs *)malloc(sizeof(struct agentArgs));
	strcpy(agent->agentArg1, a);
	strcpy(agent->agentArg2, b);
	strcpy(agent->agentArg3, c);
	log_info(logger,"PMU: arg1 %s arg2 %s arg3 %s", agent->agentArg1, agent->agentArg2, agent->agentArg3);
	pthread_create(&pmuPid, NULL, tempStartPMU, agent);
	log_info(logger,"exiting startPMU function");
}

int main(int argc, char **argv)
{
	registerFunction("startRLS", "void", &startRLS, 3, "char*" ,"char*", "char*");
	registerFunction("startPMU", "void", &startPMU, 3, "char*" ,"char*", "char*");
	registerFunction("returnWhenRLSDone", "void", &returnWhenRLSDone, 0, NULL);
	agentStart(argc,argv);
}