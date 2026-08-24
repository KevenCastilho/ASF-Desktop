"""Main application shell — polished Tkinter chrome."""
from __future__ import annotations

import tkinter as tk

from ui.theme import palette, apply_ttk, FONT_UI_BOLD, FONT_SMALL, FONT_UI, FONT_TINY, apply_widget_tree
from ui.components import widgets as W
from ui.components.controls import ThemedRadioGroup
from ui.icons.lucide import LucideIcon, icon_button
from ui.components.chrome import FlatScrollbar
from ui.screens.home import HomeScreen
from ui.screens.bots import BotsScreen
from ui.screens.settings_screen import SettingsScreen
from ui.screens.setup import SetupScreen
from ui.screens.activity import ActivityScreen
from ui.screens.tools import ToolsScreen
from ui.screens.console_screen import ConsoleScreen
from ui.screens.bot_details import BotDetailsScreen
from ui.screens.bgr import BgrScreen
from ui.screens.redeem import RedeemScreen
from ui.screens.mass_editor import MassEditorScreen
from ui.screens.inventory import InventoryScreen
from ui.screens.help_screens import (
    HelpDesktopScreen, ManualDesktopScreen, HelpAsfScreen, ManualAsfScreen,
)
from ui.screens.new_bot_wizard import NewBotWizard
from ui.screens.asf_global_config import AsfGlobalConfigScreen
from ui.screens.configure_bot import ConfigureBotScreen
from ui.screens.import_export import ImportExportScreen
from ui.screens.plugins_screen import PluginsScreen
from ui.screens.logs_manager import LogsManagerScreen
from ui.screens.desktop_update import DesktopUpdateScreen
from ui.tray_support import TrayHelper
from ui.input_popup import show_input_popup


class AsfDesktopApp:
    def __init__(self, settings, process_mgr, ipc) -> None:
        self.settings = settings
        self.process_mgr = process_mgr
        self.ipc = ipc
        self.root = tk.Tk()
        self.root.title("ASF Desktop")
        self.root.geometry(settings.get("geometry") or "1100x700")
        self.root.minsize(960, 600)

        self.colors = palette(settings.get("theme", "system"))
        self.root.configure(bg=self.colors["bg"])
        apply_ttk(self.root, self.colors)

        self._nav_stack: list[str] = []
        self._screens: dict[str, tk.Frame] = {}
        self._current = ""
        self.drawer_open = False
        self._input_busy = False
        self._sync_ipc_password()

        self._build_shell()
        self._bind_close()
        self.process_mgr.add_input_listener(self._on_asf_input)

        if not (settings.get("asf_path") or "").strip():
            self.show("setup", push=False)
        else:
            self.show("home", push=False)

        self._update_mode_badge()
        self._poll_status()
        self.tray = TrayHelper(self)

    def _build_shell(self) -> None:
        c = self.colors
        # ── Top bar ──
        self.top = tk.Frame(self.root, bg=c["header"], height=48)
        self.top.pack(fill="x")
        self.top.pack_propagate(False)
        tk.Frame(self.root, bg=c["border"], height=1).pack(fill="x")

        self.btn_menu = icon_button(self.top, "menu", c, command=self.toggle_drawer, size=18, bg=c["header"])
        self.btn_menu.pack(side="left", padx=(8, 4), pady=6)

        self.lbl_title = tk.Label(
            self.top, text="ASF Desktop", bg=c["header"], fg=c["fg"], font=FONT_UI_BOLD,
        )
        self.lbl_title.pack(side="left", padx=4)

        self.lbl_live = tk.Label(
            self.top, text="", bg=c["header"], fg=c["muted"], font=FONT_SMALL,
        )
        self.lbl_live.pack(side="left", padx=12)
        self.lbl_mode = tk.Label(
            self.top, text="", bg=c["header"], fg=c["accent"], font=FONT_SMALL,
        )
        self.lbl_mode.pack(side="left", padx=8)

        self.btn_settings = icon_button(self.top, "settings", c, command=lambda: self.show("settings"), size=18, bg=c["header"])
        self.btn_settings.pack(side="right", padx=(4, 10), pady=6)

        self.btn_back = tk.Button(
            self.top, text=" Voltar", command=self.go_back,
            bg=c["header"], fg=c["muted"], activebackground=c["card_hover"],
            activeforeground=c["fg"], relief="flat", cursor="hand2",
            font=FONT_SMALL, bd=0, padx=6, pady=4,
        )
        self._back_icon = icon_button(self.top, "back", c, command=self.go_back, size=16, bg=c["header"], color=c["muted"])

        # ── Body ──
        self.body = tk.Frame(self.root, bg=c["bg"])
        self.body.pack(fill="both", expand=True)
        self.content = tk.Frame(self.body, bg=c["bg"])
        self.content.pack(fill="both", expand=True)

        self.drawer = tk.Frame(self.body, bg=c["card"], width=c["drawer_w"])
        self.drawer.pack_propagate(False)
        self._build_drawer()

        # ── Status bar ──
        tk.Frame(self.root, bg=c["border"], height=1).pack(fill="x", side="bottom")
        self.status = tk.Frame(self.root, bg=c["status_bar"], height=30)
        self.status.pack(fill="x", side="bottom")
        self.status.pack_propagate(False)
        self.lbl_status = tk.Label(
            self.status, text="ASF: —", bg=c["status_bar"], fg=c["muted"],
            font=FONT_SMALL, anchor="w",
        )
        self.lbl_status.pack(fill="x", padx=14, pady=4)

        # Lazy: só registra classes — instancia na primeira visita (troca instantânea)
        self._screen_classes = {
            "home": HomeScreen, "bots": BotsScreen, "settings": SettingsScreen,
            "setup": SetupScreen, "activity": ActivityScreen, "tools": ToolsScreen,
            "console": ConsoleScreen, "bot_details": BotDetailsScreen,
            "bgr": BgrScreen, "redeem": RedeemScreen, "mass_editor": MassEditorScreen,
            "inventory": InventoryScreen,
            "help_desktop": HelpDesktopScreen, "manual_desktop": ManualDesktopScreen,
            "help_asf": HelpAsfScreen, "manual_asf": ManualAsfScreen,
            "new_bot": NewBotWizard, "asf_global": AsfGlobalConfigScreen,
            "configure_bot": ConfigureBotScreen, "import_export": ImportExportScreen,
            "plugins": PluginsScreen, "logs": LogsManagerScreen,
            "desktop_update": DesktopUpdateScreen,
        }
        self._screens = {}

    def _build_drawer(self) -> None:
        c = self.colors
        # header fixo
        hdr = tk.Frame(self.drawer, bg=c["card"])
        hdr.pack(fill="x")
        tk.Label(
            hdr, text="ASF Desktop", bg=c["card"], fg=c["fg"], font=FONT_UI_BOLD,
        ).pack(anchor="w", padx=18, pady=(18, 4))
        tk.Label(
            hdr, text="Navegação", bg=c["card"], fg=c["dim"], font=FONT_SMALL,
        ).pack(anchor="w", padx=18, pady=(0, 10))
        W.separator(self.drawer, c).pack(fill="x")

        # Viewport: altura limitada pelo place(relheight=1) do drawer
        self._drawer_viewport = tk.Frame(self.drawer, bg=c["card"])
        self._drawer_viewport.pack(fill="both", expand=True)

        self._drawer_canvas = tk.Canvas(
            self._drawer_viewport, bg=c["card"], highlightthickness=0, bd=0,
        )
        self._drawer_sb = FlatScrollbar(
            self._drawer_viewport, command=self._drawer_canvas.yview, colors=c, width=8,
        )
        self._drawer_inner = tk.Frame(self._drawer_canvas, bg=c["card"])
        self._drawer_win = self._drawer_canvas.create_window(
            (0, 0), window=self._drawer_inner, anchor="nw",
        )
        self._drawer_canvas.configure(yscrollcommand=self._drawer_sb_set)
        # canvas preenche o viewport; scrollbar some/aparece à direita
        self._drawer_canvas.pack(side="left", fill="both", expand=True)

        self._drawer_inner.bind("<Configure>", lambda e: self._drawer_on_inner_configure())
        self._drawer_canvas.bind("<Configure>", lambda e: self._drawer_on_canvas_configure(e))
        self._drawer_viewport.bind("<Configure>", lambda e: self._drawer_refresh_scroll())
        self.drawer.bind("<Configure>", lambda e: self._drawer_refresh_scroll())

        self._drawer_canvas.bind("<Enter>", lambda e: self._drawer_bind_wheel(True))
        self._drawer_canvas.bind("<Leave>", lambda e: self._drawer_bind_wheel(False))
        self._drawer_inner.bind("<Enter>", lambda e: self._drawer_bind_wheel(True))

        groups = [
            ("Principal", [
                ("home", "Início", "home"),
                ("bot", "Bots", "bots"),
                ("activity", "Atividade", "activity"),
                ("package", "Inventário", "inventory"),
            ]),
            ("Operação", [
                ("ticket", "BGR", "bgr"),
                ("key", "Redeem", "redeem"),
                ("pencil", "Mass Editor", "mass_editor"),
                ("wrench", "Ferramentas", "tools"),
                ("terminal", "Console", "console"),
                ("inbox", "Importar / Exportar", "import_export"),
                ("puzzle", "Plugins", "plugins"),
                ("file", "Logs", "logs"),
                ("refresh", "Update Desktop", "desktop_update"),
            ]),
            ("Sistema", [
                ("sliders", "Config global ASF", "asf_global"),
                ("settings", "Configurações", "settings"),
                ("help", "Ajuda Desktop", "help_desktop"),
                ("book", "Manual Desktop", "manual_desktop"),
                ("help", "Ajuda ASF", "help_asf"),
                ("book", "Manual ASF", "manual_asf"),
            ]),
        ]
        # D-02: Simple ≠ esconder menu — mesma navegação; densidade muda nas telas
        for title, items in groups:
            tk.Label(
                self._drawer_inner, text=title.upper(), bg=c["card"], fg=c["dim"],
                font=FONT_TINY,
            ).pack(anchor="w", padx=18, pady=(12, 4))
            for icon_name, label, route in items:
                row = tk.Frame(self._drawer_inner, bg=c["card"], cursor="hand2")
                row.pack(fill="x", padx=8, pady=1)
                ic = LucideIcon(row, icon_name, c, size=18)
                ic.pack(side="left", padx=(10, 10), pady=6)
                lbl = tk.Label(
                    row, text=label, bg=c["card"], fg=c["fg_secondary"],
                    font=FONT_UI, anchor="w", cursor="hand2",
                )
                lbl.pack(side="left", fill="x", expand=True, pady=6)

                def _enter(e, r=row, i=ic, l=lbl, col=c):
                    r.configure(bg=col["card_hover"])
                    i.configure(bg=col["card_hover"])
                    i.redraw(col["fg"])
                    l.configure(bg=col["card_hover"], fg=col["fg"])

                def _leave(e, r=row, i=ic, l=lbl, col=c):
                    r.configure(bg=col["card"])
                    i.configure(bg=col["card"])
                    i.redraw(col["fg_secondary"])
                    l.configure(bg=col["card"], fg=col["fg_secondary"])

                def _click(e, r=route):
                    self._drawer_nav(r)

                for w in (row, ic, lbl):
                    w.bind("<Enter>", _enter)
                    w.bind("<Leave>", _leave)
                    w.bind("<Button-1>", _click)

        W.separator(self._drawer_inner, c).pack(fill="x", pady=(12, 8))
        tk.Label(
            self._drawer_inner, text="INTERFACE", bg=c["card"], fg=c["dim"], font=FONT_TINY,
        ).pack(anchor="w", padx=18)
        self.mode_var = tk.StringVar(value=self.settings.get("mode", "simple"))
        mode_fr = tk.Frame(self._drawer_inner, bg=c["card"])
        mode_fr.pack(fill="x", padx=14, pady=(4, 16))
        ThemedRadioGroup(
            mode_fr, c,
            [("Simples", "simple"), ("Avançado", "advanced")],
            variable=self.mode_var,
            command=lambda: self.root.after_idle(self._set_mode),
            style="chip",
        ).pack(anchor="w")

    def _drawer_sb_set(self, first, last) -> None:
        try:
            self._drawer_sb.set(first, last)
        except Exception:
            pass
        self._drawer_sync_sb_visibility(first, last)

    def _drawer_sync_sb_visibility(self, first=None, last=None) -> None:
        try:
            self._drawer_canvas.update_idletasks()
            bbox = self._drawer_canvas.bbox("all")
            view_h = max(int(self._drawer_canvas.winfo_height()), 1)
            content_h = (bbox[3] - bbox[1]) if bbox else 0
            if first is not None and last is not None:
                need = float(first) > 0.001 or float(last) < 0.999
            else:
                need = content_h > view_h + 2
            mapped = bool(self._drawer_sb.winfo_ismapped())
            if need and not mapped:
                self._drawer_canvas.pack_forget()
                self._drawer_sb.pack(side="right", fill="y", pady=2, padx=(0, 2))
                self._drawer_canvas.pack(side="left", fill="both", expand=True)
            elif not need and mapped:
                self._drawer_sb.pack_forget()
                self._drawer_canvas.yview_moveto(0)
        except Exception:
            pass

    def _drawer_on_inner_configure(self) -> None:
        try:
            self._drawer_canvas.configure(scrollregion=self._drawer_canvas.bbox("all"))
            self._drawer_refresh_scroll()
        except Exception:
            pass

    def _drawer_on_canvas_configure(self, e) -> None:
        try:
            self._drawer_canvas.itemconfigure(self._drawer_win, width=max(int(e.width), 1))
            self._drawer_refresh_scroll()
        except Exception:
            pass

    def _drawer_refresh_scroll(self) -> None:
        try:
            self._drawer_canvas.update_idletasks()
            bbox = self._drawer_canvas.bbox("all")
            if bbox:
                self._drawer_canvas.configure(scrollregion=bbox)
            self._drawer_sync_sb_visibility()
        except Exception:
            pass

    def _drawer_bind_wheel(self, on: bool) -> None:
        if on:
            self._drawer_canvas.bind_all("<MouseWheel>", self._drawer_wheel)
            self._drawer_canvas.bind_all("<Button-4>", self._drawer_wheel)
            self._drawer_canvas.bind_all("<Button-5>", self._drawer_wheel)
        else:
            try:
                self._drawer_canvas.unbind_all("<MouseWheel>")
                self._drawer_canvas.unbind_all("<Button-4>")
                self._drawer_canvas.unbind_all("<Button-5>")
            except Exception:
                pass

    def _drawer_wheel(self, e) -> None:
        if not getattr(self, "drawer_open", False):
            return
        try:
            # só rola se houver overflow
            bbox = self._drawer_canvas.bbox("all")
            if not bbox:
                return
            if (bbox[3] - bbox[1]) <= self._drawer_canvas.winfo_height() + 1:
                return
            if hasattr(e, "delta") and e.delta:
                self._drawer_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
            elif getattr(e, "num", None) == 4:
                self._drawer_canvas.yview_scroll(-1, "units")
            elif getattr(e, "num", None) == 5:
                self._drawer_canvas.yview_scroll(1, "units")
        except Exception:
            pass


    def _set_mode(self) -> None:
        """Troca simples/avançado sem destruir a UI inteira (evita gaveta vazia)."""
        if getattr(self, "_mode_switching", False):
            return
        self._mode_switching = True
        try:
            mode = (self.mode_var.get() or "simple").strip().lower()
            if mode not in ("simple", "advanced"):
                mode = "simple"
            prev = (self.settings.get("mode") or "simple").strip().lower()
            self.settings.set("mode", mode)
            self.settings.save()
            if mode == prev:
                return

            cur = self._current or "home"
            was_open = bool(self.drawer_open)
            # reconstrói só a gaveta
            try:
                for child in list(self.drawer.winfo_children()):
                    child.destroy()
            except Exception:
                pass
            self._build_drawer()

            # recria só a tela atual (não todas)
            if cur in self._screens:
                try:
                    self._screens[cur].place_forget()
                    self._screens[cur].destroy()
                except Exception:
                    pass
                self._screens.pop(cur, None)
            self._current = ""
            self.show(cur, push=False)

            if was_open:
                self.open_drawer()
                self.root.after(50, self._drawer_refresh_scroll)
                self.root.after(200, self._drawer_refresh_scroll)

            try:
                self._update_mode_badge()
            except Exception:
                pass
        finally:
            self._mode_switching = False

    def _update_mode_badge(self) -> None:
        mode = (self.settings.get("mode") or "simple").strip().lower()
        label = "Avançado" if mode == "advanced" else "Simples"
        try:
            self.lbl_mode.config(text=f"· {label}")
            self.lbl_status.config(text=f"Interface: {label}")
        except Exception:
            pass

    def _drawer_nav(self, route: str) -> None:
        self.close_drawer()
        self.show(route)

    def toggle_drawer(self) -> None:
        if self.drawer_open:
            self.close_drawer()
        else:
            self.open_drawer()

    def open_drawer(self) -> None:
        w = int(self.colors.get("drawer_w", 300))
        self.drawer.place(x=0, y=0, relheight=1, width=w)
        self.drawer.lift()
        # dim overlay
        if not hasattr(self, "_dim") or self._dim is None:
            self._dim = tk.Frame(self.body, bg="#000000")
            try:
                self._dim.configure(bg="#000000")
            except Exception:
                pass
            self._dim.bind("<Button-1>", lambda e: self.close_drawer())
        self._dim.place(x=w, y=0, relheight=1, relwidth=1)
        try:
            self._dim.lift()
            # fake transparency via place under drawer? drawer already lifted
            self.drawer.lift()
        except Exception:
            pass
        self.drawer_open = True
        def _fix_drawer_layout():
            try:
                self._drawer_canvas.update_idletasks()
                w = max(self._drawer_canvas.winfo_width(), int(self.colors.get("drawer_w", 300)) - 16)
                self._drawer_canvas.itemconfigure(self._drawer_win, width=w)
                self._drawer_refresh_scroll()
            except Exception:
                pass
        for ms in (1, 30, 100, 250, 500):
            self.root.after(ms, _fix_drawer_layout)


    def close_drawer(self) -> None:
        self.drawer.place_forget()
        if hasattr(self, "_dim"):
            self._dim.place_forget()
        self.drawer_open = False

    def show(self, name: str, push: bool = True, **kwargs) -> None:
        if name not in getattr(self, "_screen_classes", {}) and name not in self._screens:
            return
        if push and self._current and self._current != name:
            self._nav_stack.append(self._current)
        prev = self._current
        self._current = name

        titles = {
            "home": "ASF Desktop", "bots": "Bots", "settings": "Configurações",
            "setup": "Configuração inicial", "activity": "Atividade",
            "tools": "Ferramentas", "console": "Console",
            "bot_details": kwargs.get("bot_name", "Bot"),
            "bgr": "BGR", "redeem": "Redeem", "mass_editor": "Mass Editor",
            "inventory": "Inventário", "help_desktop": "Ajuda Desktop",
            "manual_desktop": "Manual Desktop", "help_asf": "Ajuda ASF",
            "manual_asf": "Manual ASF", "new_bot": "Novo bot",
            "asf_global": "Config global ASF", "configure_bot": "Configurar bot",
            "import_export": "Importar / Exportar", "plugins": "Plugins",
            "logs": "Logs", "desktop_update": "Update Desktop",
        }
        self.lbl_title.config(text=titles.get(name, name))
        if self._nav_stack:
            self.btn_back.pack(side="right", before=self.btn_settings, padx=(0, 4))
            self._back_icon.pack(side="right", before=self.btn_back, padx=(4, 0))
        else:
            self.btn_back.pack_forget()
            try:
                self._back_icon.pack_forget()
            except Exception:
                pass

        # esconde a tela anterior de verdade (evita widgets "fantasma")
        if prev and prev in self._screens and prev != name:
            try:
                self._screens[prev].place_forget()
            except Exception:
                pass

        if name not in self._screens:
            cls = self._screen_classes[name]
            fr = cls(self.content, self)
            self._screens[name] = fr
        else:
            fr = self._screens[name]

        fr.place(relx=0, rely=0, relwidth=1, relheight=1)
        fr.lift()

        # dados: idle, nunca bloqueia o paint
        if hasattr(fr, "on_show"):
            self.root.after_idle(lambda f=fr, k=dict(kwargs): self._safe_on_show(f, k))

    def _safe_on_show(self, fr, kwargs: dict) -> None:
        try:
            fr.on_show(**kwargs)
        except Exception:
            pass




    def apply_theme(self, theme_name: str | None = None) -> None:
        """ reconstrução TOTAL do shell — única forma confiável no Tk. """
        if theme_name is not None:
            theme_name = str(theme_name).strip().lower()
            if theme_name not in ("light", "dark", "system"):
                theme_name = "system"
            self.settings.set("theme", theme_name)
            self.settings.save()

        name = str(self.settings.get("theme") or "system").strip().lower()
        if name not in ("light", "dark", "system"):
            name = "system"

        self.colors = palette(name)
        apply_ttk(self.root, self.colors)
        self.root.configure(bg=self.colors["bg"])
        self.root.title(f"ASF Desktop  [{name}]")

        # preservar navegação
        cur = self._current or "home"
        stack = list(self._nav_stack)

        # destruir TUDO que está no root (top, body, status, separadores)
        for child in list(self.root.winfo_children()):
            try:
                child.destroy()
            except Exception:
                pass

        self._screens.clear()
        self.drawer_open = False
        if hasattr(self, "_dim"):
            try:
                del self._dim
            except Exception:
                pass

        # montar shell de novo com self.colors atual
        self._build_shell()
        self._bind_close()

        self._nav_stack = stack
        self._current = ""
        self.show(cur, push=False)


    def go_back(self) -> None:
        if not self._nav_stack:
            return
        prev = self._nav_stack.pop()
        self.show(prev, push=False)

    def _bind_close(self) -> None:
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self) -> None:
        if self.settings.get("close_behavior", "tray") == "tray" and self.tray.available:
            self.root.withdraw()
            return
        self._shutdown()

    def _shutdown(self) -> None:
        # some imediatamente — limpeza em paralelo curta
        try:
            self.root.withdraw()
        except Exception:
            pass
        if self.settings.get("remember_geometry"):
            try:
                self.settings.set("geometry", self.root.geometry())
                self.settings.save()
            except Exception:
                pass
        try:
            self.tray.stop()
        except Exception:
            pass

        def cleanup():
            try:
                # timeout já é baixo no cliente IPC
                self.ipc.exit_asf()
            except Exception:
                pass
            try:
                self.process_mgr.stop(reason="shutdown")
            except Exception:
                pass

        import threading
        threading.Thread(target=cleanup, daemon=True).start()
        try:
            self.root.destroy()
        except Exception:
            pass

    def _sync_ipc_password(self) -> None:
        try:
            from integration.asf_config import read_ipc_password
            pwd = read_ipc_password(self.settings.get("asf_path") or "")
            if pwd:
                self.settings.set("ipc_password", pwd)
        except Exception:
            pass

    def exit_app(self) -> None:
        self._shutdown()

    def _on_asf_input(self, req) -> None:
        if self._input_busy:
            return
        self._input_busy = True

        def submit(val: str) -> None:
            self._input_busy = False
            bot = req.bot_name or "ASF"
            from integration.input_types import types_to_try
            order = []
            if getattr(req, "input_type", None):
                order.append(req.input_type)
            for t in types_to_try(getattr(req, "message", "") or ""):
                if t not in order:
                    order.append(t)
            for t in order:
                r = self.ipc.input_command(bot, t, val)
                if r.ok:
                    try:
                        from ui.notify import notify
                        notify(self.settings, "input_ok", f"Input aceito ({t})", bot)
                    except Exception:
                        pass
                    return
            if val.strip().lower() in ("y", "n", "yes", "no", "s", "sim", "nao", "não"):
                self.ipc.command(f"input {bot} DeviceConfirmation {val}")
            self.ipc.command(f"input {bot} SteamGuard {val}")

        try:
            self.root.after(
                0,
                lambda: show_input_popup(
                    self.root, "Entrada solicitada", req.message,
                    bot_name=req.bot_name, on_submit=submit,
                ),
            )
        except Exception:
            self._input_busy = False

    def _poll_status(self) -> None:
        import threading

        def work():
            running = self.process_mgr.is_running()
            ipc_ok = False
            bot_count = 0
            err = ""
            if running:
                r = self.ipc.get_asf()
                if r.ok:
                    ipc_ok = True
                    bot_count = len(self.ipc.bots_cached())
                    try:
                        from integration.capabilities import probe, get_cached
                        if get_cached() is None:
                            probe(self.ipc)
                    except Exception:
                        pass
                else:
                    err = self.ipc.last_error or ""
                    if r.status == 401:
                        self.root.after(0, lambda: self._apply_status(
                            "ASF: Running  ·  IPC: não autorizado", "· Unauthorized", self.colors["warn"]
                        ))
                        self.root.after(3000, self._poll_status)
                        return
            path_ok = bool((self.settings.get("asf_path") or "").strip())
            c = self.colors
            if not path_ok:
                text, live, color = "ASF: não configurado", "", c["muted"]
            elif not running:
                text, live, color = "ASF: parado", "· Stopped", c["stopped"]
            elif not ipc_ok:
                text = f"ASF: processo ok  ·  IPC: {err or 'aguardando…'}"
                live, color = "· Starting", c["warn"]
            else:
                text = f"ASF: Running  ·  Bots: {bot_count}  ·  IPC: {self.ipc.base_url}"
                live, color = "· Running", c["online"]
            self.root.after(0, lambda: self._apply_status(text, live, color))
            self.root.after(3000, self._poll_status)

        threading.Thread(target=work, daemon=True).start()

    def _apply_status(self, text: str, live: str, color: str) -> None:
        try:
            self.lbl_status.config(text=text)
            self.lbl_live.config(text=live, fg=color)
        except Exception:
            pass

    def run(self) -> None:
        self.root.mainloop()
