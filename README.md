# Broadcast Traffic Control using Mininet and POX

## Problem Statement

This project implements broadcast traffic control using Software Defined Networking. The network is emulated using Mininet and controlled using the POX OpenFlow controller.

In Ethernet networks, broadcast packets such as ARP requests are flooded to all hosts. Excessive broadcast traffic wastes bandwidth and processing resources. This project detects broadcast packets, allows normal broadcast behavior, and limits excessive broadcast traffic using OpenFlow rules.

## Tools Used

- Ubuntu on UTM
- Mininet
- Open vSwitch
- POX Controller
- OpenFlow 1.0
- arping
- Wireshark / tshark

## Topology

```text
h1 ----\
h2 -----\
         s1
h3 -----/
h4 ----/
