
#include <cstdio>
#include <cstdlib>
#include <sstream>
#include <iostream>
#include <cstring>
#include <fstream>
#include "armadillo"
using namespace std;

#define SHELLSCRIPT "\
#/bin/bash \n\
gnome-terminal -x ./ADMMServer 70000\n\
"
#define PREDEFINED_SERVER "Y1_90.txt"

int main(int argc, char *argv[])
{
/*  puts("Will execute sh in a new terminal with the following script:");
  //puts(SHELLSCRIPT);
  puts("Starting now:");
  char command[50];
  	int length;
	length = sizeof("gnome-terminal -x ./ADMMServer ");
 	cout<<"The length of command is "<<length<<endl;
	strcpy(command, "gnome-terminal -x ./ADMMServer ");
        strcat(command, argv[1]);
	cout<<"The cout command is "<<command<<endl;
	printf("The printf command is %s\n", command);
  	system(command);
  	cout<<"Happy Ending"<<endl;
  char filename[20];
  strcpy(filename,argv[1]);	
  std::cout<<"This new filename is "<<filename<<std::endl;
  if (strcmp(filename, PREDEFINED_SERVER)==0) std::cout<<"Are you happy really "<<filename<<std::endl;
 
	int i,j;
	mat A;
	A.set_size(3,3);
	for (i=0; i<3; i++){
		for (j=0; j<3; j++) A(i,j) = i+j;
	    }	
	A.print("A matrix is ");
	A.set_size(2,2);
	A.print("After resize, A is ");

*/ 

	char file1name[50];
	ofstream file1;
	
 	strcpy(file1name, argv[1]);
	strcat(file1name, "_data_delay.txt");
	
	file1.open (file1name);
	file1 << "this is data delay";
	file1.close();
	
	
	return 0;
}
