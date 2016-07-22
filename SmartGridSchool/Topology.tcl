set ns [new Simulator] 
source tb_compat.tcl 

set magi_start "sudo python /share/magi/current/magi_bootstrap.py" 

set control [$ns node]
tb-set-node-startcmd $control "$magi_start"

# Buildings (21 clients total)
set A 20 
#set clanstr ""
for {set i 0 } {$i <= $A } { incr i } {  
        set b($i) [$ns node]
        tb-set-node-startcmd $b($i) "$magi_start" 
        tb-set-node-os $b($i) Ubuntu1204-64-STD
#        append clanstr "$b($i) "
} 

# Server (1 server total)
set server [$ns node]
tb-set-node-startcmd $server "$magi_start" 
tb-set-node-os $server Ubuntu1204-64-STD

#set A 0
#set slanstr ""
#for {set i 0 } {$i <= $A } { incr i } {  
#        set server($i) [$ns node]
#        tb-set-node-startcmd $server($i) "$magi_start" 
#        append slanstr "$server($i) "
#}

# Setting links from each building client to the server
set A 20
for {set i 0 } {$i <= $A } { incr i } {
        set link($i) [$ns duplex-link $b($i) $server 100Mbps 0ms DropTail]
}

#set router [$ns node] 
#tb-set-node-startcmd $router "$magi_start"

#set lanC [$ns make-lan "router $clanstr" 10Mb 0ms]
#set lanS [$ns make-lan "router $slanstr" 10Mb 0ms]

$ns rtproto Static
$ns run
