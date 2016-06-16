#ifndef _ADMMC_H
#define _ADMMC_H

#ifdef __cplusplus
extern "C" {
#endif

	int PronyADMMClient(char* server_host, char* server_port, char* data_port,
			char* strategy, char* backupserver1_host, char* backupserver2_host,
			char* backupserver3_host, char* backupserver4_host,
			char* backupserver_port, char* num_of_attack, char* num_of_pdcs);

#ifdef __cplusplus
}
#endif

#endif
