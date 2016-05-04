#include "Prony_common.h"


extern "C" {

using namespace std;

/* declare mutex */
	pthread_mutex_t mymutex;

/* function to intilize mutex */
void Mutex_initialization(){
	pthread_mutex_init(&mymutex, NULL);
     }
/* destroy mutext */
void Mutex_destroy(){
	pthread_mutex_destroy(&mymutex);
     }

int timer_sub(const struct timeval *start_time, const struct timeval *end_time, struct timeval *result){

	if (end_time->tv_usec >= start_time->tv_usec){
		result->tv_sec = end_time->tv_sec - start_time->tv_sec;
                result->tv_usec =  end_time->tv_usec - start_time->tv_usec;          
           } else {
			result->tv_sec = end_time->tv_sec - 1 - start_time->tv_sec;
                	result->tv_usec =  end_time->tv_usec + 1000000 - start_time->tv_usec;       			
                  }
        return 0;
}


int cal_timer(const struct timeval * sending_time, const struct timeval * current_time, const struct timeval * timeout, struct timeval * timer){

	struct timeval timer_tmp_pointer;
        struct timeval *timer_tmp = &timer_tmp_pointer;
        // get the time duration of sending packet
        if (current_time->tv_usec >= sending_time->tv_usec){
		timer_tmp->tv_sec = current_time->tv_sec - sending_time->tv_sec;
                timer_tmp->tv_usec =  current_time->tv_usec - sending_time->tv_usec;          
           } else {
			timer_tmp->tv_sec = current_time->tv_sec - 1 - sending_time->tv_sec;
                	timer_tmp->tv_usec =  current_time->tv_usec + 1000000 - sending_time->tv_usec;       			
                  }
        // calculate if it is timeout or not
        if ((timer_tmp->tv_sec > timeout->tv_sec) || (timer_tmp->tv_sec == timeout->tv_sec && timer_tmp->tv_usec >= timeout->tv_usec)){

		timer->tv_sec = 0;
                timer->tv_usec = 0;
                return 0;   // timeout
            } else {
			if (timeout->tv_usec >= timer_tmp->tv_usec){

				timer->tv_sec = timeout->tv_sec - timer_tmp->tv_sec;
                                timer->tv_usec = timeout->tv_usec - timer_tmp->tv_usec;
                            } else {
					timer->tv_sec = timeout->tv_sec - 1 - timer_tmp->tv_sec;
                                	timer->tv_usec = timeout->tv_usec + 1000000 - timer_tmp->tv_usec;
                                   }
                        return 1;  // not timeout
                    }
}




/*************************************************************
 * Server_handle. For each TCP connection, Server need to read the local estimated
   parameters through each thread
 *************************************************************/
void *Server_handle(void * parmPtr)
{
        #define PARMPTR ((int *) parmPtr)
        int Client_sockfd = *PARMPTR;
	/* Claim receiving and transmitting buffer */
	char Buffer[DEFAULT_MAX_BUFFER_LEN];
	int BufferLen;
        int length;
	long int SendTime; 
	char ph2[512], pht[512];
	char *ph1;
        struct timeval tvalRecieve, tvalParse;
	
	/* lock mutex */
	pthread_mutex_lock (&mymutex);

	/* Read data from client, we here only read once.*/
	BufferLen=read(Client_sockfd, Buffer, DEFAULT_MAX_BUFFER_LEN);
	Buffer[BufferLen]=0;

 	gettimeofday (&tvalRecieve, NULL);
                   
        printf("Buffer message with size %d is \n %s", BufferLen, Buffer);
	
        // Parse messge 
	        	
	ph1 = strtok(Buffer, "\r\n");
	//strcpy(ph1, strtok(Buffer, "\r\n"));
        gettimeofday (&tvalParse, NULL);
        length = strlen(ph1);       
        //printf("Parsed First line message is %s with length %d. \n", ph1, length);	
	//ph2 = strtok(ph1+(length+1)*sizeof(char), "\r\n");
	strcpy(ph2, strtok(ph1+(length+1)*sizeof(char), "\r\n"));
        printf("Second Parsed message is %s\n", ph2);
        //pht = strtok(ph2, " ");
	//num = rand()%2;
	//if (num) sleep(1);
	strcpy(pht, strtok(ph2, " "));
        printf("First word in second line is %s\n", pht);
        //pht = strtok(NULL, " ");
	strcpy(pht, strtok(NULL, " "));
        printf("Second word in second line is %s\n", pht);      
        SendTime = strtol(pht, NULL, 10);
        printf("SendTime of message is %ld\n", SendTime); 

	/* unlock mutex */
	pthread_mutex_unlock (&mymutex);

        printf("Total communication time including data parse time in microseconds is %ld \n", (tvalParse.tv_sec)*1000000+tvalParse.tv_usec - SendTime);      
	//free(parmPtr);
        printf("this thread exits hahhaa. *********************\n\n");
    	pthread_exit(ph1);       
}

}
