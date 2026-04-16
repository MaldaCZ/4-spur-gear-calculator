import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import math
import threading
import os
import sys

# Try importing Pillow - app works without it (no schema image displayed)
try:
    from PIL import Image, ImageTk

    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


class InterpolaceOzubenychKol:
    def __init__(self):
        self.Zo = 0
        self.Zp = 0
        self.m = 0.0
        self.tolerance = 0.000003

    def _safe_acos_deg(self, value):
        if value > 1.0 + 1e-12 or value < -1.0 - 1e-12:
            raise ValueError(f"Value for acos out of range [-1,1]: {value:.6f}")
        v = max(-1.0, min(1.0, value))
        return math.degrees(math.acos(v))

    def vypocet_limitniho_uhlu_max(self):
        L1 = self.Zo * self.m / 2 + self.Zp * self.m / 2
        L2 = self.Zp * self.m
        LC = self.Zo * self.m / 2 + self.Zp * self.m / 2
        cos_alpha = (LC**2 + L1**2 - L2**2) / (2 * LC * L1)
        alpha_deg = self._safe_acos_deg(cos_alpha)
        return alpha_deg, L1, L2, LC

    def vypocet_limitniho_uhlu_min(self):
        L1 = self.Zo * self.m / 2 + self.Zp * self.m / 2
        L2 = self.Zp * self.m
        Rp = self.Zp * self.m / 2
        x1_sq = L1**2 - Rp**2
        x2_sq = L2**2 - Rp**2
        if x1_sq < 0 or x2_sq < 0:
            raise ValueError("Negative value under square root")
        x1 = math.sqrt(x1_sq)
        x2 = math.sqrt(x2_sq)
        LC = x1 + x2
        cos_alpha = (LC**2 + L1**2 - L2**2) / (2 * LC * L1)
        alpha_deg = self._safe_acos_deg(cos_alpha)
        return alpha_deg, L1, L2, LC

    def vypocet_parametru_pro_alfu(self, alfa_deg):
        R1 = self.Zo * self.m / 2
        R2 = self.Zp * self.m / 2
        alfa_rad = math.radians(alfa_deg)
        L1 = R1 + R2
        L2 = 2 * R2

        sin_beta = (L1 / L2) * math.sin(alfa_rad)
        if abs(sin_beta) > 1.0:
            raise ValueError(f"Value for arcsin out of range [-1,1]: {sin_beta:.6f}")

        beta_rad = math.asin(sin_beta)
        beta_deg = math.degrees(beta_rad)
        gamma_deg = 180 - beta_deg - alfa_deg
        epsilon_deg = 180 - gamma_deg
        epsilon_rad = math.radians(epsilon_deg)

        O1 = alfa_rad * R1
        O2 = epsilon_rad * R2
        phi1 = O1 / R2
        phi2 = O2 / R2
        phic = phi1 + phi2
        phi_final_rad = phic - alfa_rad + epsilon_rad
        phi_final_deg = math.degrees(phi_final_rad)

        zubova_roztec = 360.0 / self.Zp
        vysledek_deleni = abs(phi_final_deg) / zubova_roztec
        zbytek = vysledek_deleni % 1
        je_cele_cislo = abs(zbytek) < self.tolerance
        je_pulka = abs(zbytek - 0.5) < self.tolerance
        je_dobre_reseni = je_cele_cislo or je_pulka

        return {
            "alfa_deg": alfa_deg,
            "beta_deg": beta_deg,
            "gamma_deg": gamma_deg,
            "epsilon_deg": epsilon_deg,
            "phi_final_deg": phi_final_deg,
            "zubova_roztec": zubova_roztec,
            "vysledek_deleni": vysledek_deleni,
            "je_dobre_reseni": je_dobre_reseni,
            "typ_reseni": (
                "whole number"
                if je_cele_cislo
                else ("half" if je_pulka else "no solution")
            ),
        }

    def interpolace_v_intervalu(self, alfa_min, alfa_max, krok, progress_callback=None):
        dobra_reseni = []
        aktualni_alfa = alfa_min
        pocet_testovanych = 0
        celkovy_pocet = int((alfa_max - alfa_min) / krok) + 1

        while aktualni_alfa <= alfa_max:
            try:
                vysledek = self.vypocet_parametru_pro_alfu(aktualni_alfa)
                pocet_testovanych += 1

                if vysledek["je_dobre_reseni"]:
                    dobra_reseni.append(vysledek)

                if progress_callback and pocet_testovanych % 100 == 0:
                    progress = pocet_testovanych / celkovy_pocet * 100
                    progress_callback(progress)

            except Exception:
                pass

            aktualni_alfa += krok

        return dobra_reseni


class OzubenaKolaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Spur Gear Interpolation Calculator")
        self.root.geometry("900x800")
        self.root.minsize(800, 700)
        self.root.configure(bg="#f0f0f0")

        self.colors = {
            "primary": "#212F3C",
            "secondary": "#5DADE2",
            "accent": "#E74C3C",
            "success": "#27AE60",
            "background": "#F8F9F9",
            "surface": "#FFFFFF",
            "text": "#34495E",
            "text_light": "#95A5A6",
        }

        self.vypocet = InterpolaceOzubenychKol()
        self.nastav_styly()
        self.nastav_ikonu()
        self.vytvor_ui()

    def nastav_styly(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Header.TLabel",
            font=("Segoe UI", 14, "bold"),
            foreground=self.colors["primary"],
            background=self.colors["background"],
        )

        style.configure(
            "Subheader.TLabel",
            font=("Segoe UI", 10, "bold"),
            foreground=self.colors["text"],
        )

        style.configure(
            "Info.TLabel", font=("Segoe UI", 9), foreground=self.colors["text_light"]
        )

        style.configure(
            "Modern.TFrame",
            background=self.colors["surface"],
            relief="flat",
            borderwidth=1,
        )

        style.configure(
            "Card.TLabelframe",
            background=self.colors["surface"],
            borderwidth=1,
            relief="solid",
            focusthickness=0,
            highlightthickness=0,
        )
        style.configure(
            "Card.TLabelframe.Label",
            font=("Segoe UI", 10, "bold"),
            foreground=self.colors["primary"],
            background=self.colors["surface"],
        )

        style.configure(
            "Modern.TButton",
            font=("Segoe UI", 10, "bold"),
            borderwidth=0,
            focusthickness=0,
        )

        style.map(
            "Modern.TButton",
            background=[
                ("active", self.colors["secondary"]),
                ("!active", self.colors["primary"]),
            ],
            foreground=[("active", "white"), ("!active", "white")],
        )

        style.configure(
            "Accent.TButton",
            font=("Segoe UI", 10, "bold"),
            borderwidth=0,
            focusthickness=0,
        )
        style.map(
            "Accent.TButton",
            background=[
                ("active", self.colors["accent"]),
                ("!active", "#E74C3C"),
            ],
            foreground=[("active", "white"), ("!active", "white")],
        )

        style.configure(
            "TProgressbar", thickness=10, troughcolor=self.colors["background"]
        )
        style.configure(
            "Horizontal.TProgressbar",
            foreground=self.colors["success"],
            background=self.colors["success"],
        )

    def nastav_ikonu(self):
        try:
            icon_ico_path = "icon.ico"
            icon_png_path = "icon.png"

            if hasattr(sys, "_MEIPASS"):
                icon_ico_path = os.path.join(sys._MEIPASS, "icon.ico")
                icon_png_path = os.path.join(sys._MEIPASS, "icon.png")

            if os.path.exists(icon_ico_path):
                self.root.iconbitmap(icon_ico_path)
            elif PILLOW_AVAILABLE and os.path.exists(icon_png_path):
                icon_image = Image.open(icon_png_path)
                icon_image = icon_image.resize((32, 32), Image.Resampling.LANCZOS)
                icon_photo = ImageTk.PhotoImage(icon_image)
                self.root.iconphoto(True, icon_photo)
                self.icon_image = icon_photo

        except Exception:
            pass

    def nacti_schema_obrazek(self, cesta_k_obrazku, max_width=300, max_height=200):
        if not PILLOW_AVAILABLE:
            return None

        try:
            if hasattr(sys, "_MEIPASS"):
                cesta_k_obrazku = os.path.join(sys._MEIPASS, cesta_k_obrazku)

            if os.path.exists(cesta_k_obrazku):
                image = Image.open(cesta_k_obrazku)
                original_width, original_height = image.size

                width_ratio = max_width / original_width
                height_ratio = max_height / original_height
                ratio = min(width_ratio, height_ratio)

                new_width = int(original_width * ratio)
                new_height = int(original_height * ratio)

                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(image)
        except Exception:
            pass
        return None

    def vytvor_ui(self):
        main_container = tk.Frame(self.root, bg=self.colors["background"])
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Header
        header_frame = tk.Frame(
            main_container, bg=self.colors["surface"], relief="flat", bd=0
        )
        header_frame.pack(fill=tk.X, pady=(0, 15))

        title_frame = tk.Frame(header_frame, bg=self.colors["surface"])
        title_frame.pack(fill=tk.X, expand=True, padx=15, pady=15)

        title_label = tk.Label(
            title_frame,
            text="Spur Gear Interpolation Calculator",
            font=("Segoe UI", 14, "bold"),
            fg=self.colors["primary"],
            bg=self.colors["surface"],
        )
        title_label.pack(anchor=tk.W)

        # Main content
        content_frame = tk.Frame(main_container, bg=self.colors["background"])
        content_frame.pack(fill=tk.BOTH, expand=True)
        content_frame.grid_columnconfigure(0, weight=0)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)

        # Left panel
        left_panel = tk.Frame(content_frame, bg=self.colors["background"])
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        input_card = ttk.Labelframe(
            left_panel, text=" Input Parameters ", style="Card.TLabelframe"
        )
        input_card.pack(fill=tk.X, pady=(0, 15), padx=5, ipady=5)

        params = [
            ("Number of teeth – large gear (Zo):", "zo_var", "80"),
            ("Number of teeth – pinion (Zp):", "zp_var", "30"),
            ("Module (m):", "m_var", "2.0"),
            ("Tolerance:", "tolerance_var", "0.000003"),
            ("Interpolation step (°):", "krok_var", "0.00001"),
        ]

        for i, (label_text, var_name, default_val) in enumerate(params):
            param_frame = tk.Frame(input_card, bg=self.colors["surface"])
            param_frame.pack(fill=tk.X, pady=6, padx=15)

            label = tk.Label(
                param_frame,
                text=label_text,
                font=("Segoe UI", 10),
                fg=self.colors["text"],
                bg=self.colors["surface"],
            )
            label.pack(anchor=tk.W, pady=(0, 2))

            var = tk.StringVar(value=default_val)
            setattr(self, var_name, var)

            entry = tk.Entry(
                param_frame,
                textvariable=var,
                font=("Segoe UI", 10),
                width=20,
                relief="flat",
                bd=1,
                highlightbackground=self.colors["text_light"],
                highlightcolor=self.colors["secondary"],
                highlightthickness=1,
            )
            entry.pack(anchor=tk.W)

        # Buttons
        button_card = ttk.Labelframe(
            left_panel, text=" Controls ", style="Card.TLabelframe"
        )
        button_card.pack(fill=tk.X, pady=(0, 15), padx=5, ipady=5)

        button_frame = tk.Frame(button_card, bg=self.colors["surface"])
        button_frame.pack(padx=15, pady=10)

        self.vypocitat_btn = tk.Button(
            button_frame,
            text="🚀 Run Calculation",
            command=self.spust_vypocet,
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["primary"],
            fg="white",
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2",
        )
        self.vypocitat_btn.pack(fill=tk.X, pady=(0, 10))

        self.vymazat_btn = tk.Button(
            button_frame,
            text="🗑️ Clear Results",
            command=self.vymaz_vysledky,
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["accent"],
            fg="white",
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2",
        )
        self.vymazat_btn.pack(fill=tk.X)

        # Progress card
        progress_card = ttk.Labelframe(
            left_panel, text=" Progress ", style="Card.TLabelframe"
        )
        progress_card.pack(fill=tk.X, padx=5, ipady=5)

        progress_frame = tk.Frame(progress_card, bg=self.colors["surface"])
        progress_frame.pack(padx=15, pady=10)

        self.progress = ttk.Progressbar(
            progress_frame, mode="determinate", style="Horizontal.TProgressbar"
        )
        self.progress.pack(fill=tk.X, pady=(0, 5))

        self.progress_label = tk.Label(
            progress_frame,
            text="Ready",
            font=("Segoe UI", 9),
            fg=self.colors["text_light"],
            bg=self.colors["surface"],
        )
        self.progress_label.pack()

        # Right panel — results
        right_panel = tk.Frame(content_frame, bg=self.colors["background"])
        right_panel.grid(row=0, column=1, sticky="nsew")

        vysledky_card = ttk.Labelframe(
            right_panel, text=" Results ", style="Card.TLabelframe"
        )
        vysledky_card.pack(fill=tk.BOTH, expand=True, padx=5, ipady=5)

        text_frame = tk.Frame(vysledky_card, bg=self.colors["surface"])
        text_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        self.vysledky_text = scrolledtext.ScrolledText(
            text_frame,
            font=("Consolas", 10),
            bg=self.colors["background"],
            fg=self.colors["text"],
            wrap=tk.WORD,
            relief="flat",
            borderwidth=1,
            highlightbackground=self.colors["text_light"],
            highlightcolor=self.colors["secondary"],
            highlightthickness=1,
        )
        self.vysledky_text.pack(fill=tk.BOTH, expand=True)

        # Footer
        footer_frame = tk.Frame(self.root, bg=self.colors["primary"], height=40)
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X)
        footer_frame.pack_propagate(False)

        footer_content = tk.Frame(footer_frame, bg=self.colors["primary"])
        footer_content.place(relx=0.5, rely=0.5, anchor="center")

        author_label = tk.Label(
            footer_content,
            text="Developed by: Malý Vratislav & Karel Vondráček",
            font=("Segoe UI", 10),
            fg="white",
            bg=self.colors["primary"],
        )
        author_label.pack()

    def validuj_vstupy(self):
        try:
            zo = int(self.zo_var.get())
            zp = int(self.zp_var.get())
            m = float(self.m_var.get())
            tolerance = float(self.tolerance_var.get())
            krok = float(self.krok_var.get())

            if zo <= 0 or zp <= 0:
                raise ValueError("Tooth counts must be positive integers")
            if m <= 0:
                raise ValueError("Module must be a positive number")
            if tolerance <= 0:
                raise ValueError("Tolerance must be a positive number")
            if krok <= 0:
                raise ValueError("Step must be a positive number")

            return zo, zp, m, tolerance, krok
        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid input: {e}")
            return None

    def spust_vypocet(self):
        vstup = self.validuj_vstupy()
        if not vstup:
            return

        zo, zp, m, tolerance, krok = vstup

        # Disable both buttons while calculating
        self.vypocitat_btn.config(state="disabled")
        self.vymazat_btn.config(state="disabled")
        self.progress["value"] = 0
        self.progress_label.config(text="Starting calculation...")
        self.vysledky_text.delete(1.0, tk.END)

        # Load schema image on the main thread (PIL is not thread-safe)
        schema_image = self.nacti_schema_obrazek("schema.png")

        def _progress(value):
            # root.after() is the only thread-safe way to update tkinter widgets
            self.root.after(0, lambda v=value: (
                self.progress.configure(value=v),
                self.progress_label.config(text=f"Processed: {v:.1f}%"),
            ))

        def vypocet_thread():
            try:
                self.vypocet.Zo = zo
                self.vypocet.Zp = zp
                self.vypocet.m = m
                self.vypocet.tolerance = tolerance

                alfa_max, *_ = self.vypocet.vypocet_limitniho_uhlu_max()
                alfa_min, *_ = self.vypocet.vypocet_limitniho_uhlu_min()

                dobra_reseni = self.vypocet.interpolace_v_intervalu(
                    alfa_min, alfa_max, krok, _progress
                )

                # All widget updates scheduled on the main thread
                def _render():
                    t = self.vysledky_text
                    ins = lambda s: t.insert(tk.END, s)

                    ins("═" * 63 + "\n")
                    ins("           SPUR GEAR INTERPOLATION CALCULATION\n")
                    ins("═" * 63 + "\n\n")
                    ins("📊 INPUT PARAMETERS:\n")
                    ins(f"    • Number of teeth – large gear (Zo): {zo}\n")
                    ins(f"    • Number of teeth – pinion (Zp): {zp}\n")
                    ins(f"    • Module (m): {m}\n")
                    ins(f"    • Tolerance: ±{tolerance}\n")
                    ins(f"    • Interpolation step: {krok}°\n\n")
                    ins("🎯 INTERPOLATION INTERVAL:\n")
                    ins(f"    • α_min = {alfa_min:.6f}°\n")
                    ins(f"    • α_max = {alfa_max:.6f}°\n\n")
                    ins("📐 GEOMETRY DIAGRAM:\n\n")
                    if schema_image:
                        self.schema_image = schema_image  # keep reference alive
                        t.image_create(tk.END, image=schema_image)
                        ins("\n\n\n")
                    ins("\n")
                    if not dobra_reseni:
                        ins("❌ RESULT: No valid solutions found!\n")
                        ins("    Try adjusting the tolerance or parameters.\n")
                    else:
                        ins(f"✅ FOUND {len(dobra_reseni)} SOLUTION(S):\n")
                        ins("─" * 63 + "\n\n")
                        for i, r in enumerate(dobra_reseni, 1):
                            ins(f"🔸 SOLUTION #{i}:\n")
                            ins(f"    α = {r['alfa_deg']:.5f}°\n")
                            ins(f"    β = {r['beta_deg']:.3f}°,  γ = {r['gamma_deg']:.3f}°,  ε = {r['epsilon_deg']:.3f}°\n")
                            ins(f"    φ final = {r['phi_final_deg']:.3f}°\n")
                            ins(f"    Division = {r['vysledek_deleni']:.6f}  ({r['typ_reseni']})\n\n")

                    self.progress.configure(value=100)
                    self.progress_label.config(text="Calculation complete ✅")
                    self.vypocitat_btn.config(state="normal")
                    self.vymazat_btn.config(state="normal")
                    t.see("1.0")

                self.root.after(0, _render)

            except Exception as e:
                def _error(err=e):
                    messagebox.showerror("Calculation Error", f"An error occurred: {err}")
                    self.progress_label.config(text="Calculation error ❌")
                    self.vypocitat_btn.config(state="normal")
                    self.vymazat_btn.config(state="normal")
                self.root.after(0, _error)

        threading.Thread(target=vypocet_thread, daemon=True).start()

    def vymaz_vysledky(self):
        self.vysledky_text.delete(1.0, tk.END)
        self.progress.configure(value=0)
        self.progress_label.config(text="Ready")


if __name__ == "__main__":
    root = tk.Tk()
    app = OzubenaKolaGUI(root)
    root.mainloop()
