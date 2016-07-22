set ns [new Simulator] 
source tb_compat.tcl 

set magi_start "sudo python /share/magi/current/magi_bootstrap.py" 

# Buildings (21 clients total)
set A 20 
set clanstr ""

for {set i 0 } {$i <= $A } { incr i } {  
        set b($i) [$ns node]
        tb-set-node-startcmd $clientnode($i) "$magi_start" 
        append clanstr "$b($i) "
} 

# Server (1 server total)
set A 0
set slanstr ""

for {set i 0 } {$i <= $A } { incr i } {  
        set server($i) [$ns node]
        tb-set-node-startcmd $servernode($i) "$magi_start" 
        append slanstr "$server($i) "
}

set router [$ns node] 
tb-set-node-startcmd $router "$magi_start"

set lanC [$ns make-lan "router $clanstr" 10Mb 0ms]
set lanS [$ns make-lan "router $slanstr" 10Mb 0ms]

$ns rtproto Static
$ns run
