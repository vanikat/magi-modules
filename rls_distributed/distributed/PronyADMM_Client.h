#ifndef _PMU_H
#define _PMU_H

#ifdef __cplusplus
extern "C" {
#endif

	int PronyADMMClient(char* server_host, char* server_port,
			char* data_port, char* strategy,
			char* backupserver1_host, backupserver1_port,
			char* backupserver2_host, backupserver2_port,
			char* backupserver3_host, backupserver3_port,
			char* backupserver4_host, backupserver4_port,
			char* num_of_attack, char* num_of_pdcs);

#ifdef __cplusplus
}
#endif

#endif
