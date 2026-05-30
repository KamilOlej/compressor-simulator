#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compressor_app_pl.py
Symulator sprężarki / butli z GUI (polska wersja) i sterownikiem rozmytym.
Funkcje:
- przyciski: Sprężarka, Butla, Rozpocznij/Zatrzymaj napełnianie, Odcięcie, Awaryjne odcięcie, Resetuj awarię
- Reset logu bezpieczeństwa, Zapis logu UI, Info (Politechnika Koszalińska ...)
- Log bezpieczeństwa zapisywany do safety_log.txt
- Zakres butli 0..300 bar (maksymalnie)
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading, time, random, os
import numpy as np

# paths
BASE_DIR = os.path.dirname(__file__)
LOG_PATH = os.path.join(BASE_DIR, "safety_log.txt")

def tri_mf(x, a, b, c):
    if x <= a or x >= c:
        return 0.0
    if x == b:
        return 1.0
    if x > a and x < b:
        return (x - a) / (b - a) if (b - a) != 0 else 0.0
    return (c - x) / (c - b) if (c - b) != 0 else 0.0

# Membership functions adjusted for -300..300 domain
def input_mfs():
    return {
        'VNEG': (-300, -300, -150),
        'NEG' : (-200, -100, 0),
        'ZERO': (-30, 0, 30),
        'POS' : (0, 100, 200),
        'VPOS': (150, 300, 300)
    }

def output_mfs():
    return {
        'SHUT': (0.0, 0.0, 0.2),
        'SMALL': (0.05, 0.25, 0.45),
        'MEDIUM': (0.3, 0.5, 0.7),
        'LARGE': (0.55, 0.75, 0.95),
        'FULL': (0.8, 1.0, 1.0)
    }

RULES = [
    ('VNEG','SHUT'),
    ('NEG','SMALL'),
    ('ZERO','MEDIUM'),
    ('POS','LARGE'),
    ('VPOS','FULL')
]

def fuzzify_error(e):
    mfs = input_mfs()
    return {name: tri_mf(e, *params) for name, params in mfs.items()}

def infer_valve(fuzzy_error):
    out = output_mfs()
    y = np.linspace(0,1,401)
    agg = np.zeros_like(y)
    for in_term, out_term in RULES:
        degree = fuzzy_error.get(in_term, 0.0)
        a,b,c = out[out_term]
        mf_vals = np.array([tri_mf(v,a,b,c) for v in y])
        clipped = np.minimum(mf_vals, degree)
        agg = np.maximum(agg, clipped)
    return y, agg

def defuzzify_cog(y, agg):
    num = np.sum(y * agg)
    den = np.sum(agg)
    return num/den if den != 0 else 0.0

def append_safety_log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")
    except Exception as e:
        print("Nie udało się zapisać safety_log:", e)

def reset_safety_log():
    try:
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_PATH, "w", encoding="utf-8") as f:
            f.write(f"[{ts}] SAFETY LOG RESET (wyczyszczony przez użytkownika)\n")
        return True
    except Exception as e:
        print("Failed to reset safety log:", e)
        return False

class CompressorApp:
    def __init__(self, root):
        self.root = root
        root.title("Symulator sprężarki / butli (Sterowanie rozmyte)")
        root.geometry("840x480")
        # state
        self.compressor_connected = False
        self.cylinder_connected = False
        self.emergency = False
        self.filling = False
        self.pressure = random.uniform(10,150)  # initial 10-150
        self.setpoint = tk.DoubleVar(value=150.0)
        # UI
        main = ttk.Frame(root, padding=10)
        main.pack(fill='both', expand=True)
        left = ttk.Frame(main)
        left.pack(side='left', fill='y', padx=(0,10))
        self.comp_btn = tk.Button(left, text="Sprężarka: ODŁĄCZONA", bg='red', fg='white', width=30, command=self.toggle_compressor)
        self.comp_btn.pack(pady=6)
        self.cyl_btn = tk.Button(left, text="Butla: ODŁĄCZONA", bg='red', fg='white', width=30, command=self.toggle_cylinder)
        self.cyl_btn.pack(pady=6)
        ttk.Label(left, text="Wartość zadana (bar)").pack(pady=(12,0))
        self.sp_scale = ttk.Scale(left, from_=0, to=300, orient='horizontal', variable=self.setpoint, command=self.on_setpoint_change, length=260)
        self.sp_scale.pack(pady=6)
        self.sp_label = ttk.Label(left, text=f"Zadane: {self.setpoint.get():.1f} bar")
        self.sp_label.pack()
        ttk.Button(left, text="Losuj ciśnienie (10-150)", command=self.randomize_pressure).pack(pady=(12,4))
        self.fill_btn = tk.Button(left, text="Rozpocznij napełnianie", bg='lightgray', width=30, command=self.toggle_filling)
        self.fill_btn.pack(pady=4)
        self.cutoff_btn = tk.Button(left, text="Odcięcie (stop napełniania)", bg='orange', width=30, command=self.cutoff)
        self.cutoff_btn.pack(pady=4)
        self.emg_btn = tk.Button(left, text="Awaryjne odcięcie", bg='darkred', fg='white', width=30, command=self.emergency_cutoff)
        self.emg_btn.pack(pady=8)
        self.reset_emg_btn = tk.Button(left, text="Resetuj awarię", bg='gray', fg='white', width=30, command=self.reset_emergency)
        self.reset_emg_btn.pack(pady=(0,8))
        right = ttk.Frame(main)
        right.pack(side='left', fill='both', expand=True)
        pr_frame = ttk.LabelFrame(right, text="Butla", padding=10)
        pr_frame.pack(fill='x', padx=6, pady=6)
        self.pressure_label = ttk.Label(pr_frame, text=f"Ciśnienie: {self.pressure:.2f} bar", font=("Arial", 18))
        self.pressure_label.pack(anchor='w')
        self.cyl_status_label = ttk.Label(pr_frame, text="Stan: Niepodłączona", foreground='red')
        self.cyl_status_label.pack(anchor='w', pady=(4,0))
        fuzzy_frame = ttk.LabelFrame(right, text="Sterownik rozmyty", padding=10)
        fuzzy_frame.pack(fill='both', expand=True, padx=6, pady=6)
        self.error_label = ttk.Label(fuzzy_frame, text="Błąd (zadane - ciśnienie): 0.0")
        self.error_label.pack(anchor='w', pady=(2,0))
        self.valve_label = ttk.Label(fuzzy_frame, text="Otwarcie zaworu (0..100%): 0.0%")
        self.valve_label.pack(anchor='w', pady=(4,0))
        log_frame = ttk.LabelFrame(right, text="Dziennik", padding=6)
        log_frame.pack(fill='both', expand=True, padx=6, pady=6)
        self.log_text = tk.Text(log_frame, height=8)
        self.log_text.pack(fill='both', expand=True)
        ttk.Button(right, text="Zapisz log do pliku", command=self.save_ui_log).pack(pady=(6,2))
        ttk.Button(right, text="Resetuj log bezpieczeństwa", command=self.reset_safety_log_ui).pack(pady=(2,4))
        ttk.Button(right, text="Info", command=self.show_info).pack(pady=(2,4))
        # thread
        self._stop_thread = False
        self.thread = threading.Thread(target=self.background_loop, daemon=True)
        self.thread.start()

    # actions
    def toggle_compressor(self):
        self.compressor_connected = not self.compressor_connected
        if self.compressor_connected:
            self.comp_btn.config(text="Sprężarka: PODŁĄCZONA", bg='green', fg='white')
            self.log("Sprężarka podłączona")
        else:
            self.comp_btn.config(text="Sprężarka: ODŁĄCZONA", bg='red', fg='white')
            self.log("Sprężarka odłączona")

    def toggle_cylinder(self):
        self.cylinder_connected = not self.cylinder_connected
        if self.cylinder_connected:
            self.cyl_btn.config(text="Butla: PODŁĄCZONA", bg='green', fg='white')
            self.cyl_status_label.config(text="Stan: Podłączona", foreground='green')
            self.log("Butla podłączona")
        else:
            self.cyl_btn.config(text="Butla: ODŁĄCZONA", bg='red', fg='white')
            self.cyl_status_label.config(text="Stan: Niepodłączona", foreground='red')
            self.log("Butla odłączona")

    def on_setpoint_change(self, _=None):
        self.sp_label.config(text=f"Zadane: {self.setpoint.get():.1f} bar")

    def randomize_pressure(self):
        self.pressure = random.uniform(10,150)
        self.log(f"Wylosowano ciśnienie: {self.pressure:.2f} bar")
        self.update_ui()

    def toggle_filling(self):
        if self.emergency:
            messagebox.showwarning("Awaria", "Awaryjne odcięcie aktywne. Zresetuj przed napełnianiem.")
            return
        if not (self.compressor_connected and self.cylinder_connected):
            messagebox.showwarning("Brak połączenia", "Sprężarka i butla muszą być podłączone.")
            return
        self.filling = not self.filling
        if self.filling:
            self.fill_btn.config(text="Zatrzymaj napełnianie", bg='lightgreen')
            self.log("Rozpoczęto napełnianie")
        else:
            self.fill_btn.config(text="Rozpocznij napełnianie", bg='lightgray')
            self.log("Zatrzymano napełnianie")

    def cutoff(self):
        self.filling = False
        self.fill_btn.config(text="Rozpocznij napełnianie", bg='lightgray')
        self.log("Odcięcie: napełnianie zatrzymane")

    def emergency_cutoff(self):
        if not self.emergency:
            self.emergency = True
            self.filling = False
            self.fill_btn.config(text="Rozpocznij napełnianie", bg='lightgray')
            self.emg_btn.config(text="Awaryjne odcięcie AKTYWNE", bg='red', fg='white')
            self.log("Awaryjne odcięcie AKTYWOWANE")
            append_safety_log("Awaryjne odcięcie AKTYWOWANE - UI")

    def reset_emergency(self):
        if self.emergency:
            self.emergency = False
            self.emg_btn.config(text="Awaryjne odcięcie", bg='darkred', fg='white')
            self.log("Awaryjne odcięcie zresetowane (UI)")
            append_safety_log("Awaryjne odcięcie ZRESETOWANE - UI")
        else:
            self.log("Awaria nieaktywna; brak resetu")

    def save_ui_log(self):
        path = os.path.join(BASE_DIR, "ui_log.txt")
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.log_text.get("1.0", "end"))
            self.log(f"Log UI zapisany do {path}")
            append_safety_log(f"UI log zapisany do {path}")
        except Exception as e:
            self.log(f"Nie udało się zapisać logu UI: {e}")

    def reset_safety_log_ui(self):
        ok = reset_safety_log()
        if ok:
            self.log("Zresetowano log bezpieczeństwa (safety_log.txt wyczyszczony)")
            append_safety_log("SAFETY LOG RESET via UI")
        else:
            self.log("Nie udało się zresetować logu bezpieczeństwa")

    def show_info(self):
        info_text = "Politechnika Koszalińska 2025\nAutorzy: Arkadisz Szwed, Kamil Olejniczak"
        try:
            messagebox.showinfo("Informacje", info_text)
        except Exception:
            self.log("INFO: " + info_text)

    def log(self, msg):
        ts = time.strftime("%H:%M:%S")
        self.log_text.insert('end', f"[{ts}] {msg}\n")
        self.log_text.see('end')

    def background_loop(self):
        while not self._stop_thread:
            try:
                time.sleep(0.2)
                sp = self.setpoint.get()
                err = sp - self.pressure
                fuzzy = fuzzify_error(err)
                y, agg = infer_valve(fuzzy)
                valve = defuzzify_cog(y, agg)
                self.root.after(0, self.update_fuzzy_ui, err, valve)
                # safety: if emergency active, stop filling
                if self.emergency and self.filling:
                    self.filling = False
                if self.filling and self.compressor_connected and self.cylinder_connected and not self.emergency:
                    increase = valve * 1.0
                    distance = max(sp - self.pressure, 0)
                    scale = min(1.0, distance / 40.0)
                    self.pressure += increase * scale
                    self.pressure += random.uniform(-0.03, 0.03)
                    # safety bound - do not exceed 300
                    if self.pressure >= 300.0:
                        self.pressure = 300.0
                        self.filling = False
                        self.root.after(0, lambda: self.fill_btn.config(text="Rozpocznij napełnianie", bg='lightgray'))
                        alert_msg = "ALARM: Osiągnięto maksymalne bezpieczne ciśnienie (300 bar) - auto odcięcie"
                        self.log(alert_msg)
                        append_safety_log(alert_msg)
                else:
                    self.pressure += random.uniform(-0.06, 0.06)
                    if self.pressure < 0:
                        self.pressure = 0.0
                self.root.after(0, self.update_ui)
            except Exception as e:
                print("Background loop error:", e)
                break

    def update_fuzzy_ui(self, err, valve):
        self.error_label.config(text=f"Błąd (zadane - ciśnienie): {err:.2f} bar")
        self.valve_label.config(text=f"Otwarcie zaworu (0..100%): {valve*100:.1f}%")

    def update_ui(self):
        self.pressure_label.config(text=f"Ciśnienie: {self.pressure:.2f} bar")
        if self.cylinder_connected:
            self.cyl_status_label.config(text="Stan: Podłączona", foreground='green')
        else:
            self.cyl_status_label.config(text="Stan: Niepodłączona", foreground='red')

    def on_close(self):
        self._stop_thread = True
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = CompressorApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
