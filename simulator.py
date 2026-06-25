from network.devices import Computer, Router, Switch


class NetworkSimulator:
    """
    Simple in-memory simulator:
    - Keeps devices in self.devices
    - Keeps links (with bandwidth/delay/loss) in self.links
    - Provides BFS path finder and simple send() API
    """

    def __init__(self, base_port: int = 50000):
        self.devices: dict[int, object] = {}  # {id: device}
        self.links: list[dict] = []  # [{"a":id1,"b":id2,"bw":..,"delay":..,"loss":..}, ...]
        self._next_id: int = 1
        self._next_port: int = base_port

        # simple DHCP-like pool: 192.168.1.10 .. 192.168.1.254
        self.used_ips: set[str] = set()
        self.next_ip_idx: int = 10

    # ---------- PORT HANDLING ----------

    def _port(self) -> int:
        p = self._next_port
        self._next_port += 1
        return p

    # ---------- IP MANAGEMENT ----------

    def is_valid_ip(self, ip: str) -> bool:
        parts = ip.split(".")
        if len(parts) != 4:
            return False
        try:
            nums = list(map(int, parts))
        except ValueError:
            return False
        return all(0 <= n <= 255 for n in nums)

    def is_ip_free(self, ip: str) -> bool:
        if ip in self.used_ips:
            return False
        return all(d.ip != ip for d in self.devices.values())

    def auto_ip(self) -> str | None:
        while self.next_ip_idx < 255:
            ip = f"192.168.1.{self.next_ip_idx}"
            self.next_ip_idx += 1
            if self.is_ip_free(ip):
                return ip
        return None

    # ---------- DEVICE CREATION ----------

    def _create(self, cls, prefix: str):
        dev_id = self._next_id
        self._next_id += 1

        ip = self.auto_ip() or f"192.168.1.{dev_id}"
        port = self._port()

        dev = cls(dev_id, f"{prefix}{dev_id}", ip, port)

        self.devices[dev_id] = dev
        self.used_ips.add(ip)
        return dev

    def add_computer(self):
        return self._create(Computer, "PC")

    def add_router(self):
        return self._create(Router, "R")

    def add_switch(self):
        return self._create(Switch, "SW")

    # ---------- LINKS WITH METRICS ----------

    def connect(self, a: int, b: int):
        """Connect two devices and create a link with default metrics."""
        a = int(a)
        b = int(b)
        if a == b:
            return

        # check if link already exists
        for l in self.links:
            if {l["a"], l["b"]} == {a, b}:
                return

        # default link metrics
        link = {
            "a": a,
            "b": b,
            "bw": 100,  # Mbps
            "delay": 30,  # ms
            "loss": 0,  # %
        }
        self.links.append(link)

        # update adjacency
        self.devices[a].add_connection(b)
        self.devices[b].add_connection(a)

    def get_link(self, a: int, b: int) -> dict | None:
        """Return the link dict between a and b, or None."""
        for l in self.links:
            if {l["a"], l["b"]} == {a, b}:
                return l
        return None

    # ---------- MESSAGE PASSING ----------

    def send(self, src: int, dst: int, proto: str, msg: str):
        """
        Simulate sending a message from src to dst.
        Handles TCP, UDP, and ICMP.
        """
        # Safety check: ensure devices exist
        if src not in self.devices or dst not in self.devices:
            print(f"Error: Device {src} or {dst} not found.")
            return

        s = self.devices[src]
        d = self.devices[dst]

        p_up = proto.upper()

        if p_up == "UDP":
            # Connectionless, unreliable
            if hasattr(s, "send_udp"):
                s.send_udp(d.ip, d.port, msg)
            else:
                # Fallback log if method missing
                print(f"[UDP] {s.name} -> {d.name}: {msg}")

        elif p_up == "ICMP":
            # Ping / Echo Request
            # Check if device has a specific ICMP method, otherwise use TCP fallback
            if hasattr(s, "send_icmp"):
                s.send_icmp(d.ip, msg)
            elif hasattr(s, "send_tcp"):
                # Use TCP transport for reliability, but log as ICMP in msg
                s.send_tcp(d.ip, d.port, f"[ICMP] {msg}")
            else:
                print(f"[ICMP] {s.name} -> {d.name}: {msg}")

        else:
            # Default to TCP (Connection-oriented)
            if hasattr(s, "send_tcp"):
                s.send_tcp(d.ip, d.port, msg)
            else:
                print(f"[TCP] {s.name} -> {d.name}: {msg}")

    # ---------- BFS PATH FINDER ----------

    def find_path(self, src_id: int, dst_id: int) -> list[int]:
        """
        Simple BFS using devices[*].connections (set of neighbors).
        Returns list of device IDs like [1,3,5] or [] if no path.
        """
        from collections import deque

        if src_id not in self.devices or dst_id not in self.devices:
            return []

        queue = deque([src_id])
        visited: dict[int, int | None] = {src_id: None}

        while queue:
            cur = queue.popleft()
            if cur == dst_id:
                break
            for neigh in self.devices[cur].connections:
                if neigh not in visited:
                    visited[neigh] = cur
                    queue.append(neigh)

        if dst_id not in visited:
            return []

        # reconstruct path
        path = [dst_id]
        while visited[path[-1]] is not None:
            path.append(visited[path[-1]])
        return list(reversed(path))

    # ---------- SHUTDOWN ----------

    def shutdown(self):
        """In a more complex version you'd close sockets / threads here."""
        pass