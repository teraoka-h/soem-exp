#include "timer.h"

int clock_index = 0;
uint64_t rdtsc_clocks[10];

void reset_clock_index(void) {
  clock_index = 0;
}

// for timestamp (unix)
static struct timespec base_unix_time;
static struct timespec base_mono_time;

struct timespec unix_timestamps[10];
struct timespec tmp_timespec;

void init_base_time() {
  clock_gettime(CLOCK_REALTIME, &base_unix_time);
  clock_gettime(CLOCK_MONOTONIC, &base_mono_time);
}

void save_unix_timestamp(int index) {
  clock_gettime(CLOCK_MONOTONIC, &unix_timestamps[index]);
  // struct timespec *save_timespec = &unix_timestamps[index];
  // clock_gettime(CLOCK_MONOTONIC, &tmp_timespec);

  // save_timespec->tv_sec = base_unix_time.tv_sec + (tmp_timespec.tv_sec - base_mono_time.tv_sec);
  // save_timespec->tv_nsec = base_unix_time.tv_nsec + (tmp_timespec.tv_nsec - base_mono_time.tv_nsec);
  // if (save_timespec->tv_nsec > NSEC_MAX) {
  //   save_timespec->tv_sec += 1;
  //   save_timespec->tv_nsec -= NSEC_MAX;
  // } else if (save_timespec->tv_nsec < 0) {
  //   save_timespec->tv_sec -= 1;
  //   save_timespec->tv_nsec += NSEC_MAX;
  // }
}

// for process time