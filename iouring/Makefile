CC = gcc
SRC = soem_iouring.c
TARGET = ${SRC:.c=}

SOEM_SRCS = $(wildcard soem/*.c)
SOEM_OBJS = $(patsubst %.c, %.o, $(notdir ${SOEM_SRCS}))
IOURING_SRCS = soem_uring.c
ARCHIVE_FILE = libsoem.a
UTILS = $(wildcard ../utils/*.c)

CFLAGS = -O2 -I../utils

${SOEM_OBJS}: ${SOEM_SRCS} 
	${CC} -c $^

archive: ${SOEM_OBJS}
	ar rcs ${ARCHIVE_FILE} $^
	rm ${SOEM_OBJS}

exe: archive ${SRC}
	${CC} -o ${TARGET} ${SRC} ${ARCHIVE_FILE} ${IOURING_SRCS} ${UTILS} ${CFLAGS} -I./ -luring