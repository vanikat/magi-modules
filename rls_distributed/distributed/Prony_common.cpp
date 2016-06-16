#include "Prony_common.h"

extern "C" {

using namespace std;

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




}
