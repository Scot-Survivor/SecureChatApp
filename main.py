import kivy  # Import the main package
import re  # For regular Expressions
import os  # For i/o implications
import socket_client  # For talking with the server
from kivy.app import App  # Import the base class for the app
from kivy.uix.label import Label  # import label for text display
from kivy.uix.gridlayout import GridLayout  # Lay out type the pages. Layout within layout are used
from kivy.uix.textinput import TextInput  # Allow for text input from end user
from kivy.uix.button import Button  # Import the button class
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock  # For Task Scheduling
from kivy.core.window import Window
from kivy.uix.widget import Widget  # Custom widgets
from kivy.uix.behaviors.button import ButtonBehavior  # Allow for circular button
from kivy.uix.filechooser import \
    FileChooserIconView  # used for files this part of the app is currently in DEV and should not be used
from kivy.vector import Vector  # Math time

kivy.require("1.11.1")  # Make sure that the correct Kivy version is used mainly for dev purposes


class DarkGreyLabel(Label):
    pass


class WhiteLabel(Label):
    pass


class DarkGreyGridLayout(GridLayout):
    pass


class SlightlyBlackScrollView(ScrollView):
    pass


class SlightlyLessBlackGridLayout(GridLayout):
    pass


class CircularButton(ButtonBehavior, Widget):
    def collide_point(self, x, y):
        return Vector(x, y).distance(self.center) <= self.width / 2


class ScrollableLabel(SlightlyBlackScrollView):
    def __init__(self, **kwargs):
        super(ScrollableLabel, self).__init__(**kwargs)
        self.text_widgets = []
        # Add a layout as a widget to add multiple widgets
        self.layout = GridLayout(cols=1, size_hint_y=None)  # Use none to stop the layout snapping to window size
        self.add_widget(self.layout)

        # Two widgets One for chat history and one artificial one for the widget below
        # Enable markup for colour support
        self.ChatHistory = Label(size_hint_y=None, markup=True)
        self.ScrollToPoint = Label()

        # Add them to layout
        self.layout.add_widget(self.ChatHistory)
        self.layout.add_widget(self.ScrollToPoint)

    def update_chat_history(self, data_type, message):
        if data_type == "message":
            # First add a new line and the message its self
            self.ChatHistory.text += '\n' + message

            # Set the height of the layout to whatever the text is + 15 pixels
            # set chat history label to whatever the height of chat history text is
            # set width to chat history text to 98% of the label (Small borders)
            self.layout.height = self.ChatHistory.texture_size[1] + 15
            self.ChatHistory.height = self.ChatHistory.texture_size[1]
            self.ChatHistory.text_size = (self.ChatHistory.width * 0.98, None)

            # As we are updating above, text height, so also label and layout height are going to be bigger
            # than the area we have for this widget. ScrollView is going to add a scroll, but won't
            # scroll to the bottom, nor is there a method that can do that.
            # That's why we want additional, empty widget below whole text - just to be able to scroll to it,
            # so scroll to the bottom of the layout
            self.scroll_to(self.ScrollToPoint)


class IPInput(TextInput):
    pat = re.compile(r'[^a-z0-9.]')

    # noinspection PyUnusedLocal
    def insert_text(self, substring, from_undo=False):
        pat = self.pat
        s = ''.join([re.sub(pat, '', substring)])
        return super(IPInput, self).insert_text(s, from_undo)


class PortInput(TextInput):
    pat = re.compile(r'[^0-9]')

    def insert_text(self, substring, from_undo=False):
        pat = self.pat
        s = ''.join([re.sub(pat, '', substring)])
        return super(PortInput, self).insert_text(s, from_undo)


class UsernameInput(TextInput):
    pat = re.compile(r'[^a-zA-Z0-9_]')

    def insert_text(self, substring, from_undo=False):
        pat = self.pat
        s = ''.join([re.sub(pat, '', substring)])
        if len(self.text) > 20:
            self.text = self.text[:-(len(self.text) - 20)]
        return super(UsernameInput, self).insert_text(s, from_undo)


class MessageInput(TextInput):
    pat = re.compile(r'[^ a-zA-Z0-9\[\]/?.!,\'"\^_~]')

    def insert_text(self, substring, from_undo=False):
        pat = self.pat
        s = "".join([re.sub(pat, '', substring)])
        if len(self.text) > 100:
            self.text = self.text[:-(len(self.text) - 100)]
        return super(MessageInput, self).insert_text(s, from_undo)


class PasswordInput(TextInput):
    def insert_text(self, substring, from_undo=False):
        if len(self.text) > 35:
            self.text = self.text[:-len(self.text) - 35]
        return super(PasswordInput, self).insert_text(substring, from_undo)


class ConnectPage(SlightlyLessBlackGridLayout):  # This grabs from Gridlayout for ease of use
    def __init__(self, colour_list, **kwargs):  # Allow for extra data
        super(ConnectPage, self).__init__(**kwargs)  # Initialise the super class
        # Create colours
        self.ColourList = colour_list
        # Create the main layout
        InputField = GridLayout(rows=10, cols=2, height=(Window.size[1] * 0.85),
                                size_hint_y=None)  # This is used for the first couple of widgets on the app
        # Create the parameters for Super GridLayout
        self.cols = 1
        self.rows = 2
        self.padding = 2

        if os.path.isfile("prev_details.txt") and ChatApp.config.items('security')[0][1] == "1":
            with open("prev_details.txt", 'r') as f:
                d = f.read().split(',')
                prev_ip = d[0]
                prev_port = d[1]
                prev_username = d[2]
        else:
            prev_ip = ''
            prev_port = ''
            prev_username = ''

        # Create some of the widgets
        InputField.add_widget(DarkGreyLabel(text="IP:", size_hint=(.1, 1)))  # Top left widget for "IP"
        self.IpIField = IPInput(multiline=False, background_normal='', background_color=self.ColourList[0],
                                border=(2, 2, 2, 2), text=prev_ip)  # Top right text input for ip
        InputField.add_widget(self.IpIField)  # Add this widget to the InputField layout
        for i in range(2):
            InputField.add_widget(Label(size_hint=(1, .05)))

        # Repeat the same for the port and username areas
        InputField.add_widget(DarkGreyLabel(text="Port:"))
        self.PortIField = PortInput(multiline=False, background_normal='', background_color=self.ColourList[0],
                                    border=(2, 2, 2, 2), text=prev_port)
        InputField.add_widget(self.PortIField)
        for i in range(2):
            InputField.add_widget(Label(size_hint=(1, .05)))

        InputField.add_widget(DarkGreyLabel(text="Username:"))
        self.UsernameIField = UsernameInput(multiline=False, background_normal='', background_color=self.ColourList[0],
                                            border=(2, 2, 2, 2), text=prev_username)
        InputField.add_widget(self.UsernameIField)
        for i in range(2):
            InputField.add_widget(Label(size_hint=(1, .05)))
        InputField.add_widget(DarkGreyLabel(text="Password Max Len 35: "))
        if ChatApp.config.items('security')[1][1] == "1":
            self.show_password = False
        else:
            self.show_password = True
        self.PasswordIField = PasswordInput(multiline=False, background_normal='', background_color=self.ColourList[0],
                                            border=(2, 2, 2, 2), password=self.show_password)
        InputField.add_widget(self.PasswordIField)

        self.add_widget(InputField)  # Add the sub-layout to the super-layout
        BottomLine = GridLayout(cols=3, padding=2)

        self.SettingsButton = Button(text="Settings", size_hint=(.90, .10), background_color=self.ColourList[2],
                                     background_normal='', font_size=20)
        self.SettingsButton.bind(on_release=settings)
        BottomLine.add_widget(self.SettingsButton)
        BottomLine.add_widget(Label(size_hint=(.01, 1)))

        self.JoinButton = Button(text="Connect", size_hint=(.90, .10), background_color=self.ColourList[2],
                                 background_normal='', font_size=20)
        self.JoinButton.bind(on_release=self.join_button)
        BottomLine.add_widget(self.JoinButton)
        self.add_widget(BottomLine)

    def join_button(self, _):
        port = self.PortIField.text  # Grab the text
        ip = self.IpIField.text  # Grab the text
        username = self.UsernameIField.text  # Grab the text
        if port != '' or ip != '' or username != '' and ChatApp.config.items('security')[0][1] == "1":
            with open("prev_details.txt", "w") as f:
                f.write(f"{ip},{port},{username}")
        # print(f"Joining {ip}:{port} as {username}")  # Debug
        # Create info string, update the page then change to said page
        if ChatApp.config.items('security')[1][1] == "1":
            info = f"Joining {ip}:{port} as {username}:{self.PasswordIField.text}"
        else:
            info = f"Joining {ip}:{port} as {username}"
        ChatApp.info_page.update_info(info)
        ChatApp.ScreenManager.current = 'Info'
        Clock.schedule_once(self.connect, 1)

    # Connects to the server
    def connect(self, _):

        # Get the information required for the __active_sockets client
        port = int(self.PortIField.text)
        ip = self.IpIField.text
        username = self.UsernameIField.text
        password = self.PasswordIField.text  # Grab the text
        speed = int(ChatApp.config.items('downloads')[0][1])

        if not socket_client.connect(username, password, ip, port, show_error):
            return
        else:
            client_socket, cipher, new_username, file_socket = socket_client.connect(username, password, ip, port,
                                                                                     show_error)

        # Create Chat App page and activate it
        ChatApp.create_chat_page(client_socket, cipher, new_username, show_error, file_socket, speed)
        ChatApp.ScreenManager.current = 'Chat'


class InfoPage(GridLayout):
    def __init__(self, **kwargs):
        super(InfoPage, self).__init__(**kwargs)

        # Add just one column
        self.cols = 1

        # Add one label for a message
        self.MessageLabel = DarkGreyLabel(halign="center", valign="middle", font_size=30)

        # By default every widget returns it's side as [100, 100], it gets finally resized,
        # but we have to listen for size change to get a new one
        # more: https://github.com/kivy/kivy/issues/1044
        self.MessageLabel.bind(width=self.update_text_width)

        # Add Label to layout
        self.add_widget(self.MessageLabel)

    def update_info(self, message):
        self.MessageLabel.text = message

    def update_text_width(self, *_):
        self.MessageLabel.text_size = (self.MessageLabel.width * 0.9, None)


class ChatPage(GridLayout):
    def __init__(self, socket, cipher, username, error_callback, colour_list, sent_colour, my_colour, file_socket,
                 speed, **kwargs):
        super(ChatPage, self).__init__(**kwargs)
        self.cols = 1
        self.rows = 3
        self.socket = socket
        self.file_socket = file_socket
        self.cipher = cipher
        self.username = username
        self.error_callback = error_callback
        self.ColourList = colour_list
        self.height = self.height - Window.keyboard_height
        self.History_height = (Window.size[1] * 0.90)
        self.user_colour = my_colour
        self.other_colour = sent_colour

        # TopLine = SlightlyLessBlackGridLayout(cols=10, padding=2)
        # self.Disconnect = Button(background_normal='x-new.png')
        # TopLine.add_widget(self.Disconnect)
        # for x in range(9):
        #    TopLine.add_widget(Label())
        # self.add_widget(TopLine)

        self.History = ScrollableLabel(height=self.History_height, size_hint_y=None)
        self.add_widget(self.History)

        self.NewMessage = MessageInput(width=Window.size[0] * 0.85, size_hint_x=None, multiline=False,
                                       background_normal='', background_color=self.ColourList[5])
        self.Send = Button(text="Send", background_color=self.ColourList[2], background_normal='', size_hint=(.95, 1))
        self.Send.bind(on_release=self.send_message)

        self.Upload = Button(text="Upload", background_color=self.ColourList[2], background_normal='',
                             size_hint=(.95, 1))
        self.Upload.bind(on_release=file_upload)

        self.BottomLine = SlightlyLessBlackGridLayout(cols=3, padding=4, width=Window.size[0] * 0.15)
        self.BottomLine.add_widget(self.NewMessage)

        BottomRightCorner = SlightlyLessBlackGridLayout(rows=3, padding=2)
        BottomRightCorner.add_widget(self.Send)
        BottomRightCorner.add_widget(Label(size_hint=(.90, .05)))
        BottomRightCorner.add_widget(self.Upload)
        # BottomRightCorner.add_widget(Label(size_hint=(.90, .05)))
        # BottomRightCorner.add_widget(self.Back)

        self.BottomLine.add_widget(BottomRightCorner)

        self.add_widget(self.BottomLine)
        # Able to send a message on enter key push
        Window.bind(on_key_down=self.on_key_down)
        Window.bind(on_resize=self.on_window_resize)
        Clock.schedule_once(self.focus_text_input, 1)
        socket_client.start(self.socket, self.cipher, self.error_callback, self.incoming_message, self.file_socket, speed)

    def on_window_resize(self, *_):
        self.History.height = (Window.size[1] * 0.90)
        self.NewMessage.width = Window.size[0] * 0.85
        self.BottomLine.width = Window.size[0] * 0.15

    def incoming_image(self, username, path):
        self.History.update_chat_history("message", f"[color={self.other_colour}][b]{username}[/b][/color] > ")
        self.History.update_chat_history("image", path)

    def back(self, *_):
        self.NewMessage.text = ""
        ChatApp.ScreenManager.current = "Connect"

    def send_message(self, *_):
        # Define the message
        message = self.NewMessage.text
        self.NewMessage.text = ''  # Clear the message
        message = check_message(message)
        if message:
            # Our message
            self.History.update_chat_history("message",
                                             f'[color={self.user_colour}][b]{self.username}[/b][/color] > {message}')
            socket_client.EncryptedMessageSend(message, self.cipher, self.socket)
        Clock.schedule_once(self.focus_text_input, 0.1)

    def send_image(self, path, _):
        if path:
            self.History.update_chat_history("message", f'[color={self.user_colour}][b]{self.username}[/b][/color] > ')
            self.History.update_chat_history("image", path)
            check = socket_client.SendImage(path, self.cipher, self.file_socket, self.incoming_message)
            return check
        Clock.schedule_once(self.focus_text_input, 0.1)

    # Get's key pushes
    # noinspection PyUnusedLocal
    def on_key_down(self, instance, keyboard, keycode, text, modifiers):
        # Only take action if enter key is pressed
        if keycode == 40:
            self.send_message(None)

    # Set focus to the enter field
    def focus_text_input(self, _):
        self.NewMessage.focus = True

    def incoming_message(self, username, message):
        self.History.update_chat_history("message", f'[color={self.other_colour}][b]{username}[/b][/color] > {message}')


class FileUploadPage(GridLayout):
    def __init__(self, colour_list, **kwargs):
        super(FileUploadPage, self).__init__(**kwargs)
        self.cols = 1
        self.ColourList = colour_list
        self.File = FileChooserIconView(path='.')

        self.Upload = Button(text="Upload", background_color=self.ColourList[2], background_normal='',
                             size_hint=(.90, 1))
        self.Upload.bind(on_release=self.upload)

        self.Back = Button(text="Back", background_color=self.ColourList[2], background_normal='', size_hint=(.90, 1))
        self.Back.bind(on_release=self.back)

        self.BottomLine = SlightlyLessBlackGridLayout(cols=3, padding=4, height=Window.size[1] * 0.1, size_hint_y=None)
        self.BottomLine.add_widget(self.Back)
        self.BottomLine.add_widget(Label(size_hint=(.05, 1)))
        self.BottomLine.add_widget(self.Upload)

        self.add_widget(self.File)
        self.add_widget(self.BottomLine)

    def upload(self, *_):
        path = self.File.selection
        path = str(path[0])
        print(path)
        check = ChatApp.chat_page.send_image(path, *_)
        if check:
            ChatApp.ScreenManager.current = "Chat"

    # noinspection PyMethodMayBeStatic
    def back(self, *_):
        ChatApp.ScreenManager.current = "Chat"


#  Create the app class
# noinspection PyAttributeOutsideInit,PyShadowingNames
class ShiellsChatApp(App):

    def build(self):  # treat this as __init__ for the app
        self.config.read('app/core/config.ini')  # this will read custom settings
        self.use_kivy_settings = False

        # Return the first page for the app
        # Set some base colours for the colour scheme format (r, g, b, a)
        # Window.size = (1920, 1080)
        SilverGrey = (125 / 255, 139 / 255, 160 / 255, 1)
        LightBlue = (35 / 255, 198 / 255, 200 / 255, 1)
        DarkBlue = (12 / 255, 122 / 255, 237 / 255, 1)
        Black = (0 / 255, 0 / 255, 0 / 255, 1)
        White = (255 / 255, 255 / 255, 255 / 255, 1)
        DarkGrey = (80 / 255, 92 / 255, 112 / 255, 1)
        SlightlyBlack = (20 / 255, 20 / 255, 20 / 255)
        SlightlyLessBlack = (25 / 255, 25 / 255, 25 / 255)
        self.ColourList = [SilverGrey, LightBlue, DarkBlue, Black, White, DarkGrey, SlightlyBlack, SlightlyLessBlack]
        # Use screen manager for changing between screens
        self.ScreenManager = ScreenManager()

        self.connect_page = ConnectPage(self.ColourList)
        screen = Screen(name="Connect")
        screen.add_widget(self.connect_page)
        self.ScreenManager.add_widget(screen)

        self.info_page = InfoPage()
        screen = Screen(name="Info")
        screen.add_widget(self.info_page)
        self.ScreenManager.add_widget(screen)

        self.upload_page = FileUploadPage(self.ColourList)
        screen = Screen(name="Upload")
        screen.add_widget(self.upload_page)
        self.ScreenManager.add_widget(screen)

        return self.ScreenManager

    def build_settings(self, settings):
        settings.add_json_panel('General', self.config, filename='app/core/panel_one.json')

    def _on_config_change(self, *largs):
        section = largs[2]
        key = largs[3]
        value = largs[4]
        pass

    def create_chat_page(self, socket, cipher, username, error_callback, file_socket, speed):
        my_colour = self.config.items('chat')[0][1]
        user_colour = self.config.items('chat')[1][1]
        self.chat_page = ChatPage(socket, cipher, username, error_callback, self.ColourList, user_colour, my_colour,
                                  file_socket, speed)
        screen = Screen(name="Chat")
        screen.add_widget(self.chat_page)
        self.ScreenManager.add_widget(screen)
        del screen


# Error callback function, used by __active_sockets client
# Updates info page with an error message, shows message and schedules exit in 10 seconds
# time.sleep() won't work here - will block Kivy and page with error message won't show up
def show_error(message):
    ChatApp.info_page.update_info(message)
    ChatApp.ScreenManager.current = 'Info'
    print(f"DEBUG: {message}")
    Clock.schedule_once(go_back, 10)


def go_back(*_):
    ChatApp.ScreenManager.current = "Connect"


def settings(*_):
    ChatApp.open_settings()


def check_message(message):
    message = format_message(message)
    pat = re.compile(r'[^ a-zA-Z0-9\[\]/?.!,\']')
    message = re.sub(pat, "", message)
    if len(message) > 30:
        message = message[:-(len(message) - 100)]
    return message


def format_message(client_message):
    format_codes = {
        "[b]": "[/b]",
        "[i]": "[/i]",
        "[u]": "[/u]",
        "[s]": "[/s]",
        "[sub]": "[/sub]",
        "[sup]": "[/sup]"
    }
    for code in format_codes.keys():
        end_code = format_codes.get(code)
        if code in client_message and end_code not in client_message:
            client_message += end_code

    return client_message


def file_upload(*_):
    ChatApp.ScreenManager.current = "Upload"


if __name__ == "__main__":
    ChatApp = ShiellsChatApp()
    ChatApp.run()
