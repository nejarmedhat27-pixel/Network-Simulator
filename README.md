# Network-Simulator
Network Topology Simulator built with Python &amp; Tkinter. Add PCs, Switches &amp; Routers · Drag nodes · Connect devices · BFS-powered Ping simulation with path highlighting · Rename nodes · Delete nodes/links · Save &amp; Load topologies (JSON) · Clean, responsive GUI — no dependencies beyond Python stdlib.
# 🖧 NetSim — Network Topology Simulator

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square&logo=python)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-orange?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Zero Dependencies](https://img.shields.io/badge/Dependencies-None-brightgreen?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=flat-square)

> **A fast, lightweight network topology editor and simulator — built entirely with Python's standard library. No pip installs. No setup. Just run and simulate.**

---

## 📸 Overview

**NetSim** is a desktop-based network topology simulator that lets you visually design, connect, and test network layouts in real time. Whether you're a student learning networking fundamentals or a developer prototyping infrastructure — NetSim gives you an interactive canvas to build, drag, connect, and ping devices instantly.

---

## ⚡ Features

| Feature | Details |
|---|---|
| 🖥️ **Node Types** | Add **PC**, **Switch**, and **Router** nodes to the canvas |
| 🖱️ **Drag & Drop** | Freely reposition any device — links follow in real time |
| 🔗 **Connect Mode** | Click two nodes to draw a live link between them |
| 📡 **Ping Simulation** | BFS-powered connectivity check with full path display |
| ✏️ **Rename Nodes** | Double-click any node to rename it inline |
| 🗑️ **Delete** | Remove individual nodes or links cleanly |
| 💾 **Save / Load** | Persist and restore full topologies via JSON |

---

## 🚀 Getting Started

### Prerequisites
- Python **3.8 or higher**
- No external libraries required — Tkinter is included with Python

### Installation & Run

```bash
git clone https://github.com/nejarmedhat/Network Simulator.git
cd netsim
python main.py
```

> **Windows users:** if `python` doesn't work, try `python3 main.py`

---

## 🗺️ How to Use

### 1 — Add Devices
Click the **PC**, **Switch**, or **Router** buttons in the toolbar to place a new device on the canvas.

### 2 — Move Devices
**Click and drag** any node to reposition it. All connected links update automatically.

### 3 — Connect Devices
Enable **Connect Mode** from the toolbar → click the **first node** → click the **second node**. A link is drawn between them.

### 4 — Ping (Test Connectivity)
Select a **source** and **destination** node → click **Ping**. The simulator runs a BFS traversal and displays the full path, or reports no route found.

### 5 — Rename a Node
**Double-click** any node on the canvas to edit its name inline.

### 6 — Delete
Select a node or link and press **Delete**, or use the toolbar button.

### 7 — Save & Load
- **File → Save** — exports your full topology to a `.json` file
- **File → Load** — restores any previously saved topology

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.8+ |
| **GUI Framework** | Tkinter (Python stdlib) |
| **Pathfinding Algorithm** | BFS — Breadth-First Search |
| **Data Storage** | JSON |
| **Dependencies** | None |

---

## 📁 Project Structure

```
netsim/
│
├── main.py              # Entry point — launches the GUI
├── canvas.py            # Drawing engine — nodes, links, drag logic
├── node.py              # Node model — PC, Switch, Router
├── link.py              # Link model — connections between nodes
├── simulator.py         # BFS ping simulation logic
├── topology.py          # Save / Load JSON serialization
└── README.md
```

---

## 📌 Roadmap

The following features are planned for upcoming releases:

- [ ] **IP Address Assignment** — manual input + DHCP auto-assign simulation
- [ ] **Duplicate IP Detection** — validate and warn on conflicts
- [ ] **Static Routing Tables** — per-router route configuration
- [ ] **Dijkstra Shortest Path** — visual shortest-route highlight
- [ ] **Animated Packet Flow** — dot moving along the link during Ping
- [ ] **Right-Click Context Menu** — Rename · Delete · Configure · Set IP
- [ ] **Auto-Layout Algorithms** — Circular · Grid · Force-directed
- [ ] **Export as PNG / JPG** — snapshot canvas to image file
- [ ] **Undo / Redo System** — stack-based action history
- [ ] **Link Types** — Ethernet · Fiber · Wireless (with visual styles)
- [ ] **Bandwidth & Delay Simulation** — per-link Mbps / ms / loss rate
- [ ] **Device Icons** — replace circles with PC · Switch · Router images
- [ ] **Topology Validation** — check loops, isolated nodes, duplicate IPs
- [ ] **Event Log Panel** — live sidebar showing all topology actions
- [ ] **ARP / MAC Learning Simulation** — protocol-level simulation

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

1. Fork the repository
2. Create a new branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add: your feature"`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** — free to use, modify, and distribute.

---

## 👨‍💻 Author

Built with ❤️ using Python & Tkinter.  
If this project helped you, consider giving it a ⭐ on GitHub!
