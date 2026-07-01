import tkinter as tk
from tkinter import ttk
import requests
from PIL import Image, ImageTk
import threading
import time
import io
import sqlite3
import datetime
import psutil
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import Counter

class RoverGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SOS Dual Rover Control - James & Boris")
        self.root.geometry("1580x980")
        self.root.configure(bg="#111111")

        self.latest_frame_data = {"Rover 1 (James)": None, "Rover 2 (Boris)": None}
        self.video_aspect_ratio = 16 / 9  

        self.rovers = {
            "Rover 1 (James)": {"ctrl": "10.36.226.142", "cam": "10.36.226.77"},
            "Rover 2 (Boris)": {"ctrl": "10.0.0.80", "cam": "10.0.0.72"}
        }

        self.current_mode = tk.StringVar(value="Rover 1 (James)")
        self.status = tk.StringVar(value="Ready - Select Mode")

        self.conn = sqlite3.connect('rover_logs.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS commands 
                              (timestamp TEXT, rover TEXT, command TEXT, ip TEXT)''')
        self.conn.commit()

        self.create_widgets()
        self.on_mode_change()
        self.start_video_thread()
        self.start_monitor_thread()

        self.root.bind("<Configure>", self.on_window_resize)

    def create_widgets(self):
        tk.Label(self.root, text="SOS Dual Rover Control", font=("Arial", 26, "bold"), 
                fg="#00ff00", bg="#111111").pack(pady=8)

        top_bar = tk.Frame(self.root, bg="#1a1a1a")
        top_bar.pack(pady=5, fill="x", padx=15)

        tk.Label(top_bar, text="Control Mode:", fg="#00ff00", bg="#1a1a1a", font=("Arial", 12)).pack(side="left", padx=5)
        ttk.Combobox(top_bar, textvariable=self.current_mode, 
                    values=["Rover 1 (James)", "Rover 2 (Boris)", "Both"], 
                    state="readonly", width=25).pack(side="left", padx=5)
        self.current_mode.trace("w", self.on_mode_change)

        self.tab_control = ttk.Notebook(self.root)
        self.tab_control.pack(pady=10, padx=15, fill="both", expand=True)

        self.main_tab = ttk.Frame(self.tab_control)
        self.map_tab = ttk.Frame(self.tab_control)
        self.data_tab = ttk.Frame(self.tab_control)
        self.monitor_tab = ttk.Frame(self.tab_control)

        self.tab_control.add(self.main_tab, text="Main Control")
        self.tab_control.add(self.map_tab, text="Mapping & Plotting")
        self.tab_control.add(self.data_tab, text="Data & Logs")
        self.tab_control.add(self.monitor_tab, text="System Monitor")

        tk.Label(self.root, textvariable=self.status, fg="#00ff88", bg="#111111", font=("Arial", 11)).pack(side="bottom", fill="x", pady=5)

        self.create_main_tab()
        self.create_mapping_tab()
        self.create_data_tab()
        self.create_monitor_tab()

    def on_mode_change(self, *args):
        self.status.set(f"Switched to {self.current_mode.get()}")
        self.create_main_tab()
        self.create_mapping_tab()

    def send(self, cmd, rover_name=None):
        try:
            if self.current_mode.get() == "Both":
                for data in self.rovers.values():
                    requests.get(f"http://{data['ctrl']}/{cmd}", timeout=0.8)
                self.status.set(f"Both Rovers ΓåÆ {cmd}")
            else:
                rover = rover_name or self.current_mode.get()
                ip = self.rovers[rover]["ctrl"]
                requests.get(f"http://{ip}/{cmd}", timeout=1)
                self.status.set(f"{rover} ΓåÆ {cmd}")
            self.log_command(cmd)
        except:
            self.status.set(f"Error sending {cmd}")

    def log_command(self, cmd):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rover = self.current_mode.get()
        self.cursor.execute("INSERT INTO commands VALUES (?, ?, ?, ?)", 
                           (timestamp, rover, cmd, "Both" if rover == "Both" else self.rovers.get(rover, {})["ctrl"]))
        self.conn.commit()
        self.refresh_logs()

    # ================== TABS ==================
    def create_main_tab(self):
        for widget in self.main_tab.winfo_children(): widget.destroy()
        self.build_tab(self.main_tab, is_mapping=False)

    def create_mapping_tab(self):
        for widget in self.map_tab.winfo_children(): widget.destroy()
        self.build_tab(self.map_tab, is_mapping=True)

    def build_tab(self, parent_tab, is_mapping):
        frame = tk.Frame(parent_tab, bg="#111111")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Controls
        ctrl_frame = tk.Frame(frame, bg="#111111")
        ctrl_frame.pack(side="left", fill="y", padx=10)

        if self.current_mode.get() == "Both":
            self.build_control_panel(ctrl_frame, "Rover 1 (James)")
            self.build_control_panel(ctrl_frame, "Rover 2 (Boris)")
        else:
            self.build_control_panel(ctrl_frame, self.current_mode.get())

        # Videos
        vid_frame = tk.Frame(frame, bg="#1a1a1a")
        vid_frame.pack(side="right", fill="both", expand=True, padx=10)
        self.vid_frame = vid_frame

        mode = self.current_mode.get()
        self.video_labels = {}

        if mode == "Both":
            for name in ["Rover 1 (James)", "Rover 2 (Boris)"]:
                box = tk.Frame(vid_frame, bg="#1a1a1a")
                box.pack(side="left", fill="both", expand=True, padx=5)
                tk.Label(box, text=name, fg="#00ff00", bg="#1a1a1a", font=("Arial", 10, "bold")).pack(anchor="nw")
                label = tk.Label(box, bg="black")
                label.pack(fill="both", expand=True)
                self.video_labels[name] = label
                if is_mapping:
                    label.bind("<Button-1>", lambda e, rn=name: self.on_video_click(e, rn))
        else:
            name = mode
            box = tk.Frame(vid_frame, bg="#1a1a1a")
            box.pack(fill="both", expand=True)
            tk.Label(box, text=name, fg="#00ff00", bg="#1a1a1a", font=("Arial", 10, "bold")).pack(anchor="nw")
            label = tk.Label(box, bg="black")
            label.pack(fill="both", expand=True)
            self.video_labels[name] = label
            if is_mapping:
                label.bind("<Button-1>", lambda e, rn=name: self.on_video_click(e, rn))

        if is_mapping:
            zones = tk.Frame(vid_frame, bg="#1a1a1a")
            zones.pack(fill="x", pady=8)
            for text in ["Γåû Left+Fwd", "Γåæ Forward", "Γåù Right+Fwd", "ΓåÖ Left+Bwd", "Γûá Stop", "Γåÿ Right+Bwd"]:
                tk.Label(zones, text=text, fg="#00ff88", bg="#1a1a1a", font=("Arial", 9)).pack(side="left", expand=True)

    def build_control_panel(self, parent, rover_name):
        ctrl = tk.LabelFrame(parent, text=rover_name, font=("Arial", 13), fg="#00ff00", bg="#1a1a1a", padx=12, pady=6)
        ctrl.pack(fill="y", pady=6)

        btn_style = {"font": ("Arial", 11), "width": 10, "height": 1}

        tk.Button(ctrl, text="Forward", bg="#006600", fg="white", command=lambda: self.send("forward", rover_name), **btn_style).pack(pady=3)
        row = tk.Frame(ctrl, bg="#1a1a1a")
        row.pack(pady=3)
        tk.Button(row, text="Left", bg="#006600", fg="white", command=lambda: self.send("left", rover_name), **btn_style).pack(side="left", padx=4)
        tk.Button(row, text="STOP", bg="red", fg="white", command=lambda: self.send("stop", rover_name), **btn_style).pack(side="left", padx=4)
        tk.Button(row, text="Right", bg="#006600", fg="white", command=lambda: self.send("right", rover_name), **btn_style).pack(side="left", padx=4)
        tk.Button(ctrl, text="Backward", bg="#006600", fg="white", command=lambda: self.send("backward", rover_name), **btn_style).pack(pady=3)

        for s in ["slow", "medium", "fast"]:
            tk.Button(ctrl, text=s.capitalize(), bg="#4444aa", fg="white", command=lambda s=s: self.send(s, rover_name), font=("Arial", 10), width=8).pack(pady=2)

        panf = tk.LabelFrame(ctrl, text="Pan / Tilt", fg="#00ff00", bg="#1a1a1a", padx=8, pady=5)
        panf.pack(pady=6)
        for a in ["panLeft", "panRight", "tiltUp", "tiltDown"]:
            txt = a.replace("pan","Pan ").replace("tilt","Tilt ")
            tk.Button(panf, text=txt, command=lambda a=a: self.send(a, rover_name), font=("Arial", 10), width=8).pack(side="left", padx=4)

    def on_video_click(self, event, rover_name):
        w = event.widget.winfo_width()
        h = event.widget.winfo_height()
        x, y = event.x, event.y

        if y < h / 2:
            if x < w / 3:
                for _ in range(3): self.send("left", rover_name)
                self.send("forward", rover_name)
            elif x > (2 * w) / 3:
                for _ in range(3): self.send("right", rover_name)
                self.send("forward", rover_name)
            else:
                self.send("forward", rover_name)
        else:
            if x < w / 3:
                for _ in range(3): self.send("left", rover_name)
                self.send("backward", rover_name)
            elif x > (2 * w) / 3:
                for _ in range(3): self.send("right", rover_name)
                self.send("backward", rover_name)
            else:
                self.send("stop", rover_name)

    # ================== VIDEO THREAD ==================
    def update_video(self):
        while True:
            try:
                for name in ["Rover 1 (James)", "Rover 2 (Boris)"]:
                    if self.current_mode.get() != "Both" and name != self.current_mode.get():
                        continue
                    r = requests.get(f"http://{self.rovers[name]['cam']}/jpg", timeout=2.5)
                    if r.status_code == 200:
                        self.latest_frame_data[name] = r.content
                        self.root.after(0, self.refresh_video_display, name)
            except:
                pass
            time.sleep(0.18)

    def refresh_video_display(self, rover_name):
        if rover_name not in self.video_labels or self.latest_frame_data[rover_name] is None:
            return
        try:
            img = Image.open(io.BytesIO(self.latest_frame_data[rover_name]))
            label = self.video_labels[rover_name]
            w = label.winfo_width() or 720
            h = label.winfo_height() or 540
            ratio = min(w / img.width, h / img.height)
            new_w = int(img.width * ratio)
            new_h = int(img.height * ratio)
            img = img.resize((new_w, new_h), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            label.config(image=photo)
            label.image = photo
        except:
            pass

    def on_window_resize(self, event):
        for name in list(self.video_labels.keys()):
            self.refresh_video_display(name)

    def start_video_thread(self):
        threading.Thread(target=self.update_video, daemon=True).start()

    # ================== DATA & MONITOR ==================
    def create_data_tab(self):
        frame = tk.Frame(self.data_tab, bg="#1a1a1a")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        left = tk.Frame(frame, bg="#1a1a1a")
        left.pack(side="left", fill="both", expand=False, padx=(0,10))

        tk.Button(left, text="Refresh Logs", bg="#006600", fg="white", command=self.refresh_logs).pack(pady=5)

        self.log_tree = ttk.Treeview(left, columns=("Time", "Rover", "Command", "IP"), show="headings", height=18)
        self.log_tree.heading("Time", text="Timestamp")
        self.log_tree.heading("Rover", text="Rover")
        self.log_tree.heading("Command", text="Command")
        self.log_tree.heading("IP", text="IP")
        self.log_tree.pack(fill="both", expand=True)

        right = tk.Frame(frame, bg="#1a1a1a")
        right.pack(side="right", fill="both", expand=True)

        self.fig1 = plt.Figure(figsize=(6, 4), dpi=100)
        self.ax1 = self.fig1.add_subplot(111)
        self.canvas1 = FigureCanvasTkAgg(self.fig1, right)
        self.canvas1.get_tk_widget().pack(fill="both", expand=True, pady=5)

        self.fig2 = plt.Figure(figsize=(6, 4), dpi=100)
        self.ax2 = self.fig2.add_subplot(111)
        self.canvas2 = FigureCanvasTkAgg(self.fig2, right)
        self.canvas2.get_tk_widget().pack(fill="both", expand=True)

        self.refresh_logs()

    def create_monitor_tab(self):
        frame = tk.Frame(self.monitor_tab, bg="#1a1a1a")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.cpu_label = tk.Label(frame, text="CPU Usage: --%", font=("Arial", 16), fg="#00ff00", bg="#1a1a1a")
        self.cpu_label.pack(pady=15)
        self.mem_label = tk.Label(frame, text="Memory Usage: --%", font=("Arial", 16), fg="#00ff00", bg="#1a1a1a")
        self.mem_label.pack(pady=15)

    def start_monitor_thread(self):
        threading.Thread(target=self.update_monitor, daemon=True).start()

    def update_monitor(self):
        while True:
            cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory().percent
            self.cpu_label.config(text=f"CPU Usage: {cpu:.1f}%")
            self.mem_label.config(text=f"Memory Usage: {mem:.1f}%")
            time.sleep(2)

    def refresh_logs(self):
        for item in self.log_tree.get_children():
            self.log_tree.delete(item)
        self.cursor.execute("SELECT * FROM commands ORDER BY timestamp DESC LIMIT 100")
        for row in self.cursor.fetchall():
            self.log_tree.insert("", "end", values=row)
        self.update_graphs()

    def update_graphs(self):
        self.cursor.execute("SELECT command FROM commands")
        commands = [row[0] for row in self.cursor.fetchall()]
        if not commands: return

        self.ax1.clear()
        counts = Counter(commands)
        self.ax1.bar(counts.keys(), counts.values(), color="#00ff88")
        self.ax1.set_title("Command Frequency", color="white")
        self.ax1.tick_params(colors="white")
        self.fig1.patch.set_facecolor('#1a1a1a')
        self.canvas1.draw()

        self.ax2.clear()
        self.cursor.execute("SELECT timestamp, command FROM commands ORDER BY timestamp")
        data = self.cursor.fetchall()
        if data:
            times = [datetime.datetime.strptime(t[0], "%Y-%m-%d %H:%M:%S") for t in data]
            cmds = [t[1] for t in data]
            self.ax2.scatter(times, cmds, color="#ffff00", s=30)
            self.ax2.set_title("Command Timeline", color="white")
            self.ax2.tick_params(colors="white", rotation=45)
            self.fig2.patch.set_facecolor('#1a1a1a')
            self.canvas2.draw()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = RoverGUI()
    app.run()
