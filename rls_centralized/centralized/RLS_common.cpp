#include "RLS_common.h"


extern "C" {

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
/*
void Resize_Matries(int PMU_Num, int Index, cube phi, mat lambda0){

	Index = ParaNum*(PMU_Num+1)+PMU_Num;	
	phi.set_size(SamNum, PMU_Num, Index);
	lambda0.set_size(Index,1); 	
	lambda.set_size(Index,1);    	
	R0.set_size(Index, Index); 
   	R0.zeros();
   	for (i=0; i<Index; i++)
       		R0(i,i) = 0.001; 
	P.set_size(Index, Index);  
	P = inv(diagmat(R0));	
	// Intermedia Parameters 
	error.set_size(Index,1);
	error.zeros();
   	tmp.set_size(Index,1);  	
   	tmp.zeros();
  	tmpmat.set_size(PMU_Num, Index);
   	tmpmat.zeros(); 
   	transtmpmat.set_size(Index, PMU_Num);
   	transtmpmat.zeros();
   	tmp1.set_size(PMU_Num, 1);
   	tmp1.zeros();
   	tmp2.set_size(PMU_Num,PMU_Num);
   	tmp2.zeros();
	y_N.set_size(PMU_Num, 1);
   	y_N.zeros();
}

*/
/*************************************************************
 * RLS_Server_handle. When a PMU connection request is accepted,
 * the handler receive the data packet and return the receive_packet_content. 
 * Before read the data packet, we do the timer to check if this TCP connection is broken or not
 * Created by Jianhua Zhang at April, 15th, 2014
 *************************************************************/
void *RLS_Server_handle(void * parmPtr)
{
        #define PARMPTR ((int *) parmPtr)
        int PMU_sockfd = *PARMPTR;

	// Timer
	struct timeval currenttime, start, timer;
	struct timeval timeout={TIMEOUT_SEC, TIMEOUT_USEC};
	
	// for read sock 
	fd_set read_sock;
        int select_ret; 

	// Prepare the file receiver buffer	
	int data_length;
	int last_flag; 

	// Prepare packet receiver buffer
	char *receive_packet;		
	if((receive_packet=(char *)malloc(SERVER_MAX_BUF+sizeof(struct TCP_header)))==NULL){
		cout<<"Fail to allocate memory for receive buffer, program is exiting ... "<<endl;
		exit(1);
	   }

	struct TCP_header *receive_packet_header=(struct TCP_header *)receive_packet;
	char *receive_packet_content=(char *)(receive_packet_header+1);
	char Buffer[SERVER_MAX_BUF];

	// =================================== Resiliency Mechanisim =====================================// 
        gettimeofday(&start, NULL);
	// initializes the set of active read sockets
	FD_ZERO(&read_sock);
	FD_SET(PMU_sockfd, &read_sock);
	
	// initializes time out - get the left time compared to timeout time			
	gettimeofday(&currenttime, NULL);
	cal_timer(&start, &currenttime, &timeout, &timer);
	cout<<"After "<<timer.tv_sec<<"."<<timer.tv_usec<<" sec, this connection will be time out. "<<endl;

	// select()
	select_ret = select(PMU_sockfd+1, &read_sock, NULL, NULL, &timer);
	cout<<"The value of select_ret is "<<select_ret<<endl;
	
	// check status
	if(select_ret <= 0){ // ============ error happens to this PMU or timeout when select_ret is 0  ===========//	

		cout<<"Something wrong with the connection of this PMU. Close this TCP connection and return broken message...."<<endl;
		close(PMU_sockfd);

		// Resiliency Strategies: Return the error message "This PMU is disconnected!!!"
		sprintf(Buffer, "Failed!!!\n");
		strcpy(receive_packet_content, Buffer);
		printf("Return Package contains \n %s \n", receive_packet_content);        	
		// =============== End of Resiliency Mechanisim ==============// 

	   } else {
			// ============If connection is good, and Accept data ===========//	
			read(PMU_sockfd, receive_packet, DEFAULT_MAX_BUFFER_LEN);		
			data_length = receive_packet_header->data_length;	
			last_flag = receive_packet_header->last_flag;
			//cout<<"Received Packet length is "<<packet_length<<endl;
			//memset(receive_packet_content+data_length*sizeof(char), '\0', 20);
			//printf("Package No %ld from PMU %d with size %d is \n %s \n", packet_no, PMU_sockfd, data_length, receive_packet_content);

			// Add information of packet_length to the receive_packet_content.
			sprintf(Buffer, "%d\n%d\n", last_flag, data_length);
			//cout<<"Verify last packet flag and data_length "<<Buffer<<endl;
			strncat(Buffer, receive_packet_content, data_length);
			strcpy(receive_packet_content, Buffer);
			//printf("Return Package contains \n %s \n", receive_packet_content);          		
		  }
	//printf("Return Package contains \n %s \n", receive_packet_content);  
	printf("this thread exits hahhaa. \n");
    	pthread_exit(receive_packet_content);

}
}
