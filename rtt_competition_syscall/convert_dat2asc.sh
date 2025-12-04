#!/usr/bin/zsh

DAT_FILE=$1
ASC_FILE=${DAT_FILE:r}.asc
trace-cmd report ${DAT_FILE} > ${ASC_FILE}

