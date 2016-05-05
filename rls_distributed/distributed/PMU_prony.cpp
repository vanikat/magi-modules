#include "Prony_common.h"

#include "AgentMessenger.h"
#include "Logger.h"

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

int PMU(char * rls_host, char *rls_port, char* source_file) {
    FILE* fnFile;
    Logger* fnLogger;
    fnFile = fopen("/tmp/PMU.log", "a");
    fnLogger = Logger_create(fnFile, 0);
    log_debug(fnLogger, "Start PMU");
    
    struct timeval RTT_start, RTT_end, RTT_result, Packet_SendingTime;
    gettimeofday (&RTT_start, NULL);	
    FILE *fp;
    sockaddr_in VM_client;
    int i;
    struct hostent *he;
    struct in_addr **addr_list;
    char* ip;

    if ((he = gethostbyname(rls_host)) == NULL) {
        log_debug(fnLogger, "Error in resolving the hostname");
        exit(1);
    }

    addr_list = (struct in_addr **)he->h_addr_list;
    for(i = 0; addr_list[i] != NULL; i++) {
        ip = inet_ntoa(*addr_list[i]);
    }

    VM_client.sin_family = AF_INET;
    VM_client.sin_port = htons(atoi(rls_port));
    if(inet_pton(AF_INET, ip, &VM_client.sin_addr)<=0) {
        printf("\n inet_pton error occured\n");
        log_debug(fnLogger,"error in inet_pton");
        exit(1);
    }

    bzero(&(VM_client.sin_zero),8);
    if((fp = fopen(source_file, "rb"))==NULL) {
        log_debug(fnLogger,"error in file open");
        exit(1);
    }

    // For receive ack message
    char ackBuffer[DEFAULT_MAX_BUFFER_LEN];
    int ackBufferLen;

    /******************Setup TCP client**********************/

    int sockfd=0;
    unsigned fread_ret;
    char *send_packet;
    char *send_packet_content;
    struct TCP_header *send_packet_header;
    unsigned header_length=sizeof(struct TCP_header);
    unsigned data_length = MSS*sizeof(char);	 
    unsigned packet_length = data_length + header_length;
    unsigned current_seq_no=0;

    if((send_packet=(char *)calloc(1, packet_length))==NULL){
        log_debug(fnLogger,"send packet error");
        cout<<"Fail to allocate memory for sender buffer, program is exiting ... "<<endl;
        exit(1);
    }
    if((sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        log_debug(fnLogger,"could not create socket");
        printf("\n Error : Could not create socket \n");
        return 1;
    } 
    if( connect(sockfd, (struct sockaddr *)&VM_client, sizeof(VM_client)) < 0)   {
        log_debug(fnLogger,"connect failed");
        printf("\n Error : Connect Failed \n");
        return 1;
    } else {
        log_debug(fnLogger,"connection up");
        printf("\n Connection has been set up\n");
    }

    printf( "Client Write:\n");
    int itr = 0;

    //send out the batch sample data.
    while(1) {
        send_packet_header = (struct TCP_header *)send_packet;
        send_packet_content = (char *)(send_packet_header+1);

        fread_ret = fread(send_packet_content, 1, MSS, fp);
        if (fread_ret == 0) {			
            break;
        } else { 
            cout<<"Start to send out packet "<<current_seq_no<<endl;
            gettimeofday (&Packet_SendingTime, NULL);
            send_packet_header->packet_sending_time = Packet_SendingTime.tv_sec * 1000000 + Packet_SendingTime.tv_usec;
            send_packet_header->packet_no = current_seq_no;	
            
            if (fread_ret==MSS){
                send_packet_header->last_flag=0;
            } else {
                send_packet_header->last_flag=1;
            }
            
            send_packet_header->data_length = fread_ret;
            write(sockfd, send_packet, fread_ret+header_length);

            cout<<"This packet "<<current_seq_no<<" with data size "<<fread_ret<<" contains \n"<<send_packet_content<<endl;
            log_debug(fnLogger,"packet sent \n %s", send_packet);

            current_seq_no++;
            
            if(fread_ret < MSS){
                cout<<"This is last packet."<<endl;
                break;
            }
        } //end if-else
        log_debug(fnLogger,"read PMU file iteration %d", itr);
        itr++;

        //Wait for the ACK message from RLS machine
        cout<<"Start receiving ack message from Prony client ... "<<endl;             
        ackBufferLen = read(sockfd, ackBuffer, DEFAULT_MAX_BUFFER_LEN);
        ackBuffer[ackBufferLen]=0;
        cout<<ackBuffer<<endl;	
        if (strcmp(ackBuffer,"Distributed Prony Alogrithm finishes! \r\n\r\n")==0) break;		
    }
    
    gettimeofday (&RTT_end, NULL);	
    timer_sub(&RTT_start, &RTT_end, &RTT_result);
    cout<<"End-to-End estimation time for each sample is "<< (RTT_result.tv_sec * 1000000 + RTT_result.tv_usec)/2160 <<"  microseconds"<<endl;
    close(sockfd); 
    log_debug(fnLogger,"Exit PMU");
    fclose(fnFile);
    return 0;

} /* end of PMU function */

} // extern C

