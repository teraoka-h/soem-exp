#include "dynamic_sched.h"

int is_exp_loop = 0;
int soem_pid = 0;

uint64_t tsc_start_to_fifo[1000000];
uint64_t tsc_end_to_fifo[1000000];
uint64_t tsc_start_to_normal[1000000];
uint64_t tsc_end_to_normal[1000000];

void set_soem_pid(int pid)
{
   soem_pid = pid;
}

int set_rt_policy(int policy, int priority)
{
   struct sched_param param;
   param.sched_priority = priority;
   int ret = sched_setscheduler(soem_pid, policy, &param);
   if (ret != 0) {
      printf("[ERROR] Failed to set RT policy: %s\n", strerror(errno));
   }

   return ret;
}

int set_normal_policy(void)
{
   struct sched_param param;
   param.sched_priority = 0;
   int ret = sched_setscheduler(soem_pid, SCHED_OTHER, &param);
   if (ret != 0) {
      printf("[ERROR] Failed to set normal policy: %s\n", strerror(errno));
   }
   return ret;
}