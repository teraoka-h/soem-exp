#include <limits.h>
#include <stdint.h>

int main() {
  uint64_t max = 50000000000;
  volatile uint64_t sum = 0;

  for (uint64_t i = 0; i <= max; i++) {
    sum += 1;
  }
  
  return 0;
}