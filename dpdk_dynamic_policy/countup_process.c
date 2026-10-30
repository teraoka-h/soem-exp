#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>

volatile sig_atomic_t signal_count = 0;

void signal_handler(int sig)
{
    if (sig == SIGUSR1) {
        signal_count++;
    }
}

// argv[1] に YYYYMMDD 形式の日付を指定することで，その名前のディレクトリにログファイルを出力するように変更
int main(int argc, char *argv[])
{
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <YYYYMMDD>\n", argv[0]);
        return 1;
    }

    int day = atoi(argv[1]);

    struct sigaction sa = {0};

    sa.sa_handler = signal_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0;

    if (sigaction(SIGUSR1, &sa, NULL) == -1) {
        perror("sigaction");
        return 1;
    }

    printf("PID: %d\n", getpid());
    printf("Waiting for SIGUSR1...\n");

    unsigned long long count = 0;

    /*
     * 1回目のSIGUSR1を待つ
     */
    while (signal_count < 1) {
        pause();
    }

    printf("Start counting.\n");

    /*
     * カウント開始
     */
    while (signal_count < 2) {
        count++;
    }

    printf("Stop counting.\n");
    printf("count = %llu\n", count);

    /*
     * ファイルへ出力
     */
    char log_file[256];
    snprintf(log_file, sizeof(log_file), "log/%d/countup.log", day);

    FILE *fp = fopen(log_file, "w");
    if (fp == NULL) {
        perror("fopen");
        return 1;
    }

    fprintf(fp, "%llu\n", count);

    fclose(fp);

    return 0;
}
