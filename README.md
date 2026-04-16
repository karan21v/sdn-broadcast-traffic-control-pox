# Broadcast Traffic Control using Mininet and POX

## Project Title

**Broadcast Traffic Control in Software Defined Networks using Mininet and POX Controller**

## Problem Statement

Broadcast traffic is necessary in computer networks for operations such as ARP address resolution. However, excessive broadcast traffic can waste bandwidth because broadcast frames are flooded to all hosts in the same network segment. In large networks, uncontrolled broadcast traffic can reduce performance and may lead to broadcast storm-like behavior.

This project implements an SDN-based broadcast traffic control mechanism using Mininet and the POX OpenFlow controller. The controller detects broadcast packets, allows normal broadcast traffic, and temporarily blocks a host if it sends excessive broadcast packets within a short time window.

## Objective

The main objectives of this project are:

- To create a custom Mininet topology with multiple hosts and one OpenFlow switch.
- To use POX as a remote SDN controller.
- To detect broadcast packets using the Ethernet broadcast MAC address.
- To monitor broadcast packet count per source host.
- To install an OpenFlow drop rule when a host exceeds the broadcast threshold.
- To validate the behavior using ping, arping, POX logs, and OpenFlow flow table inspection.

## Tools and Technologies Used

| Tool / Technology | Purpose |
|---|---|
| Ubuntu on UTM | Virtual machine environment |
| Mininet | Network emulation |
| Open vSwitch | OpenFlow switch |
| POX | SDN controller framework |
| OpenFlow 1.0 | Protocol between controller and switch |
| Python | Controller implementation |
| arping | Generation of ARP broadcast traffic |
| ovs-ofctl | Flow table inspection |
| GitHub | Project submission and documentation |

## Background Theory

### Software Defined Networking

Software Defined Networking separates the control plane from the data plane. The control plane decides how packets should be handled, while the data plane forwards packets according to flow rules.

In this project:

- **POX controller** acts as the control plane.
- **Open vSwitch in Mininet** acts as the data plane.
- **OpenFlow** is used for communication between the switch and controller.

### Broadcast Traffic

Broadcast traffic is traffic sent to all devices in a local network. In Ethernet, the broadcast MAC address is:

```text
ff:ff:ff:ff:ff:ff
```

ARP requests are a common example of broadcast traffic. When a host wants to find the MAC address corresponding to an IP address, it sends an ARP request as a broadcast frame.

### Need for Broadcast Traffic Control

Normal broadcast traffic is required for network operation. However, excessive broadcast traffic is harmful because each broadcast frame is flooded to all ports. This increases unnecessary traffic and consumes network resources.

Therefore, the controller in this project allows normal broadcast packets but blocks a host if it sends too many broadcast packets in a short period.

## Network Topology

The custom Mininet topology contains four hosts connected to one OpenFlow switch.

```text
h1 ----\
h2 -----\
         s1 ----- POX Controller
h3 -----/
h4 ----/
```

| Node | IP Address | MAC Address |
|---|---|---|
| h1 | 10.0.0.1 | 00:00:00:00:00:01 |
| h2 | 10.0.0.2 | 00:00:00:00:00:02 |
| h3 | 10.0.0.3 | 00:00:00:00:00:03 |
| h4 | 10.0.0.4 | 00:00:00:00:00:04 |
| s1 | OpenFlow switch | Open vSwitch |

## Project Files

```text
sdn-broadcast-traffic-control-pox/
├── README.md
├── controllers/
│   └── broadcast_control.py
├── topos/
│   └── broadcast_topo.py
├── logs/
│   ├── flow_table.txt
│   └── test_results.txt
└── screenshots/
    ├── screenshot 1.png
    ├── screenshot 2.png
    ├── screenshot 3.png
    ├── screenshot 4.png
    ├── screenshot 5.png
    ├── screenshot 6.png
    ├── screenshot 7.png
    ├── screenshot 8.png
    ├── screenshot 9.png
    ├── screenshot 10.png
    └── screenshot 11.png
```

## Installation and Setup

### 1. Install Required Packages

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y mininet openvswitch-switch git python3 iperf arping wireshark tshark net-tools
```

### 2. Verify Mininet Installation

```bash
sudo mn --test pingall
```

Expected result:

```text
0% dropped
```

![Mininet installation test](screenshots/screenshot%201.png)

### 3. Clone and Verify POX

```bash
git clone https://github.com/noxrepo/pox.git
cd pox
python3 pox.py --help
```

![POX help output](screenshots/screenshot%202.png)

## Topology Implementation

The topology is defined in:

```text
topos/broadcast_topo.py
```

The topology creates one switch and four hosts. Each host is assigned a fixed IP address and MAC address. All hosts are connected to switch `s1`.

Important topology logic:

```python
s1 = self.addSwitch('s1')
h1 = self.addHost('h1', ip='10.0.0.1/24', mac='00:00:00:00:00:01')
self.addLink(h1, s1)
```

This creates the OpenFlow switch, creates a host, and connects the host to the switch.

## Controller Implementation

The POX controller is defined in:

```text
controllers/broadcast_control.py
```

### Broadcast Detection

The controller identifies broadcast packets using the Ethernet broadcast MAC address:

```python
BROADCAST_MAC = EthAddr("ff:ff:ff:ff:ff:ff")
```

If a packet's destination MAC address matches this value, it is treated as broadcast traffic.

### Broadcast Policy

The controller uses the following policy:

| Parameter | Value |
|---|---|
| Broadcast limit | 5 packets |
| Time window | 10 seconds |
| Block timeout | 20 seconds |
| Drop rule priority | 100 |

### Packet-In Handling

When the switch does not have a matching rule, it sends a packet-in event to the controller. The controller then decides whether to forward, flood, or drop the packet.

Main logic:

1. Learn the source MAC address and input port.
2. Check if the packet is broadcast.
3. Count broadcast packets from the source host.
4. If the count is within the limit, flood the packet.
5. If the count exceeds the limit, install a drop rule.
6. For normal unicast traffic, install forwarding rules.

### Drop Rule Installation

When a host exceeds the broadcast limit, the controller sends an OpenFlow flow modification message:

```python
msg = of.ofp_flow_mod()
msg.priority = 100
msg.match = of.ofp_match(
    in_port=event.port,
    dl_src=packet.src,
    dl_dst=BROADCAST_MAC
)
event.connection.send(msg)
```

Since no output action is added to this rule, matching packets are dropped by the switch.

## Execution Steps

### 1. Start POX Controller

```bash
cd ~/Desktop/sdn-broadcast-traffic-control-pox/pox
python3 pox.py log.level --DEBUG openflow.of_01 --port=6633 broadcast_control
```

The controller starts and listens on port `6633`.

![POX controller started](screenshots/screenshot%203.png)

### 2. Start Mininet Topology

```bash
cd ~/Desktop/sdn-broadcast-traffic-control-pox
sudo mn --custom topos/broadcast_topo.py --topo broadcasttopo --controller remote,ip=127.0.0.1,port=6633 --switch ovsk,protocols=OpenFlow10
```

The topology starts with four hosts and one switch.

Commands used to verify topology:

```bash
nodes
net
```

![Mininet topology](screenshots/screenshot%204.png)

## Testing and Validation

### Test Case 1: Normal Connectivity

Command:

```bash
h1 ping -c 2 h2
```

Result:

The ping between `h1` and `h2` was successful with `0% packet loss`.

![Normal ping test](screenshots/screenshot%205.png)

Interpretation:

This proves that normal unicast communication is working and the controller is not blocking regular host-to-host traffic.

### Test Case 2: Normal Broadcast Traffic

Command:

```bash
h1 arping -c 3 10.0.0.2
```

Result:

The ARP request was sent and replies were received from `h2`.

![Normal ARP broadcast](screenshots/screenshot%206.png)

POX logs showed that broadcast packets were detected and allowed:

```text
BROADCAST detected
BROADCAST allowed and flooded
```

![POX logs for normal broadcast](screenshots/screenshot%207.png)

Interpretation:

This shows that the controller detects normal broadcast traffic and allows it because it is below the configured threshold.

### Test Case 3: Excessive Broadcast Traffic

Command:

```bash
h1 arping -c 10 10.0.0.99
```

Result:

The IP address `10.0.0.99` does not exist in the topology, so no host replies. This causes repeated ARP broadcast requests from `h1`.

![Excessive broadcast generation](screenshots/screenshot%208.png)

POX logs showed that the broadcast count exceeded the allowed limit:

```text
BROADCAST detected: count=6/5
LIMIT EXCEEDED: installed DROP rule
```

![Limit exceeded log](screenshots/screenshot%209.png)

Interpretation:

This proves that the controller detected excessive broadcast traffic and installed a drop rule for the offending host.

### Test Case 4: Flow Table Verification

Command:

```bash
sh sudo ovs-ofctl -O OpenFlow10 dump-flows s1
```

Result:

The flow table showed a high-priority drop rule:

```text
priority=100
dl_src=00:00:00:00:00:01
dl_dst=ff:ff:ff:ff:ff:ff
actions=drop
```

![Flow table drop rule](screenshots/screenshot%2010.png)

Interpretation:

This confirms that the controller installed an explicit OpenFlow match-action rule. The rule matches broadcast traffic from `h1` and drops it.

### Cleanup

Commands:

```bash
exit
sudo mn -c
```

![Mininet cleanup](screenshots/screenshot%2011.png)

## Observations

- Mininet was successfully installed and verified.
- POX controller started successfully and listened on port `6633`.
- The custom topology with four hosts and one switch was created.
- Normal ping traffic between hosts worked successfully.
- Normal ARP broadcast traffic was detected and allowed.
- Excessive ARP broadcast traffic was detected by the POX controller.
- A high-priority OpenFlow drop rule was installed after the broadcast limit was exceeded.
- The flow table confirmed the installed drop rule.

## Results Summary

| Test | Command | Expected Result | Observed Result |
|---|---|---|---|
| Mininet verification | `sudo mn --test pingall` | 0% packet loss | Successful |
| POX verification | `python3 pox.py --help` | POX help displayed | Successful |
| Topology creation | `nodes`, `net` | 4 hosts and 1 switch visible | Successful |
| Normal connectivity | `h1 ping -c 2 h2` | Ping succeeds | Successful |
| Normal broadcast | `h1 arping -c 3 10.0.0.2` | Broadcast allowed | Successful |
| Excessive broadcast | `h1 arping -c 10 10.0.0.99` | Broadcast limit exceeded | Successful |
| Flow table check | `dump-flows s1` | Drop rule visible | Successful |

## Conclusion

This project successfully demonstrates broadcast traffic control using Software Defined Networking. The POX controller detects broadcast packets, allows normal ARP broadcast traffic, and installs a high-priority OpenFlow drop rule when a host sends excessive broadcast packets. The behavior was validated using Mininet, arping, POX logs, and OpenFlow flow table inspection.

The project demonstrates key SDN concepts such as controller-switch interaction, packet-in handling, match-action rule design, flow rule installation, and network behavior observation.

## Viva Preparation

### What is SDN?

SDN stands for Software Defined Networking. It separates the control plane from the data plane. The controller makes forwarding decisions, and the switch follows the rules installed by the controller.

### What is broadcast traffic?

Broadcast traffic is traffic sent to all hosts in a local network. The Ethernet broadcast MAC address is `ff:ff:ff:ff:ff:ff`.

### What is ARP?

ARP stands for Address Resolution Protocol. It is used to find the MAC address corresponding to an IP address. ARP requests are broadcast packets.

### Why is excessive broadcast traffic harmful?

Because broadcast packets are flooded to all hosts. Too many broadcast packets waste bandwidth and processing resources.

### How does this project detect broadcast packets?

The controller checks whether the destination MAC address is `ff:ff:ff:ff:ff:ff`.

### How does the controller limit broadcast traffic?

It counts broadcast packets from each source MAC address. If the count exceeds 5 packets in 10 seconds, it installs a drop rule.

### What is packet-in?

Packet-in is an OpenFlow message sent by the switch to the controller when the switch does not know how to handle a packet.

### What is flow mod?

Flow mod is an OpenFlow message used by the controller to install or modify flow rules in the switch.

### What is match-action?

Match-action means the switch matches packet fields such as MAC address or input port and then performs an action such as forward, flood, or drop.

### How is the packet dropped?

The controller installs a flow rule with a match condition but no forwarding action. In OpenFlow, no output action means the packet is dropped.

## References

- Mininet Overview: https://mininet.org/overview/
- Mininet Walkthrough: https://mininet.org/walkthrough/
- POX Controller Repository: https://github.com/noxrepo/pox
- OpenFlow match-action flow rule concept
