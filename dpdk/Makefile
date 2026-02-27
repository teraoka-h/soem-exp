CC = gcc
SRC = soem_dpdk.c
TARGET = ${SRC:.c=}

SOEM_SRCS = $(wildcard soem/*.c)
SOEM_OBJS = $(patsubst %.c, %.o, $(notdir ${SOEM_SRCS}))
ARCHIVE_FILE = libsoem.a
UTILS = $(wildcard ../utils/*.c)

PKGCONF ?= pkg-config

CFLAGS += -O2 -I../utils
CFLAGS_DPDK = -DALLOW_EXPERIMENTAL_API
CFLAGS_DPDK += -O3 $(shell $(PKGCONF) --cflags libdpdk)
LDFLAGS_SHARED = $(shell $(PKGCONF) --libs libdpdk)
LDFLAGS_STATIC = $(shell $(PKGCONF) --static --libs libdpdk)

${SOEM_OBJS}: ${SOEM_SRCS} 
	@echo "[INFO] Compiling soem sources..."
	${CC} -c $^ $(LDFLAGS) ${CFLAGS_DPDK} $(LDFLAGS_SHARED) 

archive: ${SOEM_OBJS}
	@echo "[INFO] Creating archive ${ARCHIVE_FILE}..."
	ar rcs ${ARCHIVE_FILE} $^
	rm ${SOEM_OBJS}

exe: archive ${SRC}
	@echo "[INFO] Compiling executable ${TARGET}..."
	${CC} -o ${TARGET} ${SRC} ${ARCHIVE_FILE} ${UTILS} ${CFLAGS} ${CFLAGS_DPDK} ${LDFLAGS_SHARED} -I./

clean:
	rm -f ${TARGET} ${ARCHIVE_FILE} ${SOEM_OBJS} 