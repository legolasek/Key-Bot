import json
import os
import requests
import logging
import yaml
from time import sleep
from datetime import timedelta
from yaml import SafeLoader
from fake_useragent import UserAgent
from pystyle import Colors, Colorate, Center
import tkinter as tk
from PIL import ImageTk, Image
import webbrowser
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget, QTextEdit
from PyQt5.QtGui import QPixmap, QColor, QPalette

# Logo.
logo = """
██╗  ██╗███████╗██╗   ██╗     ██████╗  ██████╗ ████████╗
██║ ██╔╝██╔════╝╚██╗ ██╔╝     ██╔══██╗██╔═══██╗╚══██╔══╝
█████╔╝ █████╗   ╚████╔╝█████╗██████╔╝██║   ██║   ██║   
██╔═██╗ ██╔══╝    ╚██╔╝ ╚════╝██╔══██╗██║   ██║   ██║   
██║  ██╗███████╗   ██║        ██████╔╝╚██████╔╝   ██║   
╚═╝  ╚═╝╚══════╝   ╚═╝        ╚═════╝  ╚═════╝    ╚═╝   
                                                        """

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
os.system(f"title Keydrop Battle Bot - discord.gg/zV6MQQqkFV")

class Config():
    def __init__(self):
        if not os.path.exists("konfig.yaml"):
            logging.error("Nie znaleziono pliku konfiguracyjnego! Tworze go dla ciebie...")
            with open("konfig.yaml", "w") as file:
                file.write(default_config)
            logging.info("Plik konfiguracyjny stworzony! Uzupelnij go i zrestartuj bota.")
            exit()

        with open("konfig.yaml", "r") as file:
            self.config = yaml.load(file, Loader=SafeLoader)
            self.bearer_token = self.config["bearer_token"]
            self.sleep_interval = self.config["sleep_interval"]
            self.ticket_cost_threshold = self.config["ticket_cost_threshold"]
            self.ratelimit_sleep = self.config["ratelimit_sleep"]

# Load the config.
configData = Config()

class CaseBattle:
    def __init__(self, token, sleep_interval=configData.sleep_interval, ticket_cost_threshold=configData.ticket_cost_threshold):
        self.running = False  # Dodajemy flagę "running" do oznaczania działania bota
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

    # Function to print the logo.
    def print_logo(self):
        print(Center.XCenter(Colorate.Vertical(Colors.yellow_to_red, logo, 1)))
        print(Center.XCenter(Colorate.Vertical(Colors.yellow_to_red, "Wersja 0.1.2", 1)))
        print(Center.XCenter(Colorate.Vertical(Colors.yellow_to_red, "────────────────────────────────────────────\n", 1)))
        print(Center.XCenter(Colorate.Vertical(Colors.yellow_to_red, "Szukanie bitwy...", 1)))

    # Function to get active battles.
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

    # Function to join a battle.
    def join_battle(self, battle_id):
        try:
            url = f"{self.join_battle_url}{battle_id}/1"
            response = self.session.post(url)
            response.raise_for_status()
            data = json.loads(response.text)
            if data["success"]:
                return True, response.text
            if data["errorCode"] == "slotUnavailable":
                return False, "Bitwa jest pelna!"
            if data["errorCode"] == "rateLimited":
                return False, "Ratelimited!"
            if data["errorCode"] == "userHasToWaitBeforeJoiningFreeBattle":
                return False, "Udzial w darmowej bitwie mozna brac co 24 godziny!"
            print(data)
            return False, data["errorCode"]
        except requests.HTTPError as http_err:
            if "Unauthorized" in str(response.text):
                return False, "Nieprawidlowy token bearer!"
            logging.error(f"HTTP Error: {http_err}")
            return False, str(http_err)
        except Exception as err:
            logging.error(f"Error: {err}")
            return False, str(err)

    # Function to monitor active battles and join them if they are joinable.
    def monitor_battles(self):
        clear()
        self.print_logo()
        self.running = True  # Ustawiamy flagę "running" na True
        while self.running:  # Modyfikujemy pętlę, aby działała tylko gdy "running" jest True
            # Pozostała część kodu
            battles = self.get_active_battles()
            for battle in battles:
                if self.is_joinable(battle):
                    print(Colorate.Vertical(Colors.yellow_to_red, f"\n─────────────────[ {battle['id']} ]─────────────────\n\n", 1))
                    logging.info(f"proba dolaczenia do bitwy {battle['id']}...")
                    print(Colorate.Horizontal(Colors.yellow_to_green, f"ID bitwy: {battle['id']}\n", 1))
                    success, message = self.join_battle(battle["id"])
                    if success:
                        logging.info(f"Udalo sie dolaczyc do bitwy!")
                    elif message == "Invalid token!":
                        logging.error("Nieprawidlowy token bearer!")
                        exit()
                    elif message == "Ratelimited!":
                        logging.warning("Ratelimited! Trzeba zwiekszyc czas wstrzymania, lub dodac proxy.")
                        logging.info("Wstrzymanie na 30 sekund...")
                        sleep(30)
                    elif message == "You have to wait one day between free battles!":
                        logging.warning("Musisz zaczekac 1 dzien przed ponownym dolaczaniem!")
                        exit()
                    else:
                        logging.error(f"Nie udalo sie dolaczyc do bitwy! {message}")
                        sleep(self.sleep_interval)
            sleep(self.sleep_interval)

    def stop_monitoring(self):
        self.running = False  # Ustawiamy flagę "running" na False, aby zatrzymać wyszukiwanie bitew
        # Function to check if a battle is joinable.
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

# GUI UPDATE
class GUI:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Keydrop Battle Bot")
        self.window.geometry("400x600")
        self.case_battle = None

        # Logo
        logo_path = "logo.png"
        if os.path.exists(logo_path):
            self.logo_image = ImageTk.PhotoImage(Image.open(logo_path))
            self.logo_label = tk.Label(self.window, image=self.logo_image)
            self.logo_label.pack()

        # Token label and entry
        self.token_label = tk.Label(self.window, text="Bearer Token:")
        self.token_label.pack()
        self.token_entry = tk.Entry(self.window, width=40)
        self.token_entry.pack()

        # Start button
        self.start_button = tk.Button(self.window, text="Start", command=self.start_bot)
        self.start_button.pack()

        # Stop button
        self.stop_button = tk.Button(self.window, text="Stop", command=self.stop_bot, state=tk.DISABLED)
        self.stop_button.pack()

        # Exit button
        self.exit_button = tk.Button(self.window, text="Wyjście", command=self.exit_program)
        self.exit_button.pack()

        # Footer label
        self.footer_label = tk.Label(self.window, text="Created By PSteczka", fg="blue", cursor="hand2")
        self.footer_label.pack()
        self.footer_label.bind("<Button-1>", lambda e: self.open_github_repo())

    def start_bot(self):
        bearer_token = self.token_entry.get().strip()
        if bearer_token:
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.token_entry.config(state=tk.DISABLED)
            self.case_battle = CaseBattle(bearer_token)

        # Uruchomienie monitorowania bitwy w osobnym wątku
            monitor_thread = threading.Thread(target=self.start_monitoring, args=(bearer_token,))
            monitor_thread.start()
        else:
            logging.error("Bearer Token cannot be empty!")

    def start_monitoring(self, bearer_token):
        self.case_battle.monitor_battles()

    def stop_bot(self):
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.token_entry.config(state=tk.NORMAL)

        # Zatrzymywanie monitorowania bitew
        if self.case_battle is not None:  # Sprawdź, czy case_battle zostało zainicjalizowane
            self.case_battle.stop_monitoring()

    def exit_program(self):
        self.stop_bot()
        self.window.quit()

    def open_github_repo(self):
        webbrowser.open("https://github.com/pstezynski/keydrop-battle-bot")

    def run(self):
        self.window.mainloop()

# Start the GUI
gui = GUI()
gui.run()

