#ifndef DYNAMIC_SCHED_H
#define DYNAMIC_SCHED_H

// for sched_xxx syscalls
#include <sched.h>
// for pid functions
#include <sys/types.h>
#include <unistd.h>

extern int soem_pid;

void set_soem_pid(int pid);
int set_rt_policy(int policy, int priority);
int set_normal_policy(void);

#endif // DYNAMIC_SCHED_H