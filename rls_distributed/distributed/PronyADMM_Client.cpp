#include "Prony_common.h"

#include "AgentMessenger.h"
#include "Logger.h"

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

int PronyADMMClient(char* server_host, char* server_port, char* data_port,
		char* strategy, char* backupserver1_host, char* backupserver1_port,
		char* backupserver2_host, char* backupserver2_port,
		char* backupserver3_host, char* backupserver3_port,
		char* backupserver4_host, char* backupserver4_port,
		char* num_of_attack, char* num_of_pdcs) {

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
	struct timeval tvalStart, currenttime, Start, End, Result, algo_start_time, timer;
	struct timeval timeout={TIMEOUT_SEC, TIMEOUT_USEC};
	struct timeval temp_timeout={TEMP_TIMEOUT_SEC, TEMP_TIMEOUT_USEC};
	
    gettimeofday (&Start, NULL);
	// Read sock for connection monitor of resiliency mechanism
	fd_set read_sock;
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
	int new_sockfd = 0;
   	struct sockaddr_in serv_addr, new_serv_addr;       
    memset(&serv_addr, '0', sizeof(serv_addr));   
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(atoi(server_port));

   	if(inet_pton(AF_INET, ip, &serv_addr.sin_addr)<=0) {
        printf("\n inet_pton error occured\n");
        log_debug(fLogger,"inet pton error");
        return 1;
    } 
	// Create a socket and connection with old server
	if((sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        printf("\n Error : Could not create socket \n");
        log_debug(fLogger,"socket erroe");
        return 1;
    } 
    
    if(connect(sockfd, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) == -1) {
        cout<<"connect() failed."<<endl;
        log_debug(fLogger,"connection failed");
        return 1;
    } else {
        log_debug(fLogger,"connection is up");
        printf("\n TCP Connection has been set up\n");
    }	
	
	//===============2. Setup a TCP connection of server for receving sample data from PMU============//
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
	struct timeval start;
	char *pht;

	// ======================= Main loop: Receive PMU data and Parse data and PronyADMM =========================// 

    while(1) {
        cout<<"====================== Iteration  "<<Iteration<<"  ======================"<<endl;
        
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
        
        #ifdef DEBUG
            cout<<"The length of last string is "<<last.length()<<endl;
        #endif
        
        if((last.length()!= 0) && (Iteration != 0)) strncat(Buffer, last.c_str(), last.length()+1);
        strncat(Buffer, receive_packet_content, data_length);
        lastchar = Buffer[last.length()*sizeof(char)+data_length-1]; 

        #ifdef DEBUG
            printf("After receive packet %d,  Buffer contains \n %s \n", Iteration, Buffer);
        #endif		
        
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
        #ifdef DEBUG
            cout<<"The data is "<<token<<endl;
        #endif
            theta.push_back(strtod(token, NULL));						
            length = length + strlen(token) + 1;
        } // end of parsing data
           
        if (lastchar == '\n') 
            last.append("\n"); 

        for (i=0; i<(int)theta.size(); i++) 
            //cout<<"theta["<<i<<"] is "<<theta[i]<<endl;

        // (II): Process each sample in this packet
        if (theta.size() >= IniHeight+ParaNum){  
            cout<<"size of theta is "<<theta.size()<<endl; 				
            for (k=counter; k<(int)theta.size(); k++) {
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
                size = sprintf(buffer, "Iteration: %d, %s: %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f\r\n Starttime: %ld \r\n\r\n", k, data_port, new_a(0), new_a(1), new_a(2), new_a(3), new_a(4), new_a(5), new_a(6), new_a(7), new_a(8), new_a(9), new_a(10), new_a(11), new_a(12), new_a(13), new_a(14), new_a(15), new_a(16), new_a(17), new_a(18), new_a(19), (tvalStart.tv_sec*1000000 + tvalStart.tv_usec));

                 cout<<"The value of size is "<<size<<endl;
                
                // =========================== Resiliency Mechanisim ===========================// 
                flag = 0;
                cout<<"Before write function. "<<endl;  
                flag = write(sockfd, buffer, size);
                cout<<"Return value is "<< flag <<" at Iteration index "<<k<<endl;
 
                if (flag <= 0) {
                    perror ("The following error occurred ");		
                    cout<<"Something wrong with the connection of old server. Try to connect to the new one ...."<<endl;
                    close(sockfd);
                    num_attack++;
                    cout<<"Num of attacks is "<<num_attack<<endl;
                    time(&now_time);
                    tm_info = localtime(&now_time);
                    strftime(timebuffer, 25, "%Y:%m:%d  %H:%M:%S", tm_info);
                    
                    myfile << timebuffer;
                    myfile << "  At IterationNum  ";
                    myfile << k;
                    myfile << ": For Attack Number ";
                    myfile << num_attack;
                    myfile << ", Main Server itself got attacked becasue the return value of write() function is negative!!!\n";
                    
                    if (argc==15) {					
                        if (atoi(num_of_attack)==1 && num_attack==1) {
                            //Strategy 1: run server source code in the first backup Client 1 VM background	
                            puts("Starting now:");
                            cout<<"Num of attacks is "<<num_attack<<endl;
                            char command[50];
                            strcpy(command, "ADMMServer ");
                            strcat(command, num_of_pdcs);
                            strcat(command, " ");				
                            strcat(command, backupserver1_port);
                            strcat(command, " &");
                            system(command);
                            std::cout<<"Happy New Server at PDC"<<std::endl;		
                        } 
                        if (atoi(num_of_attack)==2 && num_attack==2) {
                            //Strategy 1: run server source code in the second backup Client 2 VM background					
                            puts("Starting now:");
                            cout<<"Num of attacks is "<<num_attack<<endl;
                            char command[50];
                            strcpy(command, "ADMMServer ");
                            strcat(command, num_of_pdcs);
                            strcat(command, " ");
                            strcat(command, backupserver2_port);
                            strcat(command, " &");
                            system(command);
                            std::cout<<"Happy New Server at PDC"<<std::endl;		
                        }
                        if (atoi(num_of_attack)==3 && num_attack==3) {
                            //Strategy 1: run server source code in the third backup Client 3 VM background	
                            puts("Starting now:");
                            cout<<"Num of attacks is "<<num_attack<<endl;
                            char command[50];
                            strcpy(command, "ADMMServer ");
                            strcat(command, num_of_pdcs);
                            strcat(command, " ");				
                            strcat(command, backupserver3_port);
                            strcat(command, " &");
                            system(command);
                            std::cout<<"Happy New Server at PDC"<<std::endl;		
                        } 
                        if (atoi(num_of_attack)==4 && num_attack==4) {
                            //Strategy 1: run server source code in the fourth backup Client 4 VM background					
                            puts("Starting now:");
                            cout<<"Num of attacks is "<<num_attack<<endl;
                            char command[50];
                            strcpy(command, "ADMMServer ");
                            strcat(command, num_of_pdcs);
                            strcat(command, " ");
                            strcat(command, backupserver4_port);
                            strcat(command, " &");
                            system(command);
                            std::cout<<"Happy New Server at PDC"<<std::endl;		
                        }
                    } // if argc == 15

                    //Strategy 0&1: backup server or run a server side at client1
                    // Create a socket and connection with predefined new server
                    struct hostent *he1; 
                    struct in_addr **addr_list1; 
                    char* ip1;

                    memset(&new_serv_addr, '0', sizeof(new_serv_addr));   
                    new_serv_addr.sin_family = AF_INET;

                    if (num_attack==1) {
                        new_serv_addr.sin_port = htons(atoi(backupserver1_port));
                        if ((he1 = gethostbyname(backupserver1_host)) == NULL) {  // get the host info
                            exit(1);
                        }

                        addr_list1 = (struct in_addr **)he1->h_addr_list;
                        for(i = 0; addr_list1[i] != NULL; i++) {
                            ip1 = inet_ntoa(*addr_list1[i]);
                        }
                        
                        if(inet_pton(AF_INET, ip1, &new_serv_addr.sin_addr)<=0){
                            printf("\n inet_pton error occured\n");
                            return 1;
                        }
                    } 
                    if (num_attack==2) {
                        if ((he1 = gethostbyname(backupserver2_host)) == NULL) {  // get the host info
                            exit(1);
                        }

                        addr_list1 = (struct in_addr **)he1->h_addr_list;
                        for(i = 0; addr_list1[i] != NULL; i++) {
                            ip1 = inet_ntoa(*addr_list1[i]);
                        }
                        
                        new_serv_addr.sin_port = htons(atoi(backupserver2_port));
                        if(inet_pton(AF_INET, ip1, &new_serv_addr.sin_addr)<=0){
                            printf("\n inet_pton error occured\n");
                            return 1;
                        }
                    } 
                    if (num_attack==3) {
                        if ((he1 = gethostbyname(backupserver3_host)) == NULL) {  // get the host info
                            exit(1);
                        }

                        addr_list1 = (struct in_addr **)he1->h_addr_list;
                        for(i = 0; addr_list1[i] != NULL; i++) {
                            ip1 = inet_ntoa(*addr_list1[i]);
                        }
                        
                        new_serv_addr.sin_port = htons(atoi(backupserver3_port));
                        if(inet_pton(AF_INET, ip1, &new_serv_addr.sin_addr)<=0){
                            printf("\n inet_pton error occured\n");
                            return 1;
                          }
                    } 
                    if (num_attack==4) {
                        if ((he1 = gethostbyname(backupserver4_host)) == NULL) {  // get the host info
                            exit(1);
                        }

                        addr_list1 = (struct in_addr **)he1->h_addr_list;
                        for(i = 0; addr_list1[i] != NULL; i++) {
                                ip1 = inet_ntoa(*addr_list1[i]);
                        }
                        
                        new_serv_addr.sin_port = htons(atoi(backupserver4_port));
                        if(inet_pton(AF_INET, ip1, &new_serv_addr.sin_addr)<=0){
                            printf("\n inet_pton error occured\n");
                            return 1;
                          }
                    }
                    
                    if((new_sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0){
                        printf("\n Error : Could not create new socket \n");
                        return 1;
                    }
                    
                    while (1){
                        if(connect(new_sockfd, (struct sockaddr *)&new_serv_addr, sizeof(new_serv_addr)) < 0){
                            printf("\n Error : New connect Failed \n");
                        } else {
                            printf("\n New TCP Connection has been set up\n");
                            break;
                        }
                    } //end-while
                    
                    sockfd = new_sockfd;	
                    write(sockfd, buffer, size); // Write the local estimation to new server
                } 

                gettimeofday(&start, NULL);
                // initializes the set of active read sockets
                FD_ZERO(&read_sock);
                FD_SET(sockfd, &read_sock);

                // initializes time out - get the left time compared to timeout time			
                gettimeofday(&currenttime, NULL);
                if (Iteration == 1){		
                    cal_timer(&start, &currenttime, &temp_timeout, &timer);	
                } else {
                    cal_timer(&start, &currenttime, &timeout, &timer);
                }

                select_ret = select(sockfd+1, &read_sock, NULL, NULL, &timer);

                if(select_ret <= 0) { //case: error or timeout of select_ret is 0
                    close(sockfd);
                    num_attack++;
                    cout<<"Num of attacks is "<<num_attack<<endl;

                    time(&now_time);
                    tm_info = localtime(&now_time);
                    strftime(timebuffer, 25, "%Y:%m:%d  %H:%M:%S", tm_info);
                    myfile << timebuffer;
                    myfile << "  At IterationNum  ";
                    myfile << k;
                    myfile << ": For Attack Number ";
                    myfile << num_attack;
                    myfile << ", Main Server's link got attacked becasue the read() function times out!!!\n";

                    // 2 Resiliency Strategies
                    char filename[20];
                    strcpy(filename,data_port);
                    if (argc==15) {
                        if (atoi(num_of_attack)==1 && num_attack==1) {
                            //Strategy 1: run server source code in the first backup Client 1 VM background	
                            puts("Starting now:");
                            char command[50];
                            strcpy(command, "ADMMServer ");
                            strcat(command, num_of_pdcs);
                            strcat(command, " ");				
                            strcat(command, backupserver1_port);
                            strcat(command, " &");
                            system(command);
                            std::cout<<"Happy New Server at PDC"<<std::endl;			
                        } 
                        if (atoi(num_of_attack)==2 && num_attack==2) {
                            //Strategy 1: run server source code in the second backup Client 1 VM background					
                            puts("Starting now:");
                            char command[50];
                            strcpy(command, "ADMMServer ");
                            strcat(command, num_of_pdcs);
                            strcat(command, " ");
                            strcat(command, backupserver2_port);
                            strcat(command, " &");
                            system(command);
                            std::cout<<"Happy New Server at PDC"<<std::endl;			
                        }
                        if (atoi(num_of_attack)==3 && num_attack==3) {
                            //Strategy 1: run server source code in the third backup Client 3 VM background	
                            puts("Starting now:");
                            cout<<"Num of attacks is "<<num_attack<<endl;
                            char command[50];
                            strcpy(command, "ADMMServer ");
                            strcat(command, num_of_pdcs);
                            strcat(command, " ");				
                            strcat(command, backupserver3_port);
                            strcat(command, " &");
                            system(command);
                            std::cout<<"Happy New Server at PDC"<<std::endl;		
                        } 
                        if (atoi(num_of_attack)==4 && num_attack==4) {
                            //Strategy 1: run server source code in the fourth backup Client 4 VM background					
                            puts("Starting now:");
                            cout<<"Num of attacks is "<<num_attack<<endl;
                            char command[50];
                            strcpy(command, "ADMMServer ");
                            strcat(command, num_of_pdcs);
                            strcat(command, " ");
                            strcat(command, backupserver4_port);
                            strcat(command, " &");
                            system(command);
                            std::cout<<"Happy New Server at PDC"<<std::endl;		
                        }

                    }
                    //Strategy 0&1: backup server or run a server side at client1
                    //Create a client socket and connection with predefined new server
                    struct hostent *he2;
                    struct in_addr **addr_list2;
                    char* ip2;

                    memset(&new_serv_addr, '0', sizeof(new_serv_addr));   
                    new_serv_addr.sin_family = AF_INET;   

                    if (num_attack==1) {
                        if ((he2 = gethostbyname(backupserver1_host)) == NULL) {  // get the host info
                            exit(1);
                        }

                        addr_list2 = (struct in_addr **)he2->h_addr_list;
                        for(i = 0; addr_list2[i] != NULL; i++) {
                            ip2 = inet_ntoa(*addr_list2[i]);
                        }
                        
                        new_serv_addr.sin_port = htons(atoi(backupserver1_port));
                        if(inet_pton(AF_INET, ip2, &new_serv_addr.sin_addr)<=0){
                            printf("\n inet_pton error occured\n");
                            return 1;
                        }
                    } 
                    if (num_attack==2) {
                        if ((he2 = gethostbyname(backupserver2_host)) == NULL) {  // get the host info
                            exit(1);
                        }

                        addr_list2 = (struct in_addr **)he2->h_addr_list;
                        for(i = 0; addr_list2[i] != NULL; i++) {
                            ip2 = inet_ntoa(*addr_list2[i]);
                        }
                        
                        new_serv_addr.sin_port = htons(atoi(backupserver2_port));
                        if(inet_pton(AF_INET, ip2, &new_serv_addr.sin_addr)<=0){
                            printf("\n inet_pton error occured\n");
                            return 1;
                        }
                    }
                    if (num_attack==3) {
                        if ((he2 = gethostbyname(backupserver3_host)) == NULL) {  // get the host info
                            exit(1);
                        }

                        addr_list2 = (struct in_addr **)he2->h_addr_list;
                        for(i = 0; addr_list2[i] != NULL; i++) {
                                ip2 = inet_ntoa(*addr_list2[i]);
                        }
                        
                        new_serv_addr.sin_port = htons(atoi(backupserver3_port));
                        if(inet_pton(AF_INET, ip2, &new_serv_addr.sin_addr)<=0){
                            printf("\n inet_pton error occured\n");
                            return 1;
                        }
                    } 
                    if (num_attack==4) {
                        if ((he2 = gethostbyname(backupserver4_host)) == NULL) {  // get the host info
                            exit(1);
                        }

                        addr_list2 = (struct in_addr **)he2->h_addr_list;
                        for(i = 0; addr_list2[i] != NULL; i++) {
                            ip2 = inet_ntoa(*addr_list2[i]);
                        }
                        
                        new_serv_addr.sin_port = htons(atoi(backupserver4_port));
                        if(inet_pton(AF_INET, ip2, &new_serv_addr.sin_addr)<=0){
                            printf("\n inet_pton error occured\n");
                            return 1;
                        }
                    }  
                    
                    if((new_sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
                        printf("\n Error : Could not create new socket \n");
                        return 1;
                    }
                    
                    while (1) {
                        if(connect(new_sockfd, (struct sockaddr *)&new_serv_addr, sizeof(new_serv_addr)) < 0){
                            printf("\n Error : New connect Failed \n");
                        } else {
                            printf("\n New TCP Connection has been set up\n");
                            break;
                        }
                     } //end-while
                    
                    sockfd = new_sockfd;	
                    write(sockfd, buffer, size);
                    
                }// end if

                // ========================== End of Resiliency Mechanisim ==========================// 
                //cout<<"Before the read() function!"<<endl;
                avgBufferLen = read(sockfd, avgBuffer, DEFAULT_MAX_BUFFER_LEN);
                //cout<<"Return value for read() is "<<avgBufferLen<<endl;
                if (avgBufferLen <= 0) {
                    perror ("The following error occurred ");		
                    cout<<"Something wrong with the connection of old server. Try to connect to the new one ...."<<endl;
                    close(sockfd);
                    num_attack++;
                    cout<<"Num of attacks is "<<num_attack<<endl;
                    
                    time(&now_time);
                    tm_info = localtime(&now_time);
                    strftime(timebuffer, 25, "%Y:%m:%d  %H:%M:%S", tm_info);
                    myfile << timebuffer;
                    myfile << "  At IterationNum  ";
                    myfile << k;
                    myfile << ": For Attack Number ";
                    myfile << num_attack;
                    myfile << ", main Server itself got attacked becasue the return value of read() function is negative!!!\n";
                    
                    if (argc==15) {
                        if (atoi(num_of_attack)==1 && num_attack==1) {
                            //Strategy 1: run server source code in the first backup Client 1 VM background	
                            puts("Starting now:");
                            char command[50];
                            strcpy(command, "ADMMServer ");
                            strcat(command, num_of_pdcs);
                            strcat(command, " ");				
                            strcat(command, backupserver1_port);
                            strcat(command, " &");
                            system(command);
                            std::cout<<"Happy New Server at PDC"<<std::endl;	
                        } 
                        if (atoi(num_of_attack)==2 && num_attack==2) {
                            //Strategy 1: run server source code in the second backup Client 1 VM background					
                            puts("Starting now:");
                            char command[50];
                            strcpy(command, "ADMMServer ");
                            strcat(command, num_of_pdcs);
                            strcat(command, " ");
                            strcat(command, backupserver2_port);
                            strcat(command, " &");
                            system(command);
                            std::cout<<"Happy New Server at PDC"<<std::endl;	
                        }
                        if (atoi(num_of_attack)==3 && num_attack==3) {
                            //Strategy 1: run server source code in the third backup Client 3 VM background	
                            puts("Starting now:");
                            cout<<"Num of attacks is "<<num_attack<<endl;
                            char command[50];
                            strcpy(command, "ADMMServer ");
                            strcat(command, num_of_pdcs);
                            strcat(command, " ");				
                            strcat(command, backupserver3_port);
                            strcat(command, " &");
                            system(command);
                            std::cout<<"Happy New Server at PDC"<<std::endl;		
                        } 
                        if (atoi(num_of_attack)==4 && num_attack==4) {
                            //Strategy 1: run server source code in the fourth backup Client 4 VM background					
                            puts("Starting now:");
                            cout<<"Num of attacks is "<<num_attack<<endl;
                            char command[50];
                            strcpy(command, "ADMMServer ");
                            strcat(command, num_of_pdcs);
                            strcat(command, " ");
                            strcat(command, backupserver4_port);
                            strcat(command, " &");
                            system(command);
                            std::cout<<"Happy New Server at PDC"<<std::endl;		
                        }					
                    }

                    //Strategy 0&1: backup server or run a server side at client1
                    // Create a socket and connection with predefined new server
                    struct hostent *he3;
                    struct in_addr **addr_list3;
                    char* ip3;

                    memset(&new_serv_addr, '0', sizeof(new_serv_addr));   
                    new_serv_addr.sin_family = AF_INET;
                    if (num_attack==1) {
                        if ((he3 = gethostbyname(backupserver1_host)) == NULL) {  // get the host info
                            exit(1);
                        }

                        addr_list3 = (struct in_addr **)he3->h_addr_list;
                        for(i = 0; addr_list3[i] != NULL; i++) {
                            ip3 = inet_ntoa(*addr_list3[i]);
                        }
                        
                        new_serv_addr.sin_port = htons(atoi(backupserver1_port));
                        if(inet_pton(AF_INET, ip3, &new_serv_addr.sin_addr)<=0){
                            printf("\n inet_pton error occured\n");
                            return 1;
                        }
                    } 
                    if (num_attack==2) {
                        if ((he3 = gethostbyname(backupserver2_host)) == NULL) {  // get the host info
                            exit(1);
                        }

                        addr_list3 = (struct in_addr **)he3->h_addr_list;
                        for(i = 0; addr_list3[i] != NULL; i++) {
                            ip3 = inet_ntoa(*addr_list3[i]);
                        }
                        
                        new_serv_addr.sin_port = htons(atoi(backupserver2_port));
                        if(inet_pton(AF_INET, ip3, &new_serv_addr.sin_addr)<=0){
                            printf("\n inet_pton error occured\n");
                            return 1;
                        }
                    }
                    if (num_attack==3) {
                        if ((he3 = gethostbyname(backupserver3_host)) == NULL) {  // get the host info
                            exit(1);
                        }

                        addr_list3 = (struct in_addr **)he3->h_addr_list;
                        for(i = 0; addr_list3[i] != NULL; i++) {
                            ip3 = inet_ntoa(*addr_list3[i]);
                        }
                        
                        new_serv_addr.sin_port = htons(atoi(backupserver3_port));
                        if(inet_pton(AF_INET, ip3, &new_serv_addr.sin_addr)<=0){
                            printf("\n inet_pton error occured\n");
                            return 1;
                        }
                    } 
                    if (num_attack==4) {
                        if ((he3 = gethostbyname(backupserver4_host)) == NULL) {  // get the host info
                            exit(1);
                        }

                        // print information about this host:
                        addr_list3 = (struct in_addr **)he3->h_addr_list;
                        for(i = 0; addr_list3[i] != NULL; i++) {
                            ip3 = inet_ntoa(*addr_list3[i]);
                        }
                        new_serv_addr.sin_port = htons(atoi(backupserver4_port));
                        if(inet_pton(AF_INET, ip3, &new_serv_addr.sin_addr)<=0){
                            printf("\n inet_pton error occured\n");
                            return 1;
                        }
                    } 
                    
                    if((new_sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0){
                        printf("\n Error : Could not create new socket \n");
                        return 1;
                    }
                    while (1){
                        if(connect(new_sockfd, (struct sockaddr *)&new_serv_addr, sizeof(new_serv_addr)) < 0){
                            printf("\n Error : New connect Failed \n");
                        } else {
                            printf("\n New TCP Connection has been set up\n");
                            break;
                        }
                    } //end-while
                    
                    sockfd = new_sockfd;	
                    write(sockfd, buffer, size); // Write the local estimation to new server
                    avgBufferLen = read(sockfd, avgBuffer, DEFAULT_MAX_BUFFER_LEN);
                } 
                
                avgBuffer[avgBufferLen]=0;
                if (strcmp(avgBuffer,"Distributed Prony Alogrithm finishes! \r\n\r\n")==0) {
                    Algorithm_Finishes = 1;
                    cout<<"Algorithm finishes is "<<Algorithm_Finishes<<endl;
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

        cout<<"========================= This is end of Iteration "<<Iteration<<" . ^_^ ========================= "<<endl;

        if (Algorithm_Finishes == 1) break;
        gettimeofday (&currenttime, NULL);
        cout<<"Current time is "<<currenttime.tv_sec*1000000 + currenttime.tv_usec<<endl;
        sleep(0.05);
        gettimeofday (&currenttime, NULL);
        cout<<"Current time is "<<currenttime.tv_sec*1000000 + currenttime.tv_usec<<endl;

        counter = theta.size();
        Iteration++;	
	
    } //end big while loop
	
	if (Algorithm_Finishes == 1) {
		size=sprintf(tempBuffer, "Distributed Prony Alogrithm finishes! \r\n\r\n");
		printf( "Prony Client VM Writes to PMU machine:\n %s \n", tempBuffer);  
		write(data_sockfd, tempBuffer, size); 
    }

	close(sockfd);
	cout<<"Prony algorithm ends happily.  ^_^"<<endl;
	gettimeofday (&End, NULL); 
 	timer_sub(&Start, &End, &Result);
    log_debug(fLogger,"End Prony client");
    fclose(fFile);
    return 0;

} /* end of PronyADMMClient */

} // extern C
