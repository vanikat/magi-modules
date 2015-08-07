set ns [new Simulator]
source tb_compat.tcl

set magi_start "sudo python /share/magi/current/magi_bootstrap.py"

set servernode [$ns node]
tb-set-node-startcmd $servernode "$magi_start"
tb-set-node-os $servernode Ubuntu1404-64-STD

#Lightweight Consumer/Producers
set numclients %(numClients)s

set clanstr ""
for {set i 1} {$i <= $numclients} {incr i} {
    set clientnode($i) [$ns node]
    append clanstr "$clientnode($i) "
    tb-set-node-startcmd $clientnode($i) "$magi_start"
    tb-set-node-os $clientnode($i) Ubuntu1404-64-STD
}

#Drop route
set lanC [$ns make-lan "$servernode $clanstr" 100Mb 10ms]

$ns rtproto Static
$ns run