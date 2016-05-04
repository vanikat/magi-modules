/*
 ============================================================================
 Name        : PMU_src.cpp
 Author      : Jianhua Zhang
 Description : Simulation of PMU, this is a client side
 File        : Sending the sample data to RLS_Client through TCP
 Date	     : Mar,30th,2014
 CommandLine : ./PMU <ip of RLS_VM> <#data_port> <source file>
 ============================================================================
*/

#include "RLS_common.h"
#include "AgentRequest.h"
#include "AgentMessenger.h"

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

int PMU(char * hostName, char *portNum, char* inFile)
{
    FILE *fp;
    sockaddr_in RLS_VM;
    int i;
    struct hostent *he;
    struct in_addr **addr_list;
    char* ip;

    if ((he = gethostbyname(hostName)) == NULL) {  // get the host info
       exit(1);
    }

    // print information about this host:
    addr_list = (struct in_addr **)he->h_addr_list;
    for(i = 0; addr_list[i] != NULL; i++) {
        ip = inet_ntoa(*addr_list[i]);
    }

    RLS_VM.sin_family = AF_INET;
    RLS_VM.sin_port = htons(atoi(portNum));
    if(inet_pton(AF_INET, ip, &RLS_VM.sin_addr)<=0) {
        printf("\n inet_pton error occured\n");
        exit(1);
    } 

    bzero(&(RLS_VM.sin_zero),8); 
    if((fp = fopen(inFile, "rb"))==NULL) {
        exit(1);
    }

    // For receive ack message
    char ackBuffer[DEFAULT_MAX_BUFFER_LEN];
    int ackBufferLen;
    
    /******************Setup TCP client**********************/
    struct timeval Packet_SendingTime, RTT_start, RTT_end, RTT_result;	
    int sockfd=0;
    unsigned fread_ret;
    char *send_packet;
    char *send_packet_content;
    struct TCP_header *send_packet_header;
    unsigned header_length=sizeof(struct TCP_header);
    unsigned data_length = MSS*sizeof(char);	 
    unsigned packet_length= data_length + header_length;
    unsigned current_seq_no=0;

    if((send_packet=(char *)calloc(1, packet_length))==NULL){
        cout<<"Fail to allocate memory for sender buffer, program is exiting ... "<<endl;
        exit(1);
    }
    
    if((sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0)   {
        printf("\n Error : Could not create socket \n");
        return 1;
    } 
    
    if( connect(sockfd, (struct sockaddr *)&RLS_VM, sizeof(RLS_VM)) < 0)   {
        printf("\n Error : Connect Failed \n");
        return 1;
    } else {
        printf("\n Connection has been set up\n");
    }

    printf( "Client Write:\n");

    //send out the batch sample data.
    gettimeofday (&RTT_start, NULL);
    while(1) {
        send_packet_header = (struct TCP_header *)send_packet;
        send_packet_content = (char *)(send_packet_header+1);

        fread_ret = fread(send_packet_content, 1, MSS, fp);
        
        if (fread_ret == 0){			
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
            cout<<"Header_length is "<<header_length<<endl;
            current_seq_no++;
            if(fread_ret < MSS){
                cout<<"This is last packet."<<endl;
                break;
            }
        } //end if-else

        //Wait for the ACK message from RLS machine
        cout<<"Start receiving ack message from RLS client ... "<<endl;             
        ackBufferLen = read(sockfd, ackBuffer, DEFAULT_MAX_BUFFER_LEN);
        ackBuffer[ackBufferLen]=0;
        cout<<ackBuffer<<endl;				

    }

    gettimeofday (&RTT_end, NULL);	
    timer_sub(&RTT_start, &RTT_end, &RTT_result);
    cout<<"The estimated RTT time for each packet is "<< (RTT_result.tv_sec * 1000000 + RTT_result.tv_usec)/current_seq_no <<"  microseconds"<<endl;
    close(sockfd);         
    return 0;

    }
}

