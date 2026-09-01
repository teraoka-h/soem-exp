#include "dynamic_sched.h"

int soem_pid = 0;

void set_soem_pid(int pid)
{
   soem_pid = pid;
}

int set_rt_policy(int policy, int priority)
{
   struct sched_param param;
   param.sched_priority = priority;
   return sched_setscheduler(soem_pid, policy, &param);
}

int set_normal_policy(void)
{
   struct sched_param param;
   param.sched_priority = 0;
   return sched_setscheduler(soem_pid, SCHED_OTHER, &param);
}