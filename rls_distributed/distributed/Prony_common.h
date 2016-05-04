#include "rpoly.h"
#include "armadillo"

#include <cstring>
#include <cstdio>
#include <cstdlib>
#include <csignal>
#include <complex>
#include <ctime>
#include <cmath>
#include <cfloat>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <vector>

#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <netdb.h>
#include <netinet/in.h>
#include <pthread.h>
#include <signal.h>
#include <stdarg.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <sys/types.h>
#include <unistd.h>


extern "C" {

using namespace arma;
using namespace std;

//#define ClientNum 4  //There are four clients in Prony system
#define SamNum 90
//#define Height_H 60
#define NUM 10   // number of machine in the system;
#define PoleNum 2*NUM //  number of poles of Laplace transfer equation;
#define ParaNum PoleNum
#define Ts 0.2 // sampling time
//#define MSS 250
#define DEFAULT_QUEUE_LEN 10
#define DEFAULT_MAX_BUFFER_LEN 4096
#define SERVER_MAX_BUF 1500
#define MAX_FILENAME_LEN 50

#define TEMP_TIMEOUT_SEC 1500
#define TEMP_TIMEOUT_USEC 0
#define TIMEOUT_SEC 5
#define TIMEOUT_USEC 0

struct TCP_header
{
	long int packet_sending_time;
	long int packet_no;
	int last_flag;
	int data_length;
};

int timer_sub(const struct timeval *start_time, const struct timeval *end_time, struct timeval *result);
int cal_timer(const struct timeval * sending_time, const struct timeval * current_time, const struct timeval * timeout, struct timeval * timer);
void *Server_handle(void * parmPtr);
void Mutex_initialization();
void Mutex_destroy();
//void signal_callback_handler(int signum);

}
