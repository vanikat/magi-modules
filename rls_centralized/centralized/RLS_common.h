#include <cstring>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <cstdio>
#include <cstdlib>
#include <csignal>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <stdbool.h>
#include <ctime>
#include <cmath>
#include <cfloat>
#include <fstream>
#include <iostream>
#include <pthread.h>
#include <complex>
#include "armadillo"
#include "rpoly.h"
#include <fcntl.h>
#include <vector>
#include <errno.h>
#include <iomanip>

extern "C" {
using namespace arma;
using namespace std;

#define MSS 250
#define DEFAULT_QUEUE_LEN 20
#define DEFAULT_MAX_BUFFER_LEN 4096
#define SERVER_MAX_BUF 1500
#define MAX_FILENAME_LEN 50
//#define SamNum 90
#define NUM 10   // number of machine in the system;
#define ParaNum 2*NUM //  number of poles of Laplace transfer equation;
#define Ts 0.2 // sampling time
//#define ERROR 0.000000000000000001

#define TIMEOUT_SEC 1
#define TIMEOUT_USEC 0


struct serverParm {
           int Client_sockfd ;
       };

struct TCP_header
{
	long int packet_sending_time;
	long int packet_no;
	int last_flag;
	int data_length;
};

struct PMU_measure
{
	int PMU_no;
	int Data_index;
	double PMU_data;
};

static volatile int Exit_Flag = 0;


int timer_sub(const struct timeval *start_time, const struct timeval *end_time, struct timeval *result);
int cal_timer(const struct timeval * sending_time, const struct timeval * current_time, const struct timeval * timeout, struct timeval * timer);
void *RLS_Server_handle(void * parmPtr);
}
