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
#include "soem_uring.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <time.h>

// EXPERIMENT VALIABLES
#define MEASURE_POLLLING 0
#define MAX_LIST_SIZE 1000000

double rtt_list[MAX_LIST_SIZE];
// 

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

   printf("Initializing SOEM on '%s'... ", fieldbus->iface);
   if (!ecx_init(context, fieldbus->iface))
   {
      printf("no socket connection\n");
      return FALSE;
   }
   printf("done\n");

   printf("Finding autoconfig slaves... ");
   if (ecx_config_init(context) <= 0)
   {
      printf("no slaves found\n");
      return FALSE;
   }
   printf("%d slaves found\n", context->slavecount);

   printf("Sequential mapping of I/O... ");
   ecx_config_map_group(context, fieldbus->map, fieldbus->group);
   printf("mapped %dO+%dI bytes from %d segments",
          grp->Obytes, grp->Ibytes, grp->nsegments);
   if (grp->nsegments > 1)
   {
      /* Show how slaves are distributed */
      for (i = 0; i < grp->nsegments; ++i)
      {
         printf("%s%d", i == 0 ? " (" : "+", grp->IOsegment[i]);
      }
      printf(" slaves)");
   }
   printf("\n");

   printf("Configuring distributed clock... ");
   ecx_configdc(context);
   printf("done\n");

   printf("Waiting for all slaves in safe operational... ");
   ecx_statecheck(context, 0, EC_STATE_SAFE_OP, EC_TIMEOUTSTATE * 4);
   printf("done\n");

   printf("Send a roundtrip to make outputs in slaves happy... ");
   fieldbus_roundtrip(fieldbus);
   printf("done\n");

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
         printf(" slave %d is 0x%04X (AL-status=0x%04X %s)",
                i, slave->state, slave->ALstatuscode,
                ec_ALstatuscode2string(slave->ALstatuscode));
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
            printf("* Slave %d is in SAFE_OP+ERROR, attempting ACK\n", i);
            slave->state = EC_STATE_SAFE_OP + EC_STATE_ACK;
            ecx_writestate(context, i);
         }
         else if (slave->state == EC_STATE_SAFE_OP)
         {
            printf("* Slave %d is in SAFE_OP, change to OPERATIONAL\n", i);
            slave->state = EC_STATE_OPERATIONAL;
            ecx_writestate(context, i);
         }
         else if (slave->state > EC_STATE_NONE)
         {
            if (ecx_reconfig_slave(context, i, EC_TIMEOUTRET))
            {
               slave->islost = FALSE;
               printf("* Slave %d reconfigured\n", i);
            }
         }
         else if (!slave->islost)
         {
            ecx_statecheck(context, i, EC_STATE_OPERATIONAL, EC_TIMEOUTRET);
            if (slave->state == EC_STATE_NONE)
            {
               slave->islost = TRUE;
               printf("* Slave %d lost\n", i);
            }
         }
      }
      else if (slave->islost)
      {
         if (slave->state != EC_STATE_NONE)
         {
            slave->islost = FALSE;
            printf("* Slave %d found\n", i);
         }
         else if (ecx_recover_slave(context, i, EC_TIMEOUTRET))
         {
            slave->islost = FALSE;
            printf("* Slave %d recovered\n", i);
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
  if (argc < 3) {
    printf("[ERROR] args invalid!\n");
    return 1;
  }

  // valiables for test
  char nic[10] = "enp3s0";
  uint32_t repeat_cnt = atoi(argv[1]);
  char *id_str = argv[2];

  int interval_usec = 15;
  double CPU_HZ = 1800000000.0;

  Fieldbus fieldbus;
  ecx_contextt *context;
  ec_groupt *grp;
  uint32 n;
  int wkc, expected_wkc;

  // init logfile
  open_logfile("log/rtt_%d_%s_iouring_soem.log", repeat_cnt, id_str);

  iouring_init();

  fieldbus_initialize(&fieldbus, nic);
  if (fieldbus_start(&fieldbus))
  {
    int i, min_time, max_time;
    min_time = max_time = 0;

    #if MEASURE_POLLLING
    char info_file[256];
    sprintf(info_file, "log/info_%d_%s_iouring_soem.log", repeat_cnt, id_str);
    FILE* info_fp = fopen(info_file, "w");

    double rtt_sum = 0.0f;
    double send_poll_sum = 0.0f;
    double recv_poll_sum = 0.0f;
    double req_sum = 0.0f;

    #endif

    context = &(fieldbus.context);
    grp = context->grouplist + fieldbus.group;

    printf("\n[INFO] send cnt: %d\n", global_send_cnt);
    printf("[INFO] recv cnt: %d\n", global_recv_cnt);

    printf("----- [ Round trip start ] -----\n");

    for (i = 0; i < repeat_cnt; ++i)
    {
      // printf("Roud Trip: %d\n", i);
      get_clock_rdtsc(INDEX_RTT_START);

      ecx_send_processdata_uring(context);
      wkc = ecx_receive_processdata_uring(context, EC_TIMEOUTRET);

      get_clock_rdtsc(INDEX_RTT_END);

      #if MEASURE_POLLLING
      double req_us = calc_processtime_us_rdtsc(INDEX_REQ_START, INDEX_REQ_END, CPU_HZ);
      double send_us = calc_processtime_us_rdtsc(INDEX_REQ_START, INDEX_SEND_POLL_END, CPU_HZ);
      double recv_us = calc_processtime_us_rdtsc(INDEX_REQ_START, INDEX_RECV_POLL_END, CPU_HZ);
      double send_poll_us = calc_processtime_us_rdtsc(INDEX_SEND_POLL_START, INDEX_SEND_POLL_END, CPU_HZ);
      double recv_poll_us = calc_processtime_us_rdtsc(INDEX_RECV_POLL_START, INDEX_RECV_POLL_END, CPU_HZ);
      #endif

      double rtt_us = calc_processtime_us_rdtsc(INDEX_RTT_START, INDEX_RTT_END, CPU_HZ);
      rtt_list[i] = rtt_us;

      #if MEASURE_POLLLING
      rtt_sum += rtt_us;
      send_poll_sum += send_poll_us;
      recv_poll_sum += recv_poll_us;
      req_sum += req_us;

      #endif

      expected_wkc = grp->outputsWKC * 2 + grp->inputsWKC;
      if (wkc == EC_NOFRAME)
      {
          printf("Round %d: No frame\n", i);
          break;
      }
      else {
        // printf("WKC: %d\n", wkc);
      }

      osal_usleep(interval_usec);
    }

    printf("\n[INFO] send cnt: %d\n", global_send_cnt);
    printf("\n[INFO] recv cnt: %d\n", global_recv_cnt);
    printf("\n[INFO] send_err cnt:  %d\n", global_send_err_cnt);
    printf("\n[INFO] recv_timout cnt:  %d\n", global_recv_timeout_cnt);
    fieldbus_stop(&fieldbus);

    #if MEASURE_POLLLING
    double avg_rtt = rtt_sum / repeat_cnt;
    double avg_send_poll = send_poll_sum / repeat_cnt;
    double avg_recv_poll = recv_poll_sum / repeat_cnt;
    double send_poll_perc = (send_poll_sum / rtt_sum) * 100.0;
    double recv_poll_perc = (recv_poll_sum / rtt_sum) * 100.0;
    double req_perc = (req_sum / rtt_sum) * 100.0;

    fprintf(info_fp, "rtt_sum: %.6f (us)\nrequest_sum: %.6f (us)\nsend_poll_sum: %.6f (us)\nrecv_poll_sum: %.6f (us)\n", rtt_sum, req_sum, send_poll_sum, recv_poll_sum);
    fprintf(info_fp, "avg_rtt: %.6f (us)\navg_send_poll: %.6f (us)\navg_recv_poll: %.6f (us)\n",
            avg_rtt, avg_send_poll, avg_recv_poll);
    fprintf(info_fp, "request_perc: %.6f (%%)\nsend_poll_perc: %.6f (%%)\nrecv_poll_perc: %.6f (%%)\n",
      req_perc, send_poll_perc, recv_poll_perc);
    fclose(info_fp);
    #endif

    for (int i = 0; i < repeat_cnt; i++) {
      logfile_printf("%.6f\n", rtt_list[i]);
    }

    iouring_deinit();

    // printf("\nRoundtrip time (usec): min %d max %d\n", min_time, max_time);
  }

  close_logfile();

  return 0;
}
