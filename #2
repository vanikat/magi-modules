set ns [new Simulator] 
source tb_compat.tcl 

set magi_start "sudo python /share/magi/current/magi_bootstrap.py" 

set clientnode [$ns node]
tb-set-node-startcmd $clientnode "$magi_start"

set servernode [$ns node]
tb-set-node-startcmd $servernode "$magi_start"

set link [$ns duplex-link $clientnode $servernode 100Mbps 0ms DropTail] 

$ns rtproto Static
$ns run
