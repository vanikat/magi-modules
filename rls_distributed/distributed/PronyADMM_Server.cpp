#include "Prony_common.h"

#include "AgentMessenger.h"
#include "AgentRequest.h"
#include "Database.h"
#include "MAGIMessage.h"

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

#define ERROR 0.001
#define imagError 0.005
#define MSS 250

int ADMMServer(char* pmuNUM, char* portNum) {
    FILE* nFile;
    Logger* nLogger;
    nFile = fopen("/tmp/PronyADMM_server.log", "a");
    nLogger = Logger_create(nFile, 0);
    log_debug(nLogger,"Start Prony server");

    ofstream errorfile;
    ofstream modefile;
    char filename_error[50];
    char filename_mode[50];
    strcpy(filename_error, "DistriProny_Result_Errors.txt");
    strcpy(filename_mode, "DistriProny_Result_Modes.txt");
    
    keyValueNode_t head = (keyValueNode_t)malloc(sizeof(struct keyValueNode));
    keyValueNode_t node1 = (keyValueNode_t)malloc(sizeof(struct keyValueNode));
    keyValueNode_t node2 = (keyValueNode_t)malloc(sizeof(struct keyValueNode));

    // Delete everything in the mongoDB for collecting the data for this experiment.
    mongoDBExecute(OPER_DELETE_ALL, NULL);
    mongoDBExecute(OPER_FIND_ALL, NULL);
    
    if (errorfile.good()) {
        errorfile.open(filename_error, std::ofstream::out | std::ofstream::app); // there is this existing file, and append to it
    } else {
        errorfile.open(filename_error, std::ofstream::out); // there is no this existing file, and generate a new one
    }

    if (modefile.good()){
        modefile.open(filename_mode, std::ofstream::out | std::ofstream::app); // there is this existing file, and append to it
    } else {
        modefile.open(filename_mode, std::ofstream::out); // there is no this existing file, and generate a new one
    }

    struct timeval Start, End, Result;
    gettimeofday (&Start, NULL); 

    int CountClient,ClientNum;
    ClientNum = atoi(pmuNUM);
    int Iteration = 0;
    int i,j;
    pthread_t handler_thread[ClientNum];
    string list[ClientNum];
    char * thread_result = (char *)malloc(512);
    void * exit_status;
    double localpara[ClientNum][ParaNum];
    double avgpara[ParaNum], new_avgpara[ParaNum], error[ParaNum];
    double sum, cal_error;
    char *pht;
    double origeigen_imag[3];
    origeigen_imag[0] = 3.124981;
    origeigen_imag[1] = 5.56238;
    origeigen_imag[2] = 6.095;
    int root_count;

    // Initialize avg vectors
    for (i=0; i<ParaNum; i++){
        avgpara[i] = 0;
        new_avgpara[i] = 0;
    }

    // Prepare sending message
    char Buffer[DEFAULT_MAX_BUFFER_LEN];
    char tempBuffer[DEFAULT_MAX_BUFFER_LEN];
    char* avgBuffer = (char*)malloc(512*sizeof(char));
    unsigned size;
    struct timeval tvalStart, currenttime;

    // Set up TCP socket of server side for collection local parameters for each client
    int Server_sockfd;
    struct sockaddr_in LocalAddr;

    // collecting IP addresses of PMUs from TCP connection for latter connection
    int Client_sockfd[ClientNum];
    struct sockaddr_in Client_address;
    int Client_len = sizeof(Client_address);	
    vector<sockaddr_in> client_list;  

    // Initiate local TCP server socket
    LocalAddr.sin_family = AF_INET;
    LocalAddr.sin_addr.s_addr = htonl(INADDR_ANY);
    LocalAddr.sin_port = htons(atoi(portNum));

    // Create, bind and listen the TCP_socket 
    Server_sockfd = socket(AF_INET, SOCK_STREAM, 0);

    if (bind(Server_sockfd, (struct sockaddr *)&LocalAddr, sizeof(LocalAddr)) < 0) {
        log_debug(nLogger,"bind error");
        cout<<"Error: Can not bind the TCP socket! \n Please wait a few seconds or change port number."<<endl;
        return 1;
    }
    listen(Server_sockfd, DEFAULT_QUEUE_LEN);

    // Calculate roots
    typedef complex<double> dcomp;
    dcomp z[PoleNum];
    dcomp root_est_c[PoleNum];

    int Degree = PoleNum;
    double op[MDP1], zeroi[MAXDEGREE], zeror[MAXDEGREE]; // Coefficient vectors
    int index; // vector index
    Mutex_initialization();

    // ========================================= The below is the loop =========================================// 
    while(Iteration < 3500) {
        usleep(20000);
        //========================Step1: Collect the parameters from all clients===================//
        cout<<"Step1: start collecting localpara ..."<<endl;
        CountClient = 0;
        log_debug(nLogger, "Iteration inside while %d", Iteration);

        while(CountClient < ClientNum) {
            gettimeofday (&currenttime, NULL);
            cout<<"Current time is "<<currenttime.tv_sec*1000000 + currenttime.tv_usec<<endl;

            // Accept connection		
            if(Iteration == 0){
                Client_sockfd[CountClient] = accept(Server_sockfd,(struct sockaddr *)&Client_address, (socklen_t*)&Client_len);
                log_debug(nLogger, "Accepted connection");
                cout<<"Client_sockfd is "<<Client_sockfd[CountClient]<<endl;		
            }

            // Handle connection
            pthread_create(&handler_thread[CountClient], NULL, Server_handle, (void*) &Client_sockfd[CountClient]);
            CountClient++;             
        }

        // Wait for all threads finish and return the values
        for (CountClient = 0; CountClient < ClientNum; CountClient++){
            pthread_join(handler_thread[CountClient], &exit_status);
            thread_result = (char *)exit_status;
            list[CountClient] = thread_result;	
        }	
        cout << "All threads completed."<<endl ;

        for (i=0; i<ClientNum; i++) {
            strcpy(Buffer, list[i].c_str());
            pht = strtok(Buffer, " ");
            pht = strtok(NULL, " ");
            Iteration = strtol(pht, NULL, 10); 
            cout<<"Received iteration is "<<Iteration<<endl;
            pht = strtok(NULL, " ");
            for (j=0; j<ParaNum; j++) {
                pht = strtok(NULL, " ");
                localpara[i][j]= strtod(pht, NULL);
            }
        }

        //========================== Step2: Average collected parameters =====================//
        cout<<"Step2: Average collected parameters ..."<<endl;
        cal_error = 0;
        for (j=0; j<ParaNum; j++) {
            //1. update old avgpara
            avgpara[j] = new_avgpara[j];
            //2. calculate new_avgpara
            sum = 0;
            for (i=0; i<ClientNum; i++){
                sum = sum + localpara[i][j];
            }	
            new_avgpara[j] = sum/ClientNum;
            cout<<"avgpara ["<<j<<"] is "<<new_avgpara[j]<<endl;
            //3. Calculate the squared error
            error[j] = (new_avgpara[j] - avgpara[j])*(new_avgpara[j] - avgpara[j]);
            //4. max error
            if (error[j] > cal_error) cal_error =  error[j];	
        }	

        timeval curTime;
        gettimeofday(&curTime, NULL);
        double now = (((double)curTime.tv_sec * 1000000) + curTime.tv_usec) / 1000000;
        errorfile << fixed << Iteration << " " << now << " " << cal_error << endl;

        double *errValue = (double*)malloc(sizeof(double));
        *errValue = cal_error;
        head->key = "error";
        head->value = (void*)errValue;
        head->type = DOUBLE_TYPE;
        head->next = NULL;

        int *itrValue = (int*)malloc(sizeof(int));
        *itrValue = Iteration;
        node1->key = "itr";
        node1->value = (void*)*itrValue;
        node1->type = INT_TYPE;
        node1->next = NULL;

        head->next = node1;
        mongoDBExecute(OPER_INSERT, head);
        

        cout << fixed << now << " cal_error is "<< cal_error << endl;

        //Input the polynomial coefficients from the file and put them in the op vector
        op[0] = 1;
        for (index = 1; index < (Degree+1); index++) {
            op[index] = (-1)*new_avgpara[index-1];
        }
        
        rpoly_ak1(op, &Degree, zeror, zeroi); //Compute the poles of the polynomial equation of Z function
        cout.precision(DBL_DIG);

        root_count = 0;
        modefile << "Iteration  ";
        modefile << Iteration;
        modefile << ":		\n";
        for (index = 0; index < Degree; index++) {
            z[index] = dcomp(zeror[index], zeroi[index]);
            root_est_c[index] = log(z[index])/Ts; //Compute the poles of the polynomial equation of S function
            if ((abs(root_est_c[index].imag())>3 && abs(root_est_c[index].imag())<4) 
                 || (abs(root_est_c[index].imag())>5 && abs(root_est_c[index].imag())<7)) { 
                modefile << root_est_c[index];
                modefile << "\n";
                root_count++;
            } //end if
        } // end of for 
        
        cout<<"The root_count number is "<<root_count<<endl;

        //======================== Step3: Broadcast the average parameters ==============//

        cout<<"Step3: Broadcast avgpara ..."<<endl;  
        // Record sending time
        gettimeofday (&tvalStart, NULL);

        //1: Format the export message
        size = sprintf(avgBuffer, "Iteration: %d, new_avgpara: %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f\r\n Starttime: %ld \r\n\r\n", Iteration, new_avgpara[0], new_avgpara[1], new_avgpara[2], new_avgpara[3], new_avgpara[4], new_avgpara[5], new_avgpara[6], new_avgpara[7], new_avgpara[8], new_avgpara[9], new_avgpara[10], new_avgpara[11], new_avgpara[12], new_avgpara[13], new_avgpara[14], new_avgpara[15], new_avgpara[16], new_avgpara[17], new_avgpara[18], new_avgpara[19], (tvalStart.tv_sec*1000000 + tvalStart.tv_usec));	

        printf( "Prony_Server Write:\n %s \n", avgBuffer);    

        for (i=0; i<ClientNum; i++){
            write(Client_sockfd[i], avgBuffer, size); 
        }

        cout<<"========================= This is end of Iteration "<<Iteration<<" . ^_^ ========================= "<<endl;
    } // end big while loop

    Mutex_destroy();
    
    // Broadcast the message of "Algorithm finishes!"
    size=sprintf(tempBuffer, "Distributed Prony Alogrithm finishes! \r\n\r\n");
    printf( "Prony Server VM Writes to Prony Client:\n %s \n", tempBuffer);  
    
    for (i=0; i<ClientNum; i++){
        write(Client_sockfd[i], tempBuffer, size); 
    }     
    
    sleep(2);	
    close(Server_sockfd);


    // ========================================= Print out the roots to File =========================================//
    errorfile.close();
    modefile.close();	
    timer_sub(&Start, &End, &Result);
    cout<<"Total end-to-end delay of Prony algorithm for each sample is "<<(Result.tv_sec*1000 + Result.tv_usec/1000)/(2160-40)<<"ms.  ^_^"<<endl;
    mongoDBExecute(OPER_FIND_ALL, NULL);	
    log_debug(nLogger,"End Prony server");
    fclose(nFile);
    return 0;

} /* end of ADMMServer */
    
} // extern C

