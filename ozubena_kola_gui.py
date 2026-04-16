import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import math
import threading
import os
import sys

# Pokus o import Pillow - pokud není nainstalovaný, bude fungovat bez loga
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
        self.tolerance = 0.003

    def _safe_acos_deg(self, value):
        if value > 1.0 + 1e-12 or value < -1.0 - 1e-12:
            raise ValueError(f"Hodnota pro acos mimo interval [-1,1]: {value:.6f}")
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
            raise ValueError("Negativní hodnota pod odmocninou")
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
            raise ValueError(f"Hodnota pro arcsin mimo interval [-1,1]: {sin_beta:.6f}")

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
                "celé číslo"
                if je_cele_cislo
                else ("půlka" if je_pulka else "není řešení")
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
        self.root.title("Interpolační výpočet ozubených kol")
        self.root.geometry("900x800")
        self.root.minsize(800, 700)
        self.root.configure(bg="#f0f0f0")

        # Moderní barvy
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
        self.nastav_ikonu()  # Nová metoda pro nastavení ikony
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
        """Nastaví ikonu aplikace pro okno a taskbar"""
        try:
            # Cesty k ikonám
            icon_ico_path = "icon.ico"
            icon_png_path = "icon.png"

            # Pro EXE soubory - hledáme v dočasné složce PyInstaller
            if hasattr(sys, "_MEIPASS"):
                icon_ico_path = os.path.join(sys._MEIPASS, "icon.ico")
                icon_png_path = os.path.join(sys._MEIPASS, "icon.png")

            # Preferujeme .ico soubory pro Windows
            if os.path.exists(icon_ico_path):
                self.root.iconbitmap(icon_ico_path)
                print(f"Použita ikona: {icon_ico_path}")
            # Pokud .ico není, zkusíme .png s Pillow
            elif PILLOW_AVAILABLE and os.path.exists(icon_png_path):
                # Načteme PNG jako PhotoImage
                icon_image = Image.open(icon_png_path)
                # Změníme velikost na standardní ikonu (32x32 nebo 64x64)
                icon_image = icon_image.resize((32, 32), Image.Resampling.LANCZOS)
                icon_photo = ImageTk.PhotoImage(icon_image)
                self.root.iconphoto(True, icon_photo)
                # Uložíme referenci
                self.icon_image = icon_photo
                print(f"Použita ikona: {icon_png_path}")
            else:
                print("Varování: Nebyla nalezena žádná ikona (icon.ico nebo icon.png).")

        except Exception as e:
            print(f"Nepodařilo se nastavit ikonu: {e}")

    def nacti_logo(self, cesta_k_logu, max_height=60):
        """Načte logo - pro EXE hledá v dočasné složce PyInstaller a zachová poměr stran"""
        if not PILLOW_AVAILABLE:
            return None

        try:
            # Pro EXE soubory - hledáme v dočasné složce PyInstaller
            if hasattr(sys, "_MEIPASS"):
                cesta_k_logu = os.path.join(sys._MEIPASS, cesta_k_logu)

            if os.path.exists(cesta_k_logu):
                image = Image.open(cesta_k_logu)
                original_width, original_height = image.size

                # Vypočítáme novou šířku pro zachování poměru stran
                new_height = max_height
                new_width = int(original_width * (new_height / original_height))

                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(image)
        except Exception as e:
            print(f"Chyba při načítání loga: {e}")
        return None

    def nacti_schema_obrazek(self, cesta_k_obrazku, max_width=300, max_height=200):
        """Načte schematický obrázek pro výsledky"""
        if not PILLOW_AVAILABLE:
            return None

        try:
            # Pro EXE soubory - hledáme v dočasné složce PyInstaller
            if hasattr(sys, "_MEIPASS"):
                cesta_k_obrazku = os.path.join(sys._MEIPASS, cesta_k_obrazku)

            if os.path.exists(cesta_k_obrazku):
                image = Image.open(cesta_k_obrazku)
                original_width, original_height = image.size

                # Vypočítáme nové rozměry pro zachování poměru stran
                width_ratio = max_width / original_width
                height_ratio = max_height / original_height
                ratio = min(width_ratio, height_ratio)

                new_width = int(original_width * ratio)
                new_height = int(original_height * ratio)

                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(image)
        except Exception as e:
            print(f"Chyba při načítání schématu: {e}")
        return None

    def vytvor_ui(self):
        # Hlavní kontejner
        main_container = tk.Frame(self.root, bg=self.colors["background"])
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Header s logem a titulkem
        header_frame = tk.Frame(
            main_container, bg=self.colors["surface"], relief="flat", bd=0
        )
        header_frame.pack(fill=tk.X, pady=(0, 15))

        # Pokus o načtení loga (UMÍSTĚNO ÚPLNĚ VPRAVO)
        logo_image = self.nacti_logo("logo.png")
        if logo_image:
            logo_frame = tk.Frame(header_frame, bg=self.colors["surface"])
            logo_frame.pack(side=tk.RIGHT, padx=(0, 15), pady=10)

            logo_label = tk.Label(
                logo_frame, image=logo_image, bg=self.colors["surface"]
            )
            logo_label.pack()
            self.logo_image = logo_image

        # Titulek
        title_frame = tk.Frame(header_frame, bg=self.colors["surface"])
        title_frame.pack(
            side=tk.LEFT,
            fill=tk.X,
            expand=True,
            padx=(15, 15 if logo_image else 15),
            pady=15,
        )

        title_label = tk.Label(
            title_frame,
            text="Interpolační výpočet ozubených kol pro konfiguraci BADH",
            font=("Segoe UI", 14, "bold"),
            fg=self.colors["primary"],
            bg=self.colors["surface"],
        )
        title_label.pack(anchor=tk.W)

        # Hlavní obsah
        content_frame = tk.Frame(main_container, bg=self.colors["background"])
        content_frame.pack(fill=tk.BOTH, expand=True)
        content_frame.grid_columnconfigure(0, weight=0)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)

        # Levý panel - vstupní parametry a ovládání
        left_panel = tk.Frame(content_frame, bg=self.colors["background"])
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # Vstupní parametry v kartě
        input_card = ttk.Labelframe(
            left_panel, text=" Vstupní parametry ", style="Card.TLabelframe"
        )
        input_card.pack(fill=tk.X, pady=(0, 15), padx=5, ipady=5)

        params = [
            ("Počet zubů velkého kola (Zo):", "zo_var", "80"),
            ("Počet zubů pastorku (Zp):", "zp_var", "30"),
            ("Modul (m):", "m_var", "2.0"),
            ("Tolerance:", "tolerance_var", "0.003"),
            ("Krok interpolace (°):", "krok_var", "0.001"),
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

        # Tlačítka
        button_card = ttk.Labelframe(
            left_panel, text=" Ovládání ", style="Card.TLabelframe"
        )
        button_card.pack(fill=tk.X, pady=(0, 15), padx=5, ipady=5)

        button_frame = tk.Frame(button_card, bg=self.colors["surface"])
        button_frame.pack(padx=15, pady=10)

        self.vypocitat_btn = tk.Button(
            button_frame,
            text="🚀 Spustit výpočet",
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
            text="🗑️ Vymazat výsledky",
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
            left_panel, text=" Průběh ", style="Card.TLabelframe"
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
            text="Připraveno",
            font=("Segoe UI", 9),
            fg=self.colors["text_light"],
            bg=self.colors["surface"],
        )
        self.progress_label.pack()

        # Pravý panel - výsledky
        right_panel = tk.Frame(content_frame, bg=self.colors["background"])
        right_panel.grid(row=0, column=1, sticky="nsew")

        vysledky_card = ttk.Labelframe(
            right_panel, text=" Výsledky ", style="Card.TLabelframe"
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

        # Footer s autory
        footer_frame = tk.Frame(self.root, bg=self.colors["primary"], height=40)
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X)
        footer_frame.pack_propagate(False)

        footer_content = tk.Frame(footer_frame, bg=self.colors["primary"])
        footer_content.place(relx=0.5, rely=0.5, anchor="center")

        author_label = tk.Label(
            footer_content,
            text="Vypracoval: Malý Vratislav a Karel Vondráček",
            font=("Segoe UI", 10),
            fg="white",
            bg=self.colors["primary"],
        )
        author_label.pack()

    def vloz_obrazek_do_textu(self):
        """Vloží schematický obrázek do textového pole výsledků"""
        schema_image = self.nacti_schema_obrazek(
            "schema.png"
        )  # nebo jiný název souboru
        if schema_image:
            # Uložíme referenci na obrázek, aby se nesmazal z paměti
            self.schema_image = schema_image

            # Vložíme obrázek do textového pole
            self.vysledky_text.image_create(tk.END, image=schema_image)
            self.vysledky_text.insert(tk.END, "\n\n\n")  # Více prostoru pod obrázkem

    def validuj_vstupy(self):
        try:
            zo = int(self.zo_var.get())
            zp = int(self.zp_var.get())
            m = float(self.m_var.get())
            tolerance = float(self.tolerance_var.get())
            krok = float(self.krok_var.get())

            if zo <= 0 or zp <= 0:
                raise ValueError("Počty zubů musí být kladné")
            if m <= 0:
                raise ValueError("Modul musí být kladný")
            if tolerance <= 0:
                raise ValueError("Tolerance musí být kladná")
            if krok <= 0:
                raise ValueError("Krok musí být kladný")

            return zo, zp, m, tolerance, krok
        except ValueError as e:
            messagebox.showerror("Chyba vstupu", f"Neplatný vstup: {e}")
            return None

    def update_progress(self, value):
        self.progress["value"] = value
        self.progress_label.config(text=f"Zpracováno: {value:.1f}%")
        self.root.update_idletasks()

    def spust_vypocet(self):
        vstup = self.validuj_vstupy()
        if not vstup:
            return

        zo, zp, m, tolerance, krok = vstup

        self.vypocitat_btn.config(state="disabled")
        self.progress["value"] = 0
        self.progress_label.config(text="Spouštím výpočet...")
        self.vysledky_text.delete(1.0, tk.END)

        def vypocet_thread():
            try:
                self.vypocet.Zo = zo
                self.vypocet.Zp = zp
                self.vypocet.m = m
                self.vypocet.tolerance = tolerance

                # Výpočet limitních úhlů
                alfa_max, L1_max, L2_max, LC_max = (
                    self.vypocet.vypocet_limitniho_uhlu_max()
                )
                alfa_min, L1_min, L2_min, LC_min = (
                    self.vypocet.vypocet_limitniho_uhlu_min()
                )

                # HLAVIČKA S OBRÁZKEM
                self.vysledky_text.insert(
                    tk.END,
                    "═══════════════════════════════════════════════════════════════\n",
                )
                self.vysledky_text.insert(
                    tk.END, "           INTERPOLAČNÍ VÝPOČET OZUBENÝCH KOL\n"
                )
                self.vysledky_text.insert(tk.END, "           PRO KONFIGURACI BADH\n")
                self.vysledky_text.insert(
                    tk.END,
                    "═══════════════════════════════════════════════════════════════\n\n",
                )

                self.vysledky_text.insert(tk.END, f"📊 VSTUPNÍ PARAMETRY:\n")
                self.vysledky_text.insert(
                    tk.END, f"    • Počet zubů velkého kola (Zo): {zo}\n"
                )
                self.vysledky_text.insert(
                    tk.END, f"    • Počet zubů pastorku (Zp): {zp}\n"
                )
                self.vysledky_text.insert(tk.END, f"    • Modul (m): {m}\n")
                self.vysledky_text.insert(tk.END, f"    • Tolerance: ±{tolerance}\n")
                self.vysledky_text.insert(
                    tk.END, f"    • Krok interpolace: {krok}°\n\n"
                )

                self.vysledky_text.insert(tk.END, f"🎯 INTERVAL PRO INTERPOLACI:\n")
                self.vysledky_text.insert(tk.END, f"    • α_min = {alfa_min:.6f}°\n")
                self.vysledky_text.insert(tk.END, f"    • α_max = {alfa_max:.6f}°\n\n")

                # VLOŽENÍ SCHEMATICKÉHO OBRÁZKU - VYSVĚTLENÍ ÚHLŮ
                self.vysledky_text.insert(tk.END, "📐 SCHÉMA GEOMETRIE:\n\n")
                self.vloz_obrazek_do_textu()

                self.vysledky_text.insert(
                    tk.END, "⚙️  Probíhá interpolace, prosím čekejte...\n\n"
                )
                self.root.update_idletasks()

                # Interpolace
                dobra_reseni = self.vypocet.interpolace_v_intervalu(
                    alfa_min, alfa_max, krok, self.update_progress
                )

                # Zobrazení výsledků
                if not dobra_reseni:
                    self.vysledky_text.insert(
                        tk.END, "❌ VÝSLEDEK: Nebyla nalezena žádná dobrá řešení!\n"
                    )
                    self.vysledky_text.insert(
                        tk.END, "    Zkuste změnit toleranci nebo parametry.\n"
                    )
                else:
                    self.vysledky_text.insert(
                        tk.END, f"✅ NALEZENO {len(dobra_reseni)} ŘEŠENÍ:\n"
                    )
                    self.vysledky_text.insert(
                        tk.END,
                        "───────────────────────────────────────────────────────────────\n\n",
                    )

                    for i, r in enumerate(dobra_reseni, 1):
                        self.vysledky_text.insert(tk.END, f"🔸 ŘEŠENÍ #{i}:\n")
                        self.vysledky_text.insert(
                            tk.END, f"    α = {r['alfa_deg']:.5f}°\n"
                        )
                        self.vysledky_text.insert(
                            tk.END,
                            f"    β = {r['beta_deg']:.3f}°, γ = {r['gamma_deg']:.3f}°, ε = {r['epsilon_deg']:.3f}°\n",
                        )
                        self.vysledky_text.insert(
                            tk.END, f"    φ finální = {r['phi_final_deg']:.3f}°\n"
                        )
                        self.vysledky_text.insert(
                            tk.END,
                            f"    Dělení = {r['vysledek_deleni']:.6f} ({r['typ_reseni']})\n\n",
                        )

                self.progress["value"] = 100
                self.progress_label.config(text="Výpočet dokončen ✅")

            except Exception as e:
                messagebox.showerror("Chyba výpočtu", f"Došlo k chybě: {e}")
                self.progress_label.config(text="Chyba výpočtu ❌")
            finally:
                self.vypocitat_btn.config(state="normal")

        # Spuštění výpočtu v separátním vlákně
        thread = threading.Thread(target=vypocet_thread)
        thread.daemon = True
        thread.start()

    def vymaz_vysledky(self):
        self.vysledky_text.delete(1.0, tk.END)
        self.progress["value"] = 0
        self.progress_label.config(text="Připraveno")


if __name__ == "__main__":
    root = tk.Tk()
    app = OzubenaKolaGUI(root)
    root.mainloop()
