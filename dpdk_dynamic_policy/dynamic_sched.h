#ifndef DYNAMIC_SCHED_H
#define DYNAMIC_SCHED_H

// for sched_xxx syscalls
#include <sched.h>
// for pid functions
#include <sys/types.h>
#include <unistd.h>
#include <stdint.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>

extern int is_exp_loop;

extern int soem_pid;
extern uint64_t tsc_start_to_fifo[1000000];
extern uint64_t tsc_end_to_fifo[1000000];
extern uint64_t tsc_start_to_normal[1000000];
extern uint64_t tsc_end_to_normal[1000000];


void set_soem_pid(int pid);
int set_rt_policy(int policy, int priority);
int set_normal_policy(void);

#endif // DYNAMIC_SCHED_H