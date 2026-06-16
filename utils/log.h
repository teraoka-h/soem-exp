#ifndef LOG_H
#define LOG_H

#include <stdio.h>
#include <stdint.h>
#include <unistd.h>
#include <stdarg.h>

#define MAX_IO_COUNT 1200000

extern uint64_t io_cnt;
extern unsigned long long rtt_start[MAX_IO_COUNT];
extern unsigned long long rtt_end[MAX_IO_COUNT];
extern unsigned long long tsx_io_list[MAX_IO_COUNT];

// 送受信回数計測用
extern int global_send_cnt;
extern int global_recv_cnt;
extern int global_send_err_cnt;
extern int global_recv_err_cnt;
extern int global_recv_timeout_cnt;

// ppoll 回数計測用
extern int global_ppoll_cnt;

// tsx 回数計測用
extern int global_tsx_granted_cnt;
extern int global_tsx_granted_err_cnt;

void open_logfile(char *fmt, ...);
void close_logfile();
void logfile_printf(char *fmt, ...);

#endif