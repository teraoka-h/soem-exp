#ifndef SOEM_URING_H
#define SOEM_URING_H

#include "liburing.h"

#define IOURING_QDEPTH 32
#define REQ_ID_SEND 0
#define REQ_ID_RECV 1

#define USE_SQPOLL 0

typedef struct {
  struct io_uring ring;
  struct io_uring_sqe *sq; // submission queue
  struct io_uring_cqe *cq; // completion queue
} IOuringContext;

extern IOuringContext ioctx;

int iouring_init();
int iouring_init_flag(int flags);
void iouring_deinit();
void iouring_submit();
int iouring_request_send_recv(int sock, void *txbuf, size_t txlen, void *rxbuf, size_t rxlen, int flag);
int iouring_request_send_recv_sqpoll(int sock, void *txbuf, size_t txlen, void *rxbuf, size_t rxlen, int flag);
int iouring_request_send(int sock, void *buf, size_t len, int flag);
int iouring_wait_send_completion();
int iouring_poll_send_completion();
int iouring_request_recv(int sock, void *buf, size_t len, int flag);
int iouring_wait_recv_completion();
int iouring_poll_recv_completion();
int iouring_finish_recv();


#endif