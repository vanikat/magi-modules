#include "Prony_common.h"

#include "AgentMessenger.h"
#include "Logger.h"

#include "../rDistributed.h"

#include <string>
#include <iostream>

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


extern "C" {

#define MSS 250
#define rho 0.0005  // try smaller values, e.g. 1e-3, 1e-4, 1e-5;  0.06
#define Height_H 45
#define IniHeight 20

int attackResProtocol(char* backupserver1_host, char* backupserver2_host,
		char* backupserver3_host, char* backupserver4_host,
		char* backupserver_port, char* num_of_attack, char* num_of_pdcs,
		int num_attack, int sockfd, Logger* fLogger);

int PronyADMMClient(char* server_host, char* server_port, char* data_port,
		char* strategy, char* backupserver1_host, char* backupserver2_host,
		char* backupserver3_host, char* backupserver4_host,
		char* backupserver_port, char* num_of_attack, char* num_of_pdcs) {

    FILE* fFile;
    Logger* fLogger;
    fFile = fopen("/tmp/PronyADMM_client.log", "a");
    fLogger = Logger_create(fFile, 0);
    log_debug(fLogger,"Start Prony client");
    
	//For collecting event log and result
    int argc = 15;
	ofstream myfile;	
	char filename[50];
	char tempbuf1[5];
	char tempbuf2[5];
	char tempbuf3[5];
	char timebuffer[25];
	
	time_t now_time;
	time(&now_time);
	struct tm * tm_info;
	tm_info = localtime(&now_time);
	strcpy(filename, "/tmp/DistriProny_Result_");
	strcat(filename, data_port);

	strcat(filename, "_");
	snprintf(tempbuf1, 5, "%d", tm_info->tm_year+1900);	
	strcat(filename, tempbuf1);

	strcat(filename, "-");
	//itoa(now->tm_mon + 1, tempbuf2, 10);
	snprintf(tempbuf2, 5, "%d", tm_info->tm_mon + 1);	
	strcat(filename, tempbuf2);

	strcat(filename, "-");
	//itoa(now->tm_mday, tempbuf3, 10);
	snprintf(tempbuf3, 5, "%d", tm_info->tm_mday);	
	strcat(filename, tempbuf3);

	strcat(filename, ".txt");
	
	myfile.open(filename);
	
	int Iteration = 0; // Iteration = packet_no
	int counter = 0;
	int num_attack = 0;
	int i = 0;
	int Algorithm_Finishes = 0;
	struct timeval tvalStart, Start, End, Result, algo_start_time, timeout;

    gettimeofday (&Start, NULL);

	// Read sock for connection monitor of resiliency mechanism
	fd_set readfds;
    int select_ret; 

	// Declare a vector for store the sample data
	vector<double> theta;
	theta.clear();	

	//===============1. Setup a TCP connection of client for sending localpara to main Prony_server============//

    struct hostent *he;
    struct in_addr **addr_list;
    char* ip;

    if ((he = gethostbyname(server_host)) == NULL) {  // get the host info
       exit(1);
    }

    // print information about this host:
    addr_list = (struct in_addr **)he->h_addr_list;
    for(i = 0; addr_list[i] != NULL; i++) {
        ip = inet_ntoa(*addr_list[i]);
    }

  	int sockfd = 0;
   	struct sockaddr_in serv_addr;

    memset(&serv_addr, '0', sizeof(serv_addr));   
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(atoi(server_port));

   	if(inet_pton(AF_INET, ip, &serv_addr.sin_addr)<=0) {
        log_error(fLogger,"inet pton error");
        return 1;
    }

   	log_debug(fLogger, "Server Host: %s, IP: %s, Port:%s", server_host, ip, server_port);

	// Create a socket and connection with old server
	if((sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
		log_error(fLogger,"Could not create socket.");
        return 1;
    } 
	log_debug(fLogger,"Socket created");

    if(connect(sockfd, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) == -1) {
        log_error(fLogger,"connect() failed.");
        return 1;
    }
    log_debug(fLogger,"TCP Connection has been set up");
	

	//===============2. Setup a TCP connection of server for receiving sample data from PMU============//
	// Set up TCP socket of server side for collecting PMU measurements for single PMU machine

	int Server_sockfd, data_sockfd;
	struct sockaddr_in LocalAddr, PMU_address;
	int Client_len = sizeof(PMU_address);

	// Initiate local TCP server socket
	LocalAddr.sin_family = AF_INET;
	LocalAddr.sin_addr.s_addr = htonl(INADDR_ANY);
	LocalAddr.sin_port = htons(atoi(data_port));

	// Create, bind and listen the TCP_socket 
	Server_sockfd = socket(AF_INET, SOCK_STREAM, 0);

	if (bind(Server_sockfd, (struct sockaddr *)&LocalAddr, sizeof(LocalAddr)) < 0) {
        log_debug(fLogger,"bind issue");
		cout<<"Error: Can not bind the TCP socket! \n Please wait a few seconds or change port number."<<endl;
		return 1;
	}
    
	listen(Server_sockfd, DEFAULT_QUEUE_LEN);
	data_sockfd = accept(Server_sockfd,(struct sockaddr *)&PMU_address, (socklen_t*)&Client_len);
	printf("PMU Connection has been accepted and Prony VM is waiting for data ...\n");


	//===============3. Parameters for Receiving PMU data and Parse data ====================//	
	// Declare char pointer to token when parsing data
	char *token;
	string last;
	char b, lastchar;
	last = &b;
	int length, last_flag;
	int j, k;
	char Buffer[DEFAULT_MAX_BUFFER_LEN] = {0};
	char tempBuffer[DEFAULT_MAX_BUFFER_LEN];	
	unsigned data_length;
	long int packet_send_time;
	// Prepare packet receiver buffer
	char *receive_packet;		
	if((receive_packet=(char *)malloc(SERVER_MAX_BUF+sizeof(struct TCP_header)))==NULL) {
		cout<<"Fail to allocate memory for receive buffer, program is exiting ... "<<endl;
		exit(1);
    }

	struct TCP_header *receive_packet_header=(struct TCP_header *)receive_packet;
	char *receive_packet_content=(char *)(receive_packet_header+1);

	//================4. Calculate initial parameter vector a ================================//
		
	// Construct Intermedia Matrix H, C, a 
	mat I(ParaNum, ParaNum);
	mat a(ParaNum,1);
	mat new_a(ParaNum,1);
	mat avgpara(ParaNum,1);
	mat new_avgpara(ParaNum,1);
	mat w(ParaNum,1);
	mat new_w(ParaNum,1);
	mat H(IniHeight,ParaNum);
	mat C(IniHeight,1);
	int TT;

    for (i=0; i<ParaNum; i++) { 
        for (j=0; j<ParaNum; j++) {
            if (i==j){
                I(i,j) = 1;
            } else {
                I(i,j) = 0;
            }
        }
    }
	
	for (i=0; i<ParaNum; i++) { 
		a(i,0) = 1;
		w(i,0) = 0;
		avgpara(i,0) = 1;
    }

	//===============5. Parameters for Exchange Estimated Parameters with Server=====================//	
	// form localpara message 
	char* buffer = (char*)malloc(512*sizeof(char));
   	int size, avgBufferLen, flag;
	
	// Prepare receive buffer for avgpara
	char *avgBuffer = (char*)malloc(512*sizeof(char));

	// For calculate new local parameters
	char *pht;

	// ======================= Main loop: Receive PMU data and Parse data and PronyADMM =========================// 

    while(1) {
        log_debug(fLogger,"Main loop begin. Iteration: %d", Iteration);
        
        read(data_sockfd, receive_packet, DEFAULT_MAX_BUFFER_LEN);		
        data_length = receive_packet_header->data_length;	
        last_flag = receive_packet_header->last_flag;
        packet_send_time = receive_packet_header->packet_sending_time;

        // If this is not last package, request next one
        if (last_flag == 0) {
            size=sprintf(tempBuffer, "Request Next Package %d! \r\n\r\n",(Iteration+1));	
            printf( "Prony client VM Writes:\n %s \n", tempBuffer);        	
            write(data_sockfd, tempBuffer, size); 
            // end request next one
        }
        
        memset(Buffer, '\0', 15);
        
        //log_debug(fLogger, "The length of last string is %d", last.length());
        
        if((last.length()!= 0) && (Iteration != 0)) strncat(Buffer, last.c_str(), last.length()+1);
        strncat(Buffer, receive_packet_content, data_length);
        lastchar = Buffer[last.length()*sizeof(char)+data_length-1]; 

        //log_debug(fLogger, "After receive packet %d,  Buffer contains \n %s \n", Iteration, Buffer);
        
        memset(Buffer+(last.length()+data_length+1)*sizeof(char), '\0', 20);

        // ================= Parse the data from the Buffer ================= //
        length = 0;
        while (1) {
            token = strtok(Buffer+length*sizeof(char), "\n");
            if (token == NULL){
                if(last_flag == 0) theta.pop_back();  //if this is not last packet, the last record is discarded.
                break;	
            } 
            last = token;

            //log_debug(fLogger, "The data is %s", token);

            theta.push_back(strtod(token, NULL));						
            length = length + strlen(token) + 1;
        } // end of parsing data
           
        if (lastchar == '\n') 
            last.append("\n"); 

        for (i=0; i<(int)theta.size(); i++) 
            //cout<<"theta["<<i<<"] is "<<theta[i]<<endl;

        // (II): Process each sample in this packet
        if (theta.size() >= IniHeight+ParaNum) {

        	log_debug(fLogger, "size of theta is %d", theta.size());

        	for (k=counter; k<(int)theta.size(); k++) {

        		log_debug(fLogger, "Iteration: %d", k);

        		gettimeofday(&algo_start_time, NULL);
                // Step 1: Update matrice H and C, and Calculate new_a 
                if (IniHeight+floor(k/5)<Height_H){
                    TT = IniHeight + floor(k/5);
                } else {
                    TT = Height_H;
                }

                H.set_size(TT,ParaNum); 
                C.set_size(TT,1); 

                for (i=0; i<TT; i++){
                    C(i,0) = theta[ParaNum+i];
                }  //Note: we donot update C matrix real-time
                //C.print("C is");

                for (i=0; i<TT; i++){
                    for (j=0; j<ParaNum; j++){
                        H(i,j) = theta[i+ParaNum-1-j];
                    }
                }	

                new_a = inv(trans(H)*H + rho*I)*(trans(H) * C - w + rho*avgpara);

                // Step 2: Send out local parameter vector new_a			
                gettimeofday (&tvalStart, NULL); // Record sending time
                // Format the export message
                size = sprintf(buffer, "Iteration: %d, %s: %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f\r\n Starttime: %ld \r\n\r\n",
                		k, data_port, new_a(0), new_a(1), new_a(2), new_a(3), new_a(4), new_a(5), new_a(6), new_a(7), new_a(8),
						new_a(9), new_a(10), new_a(11), new_a(12), new_a(13), new_a(14), new_a(15), new_a(16), new_a(17), new_a(18),
						new_a(19), (tvalStart.tv_sec*1000000 + tvalStart.tv_usec));
                
                //log_debug(fLogger, "The value of size is %d", size);

                log_debug(fLogger, "Sending message with time %ld", (tvalStart.tv_sec*1000000 + tvalStart.tv_usec));

                // =========================== Resiliency Mechanism ===========================//
                //log_debug(fLogger, "Writing to server");
                flag = write(sockfd, buffer, size);
                if (flag <= 0) {
                	log_debug(fLogger, "Main server got attacked because the return value of write() function is negative.");
                	num_attack++;
                    sockfd = attackResProtocol(backupserver1_host,
                    		                   backupserver2_host,
											   backupserver3_host,
											   backupserver4_host,
											   backupserver_port, num_of_attack,
											   num_of_pdcs, num_attack,
											   sockfd, fLogger);
                    write(sockfd, buffer, size); // Write the local estimation to new server
                } 
                //log_debug(fLogger, "Write successful");

                if (Iteration == 1) {
                	timeout.tv_sec = TEMP_TIMEOUT_SEC;
                	timeout.tv_usec = TEMP_TIMEOUT_USEC;
                } else {
                	timeout.tv_sec = TIMEOUT_SEC;
                	timeout.tv_usec = TIMEOUT_USEC;
                }

                // initializes the set of active read sockets
                FD_ZERO(&readfds);
                FD_SET(sockfd, &readfds);

                log_debug(fLogger, "Selecting sockets to read");
                select_ret = select(sockfd+1, &readfds, NULL, NULL, &timeout);
                log_debug(fLogger,"Return value of select is %d", select_ret);

                if(select_ret <= 0) { //case: error or timeout of select_ret is 0
                    num_attack++;
                    log_debug(fLogger,"Main Server's link got attacked because the read() function times out.");
                    sockfd = attackResProtocol(backupserver1_host,
                    		                   backupserver2_host,
											   backupserver3_host,
											   backupserver4_host,
											   backupserver_port, num_of_attack,
											   num_of_pdcs, num_attack,
											   sockfd, fLogger);
                    write(sockfd, buffer, size); // Write the local estimation to new server
                }// end if
                //log_debug(fLogger, "Select successful");


                // ========================== End of Resiliency Mechanisim ==========================// 
                //log_debug(fLogger, "Reading from server");
                avgBufferLen = read(sockfd, avgBuffer, DEFAULT_MAX_BUFFER_LEN);
                log_debug(fLogger,"Return value of read is %d", avgBufferLen);

                if (avgBufferLen <= 0) {
                	num_attack++;
                	log_info(fLogger,"Main server got attacked because the return value of read() function is negative. Error: %d", errno);
                	sockfd = attackResProtocol(backupserver1_host,
											   backupserver2_host,
											   backupserver3_host,
											   backupserver4_host,
											   backupserver_port, num_of_attack,
											   num_of_pdcs, num_attack,
											   sockfd, fLogger);
                    write(sockfd, buffer, size); // Write the local estimation to new server
                    avgBufferLen = read(sockfd, avgBuffer, DEFAULT_MAX_BUFFER_LEN);
                } 
                //log_debug(fLogger, "Read successful");
                
                avgBuffer[avgBufferLen]=0;
                if (strcmp(avgBuffer,"Distributed Prony Alogrithm finishes! \r\n\r\n")==0) {
                    Algorithm_Finishes = 1;
                    log_info(fLogger,"Distributed Prony Alogrithm finishes!");
                    break;
                }

                //Parse new_avgpara
                pht = strtok(avgBuffer, " ");
                pht = strtok(NULL, " ");
                pht = strtok(NULL, " ");
                //printf("This should be %s\n", pht);
                for (j=0; j<ParaNum; j++){
                    pht = strtok(NULL, " ");
                    new_avgpara(j,0) = strtod(pht, NULL);
                }

                // Step 4: Update newer matrix C, H, and local para, Iteration ====================/
                new_w = w + rho*(new_a - new_avgpara);
                a = new_a;
                avgpara = new_avgpara;
                w = new_w;	

            }//end of for loop
            break;
        }//end of if sentence with theta.size()>initialHeight

        log_debug(fLogger,"End of Main loop. Iteration: %d", Iteration);

        if (Algorithm_Finishes == 1)
        	break;

        counter = theta.size();
        Iteration++;	
	
    } //end big while loop
	
	if (Algorithm_Finishes == 1) {
		size = sprintf(tempBuffer, "Distributed Prony Alogrithm finishes! \r\n\r\n");
		printf( "Prony Client VM Writes to PMU machine:\n %s \n", tempBuffer);  
		write(data_sockfd, tempBuffer, size); 
    }

	close(sockfd);
 	log_debug(fLogger,"Prony algorithm ends happily.  ^_^");

 	gettimeofday (&End, NULL);
 	timer_sub(&Start, &End, &Result);

    fclose(fFile);
    return 0;

} /* end of PronyADMMClient */

int attackResProtocol(char* backupserver1_host, char* backupserver2_host,
		char* backupserver3_host, char* backupserver4_host,
		char* backupserver_port, char* num_of_attack, char* num_of_pdcs,
		int num_attack, int sockfd, Logger* fLogger) {

	time_t now_time;
	struct tm * tm_info;
	char timebuffer[25];

	log_debug(fLogger,"Something wrong with the connection of old server. Disconnecting.");
	shutdown(sockfd, SHUT_RDWR);
    close(sockfd);

	log_debug(fLogger,"Attack Number %d", num_attack);

	char* backupserver_host;
	if (num_attack==1) {
		backupserver_host = backupserver1_host;
	}
	if (num_attack==2) {
		backupserver_host = backupserver2_host;
	}
	if (num_attack==3) {
		backupserver_host = backupserver3_host;
	}
	if (num_attack==4) {
		backupserver_host = backupserver4_host;
	}

	log_debug(fLogger,"Backup Server Host: %s", backupserver_host);

	if (atoi(num_of_attack) == num_attack) {
		//Strategy 1: run server source code in the fourth backup Client 4 VM background
		log_debug(fLogger, "This node itself is the next backup server");
		log_debug(fLogger,"Starting ADMM Server");
		startServer(num_of_pdcs, backupserver_port);
		log_debug(fLogger,"New ADMM Server started at PDC");
	}

	struct sockaddr_in new_serv_addr;
    memset(&new_serv_addr, '0', sizeof(new_serv_addr));
    new_serv_addr.sin_family = AF_INET;

    //Strategy 0&1: backup server or run a server side at client1
    // Create a socket and connection with predefined new server
    struct hostent *he1;
    struct in_addr **addr_list1;
    char* bkpsvr_ip;

    if ((he1 = gethostbyname(backupserver_host)) == NULL) {  // get the host info
		exit(1);
	}

	addr_list1 = (struct in_addr **)he1->h_addr_list;
	for(int i = 0; addr_list1[i] != NULL; i++) {
		bkpsvr_ip = inet_ntoa(*addr_list1[i]);
	}

	log_debug(fLogger, "Connecting to Backup Server");
	log_debug(fLogger, "Server Host: %s, IP: %s, Port:%s", backupserver_host, bkpsvr_ip, backupserver_port);

	new_serv_addr.sin_port = htons(atoi(backupserver_port));
	if(inet_pton(AF_INET, bkpsvr_ip, &new_serv_addr.sin_addr)<=0){
		log_error(fLogger,"inet_pton error occurred");
		return 1;
	}

	int new_sockfd;

    if((new_sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0){
    	log_error(fLogger,"Could not create socket.");
    	return 1;
    }
    log_debug(fLogger,"Socket created");

    while (1){
        if(connect(new_sockfd, (struct sockaddr *)&new_serv_addr, sizeof(new_serv_addr)) < 0){
        	//log_debug(fLogger,"Connect failed. Will try again.");
        	continue;
        } else {
        	log_debug(fLogger,"New TCP connection setup successfully.");
            break;
        }
    } //end-while

    return new_sockfd;
}


} // extern C
