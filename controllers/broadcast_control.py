from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.addresses import EthAddr
import time

log = core.getLogger()

BROADCAST_MAC = EthAddr("ff:ff:ff:ff:ff:ff")

BROADCAST_LIMIT = 5
TIME_WINDOW = 10
BLOCK_TIMEOUT = 20

class BroadcastTrafficControl(object):
    def __init__(self):
        self.mac_to_port = {}
        self.broadcast_history = {}
        core.openflow.addListeners(self)
        log.info("Broadcast Traffic Control Controller started")
        log.info("Policy: max %s broadcast packets per %s seconds",
                 BROADCAST_LIMIT, TIME_WINDOW)

    def _handle_ConnectionUp(self, event):
        log.info("Switch connected: dpid=%s", event.dpid)

    def _is_broadcast(self, packet):
        return packet.dst == BROADCAST_MAC

    def _record_broadcast(self, dpid, src_mac):
        now = time.time()
        key = (dpid, str(src_mac))

        old_times = self.broadcast_history.get(key, [])
        recent_times = []

        for timestamp in old_times:
            if now - timestamp <= TIME_WINDOW:
                recent_times.append(timestamp)

        recent_times.append(now)
        self.broadcast_history[key] = recent_times

        return len(recent_times)

    def _install_broadcast_drop_rule(self, event, packet):
        msg = of.ofp_flow_mod()
        msg.priority = 100
        msg.idle_timeout = BLOCK_TIMEOUT
        msg.hard_timeout = BLOCK_TIMEOUT
        msg.match = of.ofp_match(
            in_port=event.port,
            dl_src=packet.src,
            dl_dst=BROADCAST_MAC
        )
        event.connection.send(msg)

        log.warning("LIMIT EXCEEDED: installed DROP rule for broadcast src=%s port=%s timeout=%ss",
                    packet.src, event.port, BLOCK_TIMEOUT)

    def _flood_packet(self, event):
        msg = of.ofp_packet_out()
        msg.data = event.ofp
        msg.in_port = event.port
        msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
        event.connection.send(msg)

    def _install_unicast_forward_rule(self, event, packet, out_port):
        msg = of.ofp_flow_mod()
        msg.priority = 10
        msg.idle_timeout = 30
        msg.hard_timeout = 0
        msg.match = of.ofp_match.from_packet(packet, event.port)
        msg.actions.append(of.ofp_action_output(port=out_port))
        msg.data = event.ofp
        event.connection.send(msg)

    def _handle_PacketIn(self, event):
        packet = event.parsed

        if not packet.parsed:
            log.warning("Ignoring incomplete packet")
            return

        dpid = event.dpid
        in_port = event.port

        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][packet.src] = in_port

        if self._is_broadcast(packet):
            count = self._record_broadcast(dpid, packet.src)

            log.info("BROADCAST detected: src=%s in_port=%s count=%s/%s",
                     packet.src, in_port, count, BROADCAST_LIMIT)

            if count > BROADCAST_LIMIT:
                self._install_broadcast_drop_rule(event, packet)
                return

            self._flood_packet(event)
            log.info("BROADCAST allowed and flooded: src=%s", packet.src)
            return

        out_port = self.mac_to_port[dpid].get(packet.dst)

        if out_port is not None:
            self._install_unicast_forward_rule(event, packet, out_port)
            log.info("UNICAST forwarded: %s -> %s out_port=%s",
                     packet.src, packet.dst, out_port)
        else:
            self._flood_packet(event)
            log.info("UNKNOWN destination flooded: dst=%s", packet.dst)

def launch():
    BroadcastTrafficControl()
