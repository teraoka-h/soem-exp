#include "../utils/utils.h"
#include "soem/soem.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <time.h>

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

int main(int argc, char *argv[])
{
  if (argc < 3) {
    printf("[ERROR] args invalid!\n");
    return 1;
  }

  Fieldbus fieldbus;
  ecx_contextt *context;
  ec_groupt *grp;
  uint32 n;
  int wkc, expected_wkc;

  // valiables for test
  char nic[10] = "enp3s0";
  uint32_t repeat_cnt = atoi(argv[1]);
  char *id_str = argv[2];

  int send_start = 0;
  int send_end   = 1;
  int poll_start = 2;
  int poll_end   = 3;
  int recv_start = 4;
  int recv_end   = 5;
  int interval_usec = 20;

  double cpu_hz = 1800000000.0; // 1.8GHz

  // init logfile
  open_logfile("log/hc_%d_%s_soem.log", repeat_cnt, id_str);

  fieldbus_initialize(&fieldbus, nic);
  if (fieldbus_start(&fieldbus))
  {
    int i, min_time, max_time;
    min_time = max_time = 0;

    printf("\n[INFO] send cnt: %d\n", global_send_cnt);
    printf("\n[INFO] recv cnt: %d\n", global_recv_cnt);

    context = &(fieldbus.context);
    grp = context->grouplist + fieldbus.group;

    printf("[INFO] Interval: %d (us)\n", interval_usec);
    printf("----- [ Round trip start ] -----\n");

    for (i = 1; i <= repeat_cnt; ++i)
    {
      ecx_send_processdata(context);
      wkc = ecx_receive_processdata(context, EC_TIMEOUTRET);

      double sned_us = calc_processtime_us_rdtsc(0, 1, cpu_hz);
      double poll_us = calc_processtime_us_rdtsc(2, 3, cpu_hz);
      double recv_us = calc_processtime_us_rdtsc(4, 5, cpu_hz);
      double rtt_us = calc_processtime_us_rdtsc(0, 5, cpu_hz);

      logfile_printf("%.9f,%.9f,%.9f,%.9f\n", sned_us, poll_us, recv_us, rtt_us);

      expected_wkc = grp->outputsWKC * 2 + grp->inputsWKC;
      if (wkc == EC_NOFRAME)
      {
          printf("Round %d: No frame\n", i);
          break;
      }

      osal_usleep(interval_usec);
    }
  }

  printf("\n[INFO] send cnt: %d\n", global_send_cnt);
  printf("\n[INFO] recv cnt: %d\n", global_recv_cnt);
  printf("\n[INFO] send_err cnt:  %d\n", global_send_err_cnt);
  printf("\n[INFO] recv_timout cnt:  %d\n", global_recv_timeout_cnt);

  fieldbus_stop(&fieldbus);
  close_logfile();

  return 0;
}
