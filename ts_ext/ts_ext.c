#include "ts_ext.h"

struct rseq *rseq_tsx;

int ts_ext_init() {
  printf("GLIBC_TUNABLES=%s\n",
       getenv("GLIBC_TUNABLES"));

  int ret;

  if (posix_memalign((void **)&rseq_tsx, 128, sizeof(struct rseq)) != 0) {
    printf("[TSX] error: failed to memalign of struct rseq\n");
    return -1;
  }

  memset(rseq_tsx, 0, sizeof(struct rseq));

  rseq_tsx->cpu_id = RSEQ_CPU_ID_UNINITIALIZED;
  rseq_tsx->cpu_id_start = 0;
  rseq_tsx->flags = 0;

  // register rseq
  ret = syscall(SYS_rseq, rseq_tsx, sizeof(struct rseq), 0, RSEQ_SIG); 
  if (ret != 0) {
    printf("[TSX] error: failed to syscall of rseq\n");
    printf("ret = %d, errno = %d (%s)\n", ret, errno, strerror(errno));
    return -1;
  }

  ret = prctl(PR_RSEQ_SLICE_EXTENSION, 
    PR_RSEQ_SLICE_EXTENSION_SET,
    PR_RSEQ_SLICE_EXT_ENABLE, 0, 0
  );

  if (ret != 0) {
    printf("[TSX] error: failed to enable time slice extension\n");
    return -1;
  }

  int status = prctl(
    PR_RSEQ_SLICE_EXTENSION, 
    PR_RSEQ_SLICE_EXTENSION_GET,
    0, 0, 0
  );

  if (status & PR_RSEQ_SLICE_EXT_ENABLE) {
    printf("[TSX] success to register time slice extension\n");
  }
  else {
    printf("[TSX] error: failed to register time slice extension\n");
    return -1;
  }

  return 1;
}

void ts_ext_set_request(int request) {
  rseq_tsx->slice_ctrl.request = request;
}

int ts_ext_is_granted() {
  return rseq_tsx->slice_ctrl.granted;
}

int ts_ext_rseq_yield() {
  // printf("request=%d granted=%d cpu_id=%d\n",
  //      rseq_tsx->slice_ctrl.request,
  //      rseq_tsx->slice_ctrl.granted,
  //      rseq_tsx->cpu_id);

  int ret = syscall(SYS_rseq_slice_yield);
  if (ret != 1) {
    // printf("[TSX] error: failed to syscall of rseq_slice_yield\n");
    // printf("ret = %d, errno = %d (%s)\n", ret, errno, strerror(errno));
    return -1;
  }

  return 1;
}