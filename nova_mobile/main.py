"""
Nova Launcher - Android APK
Java Minecraft Launcher (Mobile Version)
Kivy-based Android launcher
"""

import os
import json
import threading

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.spinner import Spinner
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.utils import get_color_from_hex
from kivy.animation import Animation
from kivy.metrics import dp, sp
from kivy.core.text import LabelBase

# ─── Window setup ───────────────────────────────────────────────────────────
Window.clearcolor = get_color_from_hex('#070B14')

# ─── Color palette ──────────────────────────────────────────────────────────
BG       = get_color_from_hex('#070B14')
BG2      = get_color_from_hex('#0D1120')
CARD     = get_color_from_hex('#111827')
PURPLE   = get_color_from_hex('#8B5CF6')
PURPLE_D = get_color_from_hex('#3B1F73')
CYAN     = get_color_from_hex('#22D3EE')
CYAN_D   = get_color_from_hex('#0891B2')
GOLD     = get_color_from_hex('#F59E0B')
GREEN    = get_color_from_hex('#10B981')
RED      = get_color_from_hex('#EF4444')
WHITE    = get_color_from_hex('#F8FAFC')
MUTED    = get_color_from_hex('#6B7280')
LIGHT    = get_color_from_hex('#D1D5DB')

# ─── Minecraft versions ─────────────────────────────────────────────────────
MC_VERSIONS = [
    {"id": "1.20.4", "type": "release", "desc": "Java Edition",   "color": "#10B981"},
    {"id": "1.20.1", "type": "release", "desc": "Java Edition",   "color": "#10B981"},
    {"id": "1.19.4", "type": "release", "desc": "Java Edition",   "color": "#10B981"},
    {"id": "1.18.2", "type": "release", "desc": "Java Edition",   "color": "#10B981"},
    {"id": "1.16.5", "type": "release", "desc": "Java Edition",   "color": "#10B981"},
    {"id": "1.12.2", "type": "release", "desc": "Java Edition",   "color": "#10B981"},
    {"id": "1.8.9",  "type": "release", "desc": "Java Edition",   "color": "#10B981"},
    {"id": "1.7.10", "type": "release", "desc": "Java Edition",   "color": "#10B981"},
    {"id": "1.20.4-fabric", "type": "modded", "desc": "Fabric",   "color": "#8B5CF6"},
    {"id": "1.20.1-forge",  "type": "modded", "desc": "Forge",    "color": "#F59E0B"},
    {"id": "1.20.1-optifine","type": "modded","desc": "OptiFine", "color": "#22D3EE"},
    {"id": "snapshot-24w14a","type":"snapshot","desc":"Snapshot",  "color": "#EF4444"},
]

# ─── Data store (simple JSON file) ──────────────────────────────────────────
DATA_FILE = "nova_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {
        "username": "",
        "selected_version": "1.20.4",
        "ram": "2",
        "accounts": [],
        "installed": [],
    }

def save_data(data):
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except:
        pass

APP_DATA = load_data()

# ─── Helper: styled button ──────────────────────────────────────────────────
def make_btn(text, bg_color, text_color=None, height=dp(48), radius=12, font_size=sp(14)):
    btn = Button(
        text=text,
        size_hint_y=None,
        height=height,
        font_size=font_size,
        bold=True,
        background_normal='',
        background_color=bg_color if text_color is None else (0,0,0,0),
    )
    if text_color:
        btn.color = text_color
    else:
        btn.color = WHITE
    # Draw rounded bg
    def draw_bg(instance, *args):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(*bg_color)
            RoundedRectangle(pos=instance.pos, size=instance.size, radius=[radius])
    btn.bind(pos=draw_bg, size=draw_bg)
    draw_bg(btn)
    return btn

def make_label(text, font_size=sp(13), color=None, bold=False, halign='left'):
    lbl = Label(
        text=text,
        font_size=font_size,
        color=color or LIGHT,
        bold=bold,
        halign=halign,
        valign='middle',
        size_hint_y=None,
        height=dp(36),
    )
    lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', (val[0], None)))
    return lbl

def card_widget(child_layout, padding=dp(14), bg=None):
    """Wrap a layout in a card-style container"""
    outer = FloatLayout(size_hint_y=None)
    with outer.canvas.before:
        Color(*(bg or get_color_from_hex('#111827')))
        outer._rect = RoundedRectangle(pos=outer.pos, size=outer.size, radius=[dp(16)])
    def update_rect(inst, val):
        inst._rect.pos = inst.pos
        inst._rect.size = inst.size
    outer.bind(pos=update_rect, size=update_rect)
    child_layout.pos_hint = {'x': 0, 'top': 1}
    outer.add_widget(child_layout)
    outer.height = child_layout.height + padding * 2
    return outer

# ════════════════════════════════════════════════════════════════════════════
#  SCREENS
# ════════════════════════════════════════════════════════════════════════════

# ─── HOME SCREEN ────────────────────────────────────────────────────────────
class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        root = FloatLayout()

        # Background
        with root.canvas.before:
            Color(*BG)
            self.bg_rect = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=self._upd_bg, size=self._upd_bg)

        # Scrollable content
        scroll = ScrollView(size_hint=(1, 1))
        content = BoxLayout(
            orientation='vertical',
            spacing=dp(12),
            padding=[dp(16), dp(20), dp(16), dp(20)],
            size_hint_y=None,
        )
        content.bind(minimum_height=content.setter('height'))

        # ── Header ──────────────────────────────────────────────────────────
        header = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(10))
        with header.canvas.before:
            Color(0.08, 0.10, 0.20, 0.95)
            self.hdr_rect = RoundedRectangle(pos=header.pos, size=header.size, radius=[dp(16)])
        header.bind(pos=lambda i,v: setattr(self, '_hdr_r', self._upd_rect(self.hdr_rect, i)),
                    size=lambda i,v: setattr(self, '_hdr_s', self._upd_rect(self.hdr_rect, i)))

        logo = Image(source='assets/logo.png', size_hint=(None, None), size=(dp(40), dp(40)),
                     pos_hint={'center_y': 0.5})
        hdr_info = BoxLayout(orientation='vertical', spacing=0)
        hdr_title = Label(text='NOVA LAUNCHER', font_size=sp(16), bold=True,
                          color=WHITE, halign='left', valign='middle',
                          size_hint_y=None, height=dp(26))
        hdr_title.bind(size=lambda i,v: setattr(i, 'text_size', (v[0], None)))
        hdr_sub = Label(text='Java Minecraft Edition', font_size=sp(10),
                        color=CYAN, halign='left', valign='middle',
                        size_hint_y=None, height=dp(18))
        hdr_sub.bind(size=lambda i,v: setattr(i, 'text_size', (v[0], None)))
        hdr_info.add_widget(hdr_title)
        hdr_info.add_widget(hdr_sub)
        header.add_widget(logo)
        header.add_widget(hdr_info)
        header.add_widget(Label())  # spacer

        # Status pill
        self.status_lbl = Label(
            text='● Tayyor', font_size=sp(11), bold=True, color=GREEN,
            size_hint=(None, None), size=(dp(80), dp(28)),
            halign='center', valign='middle',
        )
        header.add_widget(self.status_lbl)
        content.add_widget(header)

        # ── Hero card ───────────────────────────────────────────────────────
        hero = FloatLayout(size_hint_y=None, height=dp(200))
        with hero.canvas.before:
            Color(0.10, 0.08, 0.22, 1)
            self.hero_rect = RoundedRectangle(pos=hero.pos, size=hero.size, radius=[dp(22)])
        hero.bind(pos=lambda i,v: self._upd_rect(self.hero_rect, i),
                  size=lambda i,v: self._upd_rect(self.hero_rect, i))

        hero_logo = Image(
            source='assets/logo.png',
            size_hint=(None, None), size=(dp(100), dp(100)),
            pos_hint={'center_x': 0.5, 'center_y': 0.62},
            allow_stretch=True, keep_ratio=True,
        )
        hero.add_widget(hero_logo)

        hero_title = Label(
            text='MINECRAFT\nJAVA EDITION',
            font_size=sp(22), bold=True, color=WHITE,
            halign='center', valign='middle',
            size_hint=(1, None), height=dp(60),
            pos_hint={'x': 0, 'y': 0.0},
        )
        hero_title.bind(size=lambda i,v: setattr(i, 'text_size', (v[0], None)))
        hero.add_widget(hero_title)
        content.add_widget(hero)

        # ── Version selector ────────────────────────────────────────────────
        ver_title = make_label('🎮  Versiya tanlang', font_size=sp(14), bold=True, color=WHITE)
        ver_title.height = dp(32)
        content.add_widget(ver_title)

        self.ver_spinner = Spinner(
            text=APP_DATA.get('selected_version', '1.20.4'),
            values=[v['id'] for v in MC_VERSIONS],
            size_hint_y=None, height=dp(48),
            font_size=sp(14),
            background_normal='',
            background_color=get_color_from_hex('#1F2937'),
            color=WHITE,
            bold=True,
        )
        self.ver_spinner.bind(text=self.on_version_select)
        content.add_widget(self.ver_spinner)

        # ── RAM setting ──────────────────────────────────────────────────────
        ram_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        ram_lbl = make_label('🖥️  RAM:', font_size=sp(13), color=MUTED)
        ram_lbl.size_hint_x = 0.4
        self.ram_spinner = Spinner(
            text=APP_DATA.get('ram', '2') + ' GB',
            values=['1 GB', '2 GB', '3 GB', '4 GB', '6 GB', '8 GB'],
            size_hint_y=None, height=dp(44),
            font_size=sp(13),
            background_normal='',
            background_color=get_color_from_hex('#1F2937'),
            color=WHITE,
        )
        self.ram_spinner.bind(text=self.on_ram_change)
        ram_row.add_widget(ram_lbl)
        ram_row.add_widget(self.ram_spinner)
        content.add_widget(ram_row)

        # ── Username ─────────────────────────────────────────────────────────
        user_lbl = make_label('👤  Nikneym:', font_size=sp(13), color=MUTED)
        user_lbl.height = dp(28)
        content.add_widget(user_lbl)

        self.username_input = TextInput(
            text=APP_DATA.get('username', ''),
            hint_text='Nikneymingizni kiriting...',
            size_hint_y=None, height=dp(46),
            font_size=sp(14),
            foreground_color=WHITE,
            hint_text_color=MUTED,
            background_color=get_color_from_hex('#1F2937'),
            cursor_color=CYAN,
            padding=[dp(12), dp(12)],
            multiline=False,
        )
        self.username_input.bind(text=self.on_username_change)
        content.add_widget(self.username_input)

        # ── Quick stats cards ────────────────────────────────────────────────
        stats_row = GridLayout(cols=3, size_hint_y=None, height=dp(80), spacing=dp(8))
        stats_data = [
            ('Versiyalar', str(len(MC_VERSIONS)), CYAN),
            ('Java', 'Ready', GREEN),
            ('Online', 'Muhim', PURPLE),
        ]
        for title, val, clr in stats_data:
            card = BoxLayout(orientation='vertical', spacing=dp(2), padding=[dp(8), dp(8)])
            with card.canvas.before:
                Color(*get_color_from_hex('#111827'))
                card._r = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(12)])
            card.bind(pos=lambda i,v,r=None: self._upd_rect(i._r, i),
                      size=lambda i,v,r=None: self._upd_rect(i._r, i))
            v_lbl = Label(text=val, font_size=sp(18), bold=True, color=clr,
                          size_hint_y=None, height=dp(30), halign='center')
            t_lbl = Label(text=title, font_size=sp(10), color=MUTED,
                          size_hint_y=None, height=dp(18), halign='center')
            card.add_widget(v_lbl)
            card.add_widget(t_lbl)
            stats_row.add_widget(card)
        content.add_widget(stats_row)

        # ── Action buttons ───────────────────────────────────────────────────
        # Install button
        self.btn_install = make_btn('⬇  O\'RNATISH', get_color_from_hex('#1F2937'),
                                    height=dp(50), font_size=sp(14))
        self.btn_install.color = CYAN
        self.btn_install.bind(on_release=self.on_install)
        content.add_widget(self.btn_install)

        # Progress bar (hidden by default)
        self.progress = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(8))
        self.progress.opacity = 0
        content.add_widget(self.progress)
        self.prog_lbl = make_label('', font_size=sp(11), color=MUTED, halign='center')
        self.prog_lbl.height = dp(20)
        self.prog_lbl.opacity = 0
        content.add_widget(self.prog_lbl)

        # PLAY button
        self.btn_play = make_btn('▶  O\'YINGA KIRISH', CYAN_D,
                                  height=dp(56), radius=14, font_size=sp(16))
        self.btn_play.bind(on_release=self.on_play)
        content.add_widget(self.btn_play)

        # ── Nav buttons ──────────────────────────────────────────────────────
        nav = GridLayout(cols=3, size_hint_y=None, height=dp(64), spacing=dp(8))
        nav_items = [
            ('👤 Profil', 'profile'),
            ('📦 Modlar', 'mods'),
            ('⚙ Sozlama', 'settings'),
        ]
        for txt, scr in nav_items:
            b = make_btn(txt, get_color_from_hex('#1F2937'), height=dp(60), font_size=sp(12))
            b.color = LIGHT
            b.bind(on_release=lambda x, s=scr: self.go(s))
            nav.add_widget(b)
        content.add_widget(nav)

        content.add_widget(Label(size_hint_y=None, height=dp(20)))  # bottom spacer

        scroll.add_widget(content)
        root.add_widget(scroll)
        self.add_widget(root)

    def _upd_bg(self, inst, val):
        self.bg_rect.pos = inst.pos
        self.bg_rect.size = inst.size

    def _upd_rect(self, rect, inst):
        rect.pos = inst.pos
        rect.size = inst.size

    def on_version_select(self, spinner, text):
        APP_DATA['selected_version'] = text
        save_data(APP_DATA)

    def on_ram_change(self, spinner, text):
        APP_DATA['ram'] = text.split()[0]
        save_data(APP_DATA)

    def on_username_change(self, inp, text):
        APP_DATA['username'] = text
        save_data(APP_DATA)

    def on_install(self, btn):
        """Simulate installation progress"""
        if not APP_DATA.get('username', '').strip():
            self._show_popup('Xato', 'Avval nikneymingizni kiriting!')
            return
        version = APP_DATA.get('selected_version', '1.20.4')
        self.progress.opacity = 1
        self.prog_lbl.opacity = 1
        self.btn_install.disabled = True
        self.btn_play.disabled = True
        self._progress = 0
        self._install_version = version
        Clock.schedule_interval(self._update_progress, 0.05)

    def _update_progress(self, dt):
        self._progress += 2
        self.progress.value = min(self._progress, 100)
        ver = self._install_version
        if self._progress < 30:
            self.prog_lbl.text = f'Java yuklanmoqda... {self._progress}%'
        elif self._progress < 60:
            self.prog_lbl.text = f'Minecraft {ver} yuklanmoqda... {self._progress}%'
        elif self._progress < 90:
            self.prog_lbl.text = f'Fayllar o\'rnatilmoqda... {self._progress}%'
        else:
            self.prog_lbl.text = f'Tayyor! {self._progress}%'

        if self._progress >= 100:
            Clock.unschedule(self._update_progress)
            if ver not in APP_DATA['installed']:
                APP_DATA['installed'].append(ver)
                save_data(APP_DATA)
            self.btn_install.disabled = False
            self.btn_play.disabled = False
            self.prog_lbl.text = f'✓ {ver} o\'rnatildi!'
            self.status_lbl.text = '● Tayyor'
            self.status_lbl.color = GREEN
            Clock.schedule_once(lambda dt: self._hide_progress(), 3)
            return False

    def _hide_progress(self):
        self.progress.opacity = 0
        self.prog_lbl.opacity = 0
        self.progress.value = 0

    def on_play(self, btn):
        if not APP_DATA.get('username', '').strip():
            self._show_popup('Xato', 'Avval nikneymingizni kiriting!')
            return
        version = APP_DATA.get('selected_version', '1.20.4')
        if version not in APP_DATA.get('installed', []):
            self._show_popup('O\'rnatilmagan',
                             f'{version} versiyasi o\'rnatilmagan.\nAvval "O\'RNATISH" tugmasini bosing.')
            return
        self.status_lbl.text = '● Ishga tushirilmoqda...'
        self.status_lbl.color = GOLD
        Clock.schedule_once(lambda dt: self._launch_done(), 2)

    def _launch_done(self):
        self.status_lbl.text = '● O\'yinda'
        self.status_lbl.color = GREEN

    def _show_popup(self, title, msg):
        content = BoxLayout(orientation='vertical', spacing=dp(12), padding=dp(16))
        content.add_widget(Label(text=msg, color=LIGHT, font_size=sp(14),
                                  halign='center', valign='middle'))
        btn = make_btn('OK', CYAN_D, height=dp(44))
        content.add_widget(btn)
        popup = Popup(title=title, content=content,
                      size_hint=(0.85, None), height=dp(200),
                      background_color=get_color_from_hex('#0D1120'),
                      title_color=WHITE, title_size=sp(15))
        btn.bind(on_release=popup.dismiss)
        popup.open()

    def go(self, screen_name):
        self.manager.current = screen_name


# ─── PROFILE SCREEN ─────────────────────────────────────────────────────────
class ProfileScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        root = BoxLayout(orientation='vertical', spacing=dp(12),
                         padding=[dp(16), dp(20), dp(16), dp(16)])
        with root.canvas.before:
            Color(*BG)
            self.bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=self._upd, size=self._upd)

        # Header
        hdr = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        back = make_btn('◀', get_color_from_hex('#1F2937'), height=dp(44),
                        font_size=sp(18))
        back.size_hint_x = None
        back.width = dp(50)
        back.bind(on_release=lambda x: setattr(self.manager, 'current', 'home'))
        hdr.add_widget(back)
        hdr.add_widget(Label(text='👤  Profil', font_size=sp(18), bold=True,
                              color=WHITE, halign='left', valign='middle'))
        root.add_widget(hdr)

        scroll = ScrollView()
        content = BoxLayout(orientation='vertical', spacing=dp(14),
                            size_hint_y=None, padding=[0, 0, 0, dp(20)])
        content.bind(minimum_height=content.setter('height'))

        # Avatar
        avatar_box = BoxLayout(size_hint_y=None, height=dp(110),
                                orientation='vertical')
        avatar_lbl = Label(text='🎮', font_size=sp(60), size_hint_y=None, height=dp(80))
        content.add_widget(avatar_lbl)

        # Username display
        uname = APP_DATA.get('username', 'O\'yinchi') or 'O\'yinchi'
        content.add_widget(Label(text=uname, font_size=sp(22), bold=True,
                                  color=WHITE, size_hint_y=None, height=dp(36)))
        content.add_widget(Label(text='Offline rejim', font_size=sp(12),
                                  color=MUTED, size_hint_y=None, height=dp(24)))

        # Stats
        stats = GridLayout(cols=2, size_hint_y=None, height=dp(100), spacing=dp(10))
        installed = APP_DATA.get('installed', [])
        for title, val, clr in [
            ('O\'rnatilgan', str(len(installed)), GREEN),
            ('Tanlangan', APP_DATA.get('selected_version', '—'), CYAN),
            ('RAM', APP_DATA.get('ram', '2') + ' GB', PURPLE),
            ('Mod', 'Offline', GOLD),
        ]:
            c = BoxLayout(orientation='vertical', padding=[dp(10), dp(8)])
            with c.canvas.before:
                Color(*get_color_from_hex('#111827'))
                c._r = RoundedRectangle(pos=c.pos, size=c.size, radius=[dp(12)])
            c.bind(pos=lambda i,v: self._upd_r(i), size=lambda i,v: self._upd_r(i))
            c.add_widget(Label(text=val, font_size=sp(16), bold=True, color=clr,
                                size_hint_y=None, height=dp(28)))
            c.add_widget(Label(text=title, font_size=sp(10), color=MUTED,
                                size_hint_y=None, height=dp(18)))
            stats.add_widget(c)
        content.add_widget(stats)

        # Installed versions list
        if installed:
            content.add_widget(make_label('📦  O\'rnatilgan versiyalar:', font_size=sp(13),
                                           bold=True, color=WHITE))
            for v in installed:
                row = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8),
                                padding=[dp(12), 0])
                with row.canvas.before:
                    Color(*get_color_from_hex('#1F2937'))
                    row._r = RoundedRectangle(pos=row.pos, size=row.size, radius=[dp(10)])
                row.bind(pos=lambda i,v2: self._upd_r(i), size=lambda i,v2: self._upd_r(i))
                row.add_widget(Label(text=f'✓  {v}', font_size=sp(13), color=GREEN,
                                      halign='left', valign='middle'))
                content.add_widget(row)

        content.add_widget(Label(size_hint_y=None, height=dp(20)))
        scroll.add_widget(content)
        root.add_widget(scroll)
        self.add_widget(root)

    def _upd(self, inst, val):
        self.bg.pos = inst.pos
        self.bg.size = inst.size

    def _upd_r(self, inst):
        inst._r.pos = inst.pos
        inst._r.size = inst.size


# ─── MODS SCREEN ────────────────────────────────────────────────────────────
class ModsScreen(Screen):
    MODS = [
        {"name": "OptiFine", "desc": "FPS boost + shaders", "cat": "Performance", "clr": "#22D3EE"},
        {"name": "Fabric API", "desc": "Fabric mod loader", "cat": "Loader", "clr": "#8B5CF6"},
        {"name": "Sodium", "desc": "Rendering optimization", "cat": "Performance", "clr": "#10B981"},
        {"name": "JEI", "desc": "Just Enough Items", "cat": "Utility", "clr": "#F59E0B"},
        {"name": "Iris Shaders", "desc": "Beautiful shaders", "cat": "Visual", "clr": "#EF4444"},
        {"name": "Forge", "desc": "Forge mod loader", "cat": "Loader", "clr": "#F59E0B"},
        {"name": "Litematica", "desc": "Blueprint building", "cat": "Utility", "clr": "#10B981"},
        {"name": "MiniHUD", "desc": "HUD overlay info", "cat": "Utility", "clr": "#22D3EE"},
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        root = BoxLayout(orientation='vertical', spacing=dp(10),
                         padding=[dp(16), dp(20), dp(16), dp(16)])
        with root.canvas.before:
            Color(*BG)
            self.bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=self._upd, size=self._upd)

        # Header
        hdr = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        back = make_btn('◀', get_color_from_hex('#1F2937'), height=dp(44), font_size=sp(18))
        back.size_hint_x = None
        back.width = dp(50)
        back.bind(on_release=lambda x: setattr(self.manager, 'current', 'home'))
        hdr.add_widget(back)
        hdr.add_widget(Label(text='📦  Modlar', font_size=sp(18), bold=True,
                              color=WHITE, halign='left', valign='middle'))
        root.add_widget(hdr)

        subtitle = make_label('Modrinth dan eng mashhur modlar', font_size=sp(11), color=MUTED)
        subtitle.height = dp(24)
        root.add_widget(subtitle)

        scroll = ScrollView()
        content = BoxLayout(orientation='vertical', spacing=dp(10),
                            size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))

        for mod in self.MODS:
            row = BoxLayout(size_hint_y=None, height=dp(72),
                            spacing=dp(10), padding=[dp(14), dp(8)])
            with row.canvas.before:
                Color(*get_color_from_hex('#111827'))
                row._r = RoundedRectangle(pos=row.pos, size=row.size, radius=[dp(14)])
            row.bind(pos=lambda i,v: self._upd_r(i), size=lambda i,v: self._upd_r(i))

            # Color indicator
            ind = BoxLayout(size_hint=(None, None), size=(dp(6), dp(40)),
                            pos_hint={'center_y': 0.5})
            with ind.canvas:
                Color(*get_color_from_hex(mod['clr']))
                RoundedRectangle(size=(dp(5), dp(40)), radius=[dp(3)])
            row.add_widget(ind)

            # Info
            info = BoxLayout(orientation='vertical', spacing=dp(2))
            name_lbl = Label(text=mod['name'], font_size=sp(14), bold=True,
                              color=WHITE, halign='left', valign='middle',
                              size_hint_y=None, height=dp(26))
            name_lbl.bind(size=lambda i,v: setattr(i, 'text_size', (v[0], None)))
            desc_lbl = Label(text=mod['desc'], font_size=sp(11), color=MUTED,
                              halign='left', valign='middle',
                              size_hint_y=None, height=dp(20))
            desc_lbl.bind(size=lambda i,v: setattr(i, 'text_size', (v[0], None)))
            cat_lbl = Label(text=mod['cat'], font_size=sp(9), bold=True,
                             color=get_color_from_hex(mod['clr']),
                             halign='left', valign='middle',
                             size_hint_y=None, height=dp(16))
            cat_lbl.bind(size=lambda i,v: setattr(i, 'text_size', (v[0], None)))
            info.add_widget(name_lbl)
            info.add_widget(desc_lbl)
            info.add_widget(cat_lbl)
            row.add_widget(info)

            # Download btn
            dl_btn = make_btn('⬇', get_color_from_hex('#1F2937'),
                               height=dp(38), font_size=sp(16))
            dl_btn.size_hint_x = None
            dl_btn.width = dp(44)
            dl_btn.color = CYAN
            dl_btn.bind(on_release=lambda x, n=mod['name']: self._on_download(n))
            row.add_widget(dl_btn)

            content.add_widget(row)

        content.add_widget(Label(size_hint_y=None, height=dp(20)))
        scroll.add_widget(content)
        root.add_widget(scroll)
        self.add_widget(root)

    def _on_download(self, name):
        content = BoxLayout(orientation='vertical', spacing=dp(12), padding=dp(16))
        content.add_widget(Label(text=f'✓ {name} yuklab olindi!', color=GREEN,
                                  font_size=sp(14), halign='center'))
        btn = make_btn('OK', CYAN_D, height=dp(44))
        content.add_widget(btn)
        popup = Popup(title='Mod', content=content,
                      size_hint=(0.8, None), height=dp(180),
                      background_color=get_color_from_hex('#0D1120'),
                      title_color=WHITE)
        btn.bind(on_release=popup.dismiss)
        popup.open()

    def _upd(self, inst, val):
        self.bg.pos = inst.pos
        self.bg.size = inst.size

    def _upd_r(self, inst):
        inst._r.pos = inst.pos
        inst._r.size = inst.size


# ─── SETTINGS SCREEN ────────────────────────────────────────────────────────
class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        root = BoxLayout(orientation='vertical', spacing=dp(12),
                         padding=[dp(16), dp(20), dp(16), dp(16)])
        with root.canvas.before:
            Color(*BG)
            self.bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=self._upd, size=self._upd)

        # Header
        hdr = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        back = make_btn('◀', get_color_from_hex('#1F2937'), height=dp(44), font_size=sp(18))
        back.size_hint_x = None
        back.width = dp(50)
        back.bind(on_release=lambda x: setattr(self.manager, 'current', 'home'))
        hdr.add_widget(back)
        hdr.add_widget(Label(text='⚙  Sozlamalar', font_size=sp(18), bold=True,
                              color=WHITE, halign='left', valign='middle'))
        root.add_widget(hdr)

        scroll = ScrollView()
        content = BoxLayout(orientation='vertical', spacing=dp(14),
                            size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))

        settings_items = [
            ('🎮  Java versiyasi', 'Java 17 (Tavsiya)', CYAN),
            ('🌐  Til', "O'zbek", GREEN),
            ('🔊  Musiqa', 'Yoqilgan', PURPLE),
            ('🎨  Tema', 'Qorong\'u (Dark)', GOLD),
            ('📁  O\'yin papkasi', '/sdcard/minecraft', MUTED),
            ('🔑  Litsenziya', 'Offline Mode', RED),
            ('📱  Nova Launcher', 'v2.5.0', LIGHT),
        ]

        for label, value, clr in settings_items:
            row = BoxLayout(size_hint_y=None, height=dp(58), spacing=dp(8),
                            padding=[dp(14), dp(8)])
            with row.canvas.before:
                Color(*get_color_from_hex('#111827'))
                row._r = RoundedRectangle(pos=row.pos, size=row.size, radius=[dp(12)])
            row.bind(pos=lambda i,v: self._upd_r(i), size=lambda i,v: self._upd_r(i))
            info = BoxLayout(orientation='vertical', spacing=dp(2))
            lbl = Label(text=label, font_size=sp(13), color=LIGHT,
                         halign='left', valign='middle',
                         size_hint_y=None, height=dp(24))
            lbl.bind(size=lambda i,v: setattr(i, 'text_size', (v[0], None)))
            val_lbl = Label(text=value, font_size=sp(11), color=clr,
                             halign='left', valign='middle',
                             size_hint_y=None, height=dp(20))
            val_lbl.bind(size=lambda i,v: setattr(i, 'text_size', (v[0], None)))
            info.add_widget(lbl)
            info.add_widget(val_lbl)
            row.add_widget(info)
            row.add_widget(Label(text='›', font_size=sp(20), color=MUTED,
                                  size_hint_x=None, width=dp(24)))
            content.add_widget(row)

        # Clear data btn
        content.add_widget(Label(size_hint_y=None, height=dp(10)))
        clear_btn = make_btn('🗑  Barcha ma\'lumotlarni tozalash',
                              get_color_from_hex('#3B0F0F'), height=dp(48))
        clear_btn.color = RED
        clear_btn.bind(on_release=self._clear_data)
        content.add_widget(clear_btn)
        content.add_widget(Label(size_hint_y=None, height=dp(20)))

        scroll.add_widget(content)
        root.add_widget(scroll)
        self.add_widget(root)

    def _clear_data(self, btn):
        global APP_DATA
        APP_DATA = {"username": "", "selected_version": "1.20.4",
                    "ram": "2", "accounts": [], "installed": []}
        save_data(APP_DATA)
        content = BoxLayout(orientation='vertical', spacing=dp(12), padding=dp(16))
        content.add_widget(Label(text='✓ Ma\'lumotlar tozalandi!', color=GREEN,
                                  font_size=sp(14), halign='center'))
        btn2 = make_btn('OK', CYAN_D, height=dp(44))
        content.add_widget(btn2)
        popup = Popup(title='Tozalandi', content=content,
                      size_hint=(0.8, None), height=dp(180),
                      background_color=get_color_from_hex('#0D1120'),
                      title_color=WHITE)
        btn2.bind(on_release=popup.dismiss)
        popup.open()

    def _upd(self, inst, val):
        self.bg.pos = inst.pos
        self.bg.size = inst.size

    def _upd_r(self, inst):
        inst._r.pos = inst.pos
        inst._r.size = inst.size


# ════════════════════════════════════════════════════════════════════════════
#  APP
# ════════════════════════════════════════════════════════════════════════════
class NovaLauncherApp(App):
    def build(self):
        self.title = 'Nova Launcher'
        self.icon = 'assets/logo.png'

        sm = ScreenManager(transition=FadeTransition(duration=0.2))
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(ProfileScreen(name='profile'))
        sm.add_widget(ModsScreen(name='mods'))
        sm.add_widget(SettingsScreen(name='settings'))
        return sm


if __name__ == '__main__':
    NovaLauncherApp().run()
