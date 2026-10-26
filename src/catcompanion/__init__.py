import random
import sys
import time
import playsound
import ctypes

ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
    "Jussi.CatCompanion"
)

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QWidget
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap, QCursor
from screeninfo import get_monitors

from pathlib import Path

def resource_path(relative_path):
    """Get the path to a bundled resource."""
    if getattr(sys, "frozen", False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).resolve().parents[2]

    return base_path / relative_path

# SETTINGS
FOOD_IN_BOWL = False
ASKING_FOR_WHAT = None
WAKE_UP_CHANCE = 0.004
#WAKE_UP_CHANCE = 0.25
ORIGINAL_SIZE = (85, 68)
SHOW_DRAG_OUTLINE = False

# Drag button
DRAG_AREA = (0, 46, 85, 20)
# Petting button while sleeping
PETTING_SLEEPING_AREA = (22, 33, 39, 12)
# Give food button
GIVE_FOOD_AREA = (6, 50, 24, 11)
# Petting button while standing
PETTING_STANDING_AREA = (31, 17, 23, 42)
# Give yarn button
GIVE_YARN_AREA = (58, 46, 17, 16)

# Purring
PURR_START_DELAY = 3.0
PURR_STREAK_GAP = 1.5
PURR_STOP_AFTER = 3.0
MIN_PETTING_TIME = 10.0

# MOUSE TRACKING
MOUSE_POSITION = QCursor.pos()
MOUSE_MOVEMENT = time.monotonic()

def check_mouse():
    """Check if the mouse has moved in the last 60 seconds."""
    global MOUSE_POSITION, MOUSE_MOVEMENT

    current_position = QCursor.pos()
    if current_position != MOUSE_POSITION:
        MOUSE_MOVEMENT = time.monotonic()
        MOUSE_POSITION = current_position

    return time.monotonic() - MOUSE_MOVEMENT < 60

# TEXTURES
TEXTURES = {
    # Textures with the layers they occupy
    # smaller number means lower layer
    # layer 0 for the application icon
    "eating_1": ("textures/cat/eating/eating_1.png", 2),
    "eating_2": ("textures/cat/eating/eating_2.png", 2),
    "eating_3": ("textures/cat/eating/eating_3.png", 2),
    "food_1": ("textures/cat/eating/food_1.png", 3),
    "food_2": ("textures/cat/eating/food_2.png", 3),
    "food_3": ("textures/cat/eating/food_3.png", 3),
    "food_4": ("textures/cat/eating/food_4.png", 3),
    "food_5": ("textures/cat/eating/food_5.png", 3),
    "playing_1": ("textures/cat/playing/playing_1.png", 2),
    "playing_2": ("textures/cat/playing/playing_2.png", 2),
    "sleeping": ("textures/cat/sleeping/sleeping.png", 2),
    "stretching": ("textures/cat/sleeping/stretching.png", 2),
    "blink": ("textures/cat/standing/blink.png", 2),
    "left": ("textures/cat/standing/left.png", 2),
    "meow": ("textures/cat/standing/meow.png", 2),
    "normal": ("textures/cat/standing/normal.png", 2),
    "purring": ("textures/cat/standing/purring.png", 2),
    "right": ("textures/cat/standing/right.png", 2),
    "bowl": ("textures/bowl.png", 3),
    "ground": ("textures/ground.png", 1),
    "yarn": ("textures/yarn.png", 4),
    "empty": ("textures/empty.png", 4),
    "icon": ("textures/icon.ico", 0)
}

# SOUNDS
SOUNDS = {
    "purring": "sounds/purring.mp3",
    "meow1": "sounds/meow1.mp3",
    "meow2": "sounds/meow2.mp3",
    "meow3": "sounds/meow3.mp3",
    "meow4": "sounds/meow4.mp3",
    "no": "sounds/no.mp3"
}

# IMAGE LABEL
class ImageLabel(QLabel):
    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.pixmap_original = pixmap
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background: transparent;")
        self.update_image()

    def resizeEvent(self, event):
        self.update_image()
        super().resizeEvent(event)

    def update_image(self):
        scaled = self.pixmap_original.scaled(
            self.size(),
            Qt.KeepAspectRatio,
            Qt.FastTransformation
        )
        self.setPixmap(scaled)

    def set_texture(self, pixmap):
        self.pixmap_original = pixmap
        self.update_image()

# DRAG HANDLE
class DragHandle(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.SizeAllCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        # Almost transparent but still receives mouse events
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))

        if SHOW_DRAG_OUTLINE:
            painter.fillRect(self.rect(), QColor(255, 0, 0, 40))
            painter.setPen(QPen(QColor(255, 0, 0), 2))
            painter.drawRect(self.rect().adjusted(1, 1, -1, -1))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            handle = self.window().windowHandle()
            if handle is not None:
                handle.startSystemMove()
            event.accept()

# SLEEPING PETTING BUTTON
class PettingSleeping(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)

        self.audio = QAudioOutput(self)
        self.player = QMediaPlayer(self)
        self.player.setAudioOutput(self.audio)
        self.player.setSource(
            QUrl.fromLocalFile(
                str(resource_path(SOUNDS["purring"]))
            )
        )
        self.player.setLoops(QMediaPlayer.Loops.Infinite)

        self.streak_start = 0.0
        self.last_press = 0.0
        self.audio.setVolume(0.0)
        self.last_tick = time.monotonic()

        self.fade_timer = QTimer(self)
        self.fade_timer.setInterval(30)
        self.fade_timer.timeout.connect(self.fade_tick)

    def is_playing(self):
        return (
            self.player.playbackState()
            == QMediaPlayer.PlaybackState.PlayingState
        )

    def fade_tick(self):
        now = time.monotonic()
        dt = now - self.last_tick
        self.last_tick = now
        volume = self.audio.volume()

        if now - self.last_press <= PURR_STREAK_GAP:
            volume = min(1.0, volume + dt / PURR_START_DELAY)
        else:
            volume = max(0.0, volume - dt / PURR_STOP_AFTER)

        self.audio.setVolume(volume)

        if volume <= 0.0:
            self.player.stop()
            self.fade_timer.stop()

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return

        now = time.monotonic()

        # Start a new petting streak
        if (
            now - self.last_press > PURR_STREAK_GAP
            and not self.is_playing()
        ):
            self.streak_start = now

        self.last_press = now

        # Start purring after enough petting
        if (
            self.is_playing()
            or now - self.streak_start >= PURR_START_DELAY
        ):
            if not self.is_playing():
                self.audio.setVolume(0.0)
                self.player.play()

            if not self.fade_timer.isActive():
                self.last_tick = now
                self.fade_timer.start()

        event.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))

        if SHOW_DRAG_OUTLINE:
            painter.fillRect(self.rect(), QColor(255, 0, 0, 40))
            painter.setPen(QPen(QColor(255, 0, 0), 2))
            painter.drawRect(self.rect().adjusted(1, 1, -1, -1))

# GIVE FOOD BUTTON
class GiveFood(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        # Almost transparent but still receives mouse events
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))

        if SHOW_DRAG_OUTLINE:
            painter.fillRect(self.rect(), QColor(255, 0, 0, 40))
            painter.setPen(QPen(QColor(255, 0, 0), 2))
            painter.drawRect(self.rect().adjusted(1, 1, -1, -1))

    def mousePressEvent(self, event):
        if FOOD_IN_BOWL:
            return
        else:
            self.parent().give_food1()

# STANDING PETTING BUTTON
class PettingStanding(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)

        self.audio = QAudioOutput(self)
        self.player = QMediaPlayer(self)
        self.player.setAudioOutput(self.audio)
        self.player.setSource(
            QUrl.fromLocalFile(
                str(resource_path(SOUNDS["purring"]))
            )
        )
        self.player.setLoops(QMediaPlayer.Loops.Infinite)

        self.streak_start = 0.0
        self.last_press = 0.0

        self.audio.setVolume(0.0)
        self.last_tick = time.monotonic()

        self.fade_timer = QTimer(self)
        self.fade_timer.setInterval(30)
        self.fade_timer.timeout.connect(self.fade_tick)

    def is_playing(self):
        return (
            self.player.playbackState()
            == QMediaPlayer.PlaybackState.PlayingState
        )

    def fade_tick(self):
        now = time.monotonic()
        dt = now - self.last_tick
        self.last_tick = now

        volume = self.audio.volume()

        # User is still clicking
        if now - self.last_press <= PURR_STREAK_GAP:
            volume = min(
                1.0,
                volume + dt / PURR_START_DELAY
            )

        # User stopped clicking
        else:
            volume = max(
                0.0,
                volume - dt / PURR_STOP_AFTER
            )

        self.audio.setVolume(volume)

        # Still purring
        if volume > 0.0:
            self.window().set_texture("purring")
            return

        # Purring has completely stopped
        self.player.stop()
        self.fade_timer.stop()

        if self.window().state != "asking":
            return

        petting_time = now - self.streak_start

        if petting_time >= MIN_PETTING_TIME:
            # Petting lasted long enough.
            self.window().start_sleeping()
        else:
            # Not enough petting.
            self.reset_purring()
            self.window().set_texture("normal")
            self.window().resume_asking_loop()

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return

        window = self.window()

        if window.state != "asking":
            return

        # If the cat did not ask for petting,
        # shake its head and continue asking.
        if ASKING_FOR_WHAT != "petting":
            self.reset_purring()
            window.shaking_head1()
            event.accept()
            return

        now = time.monotonic()

        # First click of a new petting session
        if (
            now - self.last_press > PURR_STREAK_GAP
            or self.streak_start == 0.0
        ):
            self.streak_start = now
            window.stop_asking_loop()

        self.last_press = now
        # Start purring after PURR_START_DELAY
        if now - self.streak_start >= PURR_START_DELAY:
            if not self.is_playing():
                self.audio.setVolume(0.0)
                self.player.play()

            window.set_texture("purring")

        # Timer is needed both while waiting for purring
        # and while purring.
        if not self.fade_timer.isActive():
            self.last_tick = now
            self.fade_timer.start()

        event.accept()

    def reset_purring(self):
        self.fade_timer.stop()
        self.player.stop()
        self.audio.setVolume(0.0)

        self.streak_start = 0.0
        self.last_press = 0.0

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.fillRect(
            self.rect(),
            QColor(0, 0, 0, 1)
        )

        if SHOW_DRAG_OUTLINE:
            painter.fillRect(
                self.rect(),
                QColor(255, 0, 0, 40)
            )
            painter.setPen(
                QPen(QColor(255, 0, 0), 2)
            )
            painter.drawRect(
                self.rect().adjusted(1, 1, -1, -1)
            )

# Give yarn button
class GiveYarn(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        # Almost transparent but still receives mouse events
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))

        if SHOW_DRAG_OUTLINE:
            painter.fillRect(self.rect(), QColor(255, 0, 0, 40))
            painter.setPen(QPen(QColor(255, 0, 0), 2))
            painter.drawRect(self.rect().adjusted(1, 1, -1, -1))

    def mousePressEvent(self, event):
        window = self.window()
        
        if window.state != "asking":
            return

        # If the cat did not ask for yarn,
        # shake its head and continue asking
        if ASKING_FOR_WHAT != "playing":
            window.shaking_head1()
            event.accept()
            return
        else:
            window.start_playing()
            event.accept()

# MAIN WINDOW
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Application icon and name
        self.setWindowTitle("Cat Companion")
        self.setWindowIcon(
            QIcon(str(resource_path(TEXTURES["icon"][0])))
        )


        # Buttons
        self.give_food = GiveFood(self)
        self.give_food.show()
        self.drag_handle = DragHandle(self)
        self.drag_handle.show()

        self.petting_sleeping = PettingSleeping(self)
        self.petting_sleeping.hide()

        self.petting_standing = PettingStanding(self)
        self.petting_standing.hide()

        self.give_yarn = GiveYarn(self)
        self.give_yarn.hide()

        # Window
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
        )

        # Texture layers
        self.layers = {}

        # Cat state
        self.state = "standing"

        # Main behaviour timer
        self.behaviour_timer = QTimer(self)
        self.behaviour_timer.setSingleShot(True)
        self.behaviour_timer.timeout.connect(self.next_behaviour)

        # Asking animation loop
        self.asking_timer = QTimer(self)
        self.asking_timer.setSingleShot(True)
        self.asking_timer.timeout.connect(self.asking)

    # TEXTURES
    def set_texture(self, name):
        if name not in TEXTURES:
            raise ValueError(f"Unknown texture: {name}")

        path, layer = TEXTURES[name]
        path = resource_path(path)
        pixmap = QPixmap(str(path))

        if pixmap.isNull():
            raise FileNotFoundError(f"Could not load texture: {path}")

        if layer in self.layers:
            self.layers[layer].set_texture(pixmap)
        else:
            label = ImageLabel(pixmap, self)
            label.setGeometry(self.rect())
            label.show()
            self.layers[layer] = label

        # Correct layer ordering
        for label in self.layers.values():
            label.lower()

        for current_layer in sorted(self.layers):
            self.layers[current_layer].raise_()

        # Buttons always on top
        self.drag_handle.raise_()
        if self.petting_sleeping.isVisible():
            self.petting_sleeping.raise_()
        if self.give_food.isVisible():
            self.give_food.raise_()
        if self.petting_standing.isVisible():
            self.petting_standing.raise_()
        if self.give_yarn.isVisible():
            self.give_yarn.raise_()

    # BUTTON VISIBILITY
    def enable_sleeping_petting(self):
        self.petting_sleeping.show()
        self.petting_sleeping.raise_()

    def disable_sleeping_petting(self):
        self.petting_sleeping.hide()

    def enable_standing_petting(self):
        self.petting_standing.show()
        self.petting_standing.raise_()

    def disable_standing_petting(self):
        self.petting_standing.hide()

    def enable_give_yarn(self):
        self.give_yarn.show()
        self.give_yarn.raise_()

    def disable_give_yarn(self):
        self.give_yarn.hide()

    # WINDOW SIZING
    def update_button_geometry(self):
        sx = self.width() / ORIGINAL_SIZE[0]
        sy = self.height() / ORIGINAL_SIZE[1]

        # Drag button
        x, y, w, h = DRAG_AREA
        self.drag_handle.setGeometry(
            round(x * sx),
            round(y * sy),
            round(w * sx),
            round(h * sy)
        )

        # Petting button
        x, y, w, h = PETTING_SLEEPING_AREA
        self.petting_sleeping.setGeometry(
            round(x * sx),
            round(y * sy),
            round(w * sx),
            round(h * sy)
        )

        # Give food button
        x, y, w, h = GIVE_FOOD_AREA
        self.give_food.setGeometry(
            round(x * sx),
            round(y * sy),
            round(w * sx),
            round(h * sy)
        )

        # Petting button while standing/asking
        x, y, w, h = PETTING_STANDING_AREA
        self.petting_standing.setGeometry(
            round(x * sx),
            round(y * sy),
            round(w * sx),
            round(h * sy)
        )

        # Give yarn button
        x, y, w, h = GIVE_YARN_AREA
        self.give_yarn.setGeometry(
            round(x * sx),
            round(y * sy),
            round(w * sx),
            round(h * sy)
        )

    def resizeEvent(self, event):
        for label in self.layers.values():
            label.setGeometry(self.rect())

        self.update_button_geometry()
        super().resizeEvent(event)

    # BEHAVIOUR SYSTEM
    def start(self):
        """Start the cat's behaviour system."""
        self.state = "standing"
        self.set_texture("normal")
        self.schedule_next_behaviour()

    def schedule_next_behaviour(self):
        delay = int(1000 * random.uniform(0, 10))
        self.behaviour_timer.start(delay)

    def next_behaviour(self):
        """Decide what the cat does next."""
        global ASKING_FOR_WHAT

        self.asking_timer.stop()
        decider = random.random()

        if decider <= 0.25:
            self.start_sleeping()

        elif decider <= 0.50:
            if FOOD_IN_BOWL:
                self.start_eating()
            else:
                ASKING_FOR_WHAT = "food"
                self.start_asking()

        elif decider <= 0.75:
            ASKING_FOR_WHAT = "playing"
            self.start_asking()

        else:
            ASKING_FOR_WHAT = "petting"
            self.start_asking()

    # SLEEPING
    def start_sleeping(self):
        global ASKING_FOR_WHAT

        ASKING_FOR_WHAT = None

        # Stop asking
        self.asking_timer.stop()

        # Stop standing petting
        self.petting_standing.reset_purring()
        self.disable_standing_petting()
        self.disable_give_yarn()

        self.state = "sleeping"

        self.disable_sleeping_petting()
        self.set_texture("stretching")

        # After 1 second, actually fall asleep
        QTimer.singleShot(1000, self.finish_sleeping)

    def finish_sleeping(self):
        # Make sure we're still supposed to be sleeping
        if self.state != "sleeping":
            return

        self.set_texture("sleeping")

        # Petting becomes available
        self.enable_sleeping_petting()

        # Check every 5 seconds for waking
        # The chance to wake up is 0.4% every 5 seconds
        # function to calculate the chance to have woken up
        # by a certain loop count is
        # 1 - (1 - WAKE_UP_CHANCE) ** loops
        # for example at at 30 mins/310 loops
        # the chance to have woken up is around 71%
        self.sleep_timer = QTimer(self)
        self.sleep_timer.setInterval(5000)
        self.sleep_timer.timeout.connect(self.check_wakeup)
        self.sleep_timer.start()

    def check_wakeup(self):
        if self.state != "sleeping":
            return
        # Checking for mouse movement in the last 60 secs
        # to avoid the cat waking up while the user is not active
        if not check_mouse():
            return
        if random.random() <= WAKE_UP_CHANCE:
            self.wake_up()

    # WAKING
    def wake_up(self):
        self.state = "waking"

        # Stop sleeping timer
        if hasattr(self, "sleep_timer"):
            self.sleep_timer.stop()
            self.sleep_timer.deleteLater()
            del self.sleep_timer

        self.disable_sleeping_petting()
        self.set_texture("stretching")
        QTimer.singleShot(1000, self.finish_waking)

    def finish_waking(self):
        if self.state != "waking":
            return

        self.set_texture("blink")
        QTimer.singleShot(200, self.finish_waking_blink)

    def finish_waking_blink(self):
        if self.state != "waking":
            return

        self.set_texture("normal")
        self.state = "standing"
        self.schedule_next_behaviour()

    # STANDING
    def start_standing(self):
        self.asking_timer.stop()

        self.petting_standing.reset_purring()
        self.disable_standing_petting()
        self.disable_give_yarn()

        self.disable_sleeping_petting()

        self.state = "standing"
        self.set_texture("normal")
        self.schedule_next_behaviour()

    def stop_asking_loop(self):
        """Stop the repeating asking animation."""
        self.asking_timer.stop()

    def resume_asking_loop(self):
        """Resume the repeating asking animation."""
        if self.state != "asking":
            return

        self.asking_timer.start(2000)

    # ASKING
    def start_asking(self):
        self.state = "asking"

        self.disable_sleeping_petting()
        self.enable_standing_petting()
        self.enable_give_yarn()

        self.asking()

    def asking(self):
        global ASKING_FOR_WHAT, FOOD_IN_BOWL

        # Only continue if the cat is still asking.
        if self.state != "asking":
            return

        #print(f"Cat is asking for {ASKING_FOR_WHAT}")

        self.disable_sleeping_petting()
        self.enable_standing_petting()
        self.enable_give_yarn()
        if FOOD_IN_BOWL == False:
            self.give_food.show()

        self.set_texture("normal")

        decider = random.random()

        if decider <= 1/6:
            # Blink
            QTimer.singleShot(2000, self.blink)
        elif decider <= 2/6:
            # Double blink
            QTimer.singleShot(2000, self.blink)
            QTimer.singleShot(2100, self.blink)
        else:
            # Meow
            QTimer.singleShot(2000, self.meow)

        if ASKING_FOR_WHAT == "food" and FOOD_IN_BOWL:
            self.start_eating()

        self.asking_timer.start(3000)

    def finish_asking(self):
        self.asking_timer.stop()
        self.disable_standing_petting()
        self.disable_give_yarn()

        self.state = "standing"
        self.set_texture("normal")
        self.schedule_next_behaviour()

    # GIVE FOOD
    def give_food1(self):
        self.set_texture("food_1")
        QTimer.singleShot(1000, self.give_food2)

    def give_food2(self):
        self.set_texture("food_2")
        QTimer.singleShot(200, self.give_food3)

    def give_food3(self):
        self.set_texture("food_3")
        QTimer.singleShot(200, self.give_food4)

    def give_food4(self):
        self.set_texture("food_4")
        QTimer.singleShot(200, self.finish_give_food)

    def finish_give_food(self):
        global FOOD_IN_BOWL, ASKING_FOR_WHAT
        self.set_texture("food_5")
        FOOD_IN_BOWL = True
        if ASKING_FOR_WHAT == "petting" or ASKING_FOR_WHAT == "playing":
            self.shaking_head1()
        self.give_food.hide()

    # EATING
    def start_eating(self):
        global ASKING_FOR_WHAT
        ASKING_FOR_WHAT = None

        self.disable_standing_petting()

        self.state = "eating"
        self.set_texture("eating_1")
        QTimer.singleShot(150, self.eating)

    def eating(self, loops=1):
        if loops > 41:
            self.finish_eating()
            return
        elif loops % 2 == 0:
            self.set_texture("eating_1")
        else:
            self.set_texture("eating_2")
        QTimer.singleShot(150, lambda: self.eating(loops + 1))

    def finish_eating(self):
        global FOOD_IN_BOWL
        FOOD_IN_BOWL = False
        self.set_texture("eating_3")
        self.set_texture("bowl")
        self.give_food.show()
        QTimer.singleShot(1000, self.start_sleeping)

    # BLINK
    def blink(self):
        if self.state != "asking":
            return

        self.set_texture("blink")
        QTimer.singleShot(200, self.finish_blink)

    def finish_blink(self):
        if self.state == "asking":
            self.set_texture("normal")

    #MEOW
    def meow(self):
        if self.state != "asking":
            return

        self.set_texture("meow")
        
        decider = random.random()
        if decider <= 0.005:
            meow = SOUNDS["meow4"]
        elif decider <= 1/3:
            meow = SOUNDS["meow1"]
        elif decider <= 2/3:
            meow = SOUNDS["meow2"]
        else:
            meow = SOUNDS["meow3"]

        playsound.playsound(str(resource_path(meow)), False)
        QTimer.singleShot(1500, self.finish_meow)

    def finish_meow(self):
        if self.state == "asking":
            self.set_texture("normal")

    def shaking_head1(self):
        if self.state != "asking":
            return
        # Stop normal asking animations while shaking head
        self.stop_asking_loop()
        self.petting_standing.hide()
        self.give_food.hide()
        self.disable_give_yarn()

        self.set_texture("right")
        playsound.playsound(str(resource_path(SOUNDS["no"])), False)
        QTimer.singleShot(500, self.shaking_head2)

    def shaking_head2(self):
        if self.state != "asking":
            return
        self.set_texture("left")
        QTimer.singleShot(500, self.shaking_head3)

    def shaking_head3(self):
        if self.state != "asking":
            return
        self.set_texture("right")
        QTimer.singleShot(500, self.finish_shaking_head)

    def finish_shaking_head(self):
        global FOOD_IN_BOWL

        if self.state != "asking":
            return
        self.set_texture("normal")
        # Return to the normal asking loop
        self.resume_asking_loop()
        self.petting_standing.show()
        self.petting_standing.raise_()
        self.enable_give_yarn()

        if not FOOD_IN_BOWL:
            self.give_food.show()
            self.give_food.raise_()

    def start_playing(self):
        global ASKING_FOR_WHAT
        ASKING_FOR_WHAT = None

        self.state = "playing"
        self.disable_give_yarn()
        self.disable_standing_petting()
        self.set_texture("empty")
        self.set_texture("playing_1")
        goal = random.randint(20, 100)
        QTimer.singleShot(500, lambda: self.playing(goal=goal, loops=1))

    def playing(self, goal, loops=1):
        if self.state != "playing":
            return

        if loops >= goal:
            self.finish_playing()
            return
        elif loops % 2 == 0:
            self.set_texture("playing_1")
            playing_time = random.randint(100, 1500)
        else:
            self.set_texture("playing_2")
            playing_time = random.randint(50, 500)

        QTimer.singleShot(playing_time, lambda: self.playing(goal=goal, loops=loops + 1))

    def finish_playing(self):
        self.set_texture("yarn")
        self.start_sleeping()
        
# APPLICATION
app = QApplication(sys.argv)

app.setWindowIcon(
    QIcon(str(resource_path(TEXTURES["icon"][0])))
)
app.setApplicationName("Cat Companion")

window = MainWindow()

# WINDOW SIZE
monitors = get_monitors()
for monitor in monitors:
    if monitor.is_primary:
        height = monitor.height
        if height <= 1080:
            window.resize(255, 204)
        elif height >= 2160:
            window.resize(425, 340)
        else:
            window.resize(340, 272)

# INITIAL TEXTURES
window.set_texture("yarn")
window.set_texture("bowl")
window.set_texture("ground")

# SHOW WINDOW
window.show()

# START CAT
window.start()

# START QT EVENT LOOP
sys.exit(app.exec())