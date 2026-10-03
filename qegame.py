"""
水墨风不规则六边形舒尔特方格 (1-50) - 动画音效版
保存为 qegame.py，pyinstaller -F -w qegame.py 打包
打包后把 bgm.mp3、click.mp3、error.mp3 放到 exe 同目录即可自动播放
"""

import random
import time
import math
import os
import platform

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.core.audio import SoundLoader
from kivy.animation import Animation

# ==================== 字体 ====================
CHINESE_FONT = None
if platform.system() == 'Windows':
    for p in ['C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/simhei.ttf']:
        if os.path.exists(p):
            LabelBase.register(name='ChineseFont', fn_regular=p)
            CHINESE_FONT = 'ChineseFont'
            break

def font():
    return CHINESE_FONT or 'Roboto'

# ==================== 配色 ====================
PAPER   = (0.97, 0.95, 0.92, 1)
INK_DK  = (0.12, 0.14, 0.16, 1)
INK_MD  = (0.35, 0.37, 0.40, 1)
INK_LT  = (0.55, 0.57, 0.60, 1)
INK_BD  = (0.45, 0.47, 0.50, 1)
VERM    = (0.72, 0.20, 0.15, 1)
BAMBOO  = (0.50, 0.72, 0.50, 1)

Window.clearcolor = PAPER


# ==================== 音频工具 ====================

def try_load_sound(basename):
    for ext in ['.mp3', '.wav', '.ogg']:
        path = basename + ext
        if os.path.exists(path):
            try:
                snd = SoundLoader.load(path)
                if snd:
                    return snd
            except Exception:
                pass
    return None


# ==================== 引擎 ====================

class SchulteEngine:
    def __init__(self, count=50):
        self.count = count
        self.nums = []
        self.cur = 1
        self.t0 = self.t1 = 0
        self.done = False
        self.wrong = 0

    def reset(self):
        self.nums = list(range(1, self.count + 1))
        random.shuffle(self.nums)
        self.cur = 1
        self.t0 = self.t1 = 0
        self.done = False
        self.wrong = 0

    def start(self):
        self.t0 = time.time()

    def click(self, num):
        if self.done or num != self.cur:
            self.wrong += 1
            return False
        self.cur += 1
        if self.cur > self.count:
            self.t1 = time.time()
            self.done = True
        return True

    def elapsed(self):
        if self.t0 == 0:
            return 0
        if self.done:
            return self.t1 - self.t0
        return time.time() - self.t0

    def fmt(self, t):
        m = int(t // 60)
        s = int(t % 60)
        ms = int((t % 1) * 100)
        return f"{m:02d}:{s:02d}.{ms:02d}"


# ==================== 六边形格子 ====================

class HexCell(ButtonBehavior, Widget):
    def __init__(self, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        super().__init__(**kwargs)
        self.num = 0
        self.finished = False

        with self.canvas:
            Color(rgba=(0.96, 0.94, 0.90, 1))
            self._fill = Ellipse(pos=(0, 0), size=(100, 100), segments=6)
            Color(rgba=INK_BD)
            self._line = Line(points=[0, 0, 100, 0], width=1.5, close=True)

        self.label = Label(
            text='', font_size='24sp', bold=True,
            font_name=font(), color=INK_DK,
            pos=self.pos, size=self.size
        )
        self.add_widget(self.label)
        self.bind(pos=self._draw, size=self._draw)

        self._base_font_px = self.label.font_size

    def set_num(self, n):
        self.num = n
        self.finished = False
        self.label.text = str(n)
        self.label.color = INK_DK
        self.opacity = 1
        self.label.font_size = '24sp'
        self._base_font_px = self.label.font_size

    def spawn_burst(self):
        """点击成功涟漪动画：竹青色六边形从中心扩散并淡出"""
        burst = Widget(size_hint=(None, None), size=self.size, pos=self.pos)
        with burst.canvas:
            Color(rgba=(*BAMBOO[:3], 0.5))
            Ellipse(pos=(0, 0), size=burst.size, segments=6)
        self.parent.add_widget(burst)

        def cleanup(*a):
            if burst.parent:
                burst.parent.remove_widget(burst)

        tw, th = self.width * 2.2, self.height * 2.2
        tx = self.center_x - tw / 2
        ty = self.center_y - th / 2
        anim = Animation(size=(tw, th), pos=(tx, ty), opacity=0, duration=0.35)
        anim.bind(on_complete=cleanup)
        anim.start(burst)

    def shake(self):
        """错误点击抖动"""
        orig_x = self.x
        offsets = [10, -10, 8, -8, 5, -5, 0]
        idx = 0

        def step(dt):
            nonlocal idx
            if idx >= len(offsets):
                self.x = orig_x
                return
            self.x = orig_x + offsets[idx]
            idx += 1
            Clock.schedule_once(step, 0.04)

        step(None)

    def mark_done(self, keep_visible=False):
        self.finished = True
        if not keep_visible:
            self.label.text = ''
            Animation(opacity=0, duration=0.3).start(self)
        else:
            if hasattr(self, '_orig_size'):
                self.size = self._orig_size
                del self._orig_size
            self.label.font_size = self._base_font_px
            Animation(opacity=1.0, duration=0.1).start(self)

    def flash_err(self):
        self.label.color = VERM
        def restore(dt):
            if not self.finished:
                self.label.color = INK_DK
        Clock.schedule_once(restore, 0.18)

    def _draw(self, *a):
        cx, cy = self.center_x, self.center_y
        r = min(self.width, self.height) / 2
        self._fill.pos = (cx - r, cy - r)
        self._fill.size = (r * 2, r * 2)
        pts = []
        for i in range(6):
            ang = math.radians(60 * i)
            pts.extend([cx + r * 0.92 * math.cos(ang), cy + r * 0.92 * math.sin(ang)])
        self._line.points = pts
        self.label.pos = self.pos
        self.label.size = self.size

    def on_press(self):
        if not self.finished:
            self._orig_size = (self.width, self.height)
            cx, cy = self.center_x, self.center_y
            self.size = (self._orig_size[0] * 0.92, self._orig_size[1] * 0.92)
            self.center_x, self.center_y = cx, cy
            self.label.font_size = self._base_font_px * 1.15
            Animation(opacity=0.55, duration=0.03).start(self)
            self.label.color = VERM

    def on_release(self):
        if hasattr(self, '_orig_size'):
            cx, cy = self.center_x, self.center_y
            self.size = self._orig_size
            self.center_x, self.center_y = cx, cy
            del self._orig_size
        self.label.font_size = self._base_font_px
        if not self.finished:
            Animation(opacity=1.0, duration=0.10).start(self)
            self.label.color = INK_DK


# ==================== 蜂窝棋盘 ====================

class HexBoard(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.engine = SchulteEngine(50)
        self.cells = []
        for i in range(50):
            cell = HexCell(size_hint=(None, None))
            self.cells.append(cell)
            self.add_widget(cell)
        self._jitter = [((random.random() - 0.5) * 0.05,
                         (random.random() - 0.5) * 0.05) for _ in range(50)]
        self.bind(size=self._layout)
        Clock.schedule_once(lambda dt: self._layout(), 0.1)

    def start(self):
        self.engine.reset()
        for idx, num in enumerate(self.engine.nums):
            self.cells[idx].set_num(num)
        self.engine.start()

    def _layout(self, *a):
        if self.width < 10 or self.height < 10:
            return
        cols, rows = 5, 10
        base_w = self.width / (cols + 0.5) * 0.95
        base_h = base_w * 0.866
        total_h = rows * base_h * 0.75 + base_h * 0.25
        if total_h > self.height * 0.96:
            scale = self.height * 0.96 / total_h
            base_h *= scale
            base_w = base_h / 0.866

        off_x = (self.width - (cols * base_w + base_w * 0.5)) / 2
        off_y = (self.height - total_h) / 2 + 2

        for idx, cell in enumerate(self.cells):
            row = idx // cols
            col = idx % cols
            x = col * base_w
            if row % 2 == 1:
                x += base_w * 0.5
            y = self.height - off_y - (row + 1) * base_h * 0.75

            jx, jy = self._jitter[idx]
            x += jx * base_w + off_x
            y += jy * base_h

            cell.size = (base_w * 0.85, base_h * 0.85)
            cell.pos = (x, y)


# ==================== 屏幕 ====================

class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation='vertical', padding=40, spacing=15)
        root.add_widget(Widget(size_hint_y=0.18))

        root.add_widget(Label(text='舒尔特方格', font_size='52sp', bold=True,
                              color=INK_DK, font_name=font(), size_hint_y=0.16))
        root.add_widget(Label(text='六边形 · 水墨', font_size='16sp',
                              color=INK_MD, font_name=font(), size_hint_y=0.06))

        line = Widget(size_hint_y=None, height=1)
        with line.canvas:
            Color(rgba=INK_LT)
            line._rect = Rectangle(pos=line.pos, size=line.size)
        line.bind(pos=lambda i, v: setattr(line._rect, 'pos', i.pos),
                  size=lambda i, v: setattr(line._rect, 'size', i.size))
        root.add_widget(line)

        root.add_widget(Label(
            text='50 个数字随机散布于蜂窝棋盘中\n按顺序依次点击 1 → 2 → 3 …',
            font_size='15sp', color=INK_MD, font_name=font(),
            size_hint_y=0.16, halign='center'))

        root.add_widget(Widget(size_hint_y=0.08))

        btn = Button(text='开始挑战', font_size='22sp', font_name=font(),
                     bold=True, color=(1, 1, 1, 1), size_hint_y=0.12,
                     background_normal='', background_down='',
                     background_color=(0, 0, 0, 0))
        with btn.canvas.before:
            Color(rgba=INK_DK)
            btn._r = Ellipse(pos=btn.pos, size=btn.size, segments=6)
        btn.bind(pos=lambda i, v: setattr(i._r, 'pos', i.pos),
                 size=lambda i, v: setattr(i._r, 'size', i.size))
        btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'mode'))
        root.add_widget(btn)

        root.add_widget(Widget(size_hint_y=0.3))
        self.add_widget(root)


class ModeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation='vertical', padding=40, spacing=20)
        root.add_widget(Widget(size_hint_y=0.10))

        root.add_widget(Label(text='选择难度', font_size='36sp', bold=True,
                              color=INK_DK, font_name=font(), size_hint_y=0.12))

        root.add_widget(Widget(size_hint_y=0.05))

        btn_cloud = Button(text='云隐', font_size='22sp', font_name=font(),
                           bold=True, color=(1, 1, 1, 1), size_hint_y=0.16,
                           background_normal='', background_down='',
                           background_color=(0, 0, 0, 0))
        with btn_cloud.canvas.before:
            Color(rgba=INK_DK)
            btn_cloud._bg = Ellipse(pos=btn_cloud.pos, size=btn_cloud.size, segments=6)
        btn_cloud.bind(pos=self._upd_hex, size=self._upd_hex)
        btn_cloud.bind(on_press=lambda x: self.set_mode(False))
        root.add_widget(btn_cloud)

        root.add_widget(Label(text='点过的数字隐去，留下空位',
                              font_size='14sp', color=INK_LT, font_name=font(), size_hint_y=0.05))

        root.add_widget(Widget(size_hint_y=0.03))

        btn_invis = Button(text='无痕', font_size='22sp', font_name=font(),
                           bold=True, color=INK_DK, size_hint_y=0.16,
                           background_normal='', background_down='',
                           background_color=(0, 0, 0, 0))
        with btn_invis.canvas.before:
            Color(rgba=(0.90, 0.88, 0.84, 1))
            btn_invis._bg = Ellipse(pos=btn_invis.pos, size=btn_invis.size, segments=6)
            Color(rgba=INK_BD)
            btn_invis._bd = Line(points=[], width=1.5, close=True)
        btn_invis.bind(pos=self._upd_hex_bd, size=self._upd_hex_bd)
        btn_invis.bind(on_press=lambda x: self.set_mode(True))
        root.add_widget(btn_invis)

        root.add_widget(Label(text='点过的数字仍在，全凭记忆追踪',
                              font_size='14sp', color=INK_LT, font_name=font(), size_hint_y=0.05))

        root.add_widget(Widget(size_hint_y=0.10))

        btn_back = Button(text='返回菜单', font_size='15sp', font_name=font(),
                          color=INK_MD, background_color=(0, 0, 0, 0),
                          background_normal='', background_down='')
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'menu'))
        root.add_widget(btn_back)

        root.add_widget(Widget(size_hint_y=0.15))
        self.add_widget(root)

    def _upd_hex(self, inst, val):
        cx, cy = inst.center_x, inst.center_y
        r = min(inst.width, inst.height) / 2
        inst._bg.pos = (cx - r, cy - r)
        inst._bg.size = (r * 2, r * 2)

    def _upd_hex_bd(self, inst, val):
        cx, cy = inst.center_x, inst.center_y
        r = min(inst.width, inst.height) / 2
        inst._bg.pos = (cx - r, cy - r)
        inst._bg.size = (r * 2, r * 2)
        pts = []
        for i in range(6):
            ang = math.radians(60 * i)
            pts.extend([cx + r * 0.92 * math.cos(ang), cy + r * 0.92 * math.sin(ang)])
        inst._bd.points = pts

    def set_mode(self, keep_visible):
        App.get_running_app().keep_visible_mode = keep_visible
        self.manager.current = 'game'


class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._tick = None
        root = BoxLayout(orientation='vertical', padding=12, spacing=6)

        top = BoxLayout(size_hint_y=0.08, spacing=10)
        self.target = Label(text='找: 1', font_size='26sp', bold=True,
                            color=VERM, font_name=font(), size_hint_x=0.35)
        self.mode_label = Label(text='', font_size='13sp',
                                color=INK_LT, font_name=font(), size_hint_x=0.3, halign='center')
        self.timer = Label(text='00:00.00', font_size='24sp',
                           color=INK_DK, font_name=font(), halign='right', size_hint_x=0.35)
        self.timer.bind(size=self.timer.setter('text_size'))
        top.add_widget(self.target)
        top.add_widget(self.mode_label)
        top.add_widget(self.timer)
        root.add_widget(top)

        self.count_lb = Label(text='0 / 50', font_size='14sp',
                              color=INK_LT, font_name=font(), size_hint_y=0.04)
        root.add_widget(self.count_lb)

        self.board = HexBoard(size_hint_y=0.78)
        for i, cell in enumerate(self.board.cells):
            cell.bind(on_press=lambda inst, idx=i: self.on_cell_click(idx))
        root.add_widget(self.board)

        bot = BoxLayout(size_hint_y=0.07, spacing=12)
        for txt, act in [('重置', self.restart), ('返回', lambda: setattr(self.manager, 'current', 'menu'))]:
            b = Button(text=txt, font_size='15sp', font_name=font(),
                       color=INK_MD, background_color=(0, 0, 0, 0),
                       background_normal='', background_down='')
            b.bind(on_press=lambda x, a=act: a())
            bot.add_widget(b)
        root.add_widget(bot)

        self.add_widget(root)

    def on_enter(self):
        app = App.get_running_app()
        self.mode_label.text = '无痕' if app.keep_visible_mode else '云隐'
        self.restart()

    def restart(self, *a):
        self.board.start()
        self.target.text = '找: 1'
        self.target.color = VERM
        self.count_lb.text = '0 / 50'
        self.timer.text = '00:00.00'
        if self._tick:
            self._tick.cancel()
        self._tick = Clock.schedule_interval(self._update_time, 0.05)

    def _update_time(self, dt):
        self.timer.text = self.board.engine.fmt(self.board.engine.elapsed())
        if self.board.engine.done:
            self._tick.cancel()
            self._tick = None
            Clock.schedule_once(lambda dt: self.finish(), 0.3)

    def on_cell_click(self, idx):
        if self.board.engine.done:
            return
        num = self.board.cells[idx].num
        ok = self.board.engine.click(num)
        app = App.get_running_app()

        if ok:
            # 播放点击成功音效
            if app.click_snd:
                app.click_snd.play()

            self.board.cells[idx].spawn_burst()  # 涟漪动画
            keep = app.keep_visible_mode
            self.board.cells[idx].mark_done(keep_visible=keep)
            self.target.text = f'找: {self.board.engine.cur}' if not self.board.engine.done else '完成!'
            if self.board.engine.done:
                self.target.color = BAMBOO
            self.count_lb.text = f'{self.board.engine.cur - 1} / 50'
        else:
            # 播放错误音效
            if app.error_snd:
                app.error_snd.play()

            self.board.cells[idx].shake()  # 错误抖动
            self.board.cells[idx].flash_err()

    def finish(self):
        app = App.get_running_app()
        app.last_time = self.board.engine.fmt(self.board.engine.elapsed())
        app.last_wrong = self.board.engine.wrong
        self.manager.current = 'result'


class ResultScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation='vertical', padding=40, spacing=18)
        root.add_widget(Widget(size_hint_y=0.10))

        root.add_widget(Label(text='挑战完成', font_size='40sp', bold=True,
                              color=INK_DK, font_name=font(), size_hint_y=0.12))

        self.mode_lb = Label(text='', font_size='14sp',
                             color=INK_LT, font_name=font(), size_hint_y=0.04)
        root.add_widget(self.mode_lb)

        self.big_time = Label(text='00:00.00', font_size='56sp',
                              bold=True, color=VERM, font_name=font(), size_hint_y=0.15)
        root.add_widget(self.big_time)

        self.wrong_lb = Label(text='', font_size='16sp',
                              color=INK_MD, font_name=font(), size_hint_y=0.06)
        root.add_widget(self.wrong_lb)

        line = Widget(size_hint_y=None, height=1)
        with line.canvas:
            Color(rgba=INK_LT)
            line._rect = Rectangle(pos=line.pos, size=line.size)
        line.bind(pos=lambda i, v: setattr(line._rect, 'pos', i.pos),
                  size=lambda i, v: setattr(line._rect, 'size', i.size))
        root.add_widget(line)

        self.grade = Label(text='', font_size='18sp',
                           color=INK_MD, font_name=font(), size_hint_y=0.12, halign='center')
        root.add_widget(self.grade)

        root.add_widget(Widget(size_hint_y=0.06))

        btn = Button(text='再来一局', font_size='22sp', font_name=font(),
                     bold=True, color=(1, 1, 1, 1), size_hint_y=0.12,
                     background_normal='', background_down='',
                     background_color=(0, 0, 0, 0))
        with btn.canvas.before:
            Color(rgba=INK_DK)
            btn._rect = Ellipse(pos=btn.pos, size=btn.size, segments=6)
        btn.bind(pos=lambda i, v: setattr(i._rect, 'pos', i.pos),
                 size=lambda i, v: setattr(i._rect, 'size', i.size))
        btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'game'))
        root.add_widget(btn)

        btn2 = Button(text='返回菜单', font_size='16sp', font_name=font(),
                      color=INK_MD, background_color=(0, 0, 0, 0),
                      background_normal='', background_down='', size_hint_y=0.08)
        btn2.bind(on_press=lambda x: setattr(self.manager, 'current', 'menu'))
        root.add_widget(btn2)

        root.add_widget(Widget(size_hint_y=0.18))
        self.add_widget(root)

    def on_enter(self):
        app = App.get_running_app()
        self.mode_lb.text = '无痕模式' if app.keep_visible_mode else '云隐模式'
        self.big_time.text = app.last_time
        self.wrong_lb.text = f'误点 {app.last_wrong} 次'
        parts = app.last_time.replace(':', ' ').replace('.', ' ').split()
        sec = int(parts[0]) * 60 + int(parts[1])
        if sec < 35:
            g = '行云流水 · 神乎其技'
        elif sec < 50:
            g = '挥洒自如 · 眼明手快'
        elif sec < 70:
            g = '沉稳有度 · 渐入佳境'
        elif sec < 100:
            g = '心如止水 · 持之以恒'
        else:
            g = '锲而不舍 · 终成大器'
        self.grade.text = g


class SchulteApp(App):
    def build(self):
        self.last_time = '00:00.00'
        self.last_wrong = 0
        self.keep_visible_mode = False

        # 加载音频
        self.bgm = try_load_sound('bgm')
        self.click_snd = try_load_sound('click')
        self.error_snd = try_load_sound('error')

        if self.bgm:
            self.bgm.loop = True
            self.bgm.volume = 0.45
            self.bgm.play()

        sm = ScreenManager()
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(ModeScreen(name='mode'))
        sm.add_widget(GameScreen(name='game'))
        sm.add_widget(ResultScreen(name='result'))
        return sm

    def on_stop(self):
        # 退出时释放音频
        if self.bgm:
            self.bgm.stop()
            self.bgm.unload()


if __name__ == '__main__':
    SchulteApp().run()