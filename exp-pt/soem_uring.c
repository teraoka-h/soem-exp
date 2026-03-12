#include "soem_uring.h"
#include <stdio.h>
#include <string.h>
#include <time.h>

IOuringContext ioctx;


int iouring_init() {
  // SQPOLL によりてカーネルスレッドが監視するため、システムコール現象
  return io_uring_queue_init(IOURING_QDEPTH, &(ioctx.ring), 0);
}

// int iouring_init_flag(int flags) {
//   struct io_uring_params params;
//   memset(&params, 0, sizeof(params));
//   params.flags = flags;
//   params.sq_thread_idle = 2000; // 2s
//   // params.flags = IORING_SETUP_SQPOLL;
//   // SQPOLL によりてカーネルスレッドが監視するため、システムコール現象
//   int ret = io_uring_queue_init_params(IOURING_QDEPTH, &(ioctx.ring), &params);
//   if (ret < 0) {
//     fprintf(stderr, "[ERROR] io_uring_queue_init_params failed: %d (%s)\n",
//             ret, strerror(-ret));
//     return ret;
//   }

//   fprintf(stderr,
//   "params.features=0x%x, params.wq_fd=%d, params.sq_thread_cpu=%d\n",
//   params.features, params.wq_fd, params.sq_thread_cpu);

//   if (!(params.features & IORING_FEAT_SQPOLL_NONFIXED)) {
//     printf("[WARN] kernel does not support SQPOLL (IORING_FEAT_SQPOLL_NONFIXED missing)\n");
// }

//   ioctx.sq = io_uring_get_sqe(&ioctx.ring);
//   io_uring_prep_nop(ioctx.sq);
//   // 初回 submit を一度実行して poller を確実に起こす（SQPOLL 使用時の安全策）
//   ret = io_uring_submit(&ioctx.ring);
//   if (ret < 0) {
//     fprintf(stderr, "[WARN] initial io_uring_submit returned %d (%s)\n",
//             ret, strerror(-ret));
//     // エラーでも継続するか、ここで abort するかは設計次第
//   } else {
//     fprintf(stderr, "[INFO] initial submit OK: %d\n", ret);
//   }

//   if (io_uring_wait_cqe(&ioctx.ring, &(ioctx.cq)) == 0) {
//         io_uring_cqe_seen(&ioctx.ring, &(ioctx.cq));
//         fprintf(stderr, "[INIT] poller warm-up complete\n");
//     }

//   return 0;
// }

void iouring_deinit() {
  io_uring_queue_exit(&(ioctx.ring));
}

void iouring_submit() {
  io_uring_submit(&(ioctx.ring));
}

int iouring_request_send_recv(int sock, void *txbuf, size_t txlen, void *rxbuf, size_t rxlen, int flag) {
  // printf("[CALL] iouring_request_send_recv\n");
  int submission = 0;
  ioctx.sq = io_uring_get_sqe(&(ioctx.ring));
  if (ioctx.sq == NULL) {
    printf("[ERROR] fail to iouring submissonQ\n");
    return -1;
  }
  // send syscall 要求の登録
  io_uring_prep_send(ioctx.sq, sock, txbuf, txlen, flag);
  io_uring_sqe_set_data(ioctx.sq, (void *)REQ_ID_SEND);
  ioctx.sq->flags |= IOSQE_IO_LINK;

  ioctx.sq = io_uring_get_sqe(&(ioctx.ring));
  if (ioctx.sq == NULL) {
    printf("[ERROR] fail to iouring submissonQ\n");
    return -1;
  }
  io_uring_prep_recv(ioctx.sq, sock, rxbuf, rxlen, flag);
  io_uring_sqe_set_data(ioctx.sq, (void *)REQ_ID_RECV);

  submission = io_uring_submit(&(ioctx.ring));

  if (submission <= 0) {
    printf("[ERROR] fail to iouring send-recv request submission\n");
    return -1;
  }

  return submission;
}

int iouring_request_send_recv_sqpoll(int sock, void *txbuf, size_t txlen, void *rxbuf, size_t rxlen, int flag) {
  printf("[CALL] iouring_request_send_recv\n");
  int submission = 0;
  ioctx.sq = io_uring_get_sqe(&(ioctx.ring));
  if (ioctx.sq == NULL) {
    printf("[ERROR] fail to iouring submissonQ\n");
    return -1;
  }
  // send syscall 要求の登録
  io_uring_prep_send(ioctx.sq, sock, txbuf, txlen, flag);
  io_uring_sqe_set_data(ioctx.sq, (void *)REQ_ID_SEND);
  ioctx.sq->flags |= IOSQE_IO_LINK;

  ioctx.sq = io_uring_get_sqe(&(ioctx.ring));
  if (ioctx.sq == NULL) {
    printf("[ERROR] fail to iouring submissonQ\n");
    return -1;
  }
  io_uring_prep_recv(ioctx.sq, sock, rxbuf, rxlen, flag);
  io_uring_sqe_set_data(ioctx.sq, (void *)REQ_ID_RECV);

  #if !USE_SQPOLL
  submission = io_uring_submit(&(ioctx.ring));

  if (submission <= 0) {
    printf("[ERROR] fail to iouring send-recv request submission\n");
    return -1;
  }

  return submission;
  #else
  return 1;
  #endif
}

int iouring_request_send(int sock, void *buf, size_t len, int flag) {
  // printf("[CALL] iouring_request_send\n");
  // submission queue を確保
  int submission = 0;
  ioctx.sq = io_uring_get_sqe(&(ioctx.ring));
  if (ioctx.sq == NULL) {
    printf("[ERROR] fail to iouring submissonQ\n");
    return -1;
  }
  // send syscall 要求の登録
  io_uring_prep_send(ioctx.sq, sock, buf, len, flag);
  io_uring_sqe_set_data(ioctx.sq, (void *)REQ_ID_SEND);
  submission = io_uring_submit(&(ioctx.ring));
  if (submission <= 0) {
    printf("[ERROR] fail to iouring send request submission\n");
    return -1;
  }

  // printf("[INFO] subit send request\n");

  return submission;
}

int iouring_wait_send_completion() {
  // printf("[CALL] iouring_wait_send_completion\n");
  int completion = io_uring_wait_cqe(&(ioctx.ring), &(ioctx.cq));
  if (completion < 0) {
    perror("[ERROR] fail to iouring wait send\n");
    return -1;
  }

  if (ioctx.cq->user_data != REQ_ID_SEND) {
    return -1;
  }
  // completion queue の後始末
  io_uring_cqe_seen(&(ioctx.ring), ioctx.cq);
  // printf("[INFO] complete send request\n");
  // send の返り値
  return ioctx.cq->res;
}

int iouring_poll_send_completion() {
  int completion;

  while (1) {
    completion = io_uring_peek_cqe(&(ioctx.ring), &(ioctx.cq));
    // printf("[CALL] iouring_poll_send_completion: %d\n", completion);
    if (completion == 0) {
      break;
    }
    else if (completion == -EAGAIN) {
      continue;
    }
    else if (completion < 0) {
      printf("[ERROR] fail to iouring poll send: %d\n", completion);
      return -1;
    }
  }

  if (ioctx.cq->user_data != REQ_ID_SEND) {
    return -1;
  }
  // completion queue の後始末
  io_uring_cqe_seen(&(ioctx.ring), ioctx.cq);
  // printf("[INFO] complete send request\n");
  // send の返り値
  return ioctx.cq->res;
}

int iouring_request_recv(int sock, void *buf, size_t len, int flag) {
  // submission queue を確保
  int submission = 0;
  ioctx.sq = io_uring_get_sqe(&(ioctx.ring));
  if (ioctx.sq == NULL) {
    printf("[ERROR] fail to iouring sunmissionQ\n");
    return -1;
  }
  // send syscall 要求の登録
  io_uring_prep_recv(ioctx.sq, sock, buf, len, flag);
  io_uring_sqe_set_data(ioctx.sq, (void *)REQ_ID_RECV);
  submission = io_uring_submit(&(ioctx.ring));
  if (submission <= 0) {
    printf("[ERROR] fail to iouring recv request submission\n");
    return -1;
  }

  return submission;
}

int iouring_wait_recv_completion() {
  // printf("[CALL] iouring_wait_recv_completion\n");
  // int ret = io_uring_peek_cqe(&(ioctx.ring), &(ioctx.cq));
  int ret = io_uring_wait_cqe(&(ioctx.ring), &(ioctx.cq));

  // 未完了
  if (ret < 0) {
    printf("[ERROR] fail to iouring wait recv\n");
    return -1;
  }

  if (ioctx.cq->user_data != REQ_ID_RECV) {
    return -1;
  }
  io_uring_cqe_seen(&(ioctx.ring), ioctx.cq);
  // printf("[INFO] complete recv request\n");
  
  return ioctx.cq->res;
}

int iouring_poll_recv_completion() {
  int completion;

  while (1) {
    completion = io_uring_peek_cqe(&(ioctx.ring), &(ioctx.cq));
    // printf("[CALL] iouring_poll_recv_completion\n");
    if (completion == 0) {
      break;
    }
    else if (completion == -EAGAIN) {
      continue;
    }
    else if (completion < 0) {
      printf("[ERROR] fail to iouring poll recv: %d\n", completion);
      return -1;
    }
  }

  if (ioctx.cq->user_data != REQ_ID_RECV) {
    return -1;
  }
  // completion queue の後始末
  io_uring_cqe_seen(&(ioctx.ring), ioctx.cq);
  // printf("[INFO] complete send request\n");
  // recv の返り値
  return ioctx.cq->res;
}


int iouring_finish_recv() {
  // completion queue の後始末
  io_uring_cqe_seen(&(ioctx.ring), ioctx.cq);
  // recv の返り値
  return ioctx.cq->res;
}