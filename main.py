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
from tkinter import messagebox
from PIL import ImageTk, Image
import webbrowser
import threading
from threading import Thread

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

class Config:
    def __init__(self):
        if not os.path.exists("konfig.yaml"):
            self.log_message("Nie znaleziono pliku konfiguracyjnego! Tworze go dla ciebie...")
            with open("konfig.yaml", "w") as file:
                file.write(default_config)
            self.log_message("Plik konfiguracyjny stworzony! Uzupelnij go i zrestartuj bota.")
            exit()

        with open("konfig.yaml", "r") as file:
            self.config = yaml.load(file, Loader=SafeLoader)
            self.bearer_token = self.config.get("bearer_token", "")
            self.sleep_interval = self.config.get("sleep_interval", 1)
            self.ticket_cost_threshold = self.config.get("ticket_cost_threshold", 1000)
            self.ratelimit_sleep = self.config.get("ratelimit_sleep", 15)

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
        self.log_message(Center.XCenter("────────────────────────────────────────────\n"))
        self.log_message(Center.XCenter("Szukanie bitwy..."))

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
                return True, "Udalo sie dolaczyc do bitwy!"
            if data["errorCode"] == "slotUnavailable":
                return False, "Bitwa jest pełna!"
            if data["errorCode"] == "rateLimited":
                return False, "Ratelimited!"
            if data["errorCode"] == "userHasToWaitBeforeJoiningFreeBattle":
                return False, "Udział w darmowej bitwie można brać co 24 godziny!"
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
                    print(Colorate.Vertical(Colors.yellow_to_red, f"\n─────────────────[ {battle['id']} ]─────────────────\n\n", 1))
                    self.log_message(f"proba dolaczenia do bitwy {battle['id']}...")
                    print(Colorate.Horizontal(Colors.yellow_to_green, f"ID bitwy: {battle['id']}\n", 1))
                    success, message = self.join_battle(battle["id"])
                    if success:
                        self.log_message(message, Colors.green)
                        print(Colorate.Horizontal(Colors.green, message))
                    elif message == "Invalid token!":
                        self.log_message("Nieprawidlowy token bearer!", Colors.red)
                        exit()
                    elif message == "Ratelimited!":
                        self.log_message("Ratelimited! Trzeba zwiekszyc czas wstrzymania, lub dodac proxy.", Colors.red)
                        self.log_message("Wstrzymanie na 30 sekund...", Colors.yellow)
                        sleep(30)
                    elif message == "You have to wait one day between free battles!":
                        self.log_message("Musisz zaczekac 1 dzien przed ponownym dolaczaniem!", Colors.red)
                        exit()
                    else:
                        self.log_message(f"Nie udalo sie dolaczyc do bitwy! {message}", Colors.red)
                        sleep(self.sleep_interval)
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

    def log_message(self, message, color=Colors.yellow):
        gui.log_message(message, color)

class GUI:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Keydrop Battle Bot")
        self.window.geometry("900x480")

        self.log_text = tk.Text(self.window, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        self.token_label = tk.Label(self.window, text="Bearer Token:")
        self.token_label.pack()
        self.token_entry = tk.Entry(self.window, width=40)
        self.token_entry.pack()

        self.button_frame = tk.Frame(self.window)
        self.button_frame.pack()

        self.start_button = tk.Button(self.button_frame, text="Start", command=self.start_bot)
        self.start_button.pack(side=tk.LEFT)

        self.stop_button = tk.Button(self.button_frame, text="Stop", command=self.stop_bot, state=tk.DISABLED)
        self.stop_button.pack(side=tk.RIGHT)

        self.window.protocol("WM_DELETE_WINDOW", self.close_window)

        # Wyświetlanie logo
        self.log_message(Center.XCenter(logo))
        self.log_message(Center.XCenter("Wersja 0.1.2"))

    def start_bot(self):
        bearer_token = self.token_entry.get().strip()
        if bearer_token:
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.token_entry.config(state=tk.DISABLED)
            self.case_battle = CaseBattle(bearer_token)

            monitor_thread = Thread(target=self.case_battle.monitor_battles, daemon=True)
            monitor_thread.start()
        else:
            messagebox.showerror("Error", "Bearer Token nie może być pusty!")

    def stop_bot(self):
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.token_entry.config(state=tk.NORMAL)

        if self.case_battle is not None:
            self.case_battle.stop_monitoring()

    def close_window(self):
        if self.case_battle is not None and self.case_battle.running:
            messagebox.showinfo("Warning", "Zatrzymaj bota przed wyłączeniem.")
        else:
            self.window.destroy()

    def log_message(self, message, color=Colors.yellow):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n", color)
        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END)

    def run(self):
        self.window.mainloop()


gui = GUI()
gui.run()
