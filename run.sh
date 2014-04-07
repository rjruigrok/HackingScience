#!/bin/bash 

case $1 in
	"start" )
		echo "start PaperServer"
		nohup python ./paperserver.py > /tmp/nohup.out &
		;;
	"stop" )
		echo "stop PaperServer"
		killall "python" > /dev/null
		;;
	"restart" )
		echo "restart PaperServer"
		killall "python" > /dev/null
		nohup python ./paperserver.py > /tmp/nohup.out &
		;;
	*)
		echo "need start|stop|restart"
		exit 1
esac
