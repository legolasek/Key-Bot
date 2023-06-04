import sys
import json
import os
import requests
import logging
import yaml
from time import sleep
from datetime import datetime, timedelta
from yaml import SafeLoader
from fake_useragent import UserAgent
import webbrowser
import threading
from threading import Thread
from functools import partial

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QApplication
import qdarkstyle

# Logo.
logo = """𝐊𝐄𝐘-𝐁𝐎𝐓"""
wersja = "0.1.2"

# Default config file.
default_config = """
# Konfig battle bota
bearer_token: ""
sleep_interval: 1
ticket_cost_threshold: 1000
ratelimit_sleep: 15
"""

# Clear the console.
clear = lambda: os.system("cls" if os.name in ("nt", "dos") else "clear")

# Set the console title.
os.system(f"title Key-Bot {wersja}")

class GUI(QtCore.QObject):
    startBotClicked = QtCore.pyqtSignal(str)
    updateGUI = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.case_battle = None
        self.app = QtWidgets.QApplication(sys.argv)
        self.window = QtWidgets.QMainWindow()
        
        # Apply theme
        link_style = """
        QPushButton {
            background-color: #22FFFF11;
            border: 1px solid #FFFF00;
            padding: 5px;
        }

        QPushButton:hover {
            background-color: #55FFFF11;
        }
        """

        start_style = """
        QPushButton {
            background-color: #2211FF11;
            border: 1px solid #00FF00;
            padding: 5px;
        }
        
        QPushButton:hover {
            background-color: #7711FF22;
        }
        """

        stop_style = """
        QPushButton {
            background-color: #22FF1111;
            border: 1px solid #FF0000;
            padding: 5px;
        }
        
        QPushButton:hover {
            background-color: #77FF1133;
        }
        """
        self.app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5') + link_style + start_style + stop_style)

        self.window.setWindowTitle(f"Key-Bot {wersja}")
        self.window.setGeometry(100, 100, 900, 480)

        self.central_widget = QtWidgets.QWidget(self.window)
        self.window.setCentralWidget(self.central_widget)

        self.layout = QtWidgets.QVBoxLayout(self.central_widget)

        self.log_text = QtWidgets.QPlainTextEdit(self.central_widget)
        self.log_text.setReadOnly(True)
        self.layout.addWidget(self.log_text)

        self.token_entry = QtWidgets.QLineEdit(self.central_widget)
        self.token_entry.setPlaceholderText("Bearer Token")
        self.layout.addWidget(self.token_entry)

        self.button_frame = QtWidgets.QFrame(self.central_widget)
        self.layout.addWidget(self.button_frame)

        self.button_layout = QtWidgets.QHBoxLayout(self.button_frame)

        self.start_button = QtWidgets.QPushButton("✅Start")
        self.start_button.clicked.connect(self.start_bot)
        self.start_button.setStyleSheet(start_style + "background-color: #2211FF11; border: 1px solid #00FF00; padding: 5px;")
        self.button_layout.addWidget(self.start_button)

        self.stop_button = QtWidgets.QPushButton("⛔Stop")
        self.stop_button.clicked.connect(self.stop_bot)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet(stop_style + "background-color: #22FF1111; border: 1px solid #FF0000; padding: 5px;")
        self.button_layout.addWidget(self.stop_button)

        # Linki
        self.links_frame = QtWidgets.QFrame(self.central_widget)
        self.layout.addWidget(self.links_frame)
        self.links_frame_layout = QtWidgets.QHBoxLayout(self.links_frame)

        self.keydrop_button = QtWidgets.QPushButton("Keydrop")
        self.keydrop_button.clicked.connect(partial(webbrowser.open, "https://key-drop.com/?code=KEY-BOT"))
        self.keydrop_button.setStyleSheet(link_style + "background-color: #55FFFF11; padding: 5px;")
        self.links_frame_layout.addWidget(self.keydrop_button)

        self.steam_button = QtWidgets.QPushButton("Steam")
        self.steam_button.clicked.connect(partial(webbrowser.open, "https://steamcommunity.com/id/PSteczkaCSGO/"))
        self.steam_button.setStyleSheet(link_style + "background-color: #55001166; padding: 5px;")
        self.links_frame_layout.addWidget(self.steam_button)

        self.github_button = QtWidgets.QPushButton("Github")
        self.github_button.clicked.connect(partial(webbrowser.open, "https://github.com/legolasek/Key-Bot"))
        self.github_button.setStyleSheet(link_style + "background-color: #55FFFFFF; padding: 5px;")
        self.links_frame_layout.addWidget(self.github_button)

        self.discord_button = QtWidgets.QPushButton("Discord")
        self.discord_button.clicked.connect(partial(webbrowser.open, "https://discord.gg/zV6MQQqkFV"))
        self.discord_button.setStyleSheet(link_style + "background-color: #550077FF; padding: 5px;")
        self.links_frame_layout.addWidget(self.discord_button)

        self.youtube_button = QtWidgets.QPushButton("Youtube")
        self.youtube_button.clicked.connect(partial(webbrowser.open, "https://www.youtube.com/channel/UCp_BpEmf9iUVxcspxWbgYGw"))
        self.youtube_button.setStyleSheet(link_style + "background-color: #55FF1111; padding: 5px;")
        self.links_frame_layout.addWidget(self.youtube_button)

        self.window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.window.closeEvent = self.close_window

        # Display logo
        self.log_message(f'<span style="color: gold;"><h1><b>{logo}</b></h1></span>')
        self.log_message('Program jest w pełni darmowy. Jeśli chcesz wesprzeć moją pracę możesz użyć kodu <span style="color: gold;"><b> key-bot </b></span> podczas doładowywania salda na key-drop.com')

    def start_bot(self):
        bearer_token = self.token_entry.text().strip()
        if bearer_token:
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.token_entry.setEnabled(False)
            self.startBotClicked.emit(bearer_token)
            self.updateGUI.connect(self.update_log_text)
            self.timer = QtCore.QTimer(singleShot=True)
            self.timer.timeout.connect(self.update_log_text)
            self.timer.start(100)  # Update every 100 milliseconds
        else:
            QMessageBox.critical(self.window, "Error", "Bearer Token nie może być pusty!")
        
    def update_log_text(self):
        self.log_text.viewport().repaint()

    def stop_bot(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.token_entry.setEnabled(True)

        if gui.case_battle is not None:
            gui.case_battle.stop_monitoring()
            self.log_message('<span style="color: gold;">Zatrzymano działanie bota </span>')

    def close_window(self, event):
        if gui.case_battle is not None and gui.case_battle.running:
            gui.case_battle.stop_monitoring()
        QtWidgets.QApplication.quit()

    def log_message(self, message):
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        self.log_text.appendHtml(f'{timestamp} {message}')
        self.log_text.repaint()

    def run(self):
        self.window.show()
        sys.exit(self.app.exec_())

def start_case_battle(token):
    case_battle = CaseBattle(token)
    gui.case_battle = case_battle
    case_battle.update_gui = gui.updateGUI
    gui.updateGUI.connect(gui.update_log_text)

    thread = threading.Thread(target=case_battle.monitor_battles)
    thread.daemon = True
    thread.start()
gui = GUI()

class Config:
    def __init__(self):
        if not os.path.exists("konfig.yaml"):
            self.log_message("Nie znaleziono pliku konfiguracyjnego! Tworzę go dla ciebie...")
            with open("konfig.yaml", "w") as file:
                file.write(default_config)
            self.log_message("Plik konfiguracyjny stworzony! Uzupełnij go i zrestartuj bota.")

        with open("konfig.yaml", "r") as file:
            self.config = yaml.load(file, Loader=SafeLoader)
            self.bearer_token = self.config.get("bearer_token", "")
            self.sleep_interval = self.config.get("sleep_interval", 1)
            self.ticket_cost_threshold = self.config.get("ticket_cost_threshold", 1000)
            self.ratelimit_sleep = self.config.get("ratelimit_sleep", 15)

    def log_message(self, message):
        gui.log_message(message)

# Load the config.
configData = Config()

class CaseBattle:
    def __init__(self, token, sleep_interval=configData.sleep_interval, ticket_cost_threshold=configData.ticket_cost_threshold):
        self.running = False
        self.session = requests.Session()
        self.user_agent = UserAgent()
        self.session.headers.update({
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Host": "kdrp2.com",
            "Origin": "https://key-drop.com",
            "Referer": "https://key-drop.com/",
            "authorization": f"{token}",
            "User-Agent": self.user_agent.random
        })
        self.base_url = "https://kdrp2.com/CaseBattle/"
        self.active_battles_url = f"{self.base_url}battle?type=active&page=0&priceFrom=0&priceTo=0.29&searchText=&sort=priceAscending&players=all&roundsCount=all"
        self.join_battle_url = f"{self.base_url}joinCaseBattle/"
        self.sleep_interval = sleep_interval
        self.ticket_cost_threshold = ticket_cost_threshold

    def print_logo(self):
        self.log_message('<span style="color: gold;"><b>────────────────────────────────────────────\n</b></span>')
        self.log_message("Szukanie bitwy...")

    def get_active_battles(self):
        try:
            response = self.session.get(self.active_battles_url)
            response.raise_for_status()
            return json.loads(response.text)["data"]
        except requests.HTTPError as http_err:
            logging.error(f"HTTP error occurred: {http_err}")
            return []
        except Exception as err:
            logging.error(f"Other error occurred: {err}")
            return []

    def join_battle(self, battle_id):
        try:
            url = f"{self.join_battle_url}{battle_id}/1"
            response = self.session.post(url)
            response.raise_for_status()
            data = json.loads(response.text)
            if data["success"]:
                return True, f'<span style="color: green;">Udało się dołączyć do bitwy!</span>'
            if data["errorCode"] == "slotUnavailable":
                return False, "Bitwa jest pełna!"
            if data["errorCode"] == "rateLimited":
                return False, "Ratelimited!"
            if data["errorCode"] == "userHasToWaitBeforeJoiningFreeBattle":
                return False, "Udział w darmowej bitwie można brać raz na 24 godziny!"
            return False, data["errorCode"]
        except requests.HTTPError as http_err:
            if "Unauthorized" in str(response.text):
                return False, "Nieprawidłowy token bearer!"
            logging.error(f"HTTP Error: {http_err}")
            return False, str(http_err)
        except Exception as err:
            logging.error(f"Error: {err}")
            return False, str(err)

    def monitor_battles(self):
        clear()
        self.print_logo()
        self.running = True
        while self.running:
            battles = self.get_active_battles()
            for battle in battles:
                if self.is_joinable(battle):
                    # ...
                    self.log_message(f'''<span style="color: gold;">\n<b>─────────────────[ {battle['id']} ]─────────────────</b>\n\n</span>''')
                    self.log_message(f'''ID bitwy: <span style="color: gold;">{battle['id']}\n</span>''')
                    self.log_message(f'''Próba dołączenia do bitwy...''')
                    success, message = self.join_battle(battle["id"])
                    if success:
                        self.log_message(message)
                    elif message == "Invalid token!":
                        self.log_message(f'<span style="color: red;">Nieprawidlowy token bearer!</span>')
                        sys.exit()
                    elif message == "Ratelimited!":
                        self.log_message(f'<span style="color: yellow;">Ratelimited! Trzeba zwiekszyc czas wstrzymania, lub dodac proxy.</span>')
                        self.log_message("Wstrzymanie na 30 sekund...")
                        sleep(30)
                    elif message == "You have to wait one day between free battles!":
                        self.log_message(f'<span style="color: yellow;">Musisz zaczekac 1 dzień przed ponownym dołączaniem!</span>')
                        sys.exit()
                    elif message == "notEnoughtMoney":
                        self.log_message(f'<span style="color: red;">Nie masz biletów by uczestniczyć w darmowych bitwach!</span>')
                        sys.exit()
                    else:
                        self.log_message(f'<span style="color: red;">Nie udało się dołączyć do bitwy!</span> {message}')
                        sleep(self.sleep_interval)
                    # Emit signal to update GUI
                    self.update_gui.emit()
            sleep(self.sleep_interval)

    def stop_monitoring(self):
        self.running = False

    def is_joinable(self, battle):
        isFreeBattle = battle["isFreeBattle"]
        users = battle["users"]
        maxUserCount = battle["maxUserCount"]
        if isFreeBattle and len(users) != maxUserCount:
            if battle["freeBattleTicketCost"] > self.ticket_cost_threshold:
                return False
            elif battle["freeBattleTicketCost"] < self.ticket_cost_threshold:
                return True
            return False

    def log_message(self, message):
        gui.log_message(message)
        self.update_gui.emit()

gui.startBotClicked.connect(start_case_battle)
gui.run()
