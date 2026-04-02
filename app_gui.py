# -*- coding: utf-8 -*-
"""
Created on Mon Mar  9 15:39:29 2026

@author: bramc44
"""
from tkinter import ttk
# -*- coding: utf-8 -*-
from kpfm_analysis import KPFMSpectrumAnalysis
import tkinter as tk
from tkinter import filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import threading
from adjustText import adjust_text
plt.rcParams.update({
    "font.size": 8,
    "axes.titlesize": 9,
    "axes.labelsize": 8,
    "legend.fontsize": 7,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7
})
import matplotlib.patheffects as pe
import os
import re
import numpy as np
import matplotlib.cm as cm
from datetime import datetime
np.float = float
np.int = int
import nanonispy as nap
def get_metadata_time(filepath):

    date = None
    time = None

    try:
        with open(filepath, "r", errors="ignore") as f:
            lines = f.readlines()

        for i, line in enumerate(lines):

            line = line.strip()

            if ":REC_DATE:" in line and i+1 < len(lines):
                date = lines[i+1].strip()

            if ":REC_TIME:" in line and i+1 < len(lines):
                time = lines[i+1].strip()

            if date and time:
                return datetime.strptime(
                    date + " " + time,
                    "%d.%m.%Y %H:%M:%S"
                )

            if line.startswith("Saved Date"):
                parts = line.split("\t")
                if len(parts) > 1:
                    return datetime.strptime(
                        parts[1].strip(),
                        "%d.%m.%Y %H:%M:%S"
                    )

    except Exception:
        pass

    return None
def get_scan_range(filepath):
    scan = nap.read.Scan(filepath)
    size_x = float(scan.header['scan_range'][0]) * 1e9
    size_y = float(scan.header['scan_range'][1]) * 1e9
    return size_x, size_y
def load_spectrum_data(filepath):

    with open(filepath, "r") as f:
        lines = f.readlines()

    data_start = None

    for i, line in enumerate(lines):
        if line.strip() == "[DATA]":
            data_start = i + 1
            break

    if data_start is None:
        return None

    # column headers
    headers = lines[data_start].strip().split("\t")

    data = {h: [] for h in headers}

    for line in lines[data_start+1:]:

        if line.strip() == "":
            continue

        parts = line.split()

        for i, h in enumerate(headers):
            data[h].append(float(parts[i]))

    # convert to numpy arrays
    for h in data:
        data[h] = np.array(data[h])

    return data
def get_spec_position(filepath):

    with open(filepath,"r",errors="ignore") as f:

        for line in f:

            if line.startswith("X (m)"):
                x=float(line.split()[2])

            if line.startswith("Y (m)"):
                y=float(line.split()[2])

            if line.strip()=="[DATA]":
                break

    return x*1e9 , y*1e9

def get_spec_number(filename):

    match = re.search(r'(\d+)\.dat$',filename)

    if match:
        return int(match.group(1))
    else:
        return "?"
def format_sxm_name(filename):
    """
    Move the trailing file number to the front.
    Example:
    Cu(111)_coronene_1min_RT_0008.sxm -> 0008_Cu(111)_coronene_1min_RT.sxm
    """
    match = re.search(r'(.*)_(\d+)\.sxm$', filename)

    if match:
        base = match.group(1)
        num = match.group(2)
        return f"{num}_{base}.sxm"

    return filename
def subtract_mean_plane(z):

    ny, nx = z.shape

    X, Y = np.meshgrid(np.arange(nx), np.arange(ny))

    X = X.flatten()
    Y = Y.flatten()
    Z = z.flatten()

    # plane fit: z = ax + by + c
    A = np.c_[X, Y, np.ones(X.size)]

    C, _, _, _ = np.linalg.lstsq(A, Z, rcond=None)

    plane = (C[0]*X + C[1]*Y + C[2]).reshape(ny, nx)

    return z - plane

def format_spec_name(filename):
    """
    Reduce spectrum filename to just the number.
    Example:
    Au(111)_kelvin_dIdV_set_00053.dat -> 53
    """
    match = re.search(r'(\d+)\.dat$', filename)

    if match:
        return str(int(match.group(1)))  # removes leading zeros

    return filename  
class STMSpectraViewer:

    def __init__(self, root):

        self.root = root
        self.root.title("STM Spectra Viewer")
        self.directory = None
        self.valid_specs = []
        self.records = []
        self.scan_to_specs = {}
        self.show_spec_positions = tk.BooleanVar(value=True)
        self.subtract_plane_var = tk.BooleanVar(value=False)
        self.spec_colors = {}
        self.available_channels = []
        self.overlay_artists = []
        self.setup_frames()
        self.setup_left_panel()
        self.setup_stm_plot()
        self.setup_spectra_plot()
        self.setup_right_panel()
        self.root.update_idletasks()  # let Tk calculate requested widget sizes first
        self.label_stride = 5 
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()

        win_w = int(screen_w * 0.9)
        win_h = int(screen_h * 0.9)

        pos_x = (screen_w - win_w) // 2
        pos_y = 10

        root.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")
        root.minsize(500, 400)
        
    # =========================
    # Layout
    # =========================

    def setup_frames(self):

        self.root.columnconfigure(0, weight=0)  # left panel fixed width
        self.root.columnconfigure(1, weight=2)  # STM plot expands
        self.root.columnconfigure(2, weight=1)  # spectra list panel fixed
        self.root.columnconfigure(3, weight=0)  # right panel fixed (if needed)
        self.root.rowconfigure(0, weight=1)   # main content row expands
        self.root.rowconfigure(1, weight=0)   # future rows (buttons etc.) stay fixed
        self.left_frame = tk.Frame(self.root, padx=10)
        self.left_frame.grid(row=0, column=0, sticky="ns")

        self.stm_frame = tk.Frame(self.root)
        self.stm_frame.grid(row=0, column=1, sticky="nsew")

        self.spec_frame = tk.Frame(self.root)
        self.spec_frame.grid(row=0, column=2, sticky="nsew")

        
        self.right_frame = tk.Frame(self.root, width=150, padx=5) 
        self.right_frame.grid(row=0, column=3, sticky="ns")
        self.right_frame.grid_propagate(False)  # prevent auto-expansion
    # =========================
    # LEFT PANEL
    # =========================

    def setup_left_panel(self):

        tk.Button(
            self.left_frame,
            text="Select Data Folder",
            command=self.select_folder
        ).pack(fill="x")

        self.scan_listbox = tk.Listbox(self.left_frame, height=30)
        self.scan_listbox.pack(fill="y")

        self.scan_listbox.bind("<<ListboxSelect>>", self.scan_selected)

    def select_folder(self):

        folder = filedialog.askdirectory()
        if not folder:
            return

        self.directory = folder

        files = [f for f in os.listdir(folder)
                 if f.endswith(".sxm") or f.endswith(".dat")]

        total_files = len(files)

        if total_files == 0:
            return

        progress_window = ProgressWindow(
            self.root,
            total_files,
            "Loading STM Data"
        )

        def progress_callback(message):
            def update_ui():
                progress_window.update_status(message)
                progress_window.step()
            self.root.after(0, update_ui)

        def task():

            try:
                records = []

                for f in files:
                    filepath = os.path.join(folder, f)

                    t = get_metadata_time(filepath)
                    records.append([f, t])

                    progress_callback(f"Reading {f}")

                records = sorted(records, key=lambda x: (x[1] is None, x[1]))

                
                scan_sizes = {}
                for fname, _ in records:
                    if fname.endswith(".sxm"):
                        try:
                            scan_sizes[fname] = get_scan_range(
                                os.path.join(folder, fname)
                            )
                        except Exception:
                            scan_sizes[fname] = None

                scan_to_specs = {}
                for fname, _ in records:
                    if fname.endswith(".sxm"):
                        scan_to_specs[fname] = []

                current_scan = None
                current_parent_scan = None
                parent_size = None

                for fname, _ in records:

                    if fname.endswith(".sxm"):
                        current_scan = fname
                        this_size = scan_sizes.get(fname)

                        if this_size is None:
                            continue

                        if current_parent_scan is None or parent_size is None:
                           current_parent_scan = fname
                           parent_size = this_size
                           continue

                        sx, sy = this_size
                        px, py = parent_size

                        is_small = (sx < px / 2) and (sy < py / 2)

                        if not is_small:
                            current_parent_scan = fname
                            parent_size = this_size

                    elif fname.endswith(".dat"):
                        if current_scan is not None:
                            scan_to_specs[current_scan].append(fname)

                        if (current_parent_scan is not None and
                            current_parent_scan != current_scan):
                            scan_to_specs[current_parent_scan].append(fname)

                def finish():

                    progress_window.close()

                    self.records = records
                    self.scan_to_specs = scan_to_specs

                    self.scan_listbox.delete(0, tk.END)
                    self.scan_filenames = []

                    for fname, _ in records:
                        if fname.endswith(".sxm"):
                            display = format_sxm_name(fname)
                            self.scan_listbox.insert(tk.END, display)
                            self.scan_filenames.append(fname)

                self.root.after(0, finish)

            except Exception as e:
                self.root.after(0, progress_window.close)
                print("Error:", e)

        threading.Thread(target=task).start()

    # =========================
    # STM PLOT
    # =========================

    def setup_stm_plot(self):

        self.stm_fig = Figure(figsize=(5,5))
        self.stm_ax = self.stm_fig.add_subplot(111)

        self.stm_canvas = FigureCanvasTkAgg(self.stm_fig, master=self.stm_frame)
        self.stm_canvas.get_tk_widget().pack(fill="x", expand=True)
        # ---- add checkbox below STM canvas ----
        self.label_offset_var = tk.BooleanVar(value=False)
        tk.Label(self.stm_frame, text="Label every N spectra").pack(anchor="w")

        self.label_stride_var = tk.IntVar(value=1)

        tk.OptionMenu(
            self.stm_frame,
            self.label_stride_var,
            1, 2, 3, 5
        ).pack(anchor="w")

        # update plot when changed
        self.label_stride_var.trace_add(
            "write",
            lambda *args: self.refresh_stm_overlay()
            )
        tk.Checkbutton(
            self.stm_frame,
            text="Label offset",
            variable=self.label_offset_var,
            command=self.refresh_stm_overlay
        ).pack(anchor="w", pady=2)
        tk.Checkbutton(
            self.stm_frame,
            text="Show spectra positions",
            variable=self.show_spec_positions,
            command=self.refresh_stm_overlay
        ).pack(anchor="w", pady=5)
        tk.Checkbutton(
            self.stm_frame,
            text="Subtract mean plane",
            variable=self.subtract_plane_var,
            command=self.reload_current_scan  
        ).pack(anchor="w", pady=2)
    def reload_current_scan(self):

        selection = self.scan_listbox.curselection()

        if not selection:
            return

        index = selection[0]
        scan_name = self.scan_filenames[index]

        self.load_scan(scan_name)
    # =========================
    # SPECTRA PLOT
    # =========================

    def setup_spectra_plot(self):
        

        
        self.spec_fig = Figure(figsize=(3,5))
        self.spec_ax = self.spec_fig.add_subplot(111)

        self.spec_canvas = FigureCanvasTkAgg(self.spec_fig, master=self.spec_frame)
        self.spec_canvas.get_tk_widget().pack(fill="x", expand=True)
        # --- control container ---
        control_container = tk.Frame(self.spec_frame)
        control_container.pack(fill="x")

        # ---------- ROW 1 ----------
        row1 = tk.Frame(control_container)
        row1.pack(fill="x")

        tk.Label(row1, text="X axis").pack(side="left")

        self.x_axis_var = tk.StringVar()
        self.x_menu = tk.OptionMenu(row1, self.x_axis_var, "")
        self.x_menu.pack(side="left", padx=5)

        tk.Label(row1, text="Y axis").pack(side="left")

        self.y_axis_var = tk.StringVar()
        self.y_menu = tk.OptionMenu(row1, self.y_axis_var, "")
        self.y_menu.pack(side="left", padx=5)
        self.x_axis_var.trace_add("write", lambda *args: self.plot_selected_spectra())
        self.y_axis_var.trace_add("write", lambda *args: self.plot_selected_spectra())
        self.invert_y_var = tk.BooleanVar(value=False)

        tk.Checkbutton(
            row1,
            text="Invert Y",
            variable=self.invert_y_var,
            command=self.plot_selected_spectra
        ).pack(side="left", padx=10)

        # ---------- ROW 2 ----------
        row2 = tk.Frame(control_container)
        row2.pack(fill="x", pady=2)

        self.both_dirs_var = tk.BooleanVar(value=False)
        self.sum_dirs_var = tk.BooleanVar(value=False)

        tk.Checkbutton(
            row2,
            text="Both dirs",
            variable=self.both_dirs_var,
            command=self.plot_selected_spectra
        ).pack(side="left", padx=5)

        tk.Checkbutton(
            row2,
            text="Sum dirs",
            variable=self.sum_dirs_var,
            command=self.plot_selected_spectra
        ).pack(side="left", padx=5)

        tk.Button(
            row2,
            text="KPFM Fit",
            command=self.run_kpfm_fit
        ).pack(side="left", padx=10)
        
    # =========================
    # RIGHT PANEL
    # =========================

    def setup_right_panel(self):

        tk.Label(self.right_frame, text="Spectra").pack()

        self.spec_canvas_box = tk.Canvas(self.right_frame, width=150)
        self.spec_canvas_box.pack(side="left", fill="y", expand=False)  # only vertical

        scrollbar = tk.Scrollbar(
            self.right_frame,
            orient="vertical",
            command=self.spec_canvas_box.yview
        )
        scrollbar.pack(side="right", fill="y")
        self.spec_canvas_box.configure(yscrollcommand=scrollbar.set)

        self.spec_check_frame = tk.Frame(self.spec_canvas_box)
        self.spec_canvas_box.create_window((0,0), window=self.spec_check_frame, anchor="nw")

        self.spec_check_frame.bind(
            "<Configure>",
            lambda e: self.spec_canvas_box.configure(
                scrollregion=self.spec_canvas_box.bbox("all")
            )
        )

        self.spec_vars = {}
        
    # =========================
    # SCAN SELECTED
    # =========================

    def scan_selected(self, event):

        selection = self.scan_listbox.curselection()

        if not selection:
            return

        index = selection[0]
        scan_name = self.scan_filenames[index]

        self.load_scan(scan_name)

    # =========================
    # LOAD SCAN
    # =========================

    def load_scan(self, selected_sxm):

        directory = self.directory

        valid_specs = self.scan_to_specs.get(selected_sxm, [])

        self.valid_specs = valid_specs

        scan = nap.read.Scan(os.path.join(directory, selected_sxm))

        # Read scan direction from header (default to 'up' if not present)
        scan_dir = scan.header.get('scan_dir', 'up').lower()

        # Get forward Z signal
        z = scan.signals['Z']['forward'].copy() * 1e9  # convert to nm

        # Flip depending on scan direction
        if scan_dir == 'down':
            z = np.flip(z)
            z = np.flip(z, axis =1) 
            #print('down')
        elif scan_dir == 'up':
            #print('up')
            smeg =1
        else:
            raise ValueError(f"Unknown scan direction: {scan_dir}")

        # Invert Z for visualization
        z = -z
        if self.subtract_plane_var.get():
            z = subtract_mean_plane(z)
        size_x = float(scan.header['scan_range'][0])*1e9
        size_y = float(scan.header['scan_range'][1])*1e9
        offset_x = float(scan.header['scan_offset'][0])*1e9
        offset_y = float(scan.header['scan_offset'][1])*1e9
        self.size_x = size_x
        self.size_y = size_y
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.stm_ax.clear()

        self.stm_ax.imshow(
            z,
            origin='lower',
            extent=[0,size_y,0,size_x],
            cmap='YlOrBr'
        )

        colors = cm.rainbow(np.linspace(0,1,len(valid_specs)))
        data = None
        if valid_specs:

            first_spec = os.path.join(directory, valid_specs[0])
            data = load_spectrum_data(first_spec)

        if data is not None:
            
            self.available_channels = list(data.keys())

            menu = self.x_menu["menu"]
            menu.delete(0, "end")
            for c in self.available_channels:
                menu.add_command(label=c, command=lambda v=c: self.x_axis_var.set(v))

            menu = self.y_menu["menu"]
            menu.delete(0, "end")
            for c in self.available_channels:
                menu.add_command(label=c, command=lambda v=c: self.y_axis_var.set(v))

            # default axes
            self.x_axis_var.set("Bias calc (V)")
            self.y_axis_var.set("LI Demod 1 Y (A)")
            self.spec_colors = {}
        for i, f in enumerate(valid_specs):
            self.spec_colors[f] = colors[i]

        
        
        self.stm_ax.set_xlabel("Y (nm)")
        self.stm_ax.set_ylabel("X (nm)")
        self.stm_ax.set_title(selected_sxm)
        
        self.stm_canvas.draw()
        self.stm_fig.tight_layout()

        # find spectra for scan
        self.update_spectra_list(selected_sxm)
        self.refresh_stm_overlay()
    def refresh_stm_overlay(self):

        # ---- clear old overlay ----
        for artist in self.overlay_artists:
            try:
                artist.remove()
            except Exception:
                pass
        self.overlay_artists.clear()

        if not self.show_spec_positions.get():
            self.stm_canvas.draw()
            return

        texts = []

        for i, file in enumerate(self.valid_specs):

            filepath = os.path.join(self.directory, file)

            x_nm, y_nm = get_spec_position(filepath)

            x_nm = (x_nm - self.offset_x) + self.size_x / 2
            y_nm = (y_nm - self.offset_y) + self.size_y / 2

            num = get_spec_number(file)

            # ---- scatter ----
            if self.label_offset_var.get():
                size = 5   # smaller points when offset is ON
            else:
                size = 20   # original size

            sc = self.stm_ax.scatter(
                x_nm,
                y_nm,
                color=self.spec_colors[file],
                s=size,
                edgecolor="black"
            )
            
            self.overlay_artists.append(sc)
            stride = self.label_stride_var.get()

            if stride > 1 and (i % stride != 0):
                continue
            # ---- label style ----
            if self.label_offset_var.get():
                dx, dy = 2, 2
                alpha = 0.5
            else:
                dx, dy = 0, 0
                alpha = 1.0

            txt = self.stm_ax.text(
                x_nm + dx,
                y_nm + dy,
                str(num),
                color=self.spec_colors[file],
                fontsize=8,
                ha="center",
                va="center",
                alpha=alpha,
                path_effects=[
                    pe.Stroke(linewidth=2, foreground="black"),
                    pe.Normal()
                ]
            )

            self.overlay_artists.append(txt)
            texts.append(txt)

        # ---- auto-adjust ----
        if self.label_offset_var.get():
            angle = i * (2 * np.pi / len(self.valid_specs))
            dx = 3 * np.cos(angle)
            dy = 3 * np.sin(angle)
            alpha = 0.6
        else:
            dx, dy = 0, 0
            alpha = 1.0
        self.stm_canvas.draw()
    # =========================
    # UPDATE SPECTRA LIST
    # =========================
    
    def update_spectra_list(self, selected_sxm):

        for w in self.spec_check_frame.winfo_children():
            w.destroy()

        self.spec_vars.clear()

        dat_files = self.scan_to_specs.get(selected_sxm, [])

        for f in dat_files:

            var = tk.BooleanVar()

            cb = tk.Checkbutton(
                self.spec_check_frame,
                text=format_spec_name(f),
                variable=var,
                command=self.plot_selected_spectra
            )

            cb.pack(anchor="w")

            self.spec_vars[f] = var
    # =========================
    # PLOT SPECTRA
    # =========================

    def plot_selected_spectra(self):
        
        self.spec_ax.clear()
        
        selected = [k for k,v in self.spec_vars.items() if v.get()]
        
        xvar = self.x_axis_var.get()
        yvar = self.y_axis_var.get()
    
        for f in selected:
            
            data = load_spectrum_data(os.path.join(self.directory, f))
            
            if xvar not in data or yvar not in data:
                continue
        
            x = data[xvar]
            y_fwd = data[yvar]
        
            # backward channel name
            ybwd_name = yvar.replace(" (", " [bwd] (") if "[bwd]" not in yvar else yvar
            y_bwd = data.get(ybwd_name)
        
            # invert if requested
            if self.invert_y_var.get():
                y_fwd = -y_fwd
                if y_bwd is not None:
                    y_bwd = -y_bwd
                
            label = format_spec_name(f)
        
            # ---- SUM DIRECTIONS ----
            if self.sum_dirs_var.get() and y_bwd is not None:
                
                y = y_fwd + y_bwd
                
                self.spec_ax.plot(
                    x,
                    y,
                    color=self.spec_colors[f],
                    label=label
                )
        
            # ---- BOTH DIRECTIONS ----
            elif self.both_dirs_var.get() and y_bwd is not None:
                
                if "[bwd]" in yvar:
                    # backward selected -> main backward, overlay forward
                    self.spec_ax.plot(x, y_bwd, color=self.spec_colors[f], label=label)
                    self.spec_ax.plot(x, y_fwd, color="red", alpha=0.5)
                else:
                    # forward selected -> main forward, overlay backward
                    self.spec_ax.plot(x, y_fwd, color=self.spec_colors[f], label=label)
                    self.spec_ax.plot(x, y_bwd, color="red", alpha=0.5)
        
            # ---- SINGLE DIRECTION ----
            else:
                self.spec_ax.plot(
                    x,
                    y_fwd,
                    color=self.spec_colors[f],
                    label=label
                )

        self.spec_ax.set_xlabel(xvar)
        self.spec_ax.set_ylabel(yvar)
        self.spec_ax.legend(fontsize=8)
        self.spec_canvas.draw()
        self.stm_fig.tight_layout()
        self.stm_canvas.draw()
        self.spec_fig.subplots_adjust(left=0.18, bottom=0.18)
        self.spec_canvas.draw_idle()
    #Sofia's KPFM fitting
    def run_kpfm_fit(self):

        selected = [k for k,v in self.spec_vars.items() if v.get()]

        if len(selected) != 1:
            print("Select exactly ONE spectrum for KPFM fitting")
            return

        spec_file = selected[0]

        data = load_spectrum_data(os.path.join(self.directory, spec_file))
        
        xvar = self.x_axis_var.get()
        yvar = self.y_axis_var.get()

        if xvar not in data or yvar not in data:
            print("Selected channels not found")
            return

        bias = data[xvar]
        df = data[yvar]
        
        # run analysis
        analysis = KPFMSpectrumAnalysis(bias=bias, df=df)
        
        vContact = analysis.CalcVContact()
        
        print("Vcontact =", vContact, "V")
        
        # create popup figure
        fig, axFit, axResiduals = analysis.PlotVContactCalculation()
        plt.close(fig)
        
        # embed figure in tkinter
        window = tk.Toplevel(self.root)
        window.title(f"KPFM Fit: {format_spec_name(spec_file)}")
        
        canvas = FigureCanvasTkAgg(fig, master=window)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        
        canvas.draw()

class ProgressWindow(tk.Toplevel):

    def __init__(self, parent, total_steps, title="Processing..."):
        super().__init__(parent)

        self.title(title)
        self.geometry("400x150")
        self.transient(parent)
        self.grab_set()

        self.total_steps = total_steps
        self.current_step = 0

        # ---- Widgets ----
        self.label = tk.Label(self, text="Starting...")
        self.label.pack(pady=10)

        self.progress = ttk.Progressbar(
            self,
            orient="horizontal",
            length=350,
            mode="determinate",
            maximum=total_steps
        )
        self.progress.pack(pady=10)

        self.percent_label = tk.Label(self, text="0%")
        self.percent_label.pack()

        # ---- Center Window ----
        self.update_idletasks()

        width = self.winfo_width()
        height = self.winfo_height()

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        x = int((screen_width / 2) - (width / 2))
        y = int((screen_height / 2) - (height / 2))

        self.geometry(f"{width}x{height}+{x}+{y}")

    # ---- Methods ----

    def update(self, message):
        if not self.winfo_exists():
            return
        self.update_status(message)

    def update_status(self, message):
        if self.winfo_exists():
            self.label.config(text=message)

    def step(self):
        if not self.winfo_exists():
            return

        self.current_step += 1
        self.progress["value"] = self.current_step

        if self.total_steps > 0:
            percent = int((self.current_step / self.total_steps) * 100)
        else:
            percent = 100

        self.percent_label.config(text=f"{percent}%")
        self.update_idletasks()

    def close(self):
        if self.winfo_exists():
            self.destroy()