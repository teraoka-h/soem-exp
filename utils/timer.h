#ifndef TIMER_H
#define TIMER_H

#include <x86intrin.h>
#include <stdint.h>
#include <time.h>

#define NSEC_MAX 999999999L

// for processing time 
extern int clock_index;
extern uint64_t rdtsc_clocks[10];

inline __attribute__((__always_inline__)) void get_clock_rdtsc(int index) {
  rdtsc_clocks[index] = __rdtsc();
}

void reset_clock_index(void);

// for timestamp (unix)
extern struct timespec unix_timestamps[10];
extern struct timespec tmp_timespec;

void init_base_time(void);
void save_unix_timestamp(int index);

double calc_processtime_us_rdtsc(int rtt_start, int rtt_end, double cpu_hz);

//for delay
inline void delay_us_rdtsc(uint32_t usec, double cpu_hz) {
  unsigned long long start = __rdtsc();
  unsigned long long  delay_clocks = (uint64_t)((double)usec * cpu_hz / 1000000.0);
  while ((__rdtsc() - start) < delay_clocks) {
    // busy wait
  }
}


#endif
