import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk, ImageGrab
import os
import random
import math

# Ensure this matches your project structure
from simulation.simulator import NetworkSimulator

WIRELESS_RANGE = 120  # pixels

# --------------------------------------------------------------------------
# COLOR PALETTES & THEMES
# --------------------------------------------------------------------------
THEMES = {
    "Dark Neon": {
        "bg": "#21222c",  # Window background (Deep Blue-Gray)
        "fg": "#f8f8f2",  # Text color
        "panel": "#282a36",  # Sidebar/Panel background
        "canvas": "#191a21",  # Canvas background
        "grid": "#353849",  # Grid lines
        "select": "#44475a",  # Selection/Active background
        "accent": "#bd93f9",  # General accent (Purple)
        "pc": "#8be9fd",  # Cyan
        "router": "#ff5555",  # Red/Orange
        "switch": "#50fa7b",  # Green
        "log_bg": "#1e1e1e",
        "log_fg": "#00ff00",  # Hacker Green
        "status_up": "#00ff00",
        "status_down": "#ff0000"
    },
    "Light Professional": {
        "bg": "#f0f0f0",
        "fg": "#000000",
        "panel": "#e0e0e0",
        "canvas": "#ffffff",
        "grid": "#d9d9d9",
        "select": "#c0c0c0",
        "accent": "#007acc",  # VS Code Blue
        "pc": "#007acc",  # Blue
        "router": "#d62728",  # Brick Red
        "switch": "#2ca02c",  # Forest Green
        "log_bg": "#ffffff",
        "log_fg": "#000000",
        "status_up": "#00aa00",
        "status_down": "#aa0000"
    }
}


class DeviceView:
    def __init__(self, canvas, device, x, y, icon, theme_colors):
        self.canvas = canvas
        self.device = device
        self.x, self.y = x, y
        self.theme = theme_colors
        self.icon = icon

        # Determine specific color based on device type
        if device.device_type == "Router":
            self.main_color = theme_colors["router"]
        elif device.device_type == "Switch":
            self.main_color = theme_colors["switch"]
        else:
            self.main_color = theme_colors["pc"]

        # 1. Icon (Safe fallback if icon is None)
        if icon:
            self.img = canvas.create_image(x, y, image=icon, tags="device_shape")
        else:
            # Draw a solid circle if image missing
            self.img = canvas.create_oval(
                x - 20, y - 20, x + 20, y + 20,
                fill=self.main_color, tags="device_shape"
            )

        # 2. Text Label
        self.txt = canvas.create_text(
            x, y + 40,
            text=device.name,
            fill=theme_colors["fg"],
            font=("Segoe UI", 9, "bold"),
            tags="device_text"
        )

        # 3. Status Dot (Red/Green indicator)
        s_col = theme_colors["status_up"] if device.status == "Up" else theme_colors["status_down"]
        self.status_dot = canvas.create_oval(
            x + 15, y - 25, x + 25, y - 15,
            fill=s_col,
            outline=theme_colors["fg"],
            width=1,
            tags="device_status"
        )

    def move(self, x, y):
        dx, dy = x - self.x, y - self.y
        self.canvas.move(self.img, dx, dy)
        self.canvas.move(self.txt, dx, dy)
        self.canvas.move(self.status_dot, dx, dy)
        self.x, self.y = x, y

    def update_appearance(self, new_theme):
        """Called when user switches themes (Light/Dark)"""
        self.theme = new_theme

        # Update colors based on new theme palette
        if self.device.device_type == "Router":
            self.main_color = new_theme["router"]
        elif self.device.device_type == "Switch":
            self.main_color = new_theme["switch"]
        else:
            self.main_color = new_theme["pc"]

        # Update Text
        self.canvas.itemconfig(self.txt, fill=new_theme["fg"])

        # Update Status Dot
        s_col = new_theme["status_up"] if self.device.status == "Up" else new_theme["status_down"]
        self.canvas.itemconfig(self.status_dot, fill=s_col, outline=new_theme["fg"])

        # Update fallback shape if no icon
        if not self.icon:
            self.canvas.itemconfig(self.img, fill=self.main_color)

    def update_status_visual(self):
        """Called when device goes Up/Down"""
        s_col = self.theme["status_up"] if self.device.status == "Up" else self.theme["status_down"]
        self.canvas.itemconfig(self.status_dot, fill=s_col)


class App:
    def __init__(self, root):
        self.root = root
        root.title("Network Simulator Pro")
        root.geometry("1200x800")

        self.sim = NetworkSimulator()
        self._load_icons()

        self.device_views = {}  # {id: DeviceView}
        self.link_lines = []  # list of (line_id, (a, b))
        self.wireless_ranges = {}  # {dev_id: circle_id}

        self.connect_mode = False
        self.dragging_device = None
        self.temp_line = None
        self.src_dev = None

        # Context menus context
        self.context_dev = None
        self.context_link = None

        self.undo_stack = []
        self.redo_stack = []

        # Default Theme
        self.current_theme_name = "Dark Neon"
        self.colors = THEMES[self.current_theme_name]

        # Build UI
        self._build_menu()
        self._build_ui()
        self.apply_theme(self.current_theme_name)  # Apply initial styles

        # Bindings
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Double-1>", self.on_double_click)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        # Bind right-click specifically for links
        self.canvas.tag_bind("link", "<Button-3>", self.on_link_right_click)

        # Polling
        self.root.after(500, self.poll_logs)

    # -----------------------------------------------------------
    # THEME ENGINE
    # -----------------------------------------------------------
    def _build_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Export Topology", command=self.export_topology)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # View/Theme Menu
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Theme: Dark Neon", command=lambda: self.apply_theme("Dark Neon"))
        view_menu.add_command(label="Theme: Light Professional", command=lambda: self.apply_theme("Light Professional"))
        menubar.add_cascade(label="View", menu=view_menu)

    def apply_theme(self, theme_name):
        self.current_theme_name = theme_name
        c = THEMES[theme_name]
        self.colors = c

        style = ttk.Style()
        style.theme_use('clam')

        # 1. Global Backgrounds
        self.root.configure(bg=c["bg"])
        self.canvas.configure(bg=c["canvas"])

        # 2. Standard Widgets
        style.configure("TFrame", background=c["bg"])
        style.configure("TLabel", background=c["bg"], foreground=c["fg"])
        style.configure("TLabelframe", background=c["bg"], foreground=c["fg"])
        style.configure("TLabelframe.Label", background=c["bg"], foreground=c["fg"])

        # 3. Buttons (Standard)
        style.configure("TButton",
                        background=c["panel"],
                        foreground=c["fg"],
                        borderwidth=1,
                        focuscolor=c["accent"])
        style.map("TButton", background=[("active", c["select"])])

        # 4. Custom Colored Buttons (Sidebar)
        style.configure("PC.TButton", background=c["panel"], foreground=c["pc"], font=("Segoe UI", 9, "bold"))
        style.map("PC.TButton", background=[("active", c["pc"])], foreground=[("active", c["bg"])])

        style.configure("Router.TButton", background=c["panel"], foreground=c["router"], font=("Segoe UI", 9, "bold"))
        style.map("Router.TButton", background=[("active", c["router"])], foreground=[("active", c["bg"])])

        style.configure("Switch.TButton", background=c["panel"], foreground=c["switch"], font=("Segoe UI", 9, "bold"))
        style.map("Switch.TButton", background=[("active", c["switch"])], foreground=[("active", c["bg"])])

        # 5. Notebook (Tabs)
        style.configure("TNotebook", background=c["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", background=c["panel"], foreground=c["fg"], padding=[10, 2])
        style.map("TNotebook.Tab", background=[("selected", c["accent"])], foreground=[("selected", "#ffffff")])

        # 6. Refresh Canvas Grid & Log
        self._draw_grid()
        if hasattr(self, "log_text"):
            self.log_text.config(bg=c["log_bg"], fg=c["log_fg"], insertbackground=c["fg"])

        # 7. Update Existing Devices
        for dv in self.device_views.values():
            dv.update_appearance(c)

        # 8. Update Links (refresh colors)
        self.update_links_visuals()

    def _draw_grid(self, width=3000, height=2000):
        self.canvas.delete("grid_line")
        color = self.colors["grid"]

        for i in range(0, width, 50):
            self.canvas.create_line(i, 0, i, height, fill=color, tag="grid_line")
        for i in range(0, height, 50):
            self.canvas.create_line(0, i, width, i, fill=color, tag="grid_line")

        self.canvas.tag_lower("grid_line")

    def update_links_visuals(self):
        for line_id, (a, b) in self.link_lines:
            link = self.sim.get_link(a, b) if hasattr(self.sim, "get_link") else None
            ltype = link.get("type", "Ethernet") if link else "Ethernet"
            self._apply_link_base_style(line_id, ltype)

    # -----------------------------------------------------------
    # UI BUILDER
    # -----------------------------------------------------------
    def _build_ui(self):
        root_pw = ttk.Panedwindow(self.root, orient="vertical")
        root_pw.pack(fill="both", expand=True)

        top = ttk.Frame(root_pw)
        bottom = ttk.Frame(root_pw)
        root_pw.add(top, weight=4)
        root_pw.add(bottom, weight=1)

        top_pw = ttk.Panedwindow(top, orient="horizontal")
        top_pw.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(top_pw, highlightthickness=0)
        top_pw.add(self.canvas, weight=4)

        sidebar = ttk.Frame(top_pw, width=300)
        top_pw.add(sidebar, weight=1)

        tabs = ttk.Notebook(sidebar)
        tabs.pack(fill="both", expand=True, padx=5, pady=5)

        tab_dev = ttk.Frame(tabs)
        tab_sim = ttk.Frame(tabs)
        tab_tool = ttk.Frame(tabs)

        tabs.add(tab_dev, text="Devices")
        tabs.add(tab_sim, text="Simulation")
        tabs.add(tab_tool, text="Tools")

        # --- Tab 1: Devices ---
        add_frame = ttk.LabelFrame(tab_dev, text="Add Components")
        add_frame.pack(fill="x", padx=5, pady=5)

        ttk.Button(add_frame, text="Add PC", style="PC.TButton", command=self.add_pc).pack(fill="x", pady=2)
        ttk.Button(add_frame, text="Add Router", style="Router.TButton", command=self.add_router).pack(fill="x", pady=2)
        ttk.Button(add_frame, text="Add Switch", style="Switch.TButton", command=self.add_switch).pack(fill="x", pady=2)

        con_frame = ttk.LabelFrame(tab_dev, text="Cabling")
        con_frame.pack(fill="x", padx=5, pady=5)
        self.btn_connect = ttk.Button(con_frame, text="Enable Connection Mode", command=self.toggle_connect)
        self.btn_connect.pack(fill="x", pady=2)

        # --- Tab 2: Simulation ---
        traffic_frame = ttk.LabelFrame(tab_sim, text="Traffic Generator")
        traffic_frame.pack(fill="x", padx=5, pady=5)

        tk.Label(traffic_frame, text="Source:").pack(anchor="w")
        self.ping_src = ttk.Combobox(traffic_frame, state="readonly")
        self.ping_src.pack(fill="x", pady=2)

        tk.Label(traffic_frame, text="Destination:").pack(anchor="w")
        self.ping_dst = ttk.Combobox(traffic_frame, state="readonly")
        self.ping_dst.pack(fill="x", pady=2)

        tk.Label(traffic_frame, text="Protocol:").pack(anchor="w")
        self.protocol_var = ttk.Combobox(traffic_frame, state="readonly", values=["ICMP", "TCP", "UDP"])
        self.protocol_var.current(0)
        self.protocol_var.pack(fill="x", pady=2)

        ttk.Button(traffic_frame, text="Send Packet", command=self.send_packet).pack(fill="x", pady=5)

        proto_frame = ttk.LabelFrame(tab_sim, text="Special Protocols")
        proto_frame.pack(fill="x", padx=5, pady=5)
        tk.Label(proto_frame, text="Source:").pack(anchor="w")
        self.proto_src = ttk.Combobox(proto_frame, state="readonly")
        self.proto_src.pack(fill="x", pady=2)
        tk.Label(proto_frame, text="Target IP (ARP):").pack(anchor="w")
        self.proto_target_ip = tk.Entry(proto_frame)
        self.proto_target_ip.pack(fill="x", pady=2)

        row = ttk.Frame(proto_frame)
        row.pack(fill="x", pady=2)
        ttk.Button(row, text="ARP", command=self.simulate_arp).pack(side="left", expand=True, fill="x", padx=1)
        ttk.Button(row, text="Broadcast", command=self.simulate_broadcast).pack(side="left", expand=True, fill="x",
                                                                                padx=1)

        # --- Tab 3: Tools ---
        layout_frame = ttk.LabelFrame(tab_tool, text="Auto Layout")
        layout_frame.pack(fill="x", padx=5, pady=5)
        ttk.Button(layout_frame, text="Circular", command=self.layout_circular).pack(fill="x", pady=1)
        ttk.Button(layout_frame, text="Grid", command=self.layout_grid).pack(fill="x", pady=1)
        ttk.Button(layout_frame, text="Force-Directed", command=self.layout_force).pack(fill="x", pady=1)

        act_frame = ttk.LabelFrame(tab_tool, text="Actions")
        act_frame.pack(fill="x", padx=5, pady=5)
        hrow = ttk.Frame(act_frame)
        hrow.pack(fill="x")
        ttk.Button(hrow, text="Undo", command=self.undo).pack(side="left", expand=True, fill="x")
        ttk.Button(hrow, text="Redo", command=self.redo).pack(side="left", expand=True, fill="x")
        ttk.Button(act_frame, text="Validate Topology", command=self.validate_topology).pack(fill="x", pady=2)

        # Bottom Log
        log_frame = ttk.LabelFrame(bottom, text="Event Log")
        log_frame.pack(fill="both", expand=True, padx=5, pady=5)
        log_scroll = ttk.Scrollbar(log_frame)
        self.log_text = tk.Text(log_frame, height=6, state="disabled", wrap="none", font=("Consolas", 9))
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scroll.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=log_scroll.set)
        log_scroll.config(command=self.log_text.yview)

        # Device Context Menu
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="Rename", command=self.rename_device)
        self.menu.add_command(label="Properties", command=self.open_properties_window)
        self.menu.add_command(label="Set IP", command=self.open_ip_window)
        self.menu.add_separator()
        self.menu.add_command(label="Add Interface", command=self.add_interface)
        self.menu.add_command(label="Routing Table", command=self.open_routing_table_window)
        self.menu.add_command(label="Add Static Route", command=self.open_add_route_window)
        self.menu.add_command(label="View MAC Table", command=self.open_mac_table_window)
        self.menu.add_separator()
        self.menu.add_command(label="Disable / Enable", command=self.toggle_status)
        self.menu.add_command(label="Delete Device", command=self.delete_device)

        # Link Context Menu
        self.link_menu = tk.Menu(self.root, tearoff=0)
        self.link_menu.add_command(label="Properties", command=self.open_link_config_context)
        self.link_menu.add_command(label="Delete Connection", command=self.delete_link_context)

    # -----------------------------------------------------------
    # LOGGING
    def log_event(self, msg: str):
        print(msg)
        if hasattr(self, "log_text"):
            self.log_text.config(state="normal")
            self.log_text.insert("end", msg + "\n")
            self.log_text.see("end")
            self.log_text.config(state="disabled")

    def poll_logs(self):
        for dev in self.sim.devices.values():
            for msg in dev.get_new_messages():
                self.log_event(msg)
        self.root.after(500, self.poll_logs)

    # -----------------------------------------------------------
    # ICONS
    def _load_icons(self):
        p = os.path.join(os.getcwd(), "resources")
        # Ensure icons exist, or provide fallback
        try:
            self.icons = {
                "Computer": ImageTk.PhotoImage(Image.open(os.path.join(p, "pc.png")).resize((50, 50))),
                "Router": ImageTk.PhotoImage(Image.open(os.path.join(p, "router.png")).resize((50, 50))),
                "Switch": ImageTk.PhotoImage(Image.open(os.path.join(p, "switch.png")).resize((50, 50))),
            }
        except Exception as e:
            print(f"Warning: Icons not found or error loading them ({e}). Using shapes.")
            self.icons = {}

    # -----------------------------------------------------------
    # ADD DEVICES
    def toggle_connect(self):
        self.connect_mode = not self.connect_mode
        txt = "Disable Connection Mode" if self.connect_mode else "Enable Connection Mode"
        self.btn_connect.config(text=txt)
        if self.connect_mode:
            self.btn_connect.state(['pressed'])
        else:
            self.btn_connect.state(['!pressed'])

    def add_pc(self):
        dev = self.sim.add_computer()
        self.place(dev)
        self.undo_stack.append(("remove_device", {"dev_id": dev.id}))
        self.redo_stack.clear()
        self.log_event(f"[ADD] PC added: {dev.name} ({dev.ip})")

    def add_router(self):
        dev = self.sim.add_router()
        self.place(dev)
        self.undo_stack.append(("remove_device", {"dev_id": dev.id}))
        self.redo_stack.clear()
        self.log_event(f"[ADD] Router added: {dev.name} ({dev.ip})")

    def add_switch(self):
        dev = self.sim.add_switch()
        self.place(dev)
        self.undo_stack.append(("remove_device", {"dev_id": dev.id}))
        self.redo_stack.clear()
        self.log_event(f"[ADD] Switch added: {dev.name} ({dev.ip})")

    def place(self, dev):
        x = 150 + (dev.id * 70)
        y = 150
        icon = self.icons.get(dev.device_type)  # Might be None
        dv = DeviceView(self.canvas, dev, x, y, icon, self.colors)
        self.device_views[dev.id] = dv
        self._update_dropdowns()

    def _update_dropdowns(self):
        values = [f"{i}:{d.name}" for i, d in self.sim.devices.items()]
        self.ping_src["values"] = values
        self.ping_dst["values"] = values
        self.proto_src["values"] = values

    # -----------------------------------------------------------
    # INTERACTION
    def _find(self, x, y):
        for dev_id, dv in self.device_views.items():
            bbox = self.canvas.bbox(dv.img)
            if bbox and bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3]:
                return dev_id
        return None

    def on_click(self, e):
        d = self._find(e.x, e.y)
        if not d:
            self.dragging_device = None
            return

        if self.connect_mode:
            self.src_dev = d
            dv = self.device_views[d]
            self.temp_line = self.canvas.create_line(
                dv.x, dv.y, e.x, e.y, width=2, fill=self.colors["pc"], dash=(2, 2)
            )
        else:
            self.dragging_device = d

    def on_drag(self, e):
        if self.dragging_device is not None:
            dv = self.device_views[self.dragging_device]
            dv.move(e.x, e.y)
            self.update_links()
            self.update_wireless_ranges()
        elif self.temp_line is not None and self.src_dev is not None:
            dv = self.device_views[self.src_dev]
            self.canvas.coords(self.temp_line, dv.x, dv.y, e.x, e.y)

    def on_release(self, e):
        if self.temp_line:
            d = self._find(e.x, e.y)
            self.canvas.delete(self.temp_line)
            if d and d != self.src_dev:
                self._connect_link(self.src_dev, d)
                self.undo_stack.append(("disconnect_link", {"a": self.src_dev, "b": d}))
                self.redo_stack.clear()
                self.log_event(f"[LINK] Connected {self.src_dev} <-> {d}")
            self.temp_line = None

        # Snap to grid logic
        if self.dragging_device is not None:
            dv = self.device_views[self.dragging_device]
            nx = round(dv.x / 10) * 10
            ny = round(dv.y / 10) * 10
            dv.move(nx, ny)
            self.update_links()
            self.update_wireless_ranges()

        self.dragging_device = None

    def on_double_click(self, e):
        d = self._find(e.x, e.y)
        if d:
            self.context_dev = d
            self.open_properties_window()

    def on_right_click(self, e):
        d = self._find(e.x, e.y)
        if d:
            self.context_dev = d
            self.menu.post(e.x_root, e.y_root)

    # -----------------------------------------------------------
    # LINKS
    def _apply_link_base_style(self, line_id, link_type: str):
        link_type = (link_type or "Ethernet").capitalize()

        if link_type == "Fiber":
            color = self.colors["router"]
            width = 3
            dash = (4, 2)
        elif link_type == "Wireless":
            color = self.colors["switch"]
            width = 2
            dash = (2, 4)
        else:
            color = self.colors["pc"]
            width = 2
            dash = ()

        self.canvas.itemconfig(line_id, fill=color, width=width)
        if dash:
            self.canvas.itemconfig(line_id, dash=dash)
        else:
            self.canvas.itemconfig(line_id, dash=())

    def draw_link(self, a, b):
        A = self.device_views[a]
        B = self.device_views[b]
        line_id = self.canvas.create_line(A.x, A.y, B.x, B.y, width=2, tags=("link",))

        link = self.sim.get_link(a, b) if hasattr(self.sim, "get_link") else None
        ltype = link.get("type", "Ethernet") if link else "Ethernet"
        self._apply_link_base_style(line_id, ltype)

        self.link_lines.append((line_id, (a, b)))
        return line_id

    def _connect_link(self, a, b):
        exists = False
        for link in self.sim.links:
            if isinstance(link, (tuple, list)):
                x, y = link
            else:
                x, y = link.get("a"), link.get("b")
            if {a, b} == {x, y}:
                exists = True
                break

        if not exists:
            self.sim.connect(a, b)

        if self._get_line(a, b) is None:
            self.draw_link(a, b)
        self._refresh_wireless_ranges()

    def _disconnect_link(self, a, b):
        new_lines = []
        for line_id, (x, y) in self.link_lines:
            if {a, b} == {x, y}:
                self.canvas.delete(line_id)
            else:
                new_lines.append((line_id, (x, y)))
        self.link_lines = new_lines

        new_sim_links = []
        for link in self.sim.links:
            if isinstance(link, (tuple, list)):
                x, y = link
                if {a, b} == {x, y}: continue
                new_sim_links.append(link)
            else:
                x, y = link.get("a"), link.get("b")
                if {a, b} == {x, y}: continue
                new_sim_links.append(link)
        self.sim.links = new_sim_links

        if a in self.sim.devices: self.sim.devices[a].connections.discard(b)
        if b in self.sim.devices: self.sim.devices[b].connections.discard(a)

        self._refresh_wireless_ranges()
        self.log_event(f"[LINK] Disconnected {a} <-> {b}")

    def update_links(self):
        for line_id, (a, b) in self.link_lines:
            A = self.device_views[a]
            B = self.device_views[b]
            self.canvas.coords(line_id, A.x, A.y, B.x, B.y)

    def _get_line(self, a, b):
        for line_id, (x, y) in self.link_lines:
            if {a, b} == {x, y}: return line_id
        return None

    # --- LINK CONTEXT MENU HANDLERS ---
    def on_link_right_click(self, event):
        items = event.widget.find_withtag("current")
        if items:
            line_id = items[0]
            for lid, (a, b) in self.link_lines:
                if lid == line_id:
                    self.context_link = (a, b)
                    self.link_menu.post(event.x_root, event.y_root)
                    return

    def delete_link_context(self):
        if self.context_link:
            a, b = self.context_link
            self._disconnect_link(a, b)
            self.undo_stack.append(("connect_link", {"a": a, "b": b}))
            self.context_link = None

    def open_link_config_context(self):
        if self.context_link:
            a, b = self.context_link
            self.open_link_config(a, b)

    def open_link_config(self, a, b):
        data = self.sim.get_link(a, b) if hasattr(self.sim, "get_link") else None
        if not data: return

        win = tk.Toplevel(self.root)
        win.title(f"Link: {a}-{b}")
        win.geometry("300x250")
        win.configure(bg=self.colors["bg"])

        def lbl(txt):
            tk.Label(win, text=txt, bg=self.colors["bg"], fg=self.colors["fg"]).pack(anchor="w", padx=5)

        lbl("Bandwidth (Mbps):")
        bw = tk.Entry(win);
        bw.insert(0, data.get("bw", 100));
        bw.pack(fill="x", padx=5)

        lbl("Delay (ms):")
        dl = tk.Entry(win);
        dl.insert(0, data.get("delay", 30));
        dl.pack(fill="x", padx=5)

        lbl("Loss Rate (%):")
        ls = tk.Entry(win);
        ls.insert(0, data.get("loss", 0));
        ls.pack(fill="x", padx=5)

        lbl("Type:")
        tvar = tk.StringVar(value=data.get("type", "Ethernet"))
        cb = ttk.Combobox(win, textvariable=tvar, state="readonly", values=["Ethernet", "Fiber", "Wireless"])
        cb.pack(fill="x", padx=5)

        def save():
            try:
                data["bw"] = int(bw.get())
                data["delay"] = int(dl.get())
                data["loss"] = int(ls.get())
                data["type"] = tvar.get()

                lid = self._get_line(a, b)
                if lid: self._apply_link_base_style(lid, data["type"])
                self._refresh_wireless_ranges()
                win.destroy()
            except:
                messagebox.showerror("Error", "Invalid values")

        ttk.Button(win, text="Save", command=save).pack(pady=10)

    # -----------------------------------------------------------
    # WIRELESS
    def _ensure_wireless_range(self, dev_id):
        if dev_id in self.wireless_ranges: return
        dv = self.device_views.get(dev_id)
        if not dv: return
        r = WIRELESS_RANGE
        cid = self.canvas.create_oval(
            dv.x - r, dv.y - r, dv.x + r, dv.y + r,
            outline=self.colors["pc"], dash=(4, 4)
        )
        self.canvas.tag_lower(cid)
        self.canvas.tag_raise(cid, "grid_line")
        self.wireless_ranges[dev_id] = cid

    def update_wireless_ranges(self):
        for dev_id, cid in list(self.wireless_ranges.items()):
            dv = self.device_views.get(dev_id)
            if not dv:
                self.canvas.delete(cid)
                del self.wireless_ranges[dev_id]
                continue
            r = WIRELESS_RANGE
            self.canvas.coords(cid, dv.x - r, dv.y - r, dv.x + r, dv.y + r)

    def _refresh_wireless_ranges(self):
        needed = set()
        for _, (a, b) in self.link_lines:
            link = self.sim.get_link(a, b) if hasattr(self.sim, "get_link") else None
            if link and link.get("type") == "Wireless":
                needed.add(a);
                needed.add(b)

        for did in list(self.wireless_ranges.keys()):
            if did not in needed:
                self.canvas.delete(self.wireless_ranges[did])
                del self.wireless_ranges[did]

        for did in needed: self._ensure_wireless_range(did)
        self.update_wireless_ranges()

    # -----------------------------------------------------------
    # SIMULATION: PACKET SENDING
    def send_packet(self):
        src_str = self.ping_src.get()
        dst_str = self.ping_dst.get()
        protocol = self.protocol_var.get()

        if not src_str or not dst_str: return

        try:
            s_id = int(src_str.split(":")[0])
            d_id = int(dst_str.split(":")[0])
        except:
            return

        if self.sim.devices[s_id].status == "Down" or self.sim.devices[d_id].status == "Down":
            messagebox.showerror("Failed", "Device is Down")
            return

        self.sim.send(s_id, d_id, protocol, f"{protocol} Packet")

        path = self.sim.find_path(s_id, d_id)
        if not path:
            messagebox.showerror("Failed", "No Route")
            return

        self.log_event(f"[{protocol}] {self.sim.devices[s_id].name} -> {self.sim.devices[d_id].name}")
        self.animate_path(path)

    def do_ping(self):
        self.send_packet()

    def animate_path(self, path):
        hops = [(path[i], path[i + 1]) for i in range(len(path) - 1)]
        line_ids = [self._get_line(a, b) for a, b in hops]

        for lid in line_ids:
            if lid: self.canvas.itemconfig(lid, width=4)

        self._animate_packet(path, 0, hops, line_ids)

    def _animate_packet(self, path, idx, hops, line_ids):
        if idx >= len(path) - 1:
            for (a, b), lid in zip(hops, line_ids):
                if lid:
                    link = self.sim.get_link(a, b) if hasattr(self.sim, "get_link") else None
                    self._apply_link_base_style(lid, link.get("type", "Ethernet") if link else "Ethernet")
            messagebox.showinfo("Success", "Packet Delivered!")
            return

        a, b = path[idx], path[idx + 1]

        link = self.sim.get_link(a, b) if hasattr(self.sim, "get_link") else None
        if link and random.randint(1, 100) <= link.get("loss", 0):
            messagebox.showerror("Failed", f"Packet lost on link {a}-{b}")
            return

        A, B = self.device_views[a], self.device_views[b]
        dot = self.canvas.create_oval(A.x, A.y, A.x + 10, A.y + 10, fill="#ffff00", outline="black")

        steps = 20
        dx = (B.x - A.x) / steps
        dy = (B.y - A.y) / steps
        delay = link.get("delay", 30) if link else 30

        def step(k=0):
            if k >= steps:
                self.canvas.delete(dot)
                self._animate_packet(path, idx + 1, hops, line_ids)
                return
            self.canvas.move(dot, dx, dy)
            self.root.after(max(5, delay), lambda: step(k + 1))

        step()

    # -----------------------------------------------------------
    # BROADCAST / ARP VISUALS
    def simulate_broadcast(self):
        try:
            src = int(self.proto_src.get().split(":")[0])
        except:
            return

        q = [src];
        visited = {src}
        edges = []
        while q:
            u = q.pop(0)
            for v in self.sim.devices[u].connections:
                edges.append((u, v))
                if v not in visited:
                    visited.add(v)
                    q.append(v)

        for u, v in edges:
            lid = self._get_line(u, v)
            if lid: self.canvas.itemconfig(lid, fill="#ffff00", width=3)

        def restore():
            for u, v in edges:
                lid = self._get_line(u, v)
                if lid:
                    link = self.sim.get_link(u, v) if hasattr(self.sim, "get_link") else None
                    self._apply_link_base_style(lid, link.get("type", "Ethernet") if link else "Ethernet")

        self.root.after(1500, restore)

    def simulate_arp(self):
        self.simulate_broadcast()
        target = self.proto_target_ip.get()
        found = False
        dest_id = None
        for did, d in self.sim.devices.items():
            if d.ip == target:
                found = True;
                dest_id = did
                break

        if found:
            self.root.after(1600, lambda: messagebox.showinfo("ARP", f"Target {target} is at Device {dest_id}"))
        else:
            self.root.after(1600, lambda: messagebox.showwarning("ARP", f"Who has {target}? Tell Source."))

    # -----------------------------------------------------------
    # LAYOUTS
    def layout_circular(self):
        ids = list(self.device_views.keys());
        n = len(ids)
        if not n: return
        cx, cy = 600, 400;
        r = 250
        for i, did in enumerate(ids):
            angle = 2 * math.pi * i / n
            nx = cx + int(r * math.cos(angle))
            ny = cy + int(r * math.sin(angle))
            self.device_views[did].move(nx, ny)
        self.update_links();
        self.update_wireless_ranges()

    def layout_grid(self):
        ids = list(self.device_views.keys());
        n = len(ids)
        if not n: return
        cols = math.ceil(math.sqrt(n))
        for i, did in enumerate(ids):
            r, c = divmod(i, cols)
            nx = 100 + c * 150;
            ny = 100 + r * 150
            self.device_views[did].move(nx, ny)
        self.update_links();
        self.update_wireless_ranges()

    def layout_force(self):
        ids = list(self.device_views.keys())
        for _ in range(40):
            disp = {i: [0, 0] for i in ids}
            for i in ids:
                for j in ids:
                    if i == j: continue
                    dx = self.device_views[i].x - self.device_views[j].x
                    dy = self.device_views[i].y - self.device_views[j].y
                    dist = math.hypot(dx, dy) or 1
                    f = 5000 / (dist ** 2)
                    disp[i][0] += (dx / dist) * f;
                    disp[i][1] += (dy / dist) * f
            for lid, (a, b) in self.link_lines:
                dx = self.device_views[a].x - self.device_views[b].x
                dy = self.device_views[a].y - self.device_views[b].y
                dist = math.hypot(dx, dy) or 1
                f = (dist ** 2) / 10000
                disp[a][0] -= (dx / dist) * f;
                disp[a][1] -= (dy / dist) * f
                disp[b][0] += (dx / dist) * f;
                disp[b][1] += (dy / dist) * f
            for i in ids:
                nx = self.device_views[i].x + disp[i][0]
                ny = self.device_views[i].y + disp[i][1]
                nx = max(50, min(1150, nx));
                ny = max(50, min(750, ny))
                self.device_views[i].move(nx, ny)
        self.update_links();
        self.update_wireless_ranges()

    # -----------------------------------------------------------
    # EXPORT & UNDO/REDO (FIXED)
    def export_topology(self):
        fp = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if fp:
            x = self.canvas.winfo_rootx()
            y = self.canvas.winfo_rooty()
            w = x + self.canvas.winfo_width()
            h = y + self.canvas.winfo_height()
            try:
                ImageGrab.grab(bbox=(x, y, w, h)).save(fp)
                messagebox.showinfo("Saved", f"Saved to {fp}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def undo(self):
        if not self.undo_stack: return
        action, data = self.undo_stack.pop()

        if action == "remove_device":
            snap = self._delete_device_internal(data["dev_id"])
            if snap: self.redo_stack.append(("restore_device", snap))

        elif action == "restore_device":
            snap = self._delete_device_internal(data["dev_id"])
            if snap: self.redo_stack.append(("restore_device", snap))

        elif action == "disconnect_link":
            self._disconnect_link(data["a"], data["b"])
            self.redo_stack.append(("connect_link", data))

        elif action == "connect_link":
            self._connect_link(data["a"], data["b"])
            self.redo_stack.append(("disconnect_link", data))

    def redo(self):
        if not self.redo_stack: return
        action, data = self.redo_stack.pop()

        if action == "remove_device":
            snap = self._delete_device_internal(data["dev_id"])
            if snap: self.undo_stack.append(("restore_device", snap))

        elif action == "restore_device":
            self._restore_deleted_device(data)
            self.undo_stack.append(("remove_device", {"dev_id": data["dev_id"]}))

        elif action == "disconnect_link":
            self._disconnect_link(data["a"], data["b"])
            self.undo_stack.append(("connect_link", data))

        elif action == "connect_link":
            self._connect_link(data["a"], data["b"])
            self.undo_stack.append(("disconnect_link", data))

    # -----------------------------------------------------------
    # DEVICE MANAGEMENT (Delete, Restore, Rename, Properties)
    def _delete_device_internal(self, dev_id):
        if dev_id not in self.device_views: return None

        dev = self.sim.devices[dev_id]
        dv = self.device_views[dev_id]

        # Save Neighbors
        neighbors = []
        for lid, (a, b) in self.link_lines:
            if a == dev_id:
                neighbors.append(b)
            elif b == dev_id:
                neighbors.append(a)

        snap = {
            "dev_id": dev_id,
            "device": dev,
            "x": dv.x,
            "y": dv.y,
            "neighbors": neighbors
        }

        # Remove Links
        to_remove = [lid for lid, (a, b) in self.link_lines if a == dev_id or b == dev_id]
        for lid in to_remove:
            a, b = self._find_link_by_id(lid)
            self._disconnect_link(a, b)

        # Remove Visuals
        self.canvas.delete(dv.img)
        self.canvas.delete(dv.txt)
        self.canvas.delete(dv.status_dot)
        if dev_id in self.wireless_ranges:
            self.canvas.delete(self.wireless_ranges[dev_id])

        # Remove Logic
        del self.device_views[dev_id]
        if dev_id in self.sim.devices:
            del self.sim.devices[dev_id]

        self._update_dropdowns()
        self.log_event(f"[DELETE] Device {dev_id} removed")
        return snap

    def _restore_deleted_device(self, snap):
        dev_id = snap["dev_id"]
        dev = snap["device"]

        self.sim.devices[dev_id] = dev
        self.sim.used_ips.add(dev.ip)

        icon = self.icons.get(dev.device_type)
        dv = DeviceView(self.canvas, dev, snap["x"], snap["y"], icon, self.colors)
        self.device_views[dev_id] = dv

        for neighbor in snap["neighbors"]:
            if neighbor in self.sim.devices:
                self._connect_link(dev_id, neighbor)

        self._update_dropdowns()
        self.log_event(f"[RESTORE] Device {dev.name} restored")

    def delete_device(self):
        if self.context_dev is not None:
            self._delete_device_internal(self.context_dev)

    def rename_device(self):
        if self.context_dev not in self.sim.devices: return
        d = self.sim.devices[self.context_dev]
        win = tk.Toplevel(self.root);
        win.title("Rename")
        win.configure(bg=self.colors["bg"])
        e = tk.Entry(win);
        e.insert(0, d.name);
        e.pack(padx=10, pady=10)

        def save():
            d.name = e.get()
            if d.id in self.device_views:
                self.canvas.itemconfig(self.device_views[d.id].txt, text=d.name)
            self._update_dropdowns()
            win.destroy()

        ttk.Button(win, text="OK", command=save).pack(pady=5)

    def toggle_status(self):
        if self.context_dev not in self.sim.devices: return
        d = self.sim.devices[self.context_dev]
        d.status = "Down" if d.status == "Up" else "Up"
        self.device_views[d.id].update_status_visual()

    def open_properties_window(self):
        if self.context_dev not in self.sim.devices: return
        d = self.sim.devices[self.context_dev]
        win = tk.Toplevel(self.root);
        win.title(f"Props: {d.name}")
        win.configure(bg=self.colors["bg"])

        def lbl(txt): tk.Label(win, text=txt, bg=self.colors["bg"], fg=self.colors["fg"]).pack(pady=2)

        lbl(f"Name: {d.name}")
        lbl(f"IP: {d.ip}")
        lbl(f"MAC: {d.mac}")
        lbl(f"Type: {d.device_type}")
        lbl(f"Status: {d.status}")

    # --- Restored Functionality Windows ---

    def open_ip_window(self):
        if self.context_dev not in self.sim.devices: return
        dev = self.sim.devices[self.context_dev]
        win = tk.Toplevel(self.root);
        win.title(f"IP - {dev.name}")
        win.configure(bg=self.colors["bg"])

        tk.Label(win, text=f"Current: {dev.ip}", bg=self.colors["bg"], fg=self.colors["fg"]).pack()
        e = tk.Entry(win);
        e.pack(pady=5)

        def save():
            new_ip = e.get()
            if self.sim.is_valid_ip(new_ip):
                dev.ip = new_ip
                self._update_dropdowns()
                win.destroy()
            else:
                messagebox.showerror("Error", "Invalid IP")

        ttk.Button(win, text="Save", command=save).pack(pady=5)

    def add_interface(self):
        if self.context_dev not in self.sim.devices: return
        dev = self.sim.devices[self.context_dev]
        win = tk.Toplevel(self.root);
        win.title("Add Interface")
        win.configure(bg=self.colors["bg"])
        tk.Label(win, text="Name:", bg=self.colors["bg"], fg=self.colors["fg"]).pack()
        e = tk.Entry(win);
        e.insert(0, f"eth{len(dev.interfaces)}");
        e.pack()

        def save():
            dev.interfaces.append(e.get())
            win.destroy()

        ttk.Button(win, text="Add", command=save).pack()

    def open_routing_table_window(self):
        if self.context_dev not in self.sim.devices: return
        dev = self.sim.devices[self.context_dev]
        if dev.device_type != "Router":
            messagebox.showerror("Error", "Only Router has routing table")
            return
        win = tk.Toplevel(self.root);
        win.title(f"Route Table: {dev.name}")
        win.geometry("400x300")

        cols = ("Net", "Mask", "Next", "Iface")
        tree = ttk.Treeview(win, columns=cols, show="headings")
        tree.pack(fill="both", expand=True)
        for c in cols: tree.heading(c, text=c)
        for r in dev.routing_table:
            tree.insert("", "end", values=(r["net"], r["mask"], r["next"], r["iface"]))

    def open_add_route_window(self):
        if self.context_dev not in self.sim.devices: return
        dev = self.sim.devices[self.context_dev]
        if dev.device_type != "Router": return
        win = tk.Toplevel(self.root);
        win.title("Add Route")
        win.configure(bg=self.colors["bg"])

        def entry(lbl):
            tk.Label(win, text=lbl, bg=self.colors["bg"], fg=self.colors["fg"]).pack()
            e = tk.Entry(win);
            e.pack();
            return e

        n = entry("Network")
        m = entry("Mask")
        nx = entry("Next Hop")
        i = entry("Interface")

        def save():
            dev.add_route(n.get(), m.get(), nx.get(), i.get())
            win.destroy()

        ttk.Button(win, text="Add", command=save).pack(pady=5)

    def open_mac_table_window(self):
        if self.context_dev not in self.sim.devices: return
        dev = self.sim.devices[self.context_dev]
        if dev.device_type != "Switch": return
        win = tk.Toplevel(self.root);
        win.title(f"MAC Table: {dev.name}")
        cols = ("MAC", "Port/Neighbor")
        tree = ttk.Treeview(win, columns=cols, show="headings")
        tree.pack(fill="both", expand=True)
        for c in cols: tree.heading(c, text=c)
        if hasattr(dev, "mac_table"):
            for mac, port in dev.mac_table.items():
                tree.insert("", "end", values=(mac, port))

    def validate_topology(self):
        issues = []
        if not self.sim.devices: issues.append("No devices")
        # Check loops
        visited = set();
        has_cycle = False

        def dfs(u, p):
            visited.add(u)
            for v in self.sim.devices[u].connections:
                if v == p: continue
                if v in visited: return True
                if dfs(v, u): return True
            return False

        for d in self.sim.devices:
            if d not in visited:
                if dfs(d, None): has_cycle = True

        if has_cycle: issues.append("Cycle detected")
        if issues:
            messagebox.showwarning("Validation", "\n".join(issues))
        else:
            messagebox.showinfo("Validation", "Topology OK")


def run_app():
    root = tk.Tk()
    App(root)
    root.mainloop()