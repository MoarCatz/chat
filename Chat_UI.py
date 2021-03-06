from kivy import require
require('1.9.1')

from kivy.config import Config
Config.set('graphics', 'width', 370)
Config.set('graphics', 'height', 200)
Config.set('graphics', 'resizable', False)

import string, re, os, json, webbrowser, time, queue
from datetime import datetime
from PIL import Image as _Image
from textwrap import TextWrapper
from threading import Thread
from functools import partial
from random import choice
from io import BytesIO

from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.effects.scroll import ScrollEffect
from kivy.effects.dampedscroll import DampedScrollEffect
from kivy.uix.screenmanager import (Screen, ScreenManager,
                                    NoTransition, SlideTransition)
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.bubble import Bubble
from kivy.properties import (ListProperty, BooleanProperty,
                             StringProperty, ObjectProperty, NumericProperty)
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.utils import escape_markup
from kivy.uix.dropdown import DropDown
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.clock import Clock, mainthread
from kivy.graphics import Ellipse, Color, Rectangle
from kivy.uix.image import Image, AsyncImage
from kivy.core.image import Image as CoreImage
from kivy.base import stopTouchApp, EventLoop
from kivy.uix.filechooser import FileChooserListView, FileSystemLocal
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelHeader
from kivy.uix.rst import RstDocument
from kivy.logger import Logger
from kivy.animation import Animation

from client import RequestSender


Builder.load_string('''
<Label>:
    font_name: "fonts/NotoSans_R.ttf"

<Button>:
    color: 1, 1, 1, 1
    disabled_color: 1, 1, 1, 1
    background_normal: app.theme['normal']
    background_down: app.theme['down']

<Popup>:
    size_hint: None, None
    pos_hint: {"center_x": 0.5, "center_y": 0.5}
    width: 250
    separator_height: 1
    separator_color: app.colors['light']
    title_font: "fonts/NotoSans_B.ttf"

<AvatarSelectButton>:
    color: (1, 1, 1, 0.5) if self.state == 'normal' else (1, 1, 1, 1)

<ClockLabel>:
    text_size: self.size
    valign: 'bottom'
    color: 0.23, 0.23, 0.23, 1
    font_size: 8

<DialogButton>:
    background_normal: app.theme['menubt_normal']
    background_down: app.theme['inputbt_down']
    background_disabled_normal: app.theme['menubt_normal']
    text_size: self.width - 10, self.height
    valign: 'center'
    font_size: 14
    font_name: 'fonts/NotoSans_B.ttf'

<ErrorLabel>:
    text_size: self.size
    halign: "left"
    valign: "top"

<FramedScrollView>:
    canvas:
        Color:
            rgba: 0.23, 0.23, 0.23, 1
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: 0.86, 0.86, 0.86, 1
        Rectangle:
            pos: self.x + 1, self.y + 1
            size: self.width - 2, self.height - 2

<FullSizeButton>:
    text_size: self.width - self.bound[0], self.height - self.bound[1]

<FullSizeLabel>:
    text_size: self.width - self.bound[0], self.height - self.bound[1]

<InputBox>:
    canvas:
        Color:
            rgba: 1, 1, 1, 1
        Rectangle:
            size: self.size
            pos: self.pos
            source: app.theme['input_panel']
    padding: 0, 8

<InputButton>:
    background_normal: app.theme['inputbt_normal']
    background_down: app.theme['inputbt_down']
    font_name: 'fonts/NotoSans_B.ttf'

<LoadSpinner>:
    canvas.before:
        PushMatrix
        Rotate:
            angle: root.angle
            axis: 0, 0, 1
            origin: root.center
    canvas.after:
        PopMatrix

<LoggedAsLabel>:
    text_size: self.width - 10, self.height
    halign: "left"

<LoginLayout>:
    canvas.before:
        Color:
            rgba: app.colors['border']
        RoundedRectangle:
            pos: -28, 59
            size: 352, 42
        RoundedRectangle:
            pos: -28, 109
            size: 352, 42
        Color:
            rgba: app.colors['dark'] + (1,)
        RoundedRectangle:
            pos: -27, 60
            size: 350, 40
        RoundedRectangle:
            pos: -27, 110
            size: 350, 40

<MenuAddBar>:
    canvas.before:
        Color:
            rgba: 0.86, 0.86, 0.86, 1
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: app.colors['dark'] + (1,)
        Rectangle:
            pos: self.x, self.y + 1
            size: self.width, self.height - 2

<MenuButton>:
    size_hint: 1, 0.09
    background_normal: app.theme['topbt_normal']
    background_down: app.theme['inputbt_down']
    font_name: 'fonts/NotoSans_R.ttf'
    font_size: 17
    markup: True

<MenuDivider>:
    canvas:
        Color:
            rgba: 0.86, 0.86, 0.86, 1
        Line:
            points: self.x, self.y, self.x, self.y + self.height
            width: 1.5
        Rectangle:
            source: app.theme['inputbt_normal']
            size: self.size
            pos: self.pos
        Line:
            points: self.x + self.width, self.y, \
                    self.x + self.width, self.y + self.height

<Message>:
    canvas:
        Color:
            rgba: 0.8, 0.8, 0.8, 1
        RoundedRectangle:
            pos: root.pos
            size: self.size
        Color:
            rgba: root.bg_color
        RoundedRectangle:
            pos: root.x + 1, root.y + 1
            size: self.width - 2, self.height - 2

<MessageInput>:
    background_normal: app.theme['msginput_unfocused']
    background_active: app.theme['msginput_focused']
    font_name: "fonts/NotoSans_R.ttf"
    cursor_color: 0, 0, 0, 1
    write_tab: False

<MessageView>:
    canvas:
        Color:
            rgba: 1, 1, 1, 1
        Rectangle:
            pos: self.pos
            size: self.size

    canvas.after:
        Color:
            rgba: 0.5, 0.5, 0.5, 1
        Line:
            points: self.x, self.y + self.height, \
                    self.x + self.width, self.y + self.height, \
                    self.x + self.width, self.y, \
                    self.x, self.y, \
                    self.x, self.y + self.height

<NickInput>:
    multiline: False
    font_size: 14
    font_name: "fonts/NotoSans_R.ttf"
    cursor_color: 0, 0, 0, 1
    write_tab: False
    background_normal: app.theme['field']
    background_active: app.theme['field_active']

<NickLabel>:
    background_color: 0, 0, 0, 0
    color: (0, 0, 0, 1) if self.state == 'normal' else\
           app.colors['dark'] + (1,)
    size_hint_x: None
    width: self.texture_size[0]
    font_size: 13

<OptButton>:
    size_hint_y: None
    font_size: 12
    background_normal: app.theme['drop_opt']
    background_down: app.theme['drop_opt_down']
    height: 20

<PersonLayout>:
    canvas.after:
        Color:
            rgba: 0.1, 0.1, 0.1, 1
        Line:
            points: self.x, self.y + self.height, \
                    self.x + self.width, self.y + self.height, \
                    self.x + self.width, self.y, self.x, self.y, \
                    self.x, self.y + self.height

<ProfileButton>:
    background_normal: app.theme['normal']
    background_down: app.theme['down']
    font_name: 'fonts/NotoSans_B.ttf'
    size: 145, 40
    size_hint: None, None

<RecordDivider>:
    height: 15
    color: 1, 1, 1, 1
    font_size: 12
    text_size: self.width - 10, self.height
    halign: 'left'
    size_hint: 1, None
    canvas.before:
        Color:
            rgba: 0.86, 0.86, 0.86, 1
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: 0.23, 0.23, 0.23, 1
        Rectangle:
            pos: self.x + 1, self.y + 1
            size: self.width - 2, self.height - 2

<RegLabel>:
    color: 1, 1, 1, 1
    font_name: 'fonts/NotoSans_B.ttf'
    size_hint: 0.7, 1
    text_size: self.width - 20, self.height - 10
    halign: "left"
    valign: "center"
    canvas.before:
        Color:
            rgba: 0.86, 0.86, 0.86, 1
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: app.colors['dark'] + (1,)
        Rectangle:
            pos: self.x, self.y + 1
            size: self.width, self.height - 2

<RegisterLayout>:
    canvas.before:
        Color:
            rgba: app.colors['border']
        RoundedRectangle:
            pos: -28, 52
            size: 352, 45
        RoundedRectangle:
            pos: -28, 102
            size: 352, 45
        RoundedRectangle:
            pos: -28, 153
            size: 352, 45
        Color:
            rgba: app.colors['dark'] + (1,)
        RoundedRectangle:
            pos: -27, 53
            size: 350, 43
        RoundedRectangle:
            pos: -27, 103
            size: 350, 43
        RoundedRectangle:
            pos: -27, 154
            size: 350, 43

<SmileBubble>:
    canvas:
        Color:
            rgba: app.colors['dark'] + (0.7,)
        RoundedRectangle:
            pos: self.x, self.y + 10
            size: self.width, self.height - 10

<SpinnerOption>:
    background_normal: app.theme['normal']
    background_down: app.theme['down']

<UsernameButton>:
    text_size: self.width - 10, self.height
    halign: 'left'
    valign: 'center'
    font_size: 13

<UserRecord>:
    canvas:
        Color:
            rgba: app.colors['dark'] + (1,)
        Line:
            points: self.x, self.y, \
                    self.x + self.width, self.y, \
                    self.x + self.width, self.y + self.height, \
                    self.x, self.y + self.height, \
                    self.x, self.y
        Color:
            rgba: app.colors['dark'] + (0.3,)
        Rectangle:
            pos: self.pos
            size: self.size

<YesNoButton>:
    background_normal: app.theme['normal']
    background_down: app.theme['down']
    font_name: 'fonts/NotoSans_B.ttf'
''')


def _get_settings():
    if not os.path.exists('settings.json'):
        sets = {'lang': 'English',
                'thm': 'Blue'}
        for i in range(10):
            sets[str(i)] = ''

        with open('settings.json', 'w') as f:
            json.dump(sets, f,
                      ensure_ascii = False,
                      indent = 2,
                      sort_keys = True)
        return sets

    with open('settings.json') as f:
        return json.load(f)


class TextureResolver:
    def __init__(self, atlas_path):
        # atlas_path should be given without '.atlas'
        if atlas_path[-1] != '/':
            atlas_path += '/'
        self.atlas_path = 'atlas://' + atlas_path

    def __getitem__(self, key):
        return self.atlas_path + key


class EngLoc:
    def __getitem__(self, key):
        return key


class RusLoc:
    with open('local_ru.json') as f:
        translator = json.load(f)

    def __getitem__(self, key):
        return self.translator[key]


lang = _get_settings()['lang']
# This variable will hold an object responsible for localization
l = EngLoc() if lang == 'English' else RusLoc()
del lang


class FullSizeButton(Button):
    bound = ListProperty([0, 0])


class FullSizeLabel(Label):
    bound = ListProperty([0, 0])


class HelpPage(TabbedPanelHeader):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = app.theme['tab']
        self.background_down = app.theme['tab_active']
        self.color = (0, 0, 0, 1)
        self.font_size = 11


class LinkButton(Button):
    def on_press(self):
        webbrowser.open(self.link)

    def __init__(self, link, **kwargs):
        super().__init__(**kwargs)
        self.link = link
        self.background_color = (0, 0, 0, 0)

class HelpScreen(Screen):
    def place_links(self, tm):
        # This method goes deep into the structure of an RstDocument widget
        rst = self.about_page.content
        rst_elems = rst.children[0].children[0].children

        rst_list = rst_elems[5]
        team = rst_elems[1]

        rst_list.add_widget(self.server_link)
        rst_list.add_widget(self.client_link)
        team.add_widget(self.team_link)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cont = BoxLayout(orientation = 'vertical')
        self.bar = BackBar(title = l['Help'],
                           size_hint = (1, 0.1))

        self.tabs = TabbedPanel(tab_height = 21,
                                do_default_tab = False,
                                tab_pos = 'bottom_left')

        with self.tabs.canvas:
            Color(rgba = app.colors['tab'])
            Rectangle(size = (500, 1),
                      pos = (0, 22))

        self.help_page = HelpPage(text = l['Help'])
        self.about_page = HelpPage(text = l['About'])

        link_width = 80 if app.language == 'English' else 52
        url = 'https://github.com/MoarCatz/'
        self.server_link = LinkButton(link = url + 'chat-server',
                                      size = (link_width, 20),
                                      pos = (30, 245))

        self.client_link = LinkButton(link = url + 'chat-client',
                                      size = (link_width, 20),
                                      pos = (30, 214))

        team_x = 200 if app.language == 'English' else 310
        self.team_link = LinkButton(link = url,
                                    size = (68, 20),
                                    pos = (team_x, 93))

        self.tabs.switch_to(self.help_page)

        suff = '_en.rst' if app.language == 'English' else '_ru.rst'
        self.help_page.content = RstDocument(source = 'help/help' + suff,
                                             background_color = (1, 1, 1, 1))
        self.about_page.content = RstDocument(source = 'help/about' + suff,
                                              background_color = (1, 1, 1, 1))

        self.tabs.add_widget(self.help_page)
        self.tabs.add_widget(self.about_page)
        self.tabs._tab_layout.padding = 0

        self.cont.add_widget(self.bar)
        self.cont.add_widget(self.tabs)

        self.add_widget(self.cont)
        Clock.schedule_once(self.place_links, 0.001)


class SmileButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0, 0, 0, 0)
        self.font_size = 13
        self.always_release = True
        self.font_name = "fonts/NotoSans_B.ttf"
        self.height = 20
        self.size_hint = [1, None]


    def on_press(self):
        self.color = (0.6, 0.8, 1, 1)

    def on_release(self):
        self.color = (1, 1, 1, 1)


class ClockLabel(Label):
    def __init__(self, tm, **kwargs):
        super().__init__(**kwargs)
        self.text = datetime.fromtimestamp(tm // 100).strftime("%H:%M")


class Message(BoxLayout):
    bg_color = ListProperty([0.99, 0.99, 0.99, 1])
    tw = TextWrapper(width = 30,
                     replace_whitespace = False)
    sent = (l['Sender'] + ': [color=#B6DAFF]{}[/color]\n' +
            l['Time'] + ': [color=#C8C8C8]{}[/color]\n' +
            l['Date'] + ': [color=#C8C8C8]{}[/color]')

    def width_modify(self):
        min_width = 160
        max_width = 320
        max_line = max(self.text_box._lines_labels,
                       key = lambda x: x.width).width
        curr_width = max_line + 15
        if curr_width < min_width:
            return min_width
        elif curr_width > max_width:
            return max_width
        else:
            return curr_width

    def line_wrap(self, text):
        spl = re.split('(\n{2,})', text)
        res = ''
        for idx, part in enumerate(spl):
            if idx % 2 != 0:
                # Elements with odd indexes are delimiters
                res += part
            else:
                res += '\n'.join(self.tw.fill(i) for i in part.split('\n'))
        return res

    def __init__(self, text, tm, sender, scr, **kwargs):
        super().__init__(**kwargs)
        self.text_box = TextInput(font_name = "fonts/NotoSans_R.ttf",
                                  font_size = 13,
                                  background_color = (0, 0, 0, 0),
                                  readonly = True,
                                  cursor_color = (0, 0, 0, 0))

        self.real_text = text
        self.text_box.text = self.line_wrap(text)
        self.sender = sender
        self.time = tm
        self.scr = scr

        self.height = (self.text_box.text.count('\n') + 2) * 19
        self.add_widget(self.text_box)

        if sender != app.nick:
            self.bg_color = app.colors['msg']

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            info_popup = self.scr.info_popup
            date_obj = datetime.fromtimestamp(self.time // 100)
            date, time = date_obj.strftime("%d/%m/%Y %H:%M:%S").split()
            sent_text = self.sent.format(self.sender, time, date)

            info_popup.info_view.info_lb.text = sent_text
            info_popup.info_view.msg_text.text = self.real_text
            info_popup.open()


class SmileBubble(Bubble):
    hidden = BooleanProperty(True)
    def build_btns(self):
        self.smile_grid.clear_widgets()
        smiles = self.scr.smiles[:]
        for i in range(10):
            sm = app.settings[str(i)]
            if sm:
                smiles.append(sm)

        for smile in smiles:
            bt = SmileButton(text = smile,
                             on_release = self.scr.input_bar.add_smile)
            self.smile_grid.add_widget(bt)

    def __init__(self, scr, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.show_arrow = False
        self.pos = (170, 95)
        self.size = (175, 275)
        self.background_color = (0, 0, 0, 0)
        self.scr = scr

        self.scroll = ScrollView(bar_color = (0, 0, 0, 0),
                                 do_scroll_x = False,
                                 size_hint = (1, 1))
        self.smile_grid = GridLayout(cols = 5,
                                     size_hint_y = None)
        self.smile_grid.bind(minimum_height = self.smile_grid.setter('height'))

        self.add_widget(self.scroll)
        self.scroll.add_widget(self.smile_grid)


class NickInput(TextInput):
    checker = ObjectProperty()
    def on_text(self, inst, text):
        self.checker.check_next()
        if len(text) > 15:
            self.text = text[:15]


class MessageView(ScrollView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.loaded = 0


class PersonLayout(FloatLayout):
    pass


class RegLabel(Label):
    pass


class RegisterLayout(BoxLayout):
    pass


class LoginLayout(BoxLayout):
    pass


class Status(BoxLayout):
    online = BooleanProperty(True)
    def __init__(self, online = True, **kwargs):
        super().__init__(**kwargs)
        self.img = Image(source = app.theme['status_on'])
        self.online = online
        self.add_widget(self.img)

    def on_online(self, inst, ch):
        path = app.theme['status_' + ('on' if ch else 'off')]
        self.img.source = path


class NickLabel(Button):
    pass


class InfoView(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 2

        self.info_lb = FullSizeLabel(markup = True,
                                     halign = 'left',
                                     bound = [0, 0],
                                     size_hint = (1, 0.4),
                                     font_size = 15,
                                     color = (1, 1, 1, 1))

        self.msg_label = Label(text = l["Message text:"],
                               font_name = "fonts/NotoSans_B.ttf",
                               size_hint = (1, 0.1),
                               font_size = 13,
                               color = (1, 1, 1, 1))

        self.msg_text = TextInput(readonly = True,
                                  cursor_color = (0, 0, 0, 0),
                                  size_hint = (1, 0.6),
                                  background_normal =
                                  app.theme['msginput_unfocused'],
                                  background_active =
                                  app.theme['msginput_unfocused'])

        self.add_widget(self.info_lb)
        self.add_widget(self.msg_label)
        self.add_widget(self.msg_text)


class ProfileBar(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.back_bt = Button(text = '   ' + l['Back'],
                              size_hint = (0.23, 1),
                              font_name = 'fonts/NotoSans_R.ttf',
                              background_normal = app.theme['menubt_normal'],
                              background_down = app.theme['inputbt_down'])
        self.back_bt.bind(on_release = app.back_action)
        self.plc = Button(disabled = True,
                          background_disabled_normal =
                          app.theme['menubt_normal'],
                          size_hint = (1, 1))
        self.add_widget(self.back_bt)
        self.add_widget(self.plc)


class Profile(Screen):
    def set_up_for(self, name):
        page = self.page
        profile_data = app.profiles[name]
        page.nick_field.text = profile_data.nick
        page.status_field.text = profile_data.status
        page.email_field.text = profile_data.email
        page.birthday_field.update_selectors(profile_data.bday)
        page.about_field.text = profile_data.about
        page.avatar_texture = CoreImage(BytesIO(profile_data.image_data),
                                        ext = 'png')
        page.avatar.texture = page.avatar_texture.texture

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.container = BoxLayout(orientation = "vertical")
        self.profile_bar = ProfileBar(size_hint = (1, 0.064))
        self.page = ProfilePage()

        self.add_widget(self.container)
        self.container.add_widget(self.profile_bar)
        self.container.add_widget(self.page)


class ProfileField(TextInput):
    def __init__(self, scr, **kwargs):
        self.multiline = False
        self.font_size = 13
        super().__init__(**kwargs)
        self.size = 220, kwargs.get('height', 30)
        self.size_hint = None, None
        self.background_normal = app.theme['field']
        self.background_disabled_normal = app.theme['field']
        self.background_active = app.theme['field_active']
        self.cursor_color = (0, 0, 0, 1)
        self.selection_color = app.colors['light']
        self.disabled_foreground_color = (0, 0, 0, 1)
        self.disabled = not scr.editing


class ProfileButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.disabled = False
        self.markup = True


class ProfileLabel(FullSizeLabel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.halign = 'right'
        self.font_name = kwargs.get('font_name', 'fonts/NotoSans_R.ttf')
        self.color = (0, 0, 0, 1)
        self.font_size = 12


class YesNoButton(Button):
    pass


class EditButton(ToggleButton, ProfileButton):
    pass


class ImageOnlyFileSystem(FileSystemLocal):
    def listdir(self, fn):
        try:
            for i in os.scandir(fn):
                if i.is_dir():
                    yield i.name
                else:
                    ext = i.name.lower()[-4:]
                    if ext == '.png':
                        yield i.name
        except PermissionError as e:
            # strip the '[errno N]' part
            ErrorDisp(str(e).partition('] ')[2]).open()


class AvatarSelectButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text = ''
        self.font_name = 'fonts/NotoSans_R.ttf'
        self.font_size = 50
        self.size_hint = None, None
        self.background_color = (0, 0, 0, 0)
        self.disabled_color = (0, 0, 0, 0)
        self.disabled = True


class AvatarSelectDialog(Popup):
    wrong_ext = l['The selected file should be a PNG image']
    def set_image(self, bt):
        file = self.file_select.selection
        if file:
            if not file[0].endswith('.png'):
                ErrorDisp(self.wrong_ext).open()
                return
            with open(file[0], 'rb') as f:
                img = f.read()
            id_match = app.set_image(img)
            if not id_match:
                return
            profile_data = app.profiles[self.cont.nick_field.text]
            profile_data.image_data = img
            self.cont.avatar_texture = CoreImage(BytesIO(img), ext = 'png')
            self.cont.avatar.texture = self.cont.avatar_texture.texture
            info_box = app.menu_scr.info_box
            info_box.avatar_texture = CoreImage(BytesIO(img), ext = 'png')
            info_box.avatar.texture = info_box.avatar_texture.texture
            self.dismiss()
        else:
            ErrorDisp(l['Please, select a file']).open()

    def __init__(self, cont, **kwargs):
        super().__init__(**kwargs)
        self.cont = cont
        self.content = BoxLayout(orientation = 'vertical')
        self.file_select = FileChooserListView()
        name_size = self.file_select.layout.children[0].children[1].children
        name_size[1].text = l['Size']
        name_size[2].text = l['Name']
        self.file_select.file_system = ImageOnlyFileSystem()

        self.button_box = BoxLayout(size_hint = (1, 0.1),
                                    spacing = 4)
        self.select_bt = Button(text = '[size=20][/size] ' + l['Select'],
                                font_name = 'fonts/NotoSans_R.ttf',
                                background_normal = app.theme['normal'],
                                background_down = app.theme['down'],
                                font_size = 16,
                                markup = True,
                                on_release = self.set_image)
        self.cancel_bt = Button(text = '[size=20][/size] ' + l['Cancel'],
                                font_name = 'fonts/NotoSans_R.ttf',
                                background_normal = app.theme['normal'],
                                background_down = app.theme['down'],
                                font_size = 16,
                                markup = True,
                                on_release = self.dismiss)

        self.content.add_widget(self.file_select)
        self.content.add_widget(self.button_box)
        self.button_box.add_widget(self.select_bt)
        self.button_box.add_widget(self.cancel_bt)
        self.title = l['Select a picture file']
        self.size = (330, 450)


class ProfilePage(FloatLayout):
    sect_map = {'status':   0,
                'email':    1,
                'birthday': 2,
                'about':    3}
    editing = False
    def edit(self, bt):
        for field in self.fields:
            field.disabled = self.editing
        self.birthday_field.disabled = self.editing
        if self.editing:
            profile_data = app.profiles[self.nick_field.text]
            status = self.status_field.text
            if profile_data.status != status:
                success = app.change_profile_section(self.sect_map['status'],
                                                     status)
                if success:
                    profile_data.status = status

            email = self.email_field.text
            if profile_data.email != email:
                success = app.change_profile_section(self.sect_map['email'],
                                                     email)
                if success:
                    profile_data.email = email

            bday = self.birthday_field.timestamp
            if profile_data.bday != bday:
                success = app.change_profile_section(self.sect_map['birthday'],
                                                     bday)
                if success:
                    profile_data.bday = bday

            about = self.about_field.text
            if profile_data.about != about:
                success = app.change_profile_section(self.sect_map['about'],
                                                     about)
                if success:
                    profile_data.about = about
        self.editing = not self.editing

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(rgba = (0.4, 0.4, 0.4, 1))
            Ellipse(pos = (9, 359),
                    size = (102, 102))

            Color(rgba = (1, 1, 1, 1))
            self.avatar_texture = None
            self.avatar = Ellipse(pos = (10, 360),
                                  size = (100, 100))


        self.file_chooser = AvatarSelectDialog(self)

        self.avatar_change = AvatarSelectButton(pos = (10, 360),
                                                size = (100, 100),
                                                on_press =
                                                self.file_chooser.open)

        self.nick_field = ProfileField(self,
                                       font_name = 'fonts/NotoSans_R.ttf',
                                       pos = (120, 430),
                                       font_size = 15,
                                       background_color = (0, 0, 0, 0),
                                       height = 35)

        self.status_lb = ProfileLabel(pos = (120, 410),
                                      size = (50, 15),
                                      font_size = 12,
                                      text = l['Status:'])
        self.status_field = ProfileField(self,
                                         pos = (120, 375))

        self.email_lb = ProfileLabel(pos = (10, 325),
                                     height = 20,
                                     text = l['Email:'])
        self.email_field = ProfileField(self,
                                        pos = (120, 320))

        self.birthday_lb = ProfileLabel(pos = (10, 285),
                                        height = 20,
                                        text = l['Birthday:'])
        self.birthday_field = DatePicker(pos = (120, 280),
                                         size = (220, 30),
                                         size_hint = (None, None),
                                         disabled = not self.editing)

        self.about_lb = ProfileLabel(pos = (10, 243),
                                     height = 20,
                                     text = l['About:'])
        self.about_field = ProfileField(self,
                                        pos = (120, 115),
                                        height = 155,
                                        multiline = True)

        self.edit_bt = EditButton(text = '[size=18][/size] ' + l['Edit'],
                                  pos = (20, 10),
                                  on_press = self.edit)

        self.delete_dlg = DeleteProfileDialog()

        self.delete_bt = ProfileButton(text = '[size=20][/size] ' +
                                              l['Delete'],
                                       pos = (185, 10),
                                       on_press = self.delete_dlg.open)

        self.fields = [self.avatar_change,
                       self.status_field,
                       self.email_field,
                       self.about_field]

        self.add_widget(self.avatar_change)
        self.add_widget(self.nick_field)
        self.add_widget(self.status_lb)
        self.add_widget(self.status_field)
        self.add_widget(self.email_lb)
        self.add_widget(self.email_field)
        self.add_widget(self.birthday_lb)
        self.add_widget(self.birthday_field)
        self.add_widget(self.about_lb)
        self.add_widget(self.about_field)


class SelfProfile(Profile):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.page.add_widget(self.page.delete_bt)
        self.page.add_widget(self.page.edit_bt)


class MessageInput(TextInput):
    def __init__(self, plch, **kwargs):
        self.placeholder = plch
        self.hint_text = self.placeholder
        super().__init__(**kwargs)

    def on_focus(self, inst, focus):
        self.hint_text = '' if focus or self.text else self.placeholder


class InputBox(BoxLayout):
    pass


class InputButton(Button):
    pass


class DateDropItem(SpinnerOption):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_size = 14
        self.height = 30
        self.background_normal = app.theme['drop_opt_white']
        self.background_down = app.theme['drop_opt_down']
        self.color = (0, 0, 0, 1)


class MonthSelector(Spinner):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.option_cls = DateDropItem
        self.effect_cls = ScrollEffect
        self.background_normal = app.theme['picker_mid']
        self.background_disabled_normal = app.theme['picker_mid']
        self.background_down = app.theme['picker_mid_active']
        self.disabled_color = (0, 0, 0, 1)
        self.color = (0, 0, 0, 1)
        self.font_size = 15
        self.dropdown_cls.max_height = 180


class DateTextField(TextInput):
    def __init__(self, prev, **kwargs):
        self.text_limit = len(prev)
        super().__init__(**kwargs)
        self.disabled_foreground_color = (0, 0, 0, 1)
        self.cursor_color = (0, 0, 0, 1)
        self.multiline = False
        self.write_tab = False
        self.prev = prev
        self.text = prev

    def prepare(self, inst):
        self.prev = self.text
        self.text = ''

    def on_focus(self, inst, state):
        if state:
            Clock.schedule_once(self.prepare, 0.02)
        if not state:
            self.parent.update_date(self)

    def on_text(self, inst, text):
        if not text.isdigit():
            inst.text = text[:-1]
        if len(text) > self.text_limit:
            inst.text = text[:self.text_limit]

    def on_text_validate(self):
        self.text = self.text.zfill(self.text_limit)


class DatePicker(BoxLayout):
    month_match = {l['January']:    1,
                   l['February']:   2,
                   l['March']:      3,
                   l['April']:      4,
                   l['May']:        5,
                   l['June']:       6,
                   l['July']:       7,
                   l['August']:     8,
                   l['September']:  9,
                   l['October']:   10,
                   l['November']:  11,
                   l['December']:  12}

    def update_date(self, inst, tx = None):
        try:
            ts = datetime(int(self.year.text),
                          self.month_match[self.month.text],
                          int(self.day.text))
            self.timestamp = int(ts.timestamp())
        except (ValueError, OverflowError):
            inst.text = inst.prev

    def update_selectors(self, tm):
        self.timestamp = tm
        date_obj = datetime.fromtimestamp(tm)
        self.year.text = str(date_obj.year)
        for month, num in self.month_match.items():
            if num == date_obj.month:
                self.month.text = month
        self.day.text = str(date_obj.day)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.timestamp = 0
        curr_year = datetime.now().year

        self.year = DateTextField(size_hint = (0.25, 1),
                                  background_normal =
                                  app.theme['picker_right'],
                                  background_disabled_normal =
                                  app.theme['picker_right'],
                                  background_active =
                                  app.theme['picker_right_active'],
                                  font_size = 15,
                                  prev = '1970')
        self.month = MonthSelector(size_hint = (0.6, 1),
                                   values = (l['January'], l['February'],
                                             l['March'], l['April'], l['May'],
                                             l['June'], l['July'], l['August'],
                                             l['September'], l['October'],
                                             l['November'], l['December']))

        self.day = DateTextField(size_hint = (0.15, 1),
                                 background_normal =
                                 app.theme['picker_left'],
                                 background_disabled_normal =
                                 app.theme['picker_left'],
                                 background_active =
                                 app.theme['picker_left_active'],
                                 font_size = 15,
                                 prev = '01')

        self.add_widget(self.day)
        self.add_widget(self.month)
        self.add_widget(self.year)


class ExtDateDropItem(DateDropItem):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.font_size = 10
        self.height = 15


class ExtendedDatePicker(DatePicker):
    def update_date(self, inst = None, text = None):
            try:
                ts = datetime(int(self.year.text),
                              self.month_match[self.month.text],
                              int(self.day.text),
                              hour = int(self.hour.text),
                              minute = int(self.minute.text),
                              second = int(self.second.text))
                self.timestamp = ts.timestamp()
            except (ValueError, OverflowError, KeyError):
                inst.text = inst.prev

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.day.font_size = 11
        self.month.font_size = 10
        self.month.dropdown_cls.max_height = 90
        self.month.option_cls = ExtDateDropItem
        self.month.option_cls.on_release = self.update_date
        self.month.size_hint_x = 0.4
        self.month.text = l['January']
        self.day.size_hint_x = 0.18
        self.year.font_size = 11
        self.hour = DateTextField(size_hint = (0.2, 1),
                                  prev = '00',
                                  font_size = 11,
                                  background_normal = app.theme['picker_left'],
                                  background_disabled_normal =
                                  app.theme['picker_left'],
                                  background_active =
                                  app.theme['picker_left_active'])
        self.minute = DateTextField(size_hint = (0.2, 1),
                                    prev = '00',
                                    background_normal =
                                    app.theme['picker_mid'],
                                    background_disabled_normal =
                                    app.theme['picker_mid'],
                                    background_active =
                                    app.theme['picker_mid_active'],
                                    font_size = 11)
        self.second = DateTextField(size_hint = (0.2, 1),
                                    prev = '00',
                                    background_normal =
                                    app.theme['picker_right'],
                                    background_disabled_normal =
                                    app.theme['picker_right'],
                                    background_active =
                                    app.theme['picker_right_active'],
                                    font_size = 11)

        self.add_widget(Widget(size_hint_x = 0.03))
        self.add_widget(self.hour)
        self.add_widget(self.minute)
        self.add_widget(self.second)
        self.update_selectors(datetime.now().timestamp())
        self.update_date()


class ShowPswdButton(ToggleButton):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.4, 0.15)
        self.pos_hint = {"top": 0.16, "right": 0.4}
        self.text = ' ' + l['Show password']
        self.font_name = "fonts/NotoSans_R.ttf"
        self.background_color = (0, 0, 0, 0)
        self.color = (0.4, 0.4, 0.4, 1)

    def on_state(self, bt, value):
        self.parent.toggle_psw(value)


class RegScreen(Screen):
    weak_pswd = l['The password you entered is too weak\n'
                  'It should meet the following requirements:\n'
                  '• It must be at least 8 characters long\n'
                  '• It must contain a number and a letter']
    def check_next(self):
        usr = self.tx_usr.text
        psw = self.tx_pass.text
        con = self.tx_con.text
        self.bt_next.disabled = not (usr and psw and psw == con)

    def toggle_psw(self, state):
        if state == 'down':
            self.show_psw.text = ' ' + l['Hide password']
            self.tx_pass.password = False
            self.tx_con.password = False
        else:
            self.show_psw.text = ' ' + l['Show password']
            self.tx_pass.password = True
            self.tx_con.password = True

    def strong(self, pswd):
        if len(pswd) < 8:
            return False
        let = False
        num = False
        for i in pswd:
            if i.isalpha():
                let = True
            elif i.isdigit():
                num = True
        return let and num

    def register(self, bt = None):
        pswd = self.tx_pass.text
        if not self.strong(pswd):
            ErrorDisp(self.weak_pswd).open()
            return
        app.make_key_pair(callback = app.register)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.top_box = RegisterLayout(size_hint = (1, 0.125),
                                      pos_hint = {"top": 1})

        self.lb_reg = RegLabel(text = l['Register'])

        self.to_login = InputButton(size_hint = (0.25, 1),
                                    font_name = "fonts/NotoSans_R.ttf",
                                    text = ' ' + l['Login'],
                                    on_release = app.to_login,
                                    background_normal =
                                    app.theme['menubt_normal'])

        self.lb_usr = Label(size_hint = (0.28, 0.03),
                            pos_hint = {"top": 0.75, "right": 0.255},
                            text = l['Username'],
                            color = (1, 1, 1, 1),
                            font_size = 16)

        self.tx_usr = NickInput(size_hint = (0.6, 0.13),
                                pos_hint = {"top": 0.795, "right": 0.85},
                                checker = self)

        self.lb_pass = Label(size_hint = (0.28, 0.03),
                             pos_hint = {"top": 0.54, "right": 0.25},
                             text = l['Password'],
                             color = (1, 1, 1, 1),
                             font_size = 16)

        self.tx_pass = NickInput(size_hint = (0.6, 0.13),
                                 pos_hint = {"top": 0.585, "right": 0.85},
                                 password = True,
                                 checker = self)

        self.lb_con = Label(size_hint = (0.28, 0.03),
                            pos_hint = {"top": 0.33, "right": 0.235},
                            text = l['Confirm'],
                            color = (1, 1, 1, 1),
                            font_size = 16)

        self.tx_con = NickInput(size_hint = (0.6, 0.13),
                                pos_hint = {"top": 0.375, "right": 0.85},
                                password = True,
                                checker = self)

        self.bt_next = Button(size_hint = (0.4, 0.15),
                              pos_hint = {"top": 0.15, "right": 0.94},
                              text = l['Next'],
                              font_size = 16,
                              disabled = True,
                              background_normal = app.theme['normal_intro'],
                              background_down = app.theme['down_intro'],
                              background_disabled_normal =
                              app.theme['disabled_intro'],
                              on_release = self.register)

        self.show_psw = ShowPswdButton()

        self.add_widget(self.top_box)

        self.top_box.add_widget(self.lb_reg)
        self.top_box.add_widget(self.to_login)
        self.add_widget(self.lb_usr)
        self.add_widget(self.tx_usr)
        self.tx_usr.focus = True
        self.add_widget(self.lb_pass)
        self.add_widget(self.tx_pass)
        self.add_widget(self.lb_con)
        self.add_widget(self.tx_con)
        self.add_widget(self.bt_next)
        self.add_widget(self.show_psw)


class ErrorLabel(Label):
    pass


class ErrorDisp(Popup):
    def __init__(self, text = '', **kwargs):
        super().__init__(**kwargs)
        self.content = FloatLayout()
        self.btn = Button(size_hint = (0.4, 0.2),
                          pos_hint = {"top": 0.163, "right": 0.94},
                          text = l['Back'],
                          font_size = 15,
                          background_normal = app.theme['normal_intro'],
                          background_down = app.theme['down_intro'],
                          on_release = self.dismiss)
        self.lb = ErrorLabel(text = text,
                             font_size = 13,
                             color = (1, 1, 1, 1),
                             size_hint_y = 2,
                             halign = "left",
                             valign = "top")

        self.scroll = ScrollView(size_hint = (0.95, 0.8),
                             pos_hint = {"top": 0.98, "center_x": 0.5})

        self.content.add_widget(self.scroll)
        self.scroll.add_widget(self.lb)
        self.content.add_widget(self.btn)
        self.title = l['Error']
        self.height = 180


class MenuButton(Button):
    def __init__(self, **kwargs):
        if 'text' in kwargs and 'num' in kwargs:
            text_t = kwargs.pop('text')
            num = kwargs.pop('num')
            self.text = ('[size=24]' + text_t[0] + '[/size]' +
                         ' ' * num[0] + text_t[1] + ' ' * num[1])
        super().__init__(**kwargs)


class MenuDivider(Widget):
    pass


class RecordDivider(Label):
    pass


class LoggedAsLabel(Label):
    pass


class MenuAddBar(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        size_hint_x = 0.3 if app.language == 'English' else 0.4
        self.plc = Widget(size_hint = (1 - size_hint_x, 1))
        self.add_bt = Button(text = '[size=20][/size] ' + l['Add'],
                             size_hint = (size_hint_x, 1),
                             markup = True,
                             font_name = 'fonts/NotoSans_B.ttf',
                             font_size = 16,
                             background_normal = app.theme['menubt_normal'],
                             background_down = app.theme['inputbt_down'])
        self.add_widget(self.plc)
        self.add_widget(self.add_bt)


class UsernameButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.79, 1)
        self.background_color = (0, 0, 0, 0)
        self.color = (0, 0, 0, 1)
        self.disabled_color = (0, 0, 0, 1)


class YesNoDialog(Popup):
    def ch_yes(self, bt):
        pass

    def ch_no(self, bt):
        self.dismiss()

    def __init__(self, title, question, **kwargs):
        super().__init__(**kwargs)
        box = BoxLayout(orientation = "vertical")
        self.height = 200
        self.title = title
        self.title_size = 16

        question_lb = Label(size_hint = (1, 0.7),
                            text = question,
                            color = (1, 1, 1, 1),
                            font_name = "fonts/NotoSans_R.ttf")

        answers = BoxLayout(size_hint = (1, 0.3),
                                 spacing = 4,
                                 padding = 2)
        yes = YesNoButton(text = ' ' + l['Yes'],
                          on_release = self.ch_yes)

        no = YesNoButton(text = ' ' + l['No'],
                         on_release = self.ch_no)

        box.add_widget(question_lb)
        box.add_widget(answers)

        answers.add_widget(yes)
        answers.add_widget(no)

        self.content = box


class LoadSpinner(Image):
    angle = NumericProperty(0)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source = 'themes/loading.png'
        self.anim_delay = 0.01
        anim = Animation(angle = 360, duration=1)
        anim += Animation(angle = 360, duration=1)
        anim.repeat = True
        anim.start(self)

    def on_angle(self, inst, angle):
        if angle == 360:
            inst.angle = 0


class LoadingPopup(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.content = FloatLayout()
        self.load = LoadSpinner(pos_hint = {"top": 0.8, "center_x": 0.5},
                                size_hint = (0.7, 0.7))
        self.content.add_widget(self.load)
        self.title = 'Loading...'
        self.height = 150
        self.width = 150
        self.auto_dismiss = False


class LoadingScreen(Screen):
    phrases = [l["Upgrading Windows, your PC will restart several times"],
               l["Please wait, the bits are breeding"],
               l["Please wait, the little elves are drawing your window"],
               l["Testing your patience"],
               l["Waiting for the satellite to move into position"],
               l["[color=#FFBD33]INSERT COIN[/color]"],
               l["Counting to infinity"],
               l["Please wait, we're making you a cookie"],
               l["Convincing AI not to take over the world"],
               l["Computing the answer to life, the universe, and everything"],
               l["Trying to sort in O(n)"],
               l["Making sure all the i's have dots"],
               l["Cleaning off the cobwebs"]]

    def on_enter(self):
        self.phrase.text = choice(self.phrases)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation = 'vertical')
        self.phrase = FullSizeLabel(size_hint = (1, 0.3),
                                    halign = 'center',
                                    valign = 'center',
                                    markup = True,
                                    color = (0, 0, 0, 1))
        self.load = LoadSpinner(size_hint = (0.5, 0.5),
                                pos_hint = {"center_x": 0.5})
        self.actual = Label(text =
                            l['(actually, just generating encryption keys)'],
                            size_hint = (1, 0.1),
                            font_size = 11,
                            color = (0, 0, 0, 1))
        self.add_widget(self.layout)
        self.layout.add_widget(self.phrase)
        self.layout.add_widget(self.load)
        self.layout.add_widget(Widget(size_hint = (1, 0.1)))
        self.layout.add_widget(self.actual)


class LogoutDialog(YesNoDialog):
    def __init__(self):
        super().__init__(' ' + l['Log out'],
                         l["Do you want to log out?"])

    def ch_yes(self, bt):
        self.dismiss()
        Clock.schedule_once(app.logout, 0.15)


class DeleteProfileDialog(YesNoDialog):
    def __init__(self):
        super().__init__(' ' + l['Delete profile'],
                         l['Are you sure you want\nto delete your profile?\n'
                           'This action can\'t be undone'])

    def ch_yes(self, bt):
        self.dismiss()
        app.delete_profile()


class InfoBox(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            self.avatar_texture = None
            self.avatar = Ellipse(size = (105, 105),
                                  pos = (46, 250))
        self.logged_as_lb = LoggedAsLabel(size_hint = (1, 0.25),
                                          pos_hint = {"top": 1},
                                          font_size = 13,
                                          color = (0, 0, 0, 1))
        self.add_widget(self.logged_as_lb)


class MenuScreen(Screen):
    def build_usr_list(self, users):
        self.users_disp.clear_widgets()

        add = self.users_disp.add_widget
        if users[0]:
            add(self.div_favs)
        for name, online in users[0]:
            add(FavRecord(name, online))

        if users[1]:
            add(self.div_requests)
        for name, message, online in users[1]:
            add(RequestGotRecord(name, online, msg = message))

        add(self.div_online)
        for name, online in users[2]:
            add(FriendRecord(name, online))

        add(self.div_offline)
        for name, online in users[3]:
            add(FriendRecord(name, online))

        if users[4]:
            add(self.div_req_sent)
        for name, message, online in users[4]:
            add(RequestSentRecord(name, online, msg = message))

        if users[5]:
            add(self.div_blacklist)
        for name, online in users[5]:
            add(BlacklistRecord(name, online))

    def initialize_search(self, bt):
        user_list = app.get_search_list()
        self.add_person_popup.user_list = user_list
        self.add_person_popup.open()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.container = BoxLayout()
        self.left_bar = BoxLayout(size_hint = (0.4, 1),
                                  orientation = "vertical")
        self.right_bar = BoxLayout(size_hint = (0.6, 1),
                                   orientation = "vertical")
        self.divider = MenuDivider(size_hint = (0.01, 1))

        self.menu_label = RegLabel(text = l['Menu'],
                                   size_hint = (1, 0.07),
                                   font_size = 17)

        self.info_box = InfoBox(size_hint = (1, 0.3))

        diff = 0 if app.language == 'English' else 4
        self.profile_bt = MenuButton(text = ('', l['Profile']),
                                     num = (13 - diff, 13 - diff),
                                     on_release = app.to_self_profile)

        self.logout_dlg = LogoutDialog()
        self.logout_bt = MenuButton(text = ('', l['Log out']),
                                    num = (12, 12),
                                    on_release = self.logout_dlg.open)

        self.settings_bt = MenuButton(text = ('', l['Settings']),
                                      num = (11 - diff, 12 - diff),
                                      on_release = app.to_settings)

        self.help_bt = MenuButton(text = ('', l['Help']),
                                  num = (15 - diff - 1, 15 - diff - 1),
                                  on_release = app.to_help)

        self.add_bar = MenuAddBar(size_hint = (1, 0.105))

        self.disp_scroll = ScrollView(bar_inactive_color = (0, 0, 0, 0),
                                      bar_color = (0.3, 0.3, 0.3, 0.7),
                                      bar_margin = 3,
                                      do_scroll_x = False,
                                      size_hint = (1, 1))
        self.users_disp = GridLayout(cols = 1,
                                     size_hint_y = None)
        self.users_disp.bind(minimum_height = self.users_disp.setter('height'))

        self.add_person_popup = AddPersonPopup()
        self.add_bar.add_bt.bind(on_press = self.initialize_search)

        self.div_favs = RecordDivider(text = l["favorites"])
        self.div_requests = RecordDivider(text = l["add requests"])
        self.div_online = RecordDivider(text = l["online"])
        self.div_offline = RecordDivider(text = l["offline"])
        self.div_req_sent = RecordDivider(text = l["request sent"])
        self.div_blacklist = RecordDivider(text = l["blacklisted"])

        self.add_widget(self.container)

        self.container.add_widget(self.left_bar)
        self.container.add_widget(self.divider)
        self.container.add_widget(self.right_bar)

        self.left_bar.add_widget(self.menu_label)
        self.left_bar.add_widget(self.info_box)
        self.left_bar.add_widget(self.profile_bt)
        self.left_bar.add_widget(self.logout_bt)
        self.left_bar.add_widget(self.settings_bt)
        self.left_bar.add_widget(self.help_bt)

        self.right_bar.add_widget(self.add_bar)
        self.right_bar.add_widget(self.disp_scroll)
        self.disp_scroll.add_widget(self.users_disp)


class RequestMessage(ErrorDisp):
    def __init__(self, message = '', **kwargs):
        super().__init__(**kwargs)
        self.title = l['Request Message']
        self.lb.text = message


class UserRecord(BoxLayout):
    def _nop(self, bt = None):
        pass

    def f_to_profile(self, bt):
        self.opts.dismiss()
        nick = self.name.text
        app.to_profile(nick, 'menu')

    def f_remove_favs(self, bt):
        self.opts.dismiss()
        app.remove_favs(self.name.text)

    def f_remove_friends(self, bt):
        self.opts.dismiss()
        app.remove_friends(self.name.text)

    def f_add_bl(self, bt):
        self.opts.dismiss()
        app.add_bl(self.name.text, self.status.online)

    def f_add_favs(self, bt):
        self.opts.dismiss()
        app.add_favs(self.name.text, self.status.online)

    def f_get_request_msg(self, bt):
        self.opts.dismiss()
        RequestMessage(self.message).open()

    def f_accept_request(self, bt):
        self.opts.dismiss()
        app.accept_request(self.name.text)

    def f_decline_request(self, bt):
        self.opts.dismiss()
        app.decline_request(self.name.text)

    def f_take_request_back(self, bt):
        self.opts.dismiss()
        app.take_request_back(self.name.text)

    def f_remove_bl(self, bt):
        self.opts.dismiss()
        app.remove_bl(self.name.text)

    def more_action(self, bt):
        self.opts.open(self)

    def __init__(self, nick, online, action = None, **kwargs):
        if not action:
            action = app.to_dialog
        super().__init__(**kwargs)
        self.status = Status(online = online,
                             size_hint = (0.08, 1))
        self.name = UsernameButton(text = nick,
                                   on_press = action)
        self.opts = DropDown()

        self.more = FullSizeButton(text = '',
                                   halign = 'right',
                                   font_name = 'fonts/NotoSans_R.ttf',
                                   font_size = 21,
                                   bound = [20, 0],
                                   color = (0, 0, 0, 1),
                                   size_hint = (0.13, 1),
                                   background_color = (0, 0, 0, 0),
                                   on_release = self.more_action)
        self.size_hint = [1, None]
        self.height = 30

        self.add_widget(self.status)
        self.add_widget(self.name)
        self.add_widget(self.more)


class OptButton(Button):
    def __init__(self, record, **kwargs):
        self.record = record
        super().__init__(**kwargs)


class FavRecord(UserRecord):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.profile = OptButton(self,
                                 text = l['Profile'],
                                 on_press = self.f_to_profile)
        self.remove_favs = OptButton(self,
                                     text = l["Remove from favorites"],
                                     on_press = self.f_remove_favs)
        self.remove_friends = OptButton(self,
                                        text = l["Remove from friends"],
                                        on_press = self.f_remove_friends)
        self.add_bl = OptButton(self,
                                text = l["Add to blacklist"],
                                on_press = self.f_add_bl)

        self.opts.add_widget(self.profile)
        self.opts.add_widget(self.remove_favs)
        self.opts.add_widget(self.remove_friends)
        self.opts.add_widget(self.add_bl)


class FriendRecord(UserRecord):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.profile = OptButton(self,
                                 text = l["Profile"],
                                 on_press = self.f_to_profile)
        self.add_favs = OptButton(self,
                                  text = l["Add to favorites"],
                                  on_press = self.f_add_favs)
        self.remove_friends = OptButton(self,
                                        text = l["Remove from friends"],
                                        on_press = self.f_remove_friends)
        self.add_bl = OptButton(self,
                                text = l["Add to blacklist"],
                                on_press = self.f_add_bl)

        self.opts.add_widget(self.profile)
        self.opts.add_widget(self.add_favs)
        self.opts.add_widget(self.remove_friends)
        self.opts.add_widget(self.add_bl)


class RequestGotRecord(UserRecord):
    def __init__(self, *args, **kwargs):
        self.message = kwargs.pop('msg', '')
        super().__init__(*args, action = self._nop, **kwargs)
        self.profile = OptButton(self,
                                 text = l["Profile"],
                                 on_press = self.f_to_profile)
        self.request_msg = OptButton(self,
                                     text = l["Request message"],
                                     on_press = self.f_get_request_msg)
        self.accept = OptButton(self,
                                text = l["Accept"],
                                on_press = self.f_accept_request)
        self.decline = OptButton(self,
                                 text = l["Decline"],
                                 on_press = self.f_decline_request)

        self.opts.add_widget(self.profile)
        self.opts.add_widget(self.request_msg)
        self.opts.add_widget(self.accept)
        self.opts.add_widget(self.decline)


class RequestSentRecord(UserRecord):
    def __init__(self, *args, msg = '', **kwargs):
        super().__init__(*args, action = self._nop, **kwargs)
        self.message = msg
        self.take_back = OptButton(self,
                                   text = l["Take back"],
                                   on_press = self.f_take_request_back)

        self.request_msg = OptButton(self,
                                     text = l["Request message"],
                                     on_press = self.f_get_request_msg)

        self.opts.add_widget(self.take_back)
        self.opts.add_widget(self.request_msg)


class BlacklistRecord(UserRecord):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.profile = OptButton(self,
                                 text = l["Profile"],
                                 on_press = self.f_to_profile)
        self.remove_bl = OptButton(self,
                                   text = l["Remove from blacklist"],
                                   on_press = self.f_remove_bl)

        self.opts.add_widget(self.profile)
        self.opts.add_widget(self.remove_bl)


class SearchRecord(UserRecord):
    def f_ask_msg(self, bt):
        self.opts.dismiss()
        self.popup.msg_popup.open()

    def f_send_request(self, bt = None):
        msg = self.popup.msg_input.text
        name = self.name.text

        id_match = app.send_request(name, self.status.online, msg)
        if not id_match:
            return

        self.popup.msg_input.text = ''
        self.popup.msg_popup.dismiss()
        self.popup.dismiss()

    def __init__(self, popup, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.popup = popup
        self.popup.msg_confirm.on_release = self.f_send_request
        self.send_req = OptButton(self,
                                  text = l["Send add request"],
                                  on_press = self.f_ask_msg)

        self.opts.add_widget(self.send_req)
        self.name.disabled = True


class LoginScreen(Screen):
    def check_next(self):
        usr = self.tx_usr.text
        psw = self.tx_pass.text
        self.bt_next.disabled = not (usr and psw)

    def toggle_psw(self, state):
        if state == 'down':
            self.show_psw.text = ' ' + l['Hide password']
            self.tx_pass.password = False
        else:
            self.show_psw.text = ' ' + l['Show password']
            self.tx_pass.password = True

    def login(self, bt = None):
        if app.rs.pubkey is None:
            app.make_key_pair(callback = app.login)
        else:
            app.login()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.top_box = LoginLayout(size_hint = (1, 0.15),
                                   pos_hint = {"top": 1})

        self.lb_log = RegLabel(text = l['Login'])

        self.to_register = InputButton(size_hint = (0.37, 1),
                                       font_name = "fonts/NotoSans_R.ttf",
                                       text = '[size=18][/size] ' +
                                              l['Register'],
                                       markup = True,
                                       on_release = app.to_register,
                                       background_normal =
                                       app.theme['menubt_normal'])

        self.lb_usr = Label(size_hint = (0.28, 0.03),
                            pos_hint = {"top": 0.67, "right": 0.255},
                            text = l['Username'],
                            color = (1, 1, 1, 1),
                            font_size = 16)

        self.tx_usr = NickInput(size_hint = (0.6, 0.15),
                                pos_hint = {"top": 0.73, "right": 0.85},
                                checker = self)

        self.lb_pass = Label(size_hint = (0.28, 0.03),
                             pos_hint = {"top": 0.42, "right": 0.25},
                             text = l['Password'],
                             color = (1, 1, 1, 1),
                             font_size = 16)

        self.tx_pass = NickInput(size_hint = (0.6, 0.15),
                                 pos_hint = {"top": 0.475, "right": 0.85},
                                 password = True,
                                 checker = self)

        self.bt_next = Button(size_hint = (0.4, 0.18),
                              pos_hint = {"top": 0.18, "right": 0.94},
                              text = l['Next'],
                              font_size = 16,
                              disabled = True,
                              background_normal = app.theme['normal_intro'],
                              background_down = app.theme['down_intro'],
                              background_disabled_normal =
                              app.theme['disabled_intro'],
                              on_release = self.login)

        self.show_psw = ShowPswdButton()

        self.add_widget(self.top_box)

        self.top_box.add_widget(self.lb_log)
        self.top_box.add_widget(self.to_register)
        self.add_widget(self.lb_usr)
        self.add_widget(self.tx_usr)
        self.tx_usr.focus = True
        self.add_widget(self.lb_pass)
        self.add_widget(self.tx_pass)
        self.add_widget(self.bt_next)
        self.add_widget(self.show_psw)


class FramedScrollView(ScrollView):
    pass


class SettingsItem(BoxLayout):
    def __init__(self, title = '', changer = None, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        with self.canvas:
            Rectangle(size = self.size,
                      pos = self.pos,
                      source = app.theme['menubt_normal'])
        self.changer = changer(size_hint = (0.4, 1))
        self.setting_name = FullSizeLabel(text = title,
                                          bound = (40, 20),
                                          halign = 'left',
                                          size_hint = (0.6, 1))

        self.add_widget(self.setting_name)
        self.add_widget(self.changer)


class SettingsLang(Button):
    def on_press(self):
        self.selector.open()

    def select_lang(self, bt):
        app.language = self.text = bt.text
        self.selector.dismiss()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.options = ['English', 'Русский']
        self.text = app.language
        self.background_color = (0, 0, 0, 0)
        self.selector = Popup(title = l['Select a language'],
                              size = (200, 250))
        self.selector.content = BoxLayout(orientation = 'vertical',
                                          padding = 10,
                                          spacing = 6)
        for lang in self.options:
            bt = Button(text = lang,
                        on_release = self.select_lang)
            self.selector.content.add_widget(bt)

        self.selector.content.add_widget(Widget(size_hint = (1, 0.1)))

        self.cancel = Button(text = l['Cancel'],
                             on_release = self.selector.dismiss)
        self.selector.content.add_widget(self.cancel)


class SettingsTheme(Button):
    def on_press(self):
        self.selector.open()

    def select_thm(self, bt):
        app.theme_name = self.text = bt.text
        self.selector.dismiss()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.options = [l['Blue'], l['Purple'], l['Green'],
                        l['Pink'], l['Gray']]
        self.text = l[app.theme_name]
        self.background_color = (0, 0, 0, 0)
        self.selector = Popup(title = l['Select a theme'],
                              size = (200, 350))
        self.selector.content = BoxLayout(orientation = 'vertical',
                                          padding = 10,
                                          spacing = 6)
        for theme in self.options:
            bt = Button(text = theme,
                        on_release = self.select_thm)
            self.selector.content.add_widget(bt)

        self.selector.content.add_widget(Widget(size_hint = (1, 0.1)))

        self.cancel = Button(text = l['Cancel'],
                             on_release = self.selector.dismiss)
        self.selector.content.add_widget(self.cancel)


class BackBar(BoxLayout):
    def to_menu(self, bt):
        app.to_menu()

    def __init__(self, title, **kwargs):
        super().__init__(**kwargs)
        self.back_bt = Button(text = '  ' + l['Back'],
                              size_hint = (0.15, 1),
                              font_name = 'fonts/NotoSans_B.ttf',
                              background_normal = app.theme['menubt_normal'],
                              background_down = app.theme['inputbt_down'],
                              on_release = self.to_menu)

        self.title = Button(disabled = True,
                            background_disabled_normal =
                            app.theme['menubt_normal'],
                            size_hint = (0.7, 1),
                            text = title,
                            font_name = 'fonts/NotoSans_B.ttf')
        self.plc = Button(disabled = True,
                          background_disabled_normal =
                          app.theme['menubt_normal'],
                          size_hint = (0.15, 1))

        self.add_widget(self.back_bt)
        self.add_widget(self.title)
        self.add_widget(self.plc)


class SettingsBar(BackBar):
    def to_menu(self, bt):
        sets = {'lang': app.language,
                'thm': app.theme_name}
        smiles = self.parent.smile_grid.children
        for sm in smiles:
            sets[str(sm.num)] = sm.text

        with open('settings.json', 'w') as f:
            json.dump(sets, f, ensure_ascii = False, indent = 2)

        app.settings = sets

        app.to_menu()

    def __init__(self, **kwargs):
        super().__init__(l['Settings'], **kwargs)


class SmileInput(MessageInput):
    def on_text(self, inst, text):
        if len(text) > 5:
            self.text = text[:-1]

    def __init__(self, num, **kwargs):
        super().__init__(':)', **kwargs)
        self.num = num
        self.text = app.settings[str(num)]
        self.font_size = 13
        self.background_normal = app.theme['field']
        self.background_active = app.theme['field_active']


class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bar = SettingsBar(size_hint = (1, 0.1),
                               pos_hint = {"top": 1})

        self.lang = SettingsItem(title = l['Language'],
                                 changer = SettingsLang,
                                 pos = (0, 350),
                                 size = (500, 40))

        self.thm = SettingsItem(title = l['UI Theme'],
                                changer = SettingsTheme,
                                pos = (0, 300),
                                size = (500, 40))

        width = 150 if app.language == 'English' else 220
        self.smile_lb = Button(text = l['Custom smiles:'],
                               size_hint = (None, None),
                               disabled = True,
                               background_disabled_normal =
                               app.theme['normal'],
                               size = (width, 30),
                               pos_hint = {"center_x": 0.5, "top": 0.63})

        self.smile_grid = GridLayout(size_hint = (None, None),
                                     size = (400, 80),
                                     pos = (50, 150),
                                     spacing = 20,
                                     cols = 5,
                                     rows = 2)

        for i in range(10):
            tx = SmileInput(i)
            self.smile_grid.add_widget(tx)


        self.add_widget(self.bar)
        self.add_widget(self.lang)
        self.add_widget(self.thm)
        self.add_widget(self.smile_lb)
        self.add_widget(self.smile_grid)


class SearchInput(MessageInput):
    def __init__(self, cont, plch, **kwargs):
        super().__init__(plch, **kwargs)
        self.cont = cont

    def on_text(self, inst, text):
        if len(text) > 15:
            self.text = text[:15]
        inst.cont.update_result(self.text)


class AddPersonPopup(Popup):
    def update_result(self, query):
        self.users_disp.clear_widgets()

        add = self.users_disp.add_widget

        for name, online in self.matches(query):
            add(SearchRecord(self, name, online))

    def on_dismiss(self):
        if not self.keep_text:
            self.tx_nick.text = ''
        self.user_list = None

    def matches(self, query):
        if self.user_list is None or not query:
            return []

        return [i for i in self.user_list if query.lower() in i[0].lower()]

    def on_open(self):
        self.tx_nick.focus = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_list = None
        self.title = l['Add a user']
        self.size_hint = (None, None)
        self.size = 400, 350
        self.keep_text = False
        self.box = BoxLayout(orientation = 'vertical',
                             spacing = 15,
                             padding = 10)
        self.tx_nick = SearchInput(self,
                                   l['Enter a username...'],
                                   size_hint = (1, 0.12),
                                   multiline = False,
                                   font_size = 13)

        self.disp_scroll = FramedScrollView(bar_inactive_color = (0, 0, 0, 0),
                                            bar_color = (0.3, 0.3, 0.3, 0.7),
                                            bar_margin = 3,
                                            do_scroll_x = False,
                                            size_hint = (1, 0.88))
        self.users_disp = GridLayout(cols = 1,
                                     size_hint_y = None)
        self.users_disp.bind(minimum_height = self.users_disp.setter('height'))

        self.msg_popup = Popup(height = 180,
                               title = l['Message (optional)'],
                               title_font = 'fonts/NotoSans_R.ttf')
        self.msg_cont = FloatLayout()
        self.msg_input = MessageInput('',
                                      size_hint = (0.98, 0.65),
                                      font_size = 13,
                                      pos_hint =
                                      {"top": 0.95, "center_x": 0.5})
        self.msg_confirm = Button(size_hint = (0.4, 0.25),
                                  pos_hint = {"top": 0.22, "right": 0.94},
                                  text = l['OK'],
                                  font_size = 15,
                                  background_normal =
                                  app.theme['normal_intro'],
                                  background_down = app.theme['down_intro'])

        self.msg_cont.add_widget(self.msg_input)
        self.msg_cont.add_widget(self.msg_confirm)
        self.msg_popup.content = self.msg_cont

        self.add_widget(self.box)
        self.box.add_widget(self.tx_nick)
        self.box.add_widget(self.disp_scroll)
        self.disp_scroll.add_widget(self.users_disp)


class MsgInfoPopup(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.info_view = InfoView()

        self.height = 270
        self.content = self.info_view
        self.title = l['Message Info']


class DialogScreen(Screen):
    def load_more(self, bt):
        msgs = app.get_message_history(self.number,
                                       self.msg_layout.loaded + app.msg_amount)
        self.msg_grid.clear_widgets()
        self.build_msgs(msgs)

    def build_msgs(self, msgs):
        self.msg_layout.loaded = len(msgs)
        for message in msgs:
            text, tm, nick = message
            msg_row = MessageRow(text, tm, escape_markup(nick), self)
            self.msg_grid.add_widget(msg_row)

    def __init__(self, number = -1, **kwargs):
        self.number = number
        super().__init__(**kwargs)

        self.smiles = [':)', ':D', ':]', ':3', '=)', ':D',
                       'xD', '=D', '>:(', ':-(', ':(', ':c',
                       ':<', ':[', ':{', ':\'(', ':\'-)',':P',
                       ':\')', '>:O', ':o', 'O_O', 'O_o', 'XP',
                       ':*', ';-)', ';)', ';-]', ';]', ';D',
                       ':-p', ':p', ':-Þ', ':Þ', ':þ', ':-b',
                       ':b', '>:/', ':-.', ':/', '=/', '>:P',
                       ':L', '>.<', '-_-', ':|', 'O:-)', '0:3',
                       '0:)', '>:)', '>;)', '>:-)', '%)', '<:-|',
                       '</3', '<3', '^_^', '^^', '(._.)', '/(._. )']

        self.main_box = BoxLayout(orientation = "vertical")

        self.button_bar = DialogButtonBar(self,
                                          size_hint = (1, 0.061))
        self.status_bar = DialogStatusBar(size_hint = (1, 0.059))

        self.msg_layout = MessageView(size_hint = (1, 0.66),
                                      bar_inactive_color = (0, 0, 0, 0),
                                      do_scroll_x = False,
                                      bar_margin = 3)

        self.msg_grid = GridLayout(cols = 1,
                                   padding = 10,
                                   spacing = 10,
                                   size_hint_y = None)
        self.msg_grid.bind(minimum_height = self.msg_grid.setter('height'))
        # For modifying the height when new widgets are added

        self.input_bar = DialogInputBar(size_hint = (1, 0.2))

        self.smile_bbl = SmileBubble(self)

        self.info_popup = MsgInfoPopup()

        self.add_widget(self.main_box)
        self.main_box.add_widget(self.button_bar)
        self.main_box.add_widget(self.status_bar)
        self.main_box.add_widget(self.msg_layout)
        self.main_box.add_widget(self.input_bar)

        self.msg_layout.add_widget(self.msg_grid)


class DialogButton(Button):
    pass


class DialogOptButton(Button):
    def __init__(self, sym, text, space, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.font_size = 12
        self.background_normal = app.theme['drop_opt']
        self.background_down = app.theme['drop_opt_down']
        self.font_name = 'fonts/NotoSans_B.ttf'
        self.height = 22
        self.markup = True
        self.text = ('[size=15]' + sym + '[/size] ' +
                     ' ' * space + text + ' ' * space)


class DialogButtonBar(BoxLayout):
    def drop_open(self, bt):
        self.opts_drop.open(self.opts_extender)

    def search_msg(self, bt):
        self.opts_drop.dismiss()
        SearchMsgPopup(self.scr).open()

    def __init__(self, scr, **kwargs):
        super().__init__(**kwargs)
        self.scr = scr

        self.menu = DialogButton(text = ' ' + l['Menu'],
                                 halign = 'left',
                                 size_hint = (0.2, 1),
                                 on_release = app.to_menu)
        self.plc = Button(background_disabled_normal =
                          app.theme['menubt_normal'],
                          disabled = True,
                          size_hint = (0.34, 1))

        self.opts_extender = BoxLayout(size_hint = (0.46, 1))
        self.opts_drop = DropDown()
        self.opts = DialogButton(text = l['Options'] + ' ',
                                 halign = 'right',
                                 on_release = self.drop_open)
        self.opts_plc = Button(background_disabled_normal =
                               app.theme['menubt_normal'],
                               disabled = True)

        off = 0 if app.language == 'English' else 3
        self.load_bt = DialogOptButton('', l[' Load older messages'], 1 + off,
                                       on_release = scr.load_more)
        self.search_bt = DialogOptButton('', l['Search for messages'], 2,
                                         on_release = self.search_msg)

        self.opts_drop.add_widget(self.load_bt)
        self.opts_drop.add_widget(self.search_bt)
        self.opts_drop.add_widget(self.delete_bt)

        self.opts_extender.add_widget(self.opts_plc)
        self.opts_extender.add_widget(self.opts)

        self.add_widget(self.menu)
        self.add_widget(self.plc)
        self.add_widget(self.opts_extender)


class SearchMsgButton(Button):
    def on_release(self):
        self.cont.from_picker.update_date()
        self.cont.to_picker.update_date()

        l_tm = int(self.cont.from_picker.timestamp) * 100
        u_tm = int(self.cont.to_picker.timestamp) * 100
        text = self.cont.text_to_search.text
        if l_tm > u_tm:
            ErrorDisp(l['The beginning time exceeds the end']).open()
        else:
            msgs = app.search_message(self.cont.scr.number, text, l_tm, u_tm)
            self.cont.build_msgs(msgs)

    def __init__(self, cont, **kwargs):
        super().__init__(**kwargs)
        self.cont = cont
        self.font_name = 'fonts/NotoSans_R.ttf'
        self.background_normal = app.theme['normal']
        self.background_down = app.theme['down']


class SearchMsgPopup(Popup):
    def build_msgs(self, msg_list):
        self.msg_grid.clear_widgets()
        for text, curr_time, nick in msg_list:
            msg_row = MessageRow(text,
                                 curr_time,
                                 escape_markup(nick),
                                 self.scr)

            self.msg_grid.add_widget(msg_row)

    def __init__(self, scr, **kwargs):
        super().__init__(**kwargs)
        self.title = l['Search for messages']
        self.size = (300, 400)
        self.scr = scr

        self.content = BoxLayout(orientation = "vertical",
                                 padding = 10,
                                 spacing = 10)
        self.from_box = BoxLayout(size_hint = (1, 0.1))
        self.to_box = BoxLayout(size_hint = (1, 0.1))

        self.from_lb = Label(text = l['From: '],
                             size_hint = (0.2, 1),
                             color = (1, 1, 1, 1))
        self.to_lb = Label(text = l['To: '],
                           size_hint = (0.2, 1),
                           color = (1, 1, 1, 1))
        self.from_picker = ExtendedDatePicker()
        self.to_picker = ExtendedDatePicker()

        self.from_box.add_widget(self.from_lb)
        self.from_box.add_widget(self.from_picker)
        self.to_box.add_widget(self.to_lb)
        self.to_box.add_widget(self.to_picker)

        self.src_button = SearchMsgButton(self,
                                          text = ' ' + l['Search'],
                                          size_hint = (1, 0.1))

        self.text_to_search = MessageInput(l["Text to search..."],
                                           size_hint = (1, 0.3),
                                           font_size = 13)

        self.msg_layout = MessageView(size_hint = (1, 0.5),
                                      bar_inactive_color = (0, 0, 0, 0),
                                      do_scroll_x = False,
                                      bar_margin = 3,)

        self.msg_grid = GridLayout(cols = 1,
                                   padding = 10,
                                   spacing = 10,
                                   size_hint_y = None)
        self.msg_grid.bind(minimum_height = self.msg_grid.setter('height'))

        self.msg_layout.add_widget(self.msg_grid)

        self.content.add_widget(self.from_box)
        self.content.add_widget(self.to_box)
        self.content.add_widget(self.text_to_search)
        self.content.add_widget(self.src_button)
        self.content.add_widget(self.msg_layout)


class DialogStatusBar(BoxLayout):
    def view_profile(self, bt):
        app.to_profile(self.name.text, app.person)

    def update_names(self, bt):
        self.nick = app.login_scr.tx_usr.text
        if not self.nick:
            self.nick = app.register_scr.tx_usr.text
        self.self_name.text = self.nick

        self.name.text = app.person
        self.status.online = bt.parent.status.online

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.self_name = NickLabel(halign = "right",
                                   on_release = app.to_self_profile)
        self.self_status = Status(size_hint = (0.1, 1))

        self.name = NickLabel(halign = "left",
                              on_release = self.view_profile)
        self.status = Status(size_hint = (0.1, 1))

        self.add_widget(self.self_status)
        self.add_widget(self.self_name)
        self.add_widget(Widget())
        self.add_widget(self.name)
        self.add_widget(self.status)


class MessageRow(BoxLayout):
    def __init__(self, text, tm, sender, scr, **kwargs):
        super().__init__(**kwargs)
        self.scr = scr
        self.spacing = 1

        self.msg = Message(text, tm, sender, scr,
                           size_hint = (0.7, 1))
        self.tm = ClockLabel(tm,
                             size_hint = (0.1, 1))

        self.height = self.msg.height
        self.size_hint = [1, None]

        if sender != app.nick:
            self.add_widget(Widget(size_hint = (0.2, 1)))
            self.add_widget(self.tm)
            self.add_widget(self.msg)
        else:
            self.add_widget(self.msg)
            self.add_widget(self.tm)
            self.add_widget(Widget(size_hint = (0.2, 1)))


class DialogInputBar(BoxLayout):
    def smile_show(self, bt):
        if self.scr is None:
            self.scr = self.parent.parent
        if self.scr.smile_bbl.hidden:
            self.scr.add_widget(self.scr.smile_bbl)
            self.scr.smile_bbl.hidden = False
        else:
            self.scr.remove_widget(self.scr.smile_bbl)
            self.scr.smile_bbl.hidden = True

    def send_msg(self, bt = None):
        text = self.msg_input.text.strip('\n ')
        if text not in string.whitespace:
            self.add_msg(text, app.nick)

    def add_msg(self, text, nick):
        curr_time = int(time.time() * 100)
        if self.scr is None:
            self.scr = self.parent.parent

        id_match = app.send_message(text, curr_time, self.scr.number)
        if not id_match:
            return

        self.msg_input.text = ''

        msg_row = MessageRow(text, curr_time, escape_markup(nick), self.scr)

        self.scr.msg_grid.add_widget(msg_row)
        self.scr.msg_layout.scroll_to(msg_row)
        self.scr.msg_layout.loaded += 1

    def add_smile(self, bt):
        self.msg_input.text += ' ' + bt.text + ' '

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.btn_panel = BoxLayout(orientation = "vertical",
                           size_hint = (0.1, 1))

        self.input_panel = InputBox(size_hint = (0.9, 1))

        self.msg_input = MessageInput(l['Your message here...'],
                                      font_size = 13)

        self.bt_send = InputButton(size_hint = (1, 0.35),
                                   text = "",
                                   font_size = 20,
                                   on_release = self.send_msg)

        self.bt_smile = InputButton(size_hint = (1, 0.65),
                                    text = "",
                                    font_size = 22,
                                    on_release = self.smile_show)

        self.scr = None

        self.add_widget(self.input_panel)
        self.add_widget(self.btn_panel)

        self.input_panel.add_widget(self.msg_input)

        self.btn_panel.add_widget(self.bt_smile)
        self.btn_panel.add_widget(self.bt_send)


class ProfileData:
    def __init__(self, nick, status, email, bday, about, image_data):
        self.nick = nick
        self.status = status
        self.bday = bday
        self.email = email
        self.about = about
        self.image_data = image_data


class ChatApp(App):
    nick_ptrn = re.compile('(?![ ]+)[\w ]{2,15}')
    invalid_nick = l['The username you entered is incorrect. '
                     'It should only consist of letters and spaces, '
                     'it cannot consist of spaces only and must be '
                     '2 to 15 characters long']
    nick_taken = l['There is already a user with the username you entered. '
                   'Try something different']
    wrong_pswd = l['You entered a wrong password for this username. '
                   'Try again']
    lost_conn = l['An error occured when connecting to the server.\nPossible '
                  'causes:\n• another session is opened from the same IP-'
                  'address\n• no Internet connection\n• no response from the '
                  'server\nPlease, restart the application']
    profiles = {}
    msg_amount = 50
    language = StringProperty('English')
    theme_name = StringProperty(l['Blue'])
    colors_from = {'purple': {'light': (0.83, 0.83, 0.9, 1),
                              'dark': (0.31, 0.31, 0.44),
                              'tab': (0.74, 0.54, 0.9, 1),
                              'msg': (0.95, 0.91, 1, 1),
                              'border': (0.96, 0.85, 1, 1)},
                   'blue': {'light': (0.71, 0.85, 1, 1),
                            'dark': (0.16, 0.36, 0.56),
                            'tab': (0, 0.58, 1, 1),
                            'msg': (0.91, 0.95, 1, 1),
                            'border': (0.85, 0.92, 1, 1)},
                   'green': {'light': (0.79, 0.91, 0.76, 1),
                             'dark': (0.16, 0.53, 0.35),
                             'tab': (0.38, 0.77, 0.32, 1),
                             'msg': (0.91, 1, 0.91, 1),
                             'border': (0.85, 1, 0.87, 1)},
                   'pink': {'light': (1, 0.89, 0.83, 1),
                            'dark': (0.8, 0.55, 0.55),
                            'tab': (1, 0.59, 0.53, 1),
                            'msg': (1, 0.91, 0.99, 1),
                            'border': (1, 0.85, 0.98, 1)},
                   'gray': {'light': (0.92, 0.92, 0.89, 1),
                            'dark': (0.38, 0.4, 0.41),
                            'tab': (0.31, 0.31, 0.32, 1),
                            'msg': (0.91, 0.91, 0.91, 1),
                            'border': (0.88, 0.88, 0.88, 1)}}

    def back_to_search(self, bt = None):
        self.screens.current = 'menu'
        Window.size = (500, 450)
        self.menu_scr.add_person_popup.open()

    def back_to_screen(self, bt = None):
        if self.return_scr == 'menu':
            Window.size = (500, 450)
        self.screens.current = self.return_scr

    def to_login(self, bt = None):
        Window.size = (370, 200)
        self.screens.transition = self.no_trans
        self.screens.current = 'login'
        self.login_scr.tx_usr.focus = True

    def to_register(self, bt = None):
        Window.size = (370, 240)
        self.screens.transition = self.no_trans
        self.screens.current = 'register'
        self.register_scr.tx_usr.focus = True

    def to_self_profile(self, bt = None):
        self.back_action = self.back_to_screen
        if isinstance(bt, MenuButton):
            self.return_scr = 'menu'
        else:
            self.return_scr = app.person

        self.profile_scr.profile_bar.back_bt.on_release = self.back_action

        Window.size = (350, 500)
        self.screens.transition = self.no_trans
        self.self_profile_scr.set_up_for(self.nick)
        self.screens.current = 'self_profile'

    def to_menu(self, bt = None):
        Window.size = (500, 450)
        self.screens.transition = self.no_trans
        self.screens.current = 'menu'

    def to_profile(self, nick, return_scr):
        Thread(target = self.get_profile_info, args = (nick,),
               kwargs = {'switch': True}).start()
        self.return_scr = return_scr
        self.load_popup.open()

    @mainthread
    def profile_switch(self, nick):
        self.back_action = self.back_to_screen

        self.profile_scr.profile_bar.back_bt.on_release = self.back_action

        Window.size = (350, 500)
        self.profile_scr.set_up_for(nick)
        self.load_popup.dismiss()
        self.screens.current = 'profile'

    def to_settings(self, bt = None):
        self.screens.current = 'settings'

    def to_help(self, bt = None):
        self.screens.current = 'help'

    def to_dialog(self, bt):
        Window.size = (350, 500)
        name = bt.text
        self.person = name
        d_scr = self.screens.get_screen(name)
        msgs = app.get_message_history(d_scr.number, app.msg_amount)
        d_scr.build_msgs(msgs)

        d_scr.status_bar.update_names(bt)
        d_scr.smile_bbl.build_btns()
        d_scr.input_bar.msg_input.focus = True

        self.screens.current = self.person

    def add_favs(self, name, status):
        for _name, _status in self.users[0]:
            if name == _name:
                return

        id_match = self.rs.add_to_favorites(name)
        if not id_match:
            return

        self.users[0].append((name, status))
        self.menu_scr.build_usr_list(self.users)

    def remove_favs(self, name):
        id_match = self.rs.remove_from_favorites(name)
        if not id_match:
            return

        for idx, el in enumerate(self.users[0]):
            if el[0] == name:
                self.users[0].pop(idx)
                break
        self.menu_scr.build_usr_list(self.users)

    def remove_friends(self, name):
        id_match = self.rs.delete_from_friends(name)
        if not id_match:
            return False

        for user_list in (self.users[0], self.users[2], self.users[3]):
            for idx, el in enumerate(user_list):
                if el[0] == name:
                    user_list.pop(idx)
                    break
        self.menu_scr.build_usr_list(self.users)
        self.screens.remove_widget(self.screens.get_screen(name))

    def add_bl(self, name, status):
        id_match = self.rs.add_to_blacklist(name)
        if not id_match:
            return False

        for user_list in self.users[:5]:
            for idx, el in enumerate(user_list):
                if el[0] == name:
                    user_list.pop(idx)
                    break
        self.users[5].append((name, status))
        self.menu_scr.build_usr_list(self.users)

    def remove_bl(self, name):
        id_match = self.rs.remove_from_blacklist(name)
        if not id_match:
            return False

        for idx, el in enumerate(self.users[6]):
            if el[0] == name:
                self.users[6].pop(idx)
                break
        self.menu_scr.build_usr_list(self.users)

    def accept_request(self, name):
        id_match = self.rs.confirm_add_request(name)
        if not id_match:
            return False

        self.get_user_groups()

        id_match, num = self.rs.create_dialog(name)
        if not id_match:
            return False
        self.screens.add_widget(DialogScreen(number = int(num[0]),
                                             name = name))

    def decline_request(self, name):
        id_match = self.rs.decline_add_request(name)
        if not id_match:
            return

        for idx, el in enumerate(self.users[1]):
            if el[0] == name:
                self.users[1].pop(idx)
                break
        self.menu_scr.build_usr_list(self.users)

    def take_request_back(self, name):
        id_match = self.rs.take_request_back(name)
        if not id_match:
            return False

        for idx, el in enumerate(self.users[4]):
            if el[0] == name:
                self.users[4].pop(idx)
                break
        self.menu_scr.build_usr_list(self.users)

    def send_request(self, name, status, msg):
        id_match = self.rs.send_request(name, msg)
        if not id_match:
            return False

        self.users[4].append((name, msg, status))
        self.menu_scr.build_usr_list(self.users)
        return True

    def get_user_groups(self, bt = None):
        id_match, users = self.rs.get_friends_group()
        if not id_match:
            return False
        users = users[0]
        id_match, requests = self.rs.get_add_requests()
        if not id_match:
            return False
        requests = requests[0]

        for user in (name[0] for group in users[1:] for name in group if name):
            id_match, num = self.rs.create_dialog(user)
            if not id_match:
                continue

            self.screens.add_widget(DialogScreen(name = user,
                                                 number = int(num[0])))

        users.insert(1, requests[0])
        users.insert(4, requests[1])
        self.users = users
        self.menu_scr.build_usr_list(users)

    def make_key_pair(self, callback):
        self.screens.current = 'loading'
        self.rs.ioloop.add_callback(self.rs.make_key_pair)
        check = partial(self.check_key_progress, callback)
        self.key_wait = Clock.schedule_interval(check, 0.5)

    def check_key_progress(self, callback, tm):
        if self.rs.key_made:
            self.key_wait.cancel()
            callback()

    def register(self, bt = None):
        if not re.match(self.nick_ptrn,
                        self.register_scr.tx_usr.text):
            ErrorDisp(self.invalid_nick).open()
            return

        nick = self.register_scr.tx_usr.text
        pswd = self.register_scr.tx_pass.text
        status, id_match = self.rs.register(nick, pswd)
        if not id_match:
            return False

        if not status:
            self.screens.current = 'register'
            ErrorDisp(self.nick_taken).open()
            return

        self.nick = self.register_scr.tx_usr.text
        info_box = self.menu_scr.info_box
        info_box.logged_as_lb.text = l["Logged in as\n"] + self.nick

        self.get_profile_info(self.nick)

        profile = self.profiles[self.nick]

        info_box.avatar_texture = CoreImage(BytesIO(profile.image_data),
                                            ext = 'png')
        info_box.avatar.texture = info_box.avatar_texture.texture

        self.get_user_groups()

        self.to_menu()

    def login(self, bt = None):
        nick = self.login_scr.tx_usr.text
        pswd = self.login_scr.tx_pass.text
        status, id_match = self.rs.login(nick, pswd)
        if not id_match:
            return False

        if not status:
            self.screens.current = 'login'
            ErrorDisp(self.wrong_pswd).open()
            return

        self.nick = nick
        info_box = self.menu_scr.info_box
        info_box.logged_as_lb.text = l["Logged in as\n"] + self.nick

        self.get_profile_info(self.nick)

        profile = self.profiles[self.nick]

        info_box.avatar_texture = CoreImage(BytesIO(profile.image_data),
                                            ext = 'png')
        info_box.avatar.texture = info_box.avatar_texture.texture

        self.get_user_groups()

        self.to_menu()

    def logout(self, tm = None, request = True):
        # The `tm` argument is only here because Clock passes it
        if request:
            id_match = self.rs.logout()
            if not id_match:
                return
        self.login_scr.tx_usr.text = ''
        self.login_scr.tx_pass.text = ''
        self.register_scr.tx_usr.text = ''
        self.register_scr.tx_pass.text = ''
        users_with_dialogs = [self.users[i] for i in (2, 3, 5)]
        for i in (name[0] for group in users_with_dialogs for name in group):
            scr = self.screens.get_screen(i)
            self.screens.remove_widget(scr)
        self.to_login()

    def get_search_list(self):
        id_match, search_result = self.rs.get_search_list()
        if not id_match:
            return []
        search_result = search_result[0]
        return search_result

    def search_message(self, dialog, text, l_tm, u_tm):
        id_match, search_results = self.rs.search_msg(dialog, text, l_tm, u_tm)
        if not id_match:
            return []
        return search_results[0]

    def send_message(self, text, tm, dialog):
        return self.rs.send_message(text, tm, dialog)

    def get_profile_info(self, nick, switch = False):
        id_match, profile_info = self.rs.get_profile_info(nick)
        if not id_match:
            return

        data = ProfileData(nick, *profile_info)
        self.profiles[nick] = data
        if switch:
            self.profile_switch(nick)

    def change_profile_section(self, sect, chg):
        return self.rs.change_profile_section(sect, chg)

    def set_image(self, img_data):
        return self.rs.set_image(img_data)

    def delete_profile(self):
        id_match = self.rs.delete_profile()
        if not id_match:
            return
        self.profiles.pop(self.nick)
        self.logout(request = False)

    def get_message_history(self, dialog_number, amount):
        id_match, history = self.rs.get_message_history(amount, dialog_number)
        if not id_match:
            return []
        return history[0]

    def open_settings(self):
        pass

    def check_for_signals(self, tm):
        try:
            signal = self.rs.signals.get_nowait()
            self._process_signal(signal)
        except queue.Empty:
            pass

    def _process_signal(self, sig):
        if sig == -1:
            err = ErrorDisp(self.lost_conn)
            err.bind(on_dismiss = lambda x: stopTouchApp())
            err.open()
        elif sig == 8:
            scr = self.screens.get_screen(self.screens.current)
            if isinstance(scr, DialogScreen):
                amount = scr.msg_layout.loaded + 1
                scr.msg_layout.loaded += 1
                scr.build_msgs(self.get_message_history(scr.number, amount))
        elif sig == 10:
            self.get_user_groups()
        else:
            Logger.error('Client: Unknown signal {}, ignoring'.format(sig))

    def key_pressed(self, window, char, keycode, text, modifiers):
        scr_name = self.screens.current
        scr = self.screens.get_screen(scr_name)
        if keycode == 40:
            # If the `Enter` key has been pressed
            if scr_name == 'login':
                self.login_scr.login()
            elif scr_name == 'register':
                self.register_scr.register()
            elif isinstance(scr, DialogScreen) and modifiers == ['shift']:
                scr.input_bar.send_msg()
                scr.input_bar.msg_input.text = ''

    def on_stop(self):
        if self.screens.current not in ('register', 'login', 'loading'):
            self.logout()
        self.rs.ioloop.stop()

    def build(self):
        Window.bind(on_key_down = self.key_pressed)
        self.rs = RequestSender()

        # Spin out a separate thread for communication with the server
        Thread(target = self.rs.run).start()
        Clock.schedule_interval(self.check_for_signals, 0.5)

        self.nick = ''
        self.person = ''

        self.settings = _get_settings()

        self.language = self.settings['lang']
        self.theme_name = self.settings['thm']
        self.theme = TextureResolver('themes/' + self.theme_name.lower())
        self.colors = self.colors_from[self.theme_name.lower()]

        Window.clearcolor = self.colors['light']

        self.return_scr = 'menu'
        self.back_action = self.back_to_screen

        self.no_trans = NoTransition()
        self.slide_trans = SlideTransition(direction = "up")

        self.screens = ScreenManager(transition = self.no_trans)

        self.register_scr = RegScreen(name = "register")
        self.login_scr = LoginScreen(name = "login")
        self.menu_scr = MenuScreen(name = "menu")
        self.self_profile_scr = SelfProfile(name = "self_profile")
        self.profile_scr = Profile(name = "profile")
        self.settings_scr = SettingsScreen(name = "settings")
        self.help_scr = HelpScreen(name = "help")
        self.load_scr = LoadingScreen(name = "loading")

        self.load_popup = LoadingPopup()

        self.screens.add_widget(self.login_scr)
        self.screens.add_widget(self.register_scr)
        self.screens.add_widget(self.menu_scr)
        self.screens.add_widget(self.self_profile_scr)
        self.screens.add_widget(self.profile_scr)
        self.screens.add_widget(self.settings_scr)
        self.screens.add_widget(self.help_scr)
        self.screens.add_widget(self.load_scr)

        return self.screens


if __name__ == "__main__":
    app = ChatApp()
    app.run()