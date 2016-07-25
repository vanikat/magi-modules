set ns [new Simulator] 
source tb_compat.tcl 

set magi_start "sudo python /share/magi/current/magi_bootstrap.py" 

set control [$ns node]
tb-set-node-startcmd $control "$magi_start"
tb-set-node-os $control Ubuntu1204-64-STD

# Buildings (21 clients total)
set lanstr ""
set A 20 
for {set i 0 } {$i <= $A } { incr i } {  
        set b($i) [$ns node]
        tb-set-node-startcmd $b($i) "$magi_start" 
        tb-set-node-os $b($i) Ubuntu1204-64-STD
        append lanstr "$b($i) "
} 

# Server (1 server total)
set server [$ns node]
tb-set-node-startcmd $server "$magi_start" 
tb-set-node-os $server Ubuntu1204-64-STD

# create the LAN topology
set lan0 [$ns make-lan "$lanstr $server" 100Mb 0ms]

# Setting links from each building client to the server (5 LINKS MAX)
#set A 20
#for {set i 0 } {$i <= $A } { incr i } {
#        set link($i) [$ns duplex-link $b($i) $server 100Mbps 0ms DropTail]
#}

$ns rtproto Static
$ns run
