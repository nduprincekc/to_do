#!/usr/bin/env python3
"""
TaskFlow GUI — Professional To-Do List Manager
Built with tkinter (no extra dependencies)
"""

import json
import os
import tkinter as tk
from tkinter import messagebox
from datetime import datetime

DATA_FILE = "tasks.json"

# ── Theme ─────────────────────────────────────────────────────
BG        = "#0f0f13"
SURFACE   = "#1a1a22"
SURFACE2  = "#22222e"
BORDER    = "#2e2e3e"
ACCENT    = "#c8f542"
ACCENT2   = "#7b5ea7"
TEXT      = "#f0f0f0"
MUTED     = "#6b6b80"
DANGER    = "#ff5e5e"
DONE_FG   = "#444455"
FONT_MAIN = ("Courier New", 11)
FONT_BOLD = ("Courier New", 11, "bold")
FONT_H1   = ("Courier New", 20, "bold")
FONT_SM   = ("Courier New", 9)


# ── Storage ───────────────────────────────────────────────────
def load_tasks():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []


def save_tasks(tasks):
    with open(DATA_FILE, "w") as f:
        json.dump(tasks, f, indent=2)


# ── App ───────────────────────────────────────────────────────
class TaskFlowApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TaskFlow")
        self.root.geometry("660x720")
        self.root.minsize(520, 560)
        self.root.configure(bg=BG)
        self.root.resizable(True, True)

        self.tasks  = load_tasks()
        self.filter = "all"   # all | active | done

        self._build_ui()
        self.refresh()

    # ── UI Construction ───────────────────────────────────────
    def _build_ui(self):
        # ── Header ──
        hdr = tk.Frame(self.root, bg=BG)
        hdr.pack(fill="x", padx=28, pady=(28, 0))

        tk.Label(hdr, text="Task", font=("Courier New", 22, "bold"),
                 bg=BG, fg=TEXT).pack(side="left")
        tk.Label(hdr, text="Flow", font=("Courier New", 22, "bold"),
                 bg=BG, fg=ACCENT).pack(side="left")

        self.stats_lbl = tk.Label(hdr, text="", font=FONT_SM, bg=BG, fg=MUTED, justify="right")
        self.stats_lbl.pack(side="right", anchor="s", pady=4)

        # ── Progress bar ──
        pb_frame = tk.Frame(self.root, bg=BG)
        pb_frame.pack(fill="x", padx=28, pady=(6, 18))

        self.pb_bg = tk.Canvas(pb_frame, height=4, bg=BORDER,
                               highlightthickness=0, bd=0)
        self.pb_bg.pack(fill="x")
        self.pb_fill = self.pb_bg.create_rectangle(0, 0, 0, 4, fill=ACCENT, width=0)

        # ── Input row ──
        inp_frame = tk.Frame(self.root, bg=SURFACE, bd=0, highlightthickness=1,
                             highlightbackground=BORDER)
        inp_frame.pack(fill="x", padx=28, pady=(0, 14))

        self.entry = tk.Entry(inp_frame, font=FONT_MAIN, bg=SURFACE, fg=TEXT,
                              insertbackground=ACCENT, relief="flat",
                              bd=0, highlightthickness=0)
        self.entry.pack(side="left", fill="both", expand=True, padx=16, pady=14)
        self.entry.insert(0, "")
        self.entry.bind("<Return>", lambda e: self.add_task())
        self.entry.bind("<FocusIn>",  lambda e: inp_frame.config(highlightbackground=ACCENT))
        self.entry.bind("<FocusOut>", lambda e: inp_frame.config(highlightbackground=BORDER))

        add_btn = tk.Button(inp_frame, text="+ Add", font=FONT_BOLD,
                            bg=ACCENT, fg=BG, relief="flat", bd=0,
                            padx=18, pady=10, cursor="hand2",
                            activebackground="#aad932", activeforeground=BG,
                            command=self.add_task)
        add_btn.pack(side="right", padx=8, pady=6)

        # ── Filter tabs ──
        tab_frame = tk.Frame(self.root, bg=BG)
        tab_frame.pack(fill="x", padx=28, pady=(0, 12))

        self.tab_btns = {}
        for label, key in [("All", "all"), ("Active", "active"), ("Done", "done")]:
            btn = tk.Button(tab_frame, text=label, font=FONT_SM,
                            bg=SURFACE, fg=MUTED, relief="flat", bd=0,
                            padx=14, pady=6, cursor="hand2",
                            activebackground=SURFACE2, activeforeground=ACCENT,
                            command=lambda k=key: self.set_filter(k))
            btn.pack(side="left", padx=(0, 6))
            self.tab_btns[key] = btn

        # ── Task list (scrollable) ──
        list_outer = tk.Frame(self.root, bg=BG)
        list_outer.pack(fill="both", expand=True, padx=28)

        canvas = tk.Canvas(list_outer, bg=BG, highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(list_outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self.task_frame = tk.Frame(canvas, bg=BG)
        self.canvas_window = canvas.create_window((0, 0), window=self.task_frame, anchor="nw")

        self.task_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
            lambda e: canvas.itemconfig(self.canvas_window, width=e.width))
        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"))

        self.canvas = canvas

        # ── Footer ──
        footer = tk.Frame(self.root, bg=BG)
        footer.pack(fill="x", padx=28, pady=(10, 20))

        tk.Button(footer, text="Clear completed", font=FONT_SM,
                  bg=SURFACE, fg=MUTED, relief="flat", bd=0,
                  padx=12, pady=6, cursor="hand2",
                  activebackground=SURFACE2, activeforeground=DANGER,
                  command=self.clear_done).pack(side="right")

    # ── Logic ─────────────────────────────────────────────────
    def add_task(self):
        text = self.entry.get().strip()
        if not text:
            self.shake_entry()
            return
        self.tasks.insert(0, {
            "id":      int(datetime.now().timestamp() * 1000),
            "text":    text,
            "done":    False,
            "created": datetime.now().strftime("%b %d, %H:%M")
        })
        self.entry.delete(0, "end")
        save_tasks(self.tasks)
        self.refresh()
        self.toast("Task added ✓")

    def toggle_task(self, tid):
        for t in self.tasks:
            if t["id"] == tid:
                t["done"] = not t["done"]
        save_tasks(self.tasks)
        self.refresh()

    def delete_task(self, tid):
        self.tasks = [t for t in self.tasks if t["id"] != tid]
        save_tasks(self.tasks)
        self.refresh()
        self.toast("Task deleted")

    def clear_done(self):
        count = sum(1 for t in self.tasks if t["done"])
        if not count:
            self.toast("Nothing to clear")
            return
        self.tasks = [t for t in self.tasks if not t["done"]]
        save_tasks(self.tasks)
        self.refresh()
        self.toast(f"Cleared {count} task(s)")

    def set_filter(self, f):
        self.filter = f
        self.refresh()

    def filtered(self):
        if self.filter == "active": return [t for t in self.tasks if not t["done"]]
        if self.filter == "done":   return [t for t in self.tasks if t["done"]]
        return self.tasks

    # ── Render ────────────────────────────────────────────────
    def refresh(self):
        # Update stats
        total = len(self.tasks)
        done  = sum(1 for t in self.tasks if t["done"])
        rem   = total - done
        pct   = (done / total) if total else 0
        self.stats_lbl.config(text=f"{done}/{total} done · {rem} remaining")

        # Update progress bar
        self.pb_bg.update_idletasks()
        w = self.pb_bg.winfo_width()
        self.pb_bg.coords(self.pb_fill, 0, 0, int(w * pct), 4)

        # Update tab styles
        for key, btn in self.tab_btns.items():
            if key == self.filter:
                btn.config(fg=ACCENT, bg=SURFACE2)
            else:
                btn.config(fg=MUTED, bg=SURFACE)

        # Clear task list
        for w in self.task_frame.winfo_children():
            w.destroy()

        tasks = self.filtered()

        if not tasks:
            msgs = {
                "all":    "No tasks yet — add one above!",
                "active": "All caught up! No active tasks.",
                "done":   "Nothing completed yet."
            }
            tk.Label(self.task_frame, text=msgs[self.filter],
                     font=FONT_SM, bg=BG, fg=MUTED,
                     pady=40).pack()
            return

        for i, task in enumerate(tasks):
            self._task_row(task, i + 1)

    def _task_row(self, task, num):
        done = task["done"]

        row = tk.Frame(self.task_frame, bg=SURFACE if not done else "#141418",
                       bd=0, highlightthickness=1,
                       highlightbackground=BORDER)
        row.pack(fill="x", pady=(0, 8))

        inner = tk.Frame(row, bg=row["bg"])
        inner.pack(fill="x", padx=14, pady=12)

        # Checkbox
        check_text = "✓" if done else "○"
        check_fg   = ACCENT if done else MUTED
        chk = tk.Button(inner, text=check_text, font=FONT_BOLD,
                        bg=row["bg"], fg=check_fg, relief="flat", bd=0,
                        cursor="hand2", width=2,
                        activebackground=row["bg"], activeforeground=ACCENT,
                        command=lambda tid=task["id"]: self.toggle_task(tid))
        chk.pack(side="left")

        # Task text
        txt_fg = DONE_FG if done else TEXT
        # Strikethrough effect via font (tkinter doesn't support real strikethrough easily)
        txt_font = ("Courier New", 11, "overstrike") if done else FONT_MAIN
        tk.Label(inner, text=task["text"], font=txt_font,
                 bg=row["bg"], fg=txt_fg,
                 anchor="w", wraplength=380, justify="left").pack(side="left", fill="x", expand=True, padx=10)

        # Date + delete
        right = tk.Frame(inner, bg=row["bg"])
        right.pack(side="right")

        tk.Label(right, text=task["created"], font=FONT_SM,
                 bg=row["bg"], fg=MUTED).pack(side="left", padx=(0, 10))

        tk.Button(right, text="✕", font=FONT_SM,
                  bg=row["bg"], fg=MUTED, relief="flat", bd=0,
                  cursor="hand2",
                  activebackground=row["bg"], activeforeground=DANGER,
                  command=lambda tid=task["id"]: self.delete_task(tid)).pack(side="left")

        # Hover effect
        def on_enter(e, r=row, i=inner):
            r.config(highlightbackground=ACCENT2)
        def on_leave(e, r=row):
            r.config(highlightbackground=BORDER)

        for widget in [row, inner, chk]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)

    # ── Helpers ───────────────────────────────────────────────
    def shake_entry(self):
        orig_x = self.entry.winfo_x()
        for dx in [6, -6, 4, -4, 2, -2, 0]:
            self.root.after(30, lambda d=dx: self.entry.place_configure())
        # Flash red border
        parent = self.entry.master
        parent.config(highlightbackground=DANGER)
        self.root.after(600, lambda: parent.config(highlightbackground=BORDER))

    def toast(self, msg):
        if hasattr(self, "_toast_win") and self._toast_win.winfo_exists():
            self._toast_win.destroy()

        tw = tk.Toplevel(self.root)
        tw.overrideredirect(True)
        tw.attributes("-topmost", True)
        tw.configure(bg=SURFACE2)

        tk.Label(tw, text=f"  {msg}  ", font=FONT_SM,
                 bg=SURFACE2, fg=TEXT, pady=10).pack()

        # Position bottom-center of main window
        self.root.update_idletasks()
        rx = self.root.winfo_x() + self.root.winfo_width() // 2
        ry = self.root.winfo_y() + self.root.winfo_height() - 60
        tw.geometry(f"+{rx - 80}+{ry}")
        self._toast_win = tw
        self.root.after(2000, tw.destroy)


# ── Entry point ───────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app  = TaskFlowApp(root)
    root.mainloop()