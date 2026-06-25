import random


class NetworkDevice:
    """
    Base class for all devices in the simulator.


    """

    def __init__(self, dev_id: int, name: str, device_type: str, ip: str, port: int):
        self.id = dev_id
        self.name = name
        self.device_type = device_type  # "Computer", "Router", "Switch"
        self.ip = ip
        self.port = port

        # random MAC address
        self.mac = self._generate_mac()

        # Up/Down status
        self.status = "Up"

        # Connected neighbors (device IDs)
        self.connections: set[int] = set()

        # Simple interface list
        self.interfaces: list[str] = ["eth0"]

        # Optional text description
        self.notes: str = ""

        # For logging events to show in terminal
        self._log_buffer: list[str] = []

        # Routers will use this, but keeping it for all
        self.routing_table: list[dict] = []

    # ------------- helpers -------------

    def _generate_mac(self) -> str:
        """Generate a random MAC address like AA:BB:CC:DD:EE:FF"""
        return ":".join(f"{random.randint(0, 255):02X}" for _ in range(6))

    def add_connection(self, other_id: int):
        self.connections.add(other_id)

    def add_interface(self, name: str):
        if name not in self.interfaces:
            self.interfaces.append(name)

    def add_route(self, net: str, mask: str, next_hop: str, iface: str):
        """Used by routers for static routes."""
        self.routing_table.append({
            "net": net,
            "mask": mask,
            "next": next_hop,
            "iface": iface,
        })

    # ------------- logging -------------

    def log(self, msg: str):
        """Append a log message for poll_logs() in the GUI."""
        self._log_buffer.append(msg)

    def get_new_messages(self) -> list[str]:
        """Return and clear buffered messages."""
        msgs = self._log_buffer[:]
        self._log_buffer.clear()
        return msgs

    # ------------- "network" sends (simulated) -------------

    def send_tcp(self, dst_ip: str, dst_port: int, msg: str):
        """
        Simulate a TCP send.
        In a real app you would use sockets; here we just log.
        """
        self.log(f"[TCP] {self.name} ({self.ip}:{self.port}) -> {dst_ip}:{dst_port} : {msg}")

    def send_udp(self, dst_ip: str, dst_port: int, msg: str):
        """Simulate a UDP send."""
        self.log(f"[UDP] {self.name} ({self.ip}:{self.port}) -> {dst_ip}:{dst_port} : {msg}")


class Computer(NetworkDevice):
    def __init__(self, dev_id: int, name: str, ip: str, port: int):
        super().__init__(dev_id, name, "Computer", ip, port)


class Router(NetworkDevice):
    def __init__(self, dev_id: int, name: str, ip: str, port: int):
        super().__init__(dev_id, name, "Router", ip, port)
        # routers use routing_table more heavily; already defined in base


class Switch(NetworkDevice):
    def __init__(self, dev_id: int, name: str, ip: str, port: int):
        super().__init__(dev_id, name, "Switch", ip, port)