/*
 ============================================================================
 Name        : RLS_Auto.cpp
 Author      : Jianhua Zhang
 Description : Streaming measurement data from m PMUs and do RLS iteratively. Once one or two of PMUs is/are disconnected, RLS_Auto will continue to accomodate the rest of PMUs.
 File        : Initiating and running the Server to receive data from PMU first.
 Data        : May,20th,2014 to write the detailed log into output file
 CommandLine : ./RLS <initial#ofPMUs> <#data_port> <FileofInitials>
 ============================================================================
*/

#include "RLS_common.h"

#include "AgentRequest.h"
#include "AgentMessenger.h"

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

#include "Database.h"

#define InitError 1.1
#define ErrorMessage "Failed!!!"
#define SamNum 3581
#define ERROR 0.000000000000000001


void signal_callback_handler(int signum) {
    cout<<"Caught signal "<<signum<<endl; 
}

int RLS(char* pmuNUM, char* portNum, char* inFile) {
    //Register siganl and signal handler
    signal(SIGPIPE, signal_callback_handler);

    //For collecting event log and result
    ofstream myfile;
    ofstream errorfile;
    ofstream modefile;
    char filename[50];
    char filename_error[50];
    char filename_mode[50];
    char tempbuf1[5];
    char tempbuf2[5];
    char tempbuf3[5];
    char timebuffer[25];
    keyValueNode_t head = (keyValueNode_t)malloc(sizeof(struct keyValueNode));
    keyValueNode_t node1 = (keyValueNode_t)malloc(sizeof(struct keyValueNode));
    keyValueNode_t node2 = (keyValueNode_t)malloc(sizeof(struct keyValueNode));

    mongoDBExecute(OPER_DELETE_ALL, NULL);
    mongoDBExecute(OPER_FIND_ALL, NULL);

    time_t timer;
    time(&timer);
    struct tm * tm_info;
    tm_info = localtime(&timer);
    strcpy(filename, "CentralRLS_Result_");
    snprintf(tempbuf1, 5, "%d", tm_info->tm_year+1900);	
    strcat(filename, tempbuf1);
    strcat(filename, "-");
    snprintf(tempbuf2, 5, "%d", tm_info->tm_mon + 1);	
    strcat(filename, tempbuf2);
    strcat(filename, "-");
    snprintf(tempbuf3, 5, "%d", tm_info->tm_mday);	
    strcat(filename, tempbuf3);
    strcat(filename, ".txt");

    strcpy(filename_error, "/tmp/CentralRLS_Result_Errors.txt");
    strcpy(filename_mode, "/tmp/CentralRLS_Result_Modes.txt");

    myfile.open(filename);
    errorfile.open(filename_error, std::fstream::out);
    modefile.open(filename_mode);

    //=============================== Declare All Parameters non related with PMU_Num =================================/
    myfile << "=============================================================================================\n";
    time(&timer);
    tm_info = localtime(&timer);
    strftime(timebuffer, 25, "%Y:%m:%d  %H:%M:%S", tm_info);
    myfile << timebuffer;
    myfile << ":  Centralized RLS starts ...........\n";

    // Declare a vector for store the sample data
    vector<PMU_measure> y;
    y.clear();
    PMU_measure temp;

    struct timeval currenttime;
    int RLS_Exit_Flag = 0;
    int CountPMU = 0;
    int Iteration = 0;
    int IterationNum = 0; 

    char * thread_result = (char *)malloc(512);
    void * exit_status;
    int i, j, k, m, ii;

    struct sockaddr_in PMU_address;
    int Client_len = sizeof(PMU_address);	
    vector<int> Client_sockfd;
    Client_sockfd.clear(); 

    char Buffer[DEFAULT_MAX_BUFFER_LEN];
    char tempBuffer[DEFAULT_MAX_BUFFER_LEN];
    char lastchar, a;
    int size, length, last_flag, data_length;	
    char *token, *ph0, *ph1,*last_temp;
    last_temp = &a;
    double cal_error, tmp_error;
    cal_error = double(1000000000);
    int Index;  
    
    mat U(SamNum, ParaNum+1); 
    vec u(SamNum);
    u(0) = 1;
    u(1) = 1;
    u(2) = 1;
    for (i=3; i<SamNum; i++)
        u(i) = 0;
    
    // Construct intermedian vector U, input vector
    for (k=0; k<SamNum; k++) {
        if (k<ParaNum+1) {
            for (ii=0; ii<k+1; ii++)
                    U(k,ii) = u(k-ii);                               
            for (ii=k+1;ii<ParaNum+1;ii++)
                    U(k,ii) = 0;                           
        } else {
            for (ii=0; ii<ParaNum+1; ii++)
                    U(k,ii) = u(k-ii);                                 
        } //end if-else                   
    }//end for 

    // Parameters to compute the poles of the polynomial equation of Z function
    typedef complex<double> dcomp;
    dcomp z[ParaNum];
    dcomp root_est_c[ParaNum];
    int Degree = ParaNum;
    double op[MDP1], zeroi[MAXDEGREE], zeror[MAXDEGREE];   	
    int order;

    // =============================== Routine1: Setup TCP server side for several PMUs at RLS algorithm VM ================== //
    // Read out the initial PMU numbers
    int PMU_Num = 0;
    PMU_Num = atoi(pmuNUM);
    int PMU_Failure_Flag[PMU_Num];
    vector<int> LivePMU; // Store all live PMU number
    LivePMU.clear();
    
    for (i=0; i<PMU_Num; i++) {
        LivePMU.push_back(i);  //for change PMU_Num once one PMU is disconnected
        PMU_Failure_Flag[i] = 0;
    }
    
    // Set up TCP socket of server side for collecting PMU measurements for serveral PMU machines
    int Server_sockfd;
    struct sockaddr_in LocalAddr;

    // Initiate local TCP server socket
    LocalAddr.sin_family = AF_INET;
    LocalAddr.sin_addr.s_addr = htonl(INADDR_ANY);
    LocalAddr.sin_port = htons(atoi(portNum));

    // Create, bind and listen the TCP_socket 
    Server_sockfd = socket(AF_INET, SOCK_STREAM, 0);

    if (bind(Server_sockfd, (struct sockaddr *)&LocalAddr, sizeof(LocalAddr)) < 0) {
        cout<<"Error: Can not bind the TCP socket! \n Please wait a few seconds or change port number."<<endl;
        return 1;
    }
    listen(Server_sockfd, DEFAULT_QUEUE_LEN);


    // ============================== Routine2: Accept Initial Connections from PMUs ============================== //	
    while(CountPMU < PMU_Num) {
        Client_sockfd.push_back(accept(Server_sockfd,(struct sockaddr *)&PMU_address, (socklen_t*)&Client_len));		
        cout<<"Client_sockfd is "<<Client_sockfd[CountPMU]<<endl;
        cout<<"CountPMU is "<<CountPMU<<" and total PMU_Num is "<<PMU_Num<<endl;
        CountPMU++;
    }

    time(&timer);
    tm_info = localtime(&timer);
    strftime(timebuffer, 25, "%Y:%m:%d  %H:%M:%S", tm_info);
    myfile << timebuffer;
    myfile << ":  Accept all connection!! \n";

    // ============================== Routine3: Declare All PMU_Num-related Parameters ============================== //

    // =============== Parameters Initialization of RLS =============== //		
    vec beta(ParaNum);    // Denominator parameters	

    cube phi;
    mat lambda0; // Initial guess
    mat lambda;  // Parameters needed to be estimated 
    mat R0;	     // Sort of a confidence
    mat P;       // Initialize P for iteration computation
    mat error, tmp, tmpmat, transtmpmat, tmp1, tmp2, y_N;

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

    //Initial guess
    //ifstream inputFile(argv[3]);
    ifstream inputFile(inFile);
    string line;
    i = 0;
    while (getline(inputFile, line) && i<Index){
        istringstream ss(line);
        ss >> lambda0(i,0);      			
        i++;  		    
    }
    
    lambda0 = InitError*lambda0; 
    lambda = lambda0;

    // ============================ Routine4: Main Loop Process: Receive Data, Parse Data, RLS =======================//

    // Synchronize the data receiving from different PMU
    pthread_t handler_thread[PMU_Num];
    // Accomodate the last record of the previous data packet
    string list[PMU_Num];
    for (i=0; i<PMU_Num; i++)
        list[i]=last_temp;

    int least_index;
    int index[PMU_Num], counter[PMU_Num];
    for (i=0; i<PMU_Num; i++) {
        index[i]=0;  //for recording the PMU measurements index received from each PMU
        counter[i]=0;//for recording interation of RLS algorithm
    }
    
    while(1){
        //============Step1: Collect the PMU measurements from all PMUs=====================================//

        cout<<"Step1: start collecting PMU measurements ..."<<endl;
        CountPMU = 0;
        least_index = SamNum;

        while(CountPMU < PMU_Num) {                        
            gettimeofday (&currenttime, NULL);
            cout<<"Current time is "<<currenttime.tv_sec*1000000 + currenttime.tv_usec<<endl;		   
            // Handle connection
            pthread_create(&handler_thread[LivePMU[CountPMU]], NULL, RLS_Server_handle, (void*) &Client_sockfd[LivePMU[CountPMU]]);
            CountPMU++;             
        }

        //============Step2: Check PMU status and Parse the PMU measurements for each live PMU ==============//

        cout<<"The PMU_Num is "<<PMU_Num<<endl;
        
        // Wait for all threads finish and return the values
        for (CountPMU = 0; CountPMU < PMU_Num; CountPMU++) {
            // Return receive_packet_content with data_length from thread or ErrorMessage
            pthread_join(handler_thread[LivePMU[CountPMU]], &exit_status);
            thread_result = (char *)exit_status;

            // Parse the message from each thread, which could be PMU measurement data or the error message
            ph0 = strtok(thread_result, "\n");
            
            if (strcmp(ph0, ErrorMessage)==0) { // This PMU is disconnect. Resiliency Strategy is to update state of PMU_Failure
                PMU_Failure_Flag[LivePMU[CountPMU]] = 1;
                time(&timer);
                tm_info = localtime(&timer);
                strftime(timebuffer, 25, "%Y:%m:%d  %H:%M:%S", tm_info);
                myfile << timebuffer;
                myfile << "  At IterationNum  ";
                myfile << IterationNum;
                myfile << ":  PMU";
                myfile << LivePMU[CountPMU];
                myfile << "'s link got attacked becasue the read() function times out!!!\n";

            } else { // This PMU works well and continue to parse the measurement data
                    last_flag = atoi(ph0);
                    length = strlen(ph0);
                
                    ph1 = strtok(NULL, "\n") ;
                    data_length = atoi(ph1);
                
                    cout<<"Iteration is "<<Iteration<<endl;
                    memset(Buffer, '\0', DEFAULT_MAX_BUFFER_LEN);
                    printf("list[%d] contains %s", LivePMU[CountPMU], list[LivePMU[CountPMU]].c_str());	
                
                    //Attach the new packet data to the last record of previous packet
                    if((list[LivePMU[CountPMU]].length()!= 0) && (Iteration != 0)) {
                        strncat(Buffer, list[LivePMU[CountPMU]].c_str(), list[LivePMU[CountPMU]].length()+1);// Interation = packet_no
                    }
                
                    strncat(Buffer, thread_result+(length+strlen(ph1)+2)*sizeof(char), data_length);
                    printf("After receive packet %d, content Buffer contains \n %s \n", Iteration, Buffer);
                
                    //If last valid char in Buffer is '\n', we need do special process, because it will not be parsed correctly
                    lastchar = Buffer[list[LivePMU[CountPMU]].length()*sizeof(char)+data_length-1]; 
                    cout<<"Show us the last character is "<<lastchar<<endl;
                    memset(Buffer+(list[LivePMU[CountPMU]].length()+1+data_length)*sizeof(char), '\0', 20);	
                    length = 0;
                
                    while (1) {
                        token = strtok(Buffer+length*sizeof(char), "\n");
                        temp.PMU_no = LivePMU[CountPMU];
                        temp.Data_index = index[LivePMU[CountPMU]];
                        if (token == NULL) {
                            cout<<"receive_packet_length is "<<data_length<<endl;
                            if(last_flag == 0) y.pop_back();  //if this is not last packet, the last record is discarded.
                            index[LivePMU[CountPMU]] = index[LivePMU[CountPMU]]-1;
                            break;	
                        } 
                        list[LivePMU[CountPMU]] = token;
                        temp.PMU_data = strtod(token, NULL);
                        y.push_back(temp);
                        index[LivePMU[CountPMU]] = index[LivePMU[CountPMU]]+1;						
                        length = length + strlen(token) + 1;			   			
                    } // end of parsing data
                
                    cout<<"Show us the last character is "<<lastchar<<endl;
                
                    if (lastchar == '\n') list[LivePMU[CountPMU]].append("\n");
                    cout<<"last record list["<<LivePMU[CountPMU]<<"] is "<<list[LivePMU[CountPMU]].c_str()<<endl;
                    
                    cout<<"Size of y is"<<(int)y.size()<<endl;
                   } // end else-if
        } // end for	
        cout << "All threads completed."<<endl;

        //============ Step3: Update the live PMU numbers and Resize all matrices ========================//

        // Update live PMU list
        for (m=0; m<(int)LivePMU.size(); m++) {
            if (PMU_Failure_Flag[LivePMU[m]]==1) LivePMU.erase(LivePMU.begin()+m);
        }	
        
        if ((int)LivePMU.size() == 0) break;

        if (PMU_Num != (int)LivePMU.size()){

            //1. Update PMU_Num
            PMU_Num = LivePMU.size();

            //2. Resize all related matrices
            Index = ParaNum*(PMU_Num+1)+PMU_Num;	
            phi.set_size(SamNum, PMU_Num, Index); 	
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

            //3. Reinitialize Guess
            lambda0 = lambda; //Save the previous estimated result as new Initial Guess
            lambda.set_size(Index,1);   
            for (i=0; i<ParaNum; i++)
                lambda[i]=lambda0[i];
            for (j=0; j<PMU_Num; j++){
                for (i=0; i<ParaNum+1; i++)
                    lambda[ParaNum+(ParaNum+1)*j+i] = lambda0[ParaNum+(ParaNum+1)*LivePMU[j]+i];
                }
            //4. Other reinitialization
            cal_error = double(1000000000);
           }
        cout<<"The PMU number is "<<PMU_Num<<endl;

        //========== Step4: Broadcast Package ACK message ====================================================//

        size=sprintf(tempBuffer, "Request Next Package %d! \r\n\r\n",(Iteration+1));	
            printf( "RLS client VM Writes:\n %s \n", tempBuffer);
        //cout<<"Error happens before for loop!"<<endl;        
        for (i=0; i<PMU_Num; i++){
            j = 0;
            cout<<"Error happens after for loop! at PMU "<<i<<endl;   
            j=write(Client_sockfd[LivePMU[i]], tempBuffer, size);
            cout<<"Return value is "<< j <<endl;
            if(j<0) {			
                perror ("The following error occurred ");
                cout<<"\n at client_sockfd:  "<<Client_sockfd[LivePMU[i]]<<endl;
                PMU_Failure_Flag[LivePMU[i]] = 1;	
                time(&timer);
                    tm_info = localtime(&timer);
                    strftime(timebuffer, 25, "%Y:%m:%d  %H:%M:%S", tm_info);
                myfile << timebuffer;
                myfile << "  At IterationNum  ";
                myfile << IterationNum;
                myfile << ":  PMU";
                myfile << LivePMU[i];
                myfile << " itself got attacked with error 'Broken pipe'!!! \n";
            } else if (j==0){
                PMU_Failure_Flag[LivePMU[i]] = 1;		
            }			
        }

        //============ Step5: Data Preparation of Matrix phi for the live PMU measurements ===============//

        for (CountPMU = 0; CountPMU < PMU_Num; CountPMU++){
            for (k=counter[CountPMU]; k<index[CountPMU]; k++){
                for (i=0; i<ParaNum; i++) phi(0,CountPMU,i)=0;
                //Construct psi
                for (i=0; i<ParaNum; i++){
                    if (k<ParaNum){
                        for (ii=0; ii<k; ii++){
                            for (m=0; m<(int)y.size();m++){
                                if ((y[m].PMU_no==LivePMU[CountPMU])&&((k-ii-1)==y[m].Data_index)) phi(k,CountPMU,ii) = y[m].PMU_data;
                                }						
                            }
                        for (ii=k; ii<ParaNum; ii++)
                            phi(k,CountPMU,ii) = 0;						  
                        } else {
                        for (ii=0; ii<ParaNum; ii++)
                                        for (m=0; m<(int)y.size();m++){
                                if ((y[m].PMU_no==LivePMU[CountPMU])&&((k-ii-1)==y[m].Data_index)) phi(k,CountPMU,ii) = y[m].PMU_data;
                                }			
                           } //end if-else				   
                         } //end for construct psi

                //Construct U diagonal matrix
                for (m=0; m<PMU_Num; m++){	
                    for (ii=0; ii<ParaNum+1; ii++){
                        if (m==CountPMU) {
                            phi(k,CountPMU,ParaNum+(ParaNum+1)*m+ii) = U(k,ii);
                          } else {
                                phi(k,CountPMU,ParaNum+(ParaNum+1)*m+ii) = 0;
                                 } // end of if-else
                            }
                    } // end for construct U

                 } //end for each measurement
               } //end Data Preparation for all valid PMU measurements

        //=========== Step6: Run RLS Algorithm ==========================================================//
        // Compute out the smallest index for all live PMUs
        for (i=0; i<PMU_Num; i++){
            if (least_index > index[LivePMU[i]]) least_index = index[LivePMU[i]];
           }
        while (1) {
            if (IterationNum >= least_index || cal_error <= ERROR ) {
                if (IterationNum >= SamNum || cal_error <= ERROR) RLS_Exit_Flag = 1;
                break;
            }
            //-----theta_N
            for (i=0; i<Index; i++)
                tmp(i,0) = lambda(i,0);

            //-----phi_N & phi_N^T
            for (j=0; j<PMU_Num; j++)
                for (i=0; i<Index; i++)
                    tmpmat(j,i) = phi(IterationNum, j, i);         		    
                transtmpmat = trans(tmpmat);

            //-----Calculate P_N+1			     
            tmp2 = eye(PMU_Num,PMU_Num) + tmpmat*P*transtmpmat;
            tmp2 = inv(tmp2);
            P = P-P*transtmpmat*tmp2*tmpmat*P;				    

            //-----Calculate theta_N+1
            for (j=0; j<PMU_Num; j++) {
                for (m=0; m<(int)y.size();m++) {
                    if ((y[m].PMU_no==LivePMU[j])&&(y[m].Data_index==IterationNum)) y_N(j,0) = y[m].PMU_data;
                }				
            }
            
            tmp1 = y_N - tmpmat*tmp;			
            lambda = tmp + P*transtmpmat*tmp1;

            //-----Calculate error between Lambda_N and Lambda_N+1
            error =  lambda + (-1)*tmp;
            cal_error = 0;
            for (i=0; i<Index; i++) {
                if (error(i,0) < 0) {
                    tmp_error = (-1) * error(i,0);
                } else {
                    tmp_error = error(i,0);
                }	  
                //tmp_error = error(i,0) * error(i,0);
                if (tmp_error > cal_error)  cal_error = tmp_error;
            }

            timeval curTime;
            gettimeofday(&curTime, NULL);
            double now = (((double)curTime.tv_sec * 1000000) + curTime.tv_usec) / 1000000;
            errorfile << fixed << IterationNum << " " << now << " " << cal_error << endl;

            cout << fixed << now << " cal_error is "<< cal_error << endl;

            double *errValue = (double*)malloc(sizeof(double));
            *errValue = cal_error;
            head->key = "error";
            head->value = (void*)errValue;
            head->type = DOUBLE_TYPE;
            head->next = NULL;

            int *itrValue = (int*)malloc(sizeof(int));
            *itrValue = IterationNum;
            node1->key = "itr";
            node1->value = (void*)*itrValue;
            node1->type = INT_TYPE;
            node1->next = NULL;

            head->next = node1;

            mongoDBExecute(OPER_INSERT, head);

            // Compute the poles at each iteration
            for (i=0; i<ParaNum; i++)
                beta(i) = (-1)*lambda(i);
            op[0] = 1;
            for (order = 1; order < (Degree+1); order++)
                    op[order] = beta(order-1);         
            rpoly_ak1(op, &Degree, zeror, zeroi); // Compute the poles of the polynomial equation of Z function	
            modefile << "IterationNum  ";
            modefile << IterationNum;
            modefile << ":		\n";
            
            for (order = 0; order < Degree; order++){
                    z[order] = dcomp(zeror[order], zeroi[order]);
                    root_est_c[order] = log(z[order])/Ts; // Compute the poles of the polynomial equation of S function
                if ((abs(root_est_c[order].imag())>3 && abs(root_est_c[order].imag())<4) || (abs(root_est_c[order].imag())>5 && abs(root_est_c[order].imag())<7)){ 
                modefile << root_est_c[order];
                modefile << "\n";
                } //end if
            } //end for			   

            IterationNum++;         
        } //end RLS while 

        if (RLS_Exit_Flag == 1) {
            time(&timer);
                tm_info = localtime(&timer);
                strftime(timebuffer, 25, "%Y:%m:%d  %H:%M:%S", tm_info);
            myfile << timebuffer;
            myfile << ":  Algorithm ends due to estimated results converge!!! \n";			
            break;
        }	
        
        if ( last_flag ==1 ) {
            time(&timer);
                tm_info = localtime(&timer);
                strftime(timebuffer, 25, "%Y:%m:%d  %H:%M:%S", tm_info);
            myfile << timebuffer;
            myfile << ":  Algorithm ends due to running out the sample data!!! \n";			
            break;
        }	
        
        //========= Step7: Update some parameters ===========================================================//
        // update the counter of sample data
        for(i=0; i<PMU_Num; i++) counter[LivePMU[i]]=index[LivePMU[i]];
            Iteration++;

    } // end Main Loop

    close(Server_sockfd);

    // ======================= Routine5: Postpone Process: Printout of RLS and Postpone Calculation =========================//

    // ============== Step1: Printout the result of RLS ==============//
    cout<<"This is Iteration number "<<IterationNum<<endl;
    for (i=0; i<ParaNum; i++)
        beta(i) = (-1)*lambda(i);

    printf("The Initial guess is %f,  %f,  %f, %f, %f,  %f,  %f, %f, %f\n", (-1)*lambda0(0), (-1)*lambda0(1), (-1)*lambda0(2), (-1)*lambda0(3), (-1)*lambda0(4), (-1)*lambda0(5), (-1)*lambda0(6), (-1)*lambda0(7), (-1)*lambda0(8)); 
    //printf("The Estimated denominator parameter is %f,  %f,  %f, %f\n", beta(0), beta(1), beta(2), beta(3));
    beta.print("The Estimated denominator parameter is ");
    printf("The Estimated nomerator parameter is %f,  %f,  %f, %f, %f\n", lambda(4), lambda(5), lambda(6), lambda(7), lambda(8));


    // ==============Step2: Postpone Calculation ==============//

    //Input the polynomial coefficients from the file and put them in the op vector
    op[0] = 1;
    for (order = 1; order < (Degree+1); order++)
        op[order] = beta(order-1);     

    rpoly_ak1(op, &Degree, zeror, zeroi);

    // S2: Compute the poles of the polynomial equation of S function
    for (order = 0; order < Degree; order++){
        z[order] = dcomp(zeror[order], zeroi[order]);
        root_est_c[order] = log(z[order])/Ts;
        cout<<root_est_c[order]<<endl;   
    }

    // ============== Step3: Print out the roots to File =========================================/
    myfile << "\n";
    myfile << "\n";
    time(&timer);
        tm_info = localtime(&timer);
        strftime(timebuffer, 25, "%Y:%m:%d  %H:%M:%S", tm_info);
    myfile << timebuffer;
        myfile << ":  CentralRLS algorithm ends happily.  ^_^\n";
    myfile << "Estimated Result is \n";
    for (order = 0; order < Degree; order++){
        if ((abs(root_est_c[order].imag())>3 && abs(root_est_c[order].imag())<4) || (abs(root_est_c[order].imag())>5 && abs(root_est_c[order].imag())<7)){
            myfile << root_est_c[order];
            myfile << "\n";
        } //end if
    } //end for
    myfile.close();
    errorfile.close();
    modefile.close();

    mongoDBExecute(OPER_FIND_ALL, NULL);
    return EXIT_SUCCESS;
    }
}

