/** \file
 * \brief Example code for Simple Open EtherCAT master
 *
 * Usage: simple_ng IFNAME1
 * IFNAME1 is the NIC interface name, e.g. 'eth0'
 *
 * This is a minimal test.
 */

#include "soem/soem.h"
#include "soem/log_config.h"
#include "../utils/utils.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <time.h>

// for dpdk
#include <rte_eal.h>
#include <rte_ethdev.h>
#include <rte_cycles.h>
#include <rte_lcore.h>
#include <rte_mbuf.h>

#include "exp_config.h"

#if USE_TSX
#include "../ts_ext/ts_ext.h"
#endif

#define MEASURE_POLLLING 0
#define MAX_LIST_SIZE 1000000

typedef struct
{
   ecx_contextt context;
   char *iface;
   uint8 group;
   int roundtrip_time;
   uint8 map[4096];
} Fieldbus;

static void
fieldbus_initialize(Fieldbus *fieldbus, char *iface)
{
   /* Let's start by 0-filling `fieldbus` to avoid surprises */
   memset(fieldbus, 0, sizeof(*fieldbus));

   fieldbus->iface = iface;
   fieldbus->group = 0;
   fieldbus->roundtrip_time = 0;
}

static int
fieldbus_roundtrip(Fieldbus *fieldbus)
{
   ecx_contextt *context;
   ec_timet start, end, diff;
   int wkc;

   context = &fieldbus->context;

   start = osal_current_time();
   ecx_send_processdata(context);
   wkc = ecx_receive_processdata(context, EC_TIMEOUTRET);
   end = osal_current_time();
   osal_time_diff(&start, &end, &diff);
   fieldbus->roundtrip_time = (int)(diff.tv_sec * 1000000 + diff.tv_nsec / 1000);

   return wkc;
}

static boolean
fieldbus_start(Fieldbus *fieldbus)
{
   ecx_contextt *context;
   ec_groupt *grp;
   ec_slavet *slave;
   int i;

   context = &fieldbus->context;
   grp = context->grouplist + fieldbus->group;

  //  printf("Initializing SOEM on '%s'... ", fieldbus->iface);
   if (!ecx_init(context, fieldbus->iface))
   {
      printf("no socket connection\n");
      return FALSE;
   }
  //  printf("done\n");

  //  printf("Finding autoconfig slaves...\n");
   if (ecx_config_init(context) <= 0)
   {
      printf("no slaves found\n");
      return FALSE;
   }
   printf("%d slaves found\n", context->slavecount);

  //  printf("Sequential mapping of I/O...\n");
   ecx_config_map_group(context, fieldbus->map, fieldbus->group);
  //  printf("mapped %dO+%dI bytes from %d segments\n",
          // grp->Obytes, grp->Ibytes, grp->nsegments);
   if (grp->nsegments > 1)
   {
      /* Show how slaves are distributed */
      for (i = 0; i < grp->nsegments; ++i)
      {
        //  printf("%s%d", i == 0 ? " (" : "+", grp->IOsegment[i]);
      }
      // printf(" slaves)");
   }
  //  printf("\n");

  //  printf("Configuring distributed clock... ");
   ecx_configdc(context);
  //  printf("done\n");

  //  printf("Waiting for all slaves in safe operational... ");
   ecx_statecheck(context, 0, EC_STATE_SAFE_OP, EC_TIMEOUTSTATE * 4);
  //  printf("done\n");

  //  printf("Send a roundtrip to make outputs in slaves happy... ");
   fieldbus_roundtrip(fieldbus);
  //  printf("done\n");

   printf("Setting operational state.. \n");
   /* Act on slave 0 (a virtual slave used for broadcasting) */
   slave = context->slavelist;
   slave->state = EC_STATE_OPERATIONAL;
   ecx_writestate(context, 0);
   /* Poll the result ten times before giving up */
   for (i = 0; i < 10; ++i)
   {
      printf(".");
      fieldbus_roundtrip(fieldbus);
      ecx_statecheck(context, 0, EC_STATE_OPERATIONAL, EC_TIMEOUTSTATE / 10);
      if (slave->state == EC_STATE_OPERATIONAL)
      {
         printf(" all slaves are now operational\n");
         return TRUE;
      }
   }

   printf(" failed,");
   ecx_readstate(context);
   for (i = 1; i <= context->slavecount; ++i)
   {
      slave = context->slavelist + i;
      if (slave->state != EC_STATE_OPERATIONAL)
      {
        //  printf(" slave %d is 0x%04X (AL-status=0x%04X %s)",
        //         i, slave->state, slave->ALstatuscode,
        //         ec_ALstatuscode2string(slave->ALstatuscode));
      }
   }
   printf("\n");

   return FALSE;
}

static void
fieldbus_stop(Fieldbus *fieldbus)
{
   ecx_contextt *context;
   ec_slavet *slave;

   context = &fieldbus->context;
   /* Act on slave 0 (a virtual slave used for broadcasting) */
   slave = context->slavelist;

   printf("Requesting init state on all slaves... ");
   slave->state = EC_STATE_INIT;
   ecx_writestate(context, 0);
   printf("done\n");

   printf("Close socket... ");
   ecx_close(context);
   printf("done\n");
}

static boolean
fieldbus_dump(Fieldbus *fieldbus)
{
   ecx_contextt *context;
   ec_groupt *grp;
   uint32 n;
   int wkc, expected_wkc;

   context = &fieldbus->context;
   grp = context->grouplist + fieldbus->group;

   wkc = fieldbus_roundtrip(fieldbus);
   expected_wkc = grp->outputsWKC * 2 + grp->inputsWKC;
  //  printf("%6d usec  WKC %d", fieldbus->roundtrip_time, wkc);
   if (wkc < expected_wkc)
   {
      global_recv_timeout_cnt++;
      // printf(" wrong (expected %d)\n", expected_wkc);
      return FALSE;
   }

  //  printf("  O:");
  //  for (n = 0; n < grp->Obytes; ++n)
  //  {
  //     printf(" %02X", grp->outputs[n]);
  //  }
  //  printf("  I:");
  //  for (n = 0; n < grp->Ibytes; ++n)
  //  {
  //     printf(" %02X", grp->inputs[n]);
  //  }
  //  printf("  T: %lld\r", (long long)context->DCtime);
   return TRUE;
}

static void
fieldbus_check_state(Fieldbus *fieldbus)
{
   ecx_contextt *context;
   ec_groupt *grp;
   ec_slavet *slave;
   int i;

   context = &fieldbus->context;
   grp = context->grouplist + fieldbus->group;
   grp->docheckstate = FALSE;
   ecx_readstate(context);
   for (i = 1; i <= context->slavecount; ++i)
   {
      slave = context->slavelist + i;
      if (slave->group != fieldbus->group)
      {
         /* This slave is part of another group: do nothing */
      }
      else if (slave->state != EC_STATE_OPERATIONAL)
      {
         grp->docheckstate = TRUE;
         if (slave->state == EC_STATE_SAFE_OP + EC_STATE_ERROR)
         {
            // printf("* Slave %d is in SAFE_OP+ERROR, attempting ACK\n", i);
            slave->state = EC_STATE_SAFE_OP + EC_STATE_ACK;
            ecx_writestate(context, i);
         }
         else if (slave->state == EC_STATE_SAFE_OP)
         {
            // printf("* Slave %d is in SAFE_OP, change to OPERATIONAL\n", i);
            slave->state = EC_STATE_OPERATIONAL;
            ecx_writestate(context, i);
         }
         else if (slave->state > EC_STATE_NONE)
         {
            if (ecx_reconfig_slave(context, i, EC_TIMEOUTRET))
            {
               slave->islost = FALSE;
              //  printf("* Slave %d reconfigured\n", i);
            }
         }
         else if (!slave->islost)
         {
            ecx_statecheck(context, i, EC_STATE_OPERATIONAL, EC_TIMEOUTRET);
            if (slave->state == EC_STATE_NONE)
            {
               slave->islost = TRUE;
              //  printf("* Slave %d lost\n", i);
            }
         }
      }
      else if (slave->islost)
      {
         if (slave->state != EC_STATE_NONE)
         {
            slave->islost = FALSE;
            // printf("* Slave %d found\n", i);
         }
         else if (ecx_recover_slave(context, i, EC_TIMEOUTRET))
         {
            slave->islost = FALSE;
            // printf("* Slave %d recovered\n", i);
         }
      }
   }

   if (!grp->docheckstate)
   {
      printf("All slaves resumed OPERATIONAL\n");
   }
}

int main(int argc, char *argv[])
{
  if (argc < 2) {
    printf("[ERROR] args invalid!\n");
    return 1;
  }

  // valiables for test
  char nic[10] = "enp3s0";
  uint32_t repeat_cnt = 1000000;
  int num_competition_process = atoi(argv[1]);
  int tsx_us = atoi(argv[2]);
  // int log_num = atoi(argv[2]);

  int interval_usec = 30;
  double CPU_HZ = 2000000000.0;

  Fieldbus fieldbus;
  ecx_contextt *context;
  ec_groupt *grp;
  uint32 n;
  int wkc, expected_wkc;

  // init logfile
  char log_name[256];

  sprintf(log_name, "log/tsx_%dus/rtt_dpdk_tsx_c%d.log", tsx_us, num_competition_process);

  FILE *log_fp = fopen(log_name, "w");

  // tsx log file
  #if USE_TSX
  FILE *tsx_log_fp = fopen("log/tsx_grant.log", "a");
  #endif

  if (log_fp == NULL) {
    printf("Failed to open log files\n");
    return 1;
  }

  // dpdk 初期化
  int ret = rte_eal_init(argc - 1, &argv[1]);
  if (ret < 0) {
    rte_exit(EXIT_FAILURE, "[ERROR] EAL initialization\n");
  }

  unsigned int num_ports = rte_eth_dev_count_avail();
  if (num_ports < 1) {
    rte_exit(EXIT_FAILURE, "[ERROR] Cannot fing available port\n");
  }

  #if USE_TSX
  if (ts_ext_init() < 0) {
    printf("[ERROR] failed to initialize time slice extension\n");
    return 1;
  }
  printf("[INFO] time slice extension initialized\n");
  #endif

  fieldbus_initialize(&fieldbus, nic);
  if (fieldbus_start(&fieldbus))
  {
    int i, min_time, max_time;
    min_time = max_time = 0;

    // for measure valiables
    // double rtt_sum = 0.0f;
    // double cycle_sum = 0.0f;
    // double rtt_avg = 0.0f;
    // double rtt_avg_ndelay = 0.0f;
    // double cycle_avg = 0.0f;
    // double cycle_avg_ndelay = 0.0f;
    // double processing_time = 0.0f;
    uint64_t rdtsc_start, rdtsc_end;
    //

    // レコード用配列をなめる
    unsigned long long dummy = 0;
    for (int i = 0; i < MAX_IO_COUNT; i++) {
      rtt_start[i] = dummy;
      rtt_end[i] = dummy;
    }

    context = &(fieldbus.context);
    grp = context->grouplist + fieldbus.group;

    // printf("[INFO] Using standard SOEM for processdata transfer\n");

    printf("[INFO] send cnt: %d\n", global_send_cnt);
    printf("[INFO] recv cnt: %d\n", global_recv_cnt);

    printf("----- [ Round trip start ] -----\n");

    // mark_trace_label("MEASURE_BEGIN");
    rdtsc_start = __rdtsc();

    for (i = 0; i < repeat_cnt; ++i)
    {

      #if USE_IOURING
      ecx_send_processdata_uring(context);
      wkc = ecx_receive_processdata_uring(context, EC_TIMEOUTRET);
      #else
      ecx_send_processdata(context);
      wkc = ecx_receive_processdata(context, EC_TIMEOUTRET);
      #endif 

      // printf("!!! Round Trip !!!\n");

      expected_wkc = grp->outputsWKC * 2 + grp->inputsWKC;
      if (wkc == EC_NOFRAME)
      {
          printf("Round %d: No frame\n", i);
          break;
      }

      io_cnt++;

      delay_us_rdtsc(interval_usec, CPU_HZ);
      // osal_usleep(interval_usec);
      // cycle_end[i] = __rdtsc();
    }

    rdtsc_end = __rdtsc();
    // mark_trace_label("MEASURE_END");

    fieldbus_stop(&fieldbus);

    printf("\n[INFO] send cnt: %d\n", global_send_cnt);
    printf("[INFO] recv cnt: %d\n", global_recv_cnt);
    printf("[INFO] send_err cnt:  %d\n", global_send_err_cnt);
    printf("[INFO] recv_timout cnt:  %d\n", global_recv_timeout_cnt);
    printf("[INFO] elapsed (s): %.6f\n", (double)(rdtsc_end - rdtsc_start) / CPU_HZ);
    #if USE_TSX
    printf("\n[INFO] tsx granted cnt:  %d\n", global_tsx_granted_cnt);
    printf("\n[INFO] tsx granted err cnt:  %d\n", global_tsx_granted_err_cnt);
    #endif

    double processing_time = (rdtsc_end - rdtsc_start) / CPU_HZ;
    printf("[INFO] processing time: %.9f (s)\n", processing_time);

    if (io_cnt != repeat_cnt) {
      printf("[ERROR] Don't match io count\n");
    }

    int delay_count = 0;

    for (int i = 0; i < repeat_cnt; i++) {
      // micro second
      double rtt_usec = (double)(rtt_end[i] - rtt_start[i]) / CPU_HZ * 1000000;
      fprintf(log_fp, "%.6f\n", rtt_usec);
    }

    #if USE_TSX
    fprintf(tsx_log_fp, "tsx=%dus,comp=%d,granted=%d,yield_failed=%d\n", tsx_us, num_competition_process, global_tsx_granted_cnt, global_tsx_granted_err_cnt);
    #endif

    fclose(log_fp);

    #if USE_TSX
    fclose(tsx_log_fp);
    #endif


    // printf("\nRoundtrip time (usec): min %d max %d\n", min_time, max_time);
  }

  return 0;
}
