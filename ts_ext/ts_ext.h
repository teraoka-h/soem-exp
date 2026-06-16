#include "/tmp/linux-headers/include/linux/rseq.h"
#include "/tmp/linux-headers/include/linux/prctl.h"

#include <sys/syscall.h>
#include <sys/prctl.h>
#include <sys/auxv.h>
#include <unistd.h>
#include <string.h>
#include <stddef.h>
#include <stdlib.h>
#include <stdio.h>
#include <errno.h>

// rseq_slice_yield(2) の syscall number
#ifndef SYS_rseq_slice_yield
#define SYS_rseq_slice_yield 471
#endif

// rseq ABI 整合性チェック用のシグネチャ
#define RSEQ_SIG	0x53053053

extern struct rseq *rseq_tsx;

int ts_ext_init();
void ts_ext_set_request(int request);
int ts_ext_is_granted();
int ts_ext_rseq_yield();