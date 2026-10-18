
import os
import queue
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox, ttk

APP_NAME = "EasyInstall"

APPS = [
    {"name": "Discord", "id": "Discord.Discord",
     "category": "Social", "description": "Chat, voice and communities"},
    {"name": "Steam", "id": "Valve.Steam",
     "category": "Gaming", "description": "PC games and gaming community"},
    {"name": "Epic Games Launcher", "id": "EpicGames.EpicGamesLauncher",
     "category": "Gaming", "description": "Games and the Epic Games Store"},
    {"name": "Spotify", "id": "Spotify.Spotify",
     "category": "Music", "description": "Music and podcasts"},
    {"name": "Google Chrome", "id": "Google.Chrome",
     "category": "Internet", "description": "Web browser"},
    {"name": "Mozilla Firefox", "id": "Mozilla.Firefox",
     "category": "Internet", "description": "Privacy-focused web browser"},
    {"name": "VLC Media Player", "id": "VideoLAN.VLC",
     "category": "Utilities", "description": "Play video and audio files"},
    {"name": "7-Zip", "id": "7zip.7zip",
     "category": "Utilities", "description": "File compression utility"},
    {"name": "Visual Studio Code", "id": "Microsoft.VisualStudioCode",
     "category": "Development", "description": "Code editor"},
]

BG = "#111827"
PANEL = "#1F2937"
CARD = "#273449"
TEXT = "#F9FAFB"
MUTED = "#9CA3AF"
ACCENT = "#6366F1"
GREEN = "#22C55E"


class EasyInstall:
    def __init__(self, root):
        self.root = root
        self.root.title("EasyInstall")
        self.root.geometry("1040x720")
        self.root.minsize(780, 560)
        self.root.configure(bg=BG)

        self.events = queue.Queue()
        self.busy = set()
        self.installed = set()
        self.category = tk.StringVar(value="All apps")
        self.search = tk.StringVar()
        self.status = tk.StringVar(value="Ready")
        self.winget = shutil.which("winget")

        self.configure_styles()
        self.build_ui()
        self.root.after(100, self.process_events)

        if not self.winget:
            self.status.set("Windows Package Manager was not found")
            self.log("Install or update 'App Installer' from Microsoft Store.")
        else:
            self.log("Ready. Choose an app to install.")
            self.refresh_installed()

    def configure_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Easy.Horizontal.TProgressbar",
            troughcolor=PANEL, background=ACCENT, bordercolor=PANEL
        )

    def build_ui(self):
        header = tk.Frame(self.root, bg=BG, padx=24, pady=20)
        header.pack(fill="x")

        tk.Label(
            header, text="⬡  EasyInstall", bg=BG, fg=TEXT,
            font=("Segoe UI", 23, "bold")
        ).pack(side="left")

        tk.Label(
            header, text="WINDOWS SOFTWARE HUB", bg=BG, fg=MUTED,
            font=("Segoe UI", 9, "bold")
        ).pack(side="right", pady=10)

        search_row = tk.Frame(self.root, bg=BG, padx=24)
        search_row.pack(fill="x", pady=(0, 16))

        entry = tk.Entry(
            search_row, textvariable=self.search, font=("Segoe UI", 12),
            bg=PANEL, fg=TEXT, insertbackground=TEXT,
            relief="flat", highlightthickness=1,
            highlightbackground=PANEL, highlightcolor=ACCENT
        )
        entry.pack(fill="x", ipady=12)
        entry.insert(0, "")
        self.search.trace_add("write", lambda *_: self.render_apps())

        category_row = tk.Frame(self.root, bg=BG, padx=24)
        category_row.pack(fill="x", pady=(0, 14))

        for category in [
            "All apps", "Gaming", "Social", "Music",
            "Internet", "Utilities", "Development"
        ]:
            tk.Button(
                category_row, text=category,
                command=lambda c=category: self.select_category(c),
                bg=ACCENT if category == "All apps" else PANEL,
                fg=TEXT, activebackground=ACCENT, activeforeground=TEXT,
                relief="flat", padx=12, pady=8, cursor="hand2"
            ).pack(side="left", padx=(0, 6))

        self.canvas = tk.Canvas(
            self.root, bg=BG, highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(
            self.root, orient="vertical", command=self.canvas.yview
        )
        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="top", fill="both", expand=True)

        self.cards_frame = tk.Frame(self.canvas, bg=BG)
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.cards_frame, anchor="nw"
        )
        self.cards_frame.bind(
            "<Configure>",
            lambda _: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfigure(
                self.canvas_window, width=e.width
            )
        )

        footer = tk.Frame(self.root, bg=PANEL, padx=18, pady=10)
        footer.pack(side="bottom", fill="x")

        tk.Label(
            footer, textvariable=self.status, bg=PANEL, fg=MUTED,
            font=("Segoe UI", 9)
        ).pack(side="left")

        tk.Button(
            footer, text="Check installed apps",
            command=self.refresh_installed, bg=ACCENT, fg=TEXT,
            activebackground=ACCENT, activeforeground=TEXT,
            relief="flat", padx=12, pady=7, cursor="hand2"
        ).pack(side="right")

        self.render_apps()

    def select_category(self, category):
        self.category.set(category)
        self.render_apps()

    def render_apps(self):
        for child in self.cards_frame.winfo_children():
            child.destroy()

        query = self.search.get().strip().lower()
        category = self.category.get()

        matches = [
            app for app in APPS
            if (category == "All apps" or app["category"] == category)
            and (query in app["name"].lower()
                 or query in app["description"].lower()
                 or query in app["category"].lower())
        ]

        for column in range(2):
            self.cards_frame.grid_columnconfigure(column, weight=1)

        if not matches:
            tk.Label(
                self.cards_frame, text="No apps found.",
                bg=BG, fg=MUTED, font=("Segoe UI", 12)
            ).grid(row=0, column=0, padx=24, pady=30)
            return

        for index, app in enumerate(matches):
            row, column = divmod(index, 2)
            card = tk.Frame(
                self.cards_frame, bg=CARD, padx=16, pady=15
            )
            card.grid(
                row=row, column=column, sticky="nsew",
                padx=(24 if column == 0 else 8, 8 if column == 0 else 24),
                pady=7
            )

            tk.Label(
                card, text=app["name"], bg=CARD, fg=TEXT,
                font=("Segoe UI", 13, "bold"), anchor="w"
            ).pack(fill="x")

            tk.Label(
                card, text=app["category"].upper(), bg=CARD, fg="#A5B4FC",
                font=("Segoe UI", 8, "bold"), anchor="w"
            ).pack(fill="x", pady=(3, 0))

            tk.Label(
                card, text=app["description"], bg=CARD, fg=MUTED,
                font=("Segoe UI", 10), anchor="w"
            ).pack(fill="x", pady=(7, 12))

            row_frame = tk.Frame(card, bg=CARD)
            row_frame.pack(fill="x")

            if app["id"] in self.busy:
                label, enabled = "Installing...", False
            elif app["id"] in self.installed:
                label, enabled = "Installed", False
            else:
                label, enabled = "Install", True

            tk.Button(
                row_frame, text=label,
                command=lambda a=app: self.install(a),
                state="normal" if enabled else "disabled",
                bg=ACCENT if enabled else "#374151",
                disabledforeground=GREEN if not enabled else TEXT,
                fg=TEXT, relief="flat", padx=16, pady=7,
                cursor="hand2"
            ).pack(side="left")

            tk.Label(
                row_frame, text=app["id"], bg=CARD, fg=MUTED,
                font=("Segoe UI", 8)
            ).pack(side="right")

    def log(self, message):
        self.events.put(("log", message))

    def install(self, app):
        if not self.winget:
            messagebox.showerror(
                "winget unavailable",
                "Install App Installer from the Microsoft Store first."
            )
            return

        if app["id"] in self.busy:
            return

        if not messagebox.askyesno(
            "Confirm installation",
            f"Install {app['name']} using Windows Package Manager?\n\n"
            "The package manager will contact its configured sources. "
            "Windows may request administrator permission."
        ):
            return

        self.busy.add(app["id"])
        self.render_apps()
        self.status.set(f"Installing {app['name']}...")
        self.log(f"Starting installation: {app['name']}")

        threading.Thread(
            target=self.install_worker, args=(app,), daemon=True
        ).start()

    def install_worker(self, app):
        command = [
            self.winget, "install",
            "--id", app["id"], "--exact",
            "--source", "winget",
            "--accept-source-agreements",
            "--accept-package-agreements",
            "--disable-interactivity"
        ]

        try:
            result = subprocess.run(
                command, capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=1800,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
            )
            output = (result.stdout + "\n" + result.stderr).strip()
            success = result.returncode == 0

            self.events.put((
                "install_done", app["id"], app["name"],
                success, result.returncode, output[-5000:]
            ))
        except subprocess.TimeoutExpired:
            self.events.put((
                "install_done", app["id"], app["name"],
                False, -1, "Installation timed out after 30 minutes."
            ))
        except Exception as exc:
            self.events.put((
                "install_done", app["id"], app["name"],
                False, -1, str(exc)
            ))

    def refresh_installed(self):
        if not self.winget:
            self.status.set("winget is unavailable")
            return

        self.status.set("Checking installed applications...")
        threading.Thread(
            target=self.refresh_worker, daemon=True
        ).start()

    def refresh_worker(self):
        found = set()

        for app in APPS:
            try:
                result = subprocess.run(
                    [
                        self.winget, "list",
                        "--id", app["id"], "--exact",
                        "--disable-interactivity"
                    ],
                    capture_output=True, text=True,
                    encoding="utf-8", errors="replace", timeout=30,
                    creationflags=getattr(
                        subprocess, "CREATE_NO_WINDOW", 0
                    )
                )
                output = (result.stdout + result.stderr).lower()
                if app["id"].lower() in output:
                    found.add(app["id"])
            except Exception:
                pass

        self.events.put(("refresh_done", found))

    def process_events(self):
        try:
            while True:
                event = self.events.get_nowait()
                kind = event[0]

                if kind == "log":
                    # Keep the activity log available in the console
                    print(f"[{APP_NAME}] {event[1]}")

                elif kind == "install_done":
                    _, app_id, name, success, code, output = event
                    self.busy.discard(app_id)

                    if success:
                        self.installed.add(app_id)
                        self.status.set(f"{name} installed successfully")
                        messagebox.showinfo(
                            "Installation complete",
                            f"{name} was installed successfully."
                        )
                    else:
                        self.status.set(f"Installation failed: {name}")
                        messagebox.showerror(
                            "Installation failed",
                            f"Could not install {name}.\n"
                            f"Exit code: {code}\n\n"
                            f"{output[-2500:] or 'No diagnostic output.'}"
                        )

                    self.render_apps()

                elif kind == "refresh_done":
                    self.installed = event[1]
                    self.status.set(
                        f"{len(self.installed)} listed apps detected"
                    )
                    self.render_apps()

        except queue.Empty:
            pass

        self.root.after(100, self.process_events)


if __name__ == "__main__":
    root = tk.Tk()
    app = EasyInstall(root)
    root.mainloop()
