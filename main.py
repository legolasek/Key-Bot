import json, os, requests, logging, yaml, re, colorer
from time import sleep
from datetime import timedelta
from yaml import SafeLoader
from fake_useragent import UserAgent
from pystyle import Colors, Colorate, Center

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
    # Initialize the class.
    def __init__(self, token, sleep_interval=configData.sleep_interval, ticket_cost_threshold=configData.ticket_cost_threshold):
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
        print(Center.XCenter(Colorate.Vertical(Colors.yellow_to_red, "Wersja 0.1.1", 1)))
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
        while True:
            battles = self.get_active_battles()
            for battle in battles:
                if self.is_joinable(battle):
                    print (Colorate.Vertical(Colors.yellow_to_red, f"\n─────────────────[ {battle['id']} ]─────────────────\n\n", 1))
                    logging.info(f"proba dolaczenia do bitwy {battle['id']}...")
                    print (Colorate.Horizontal(Colors.yellow_to_green, f"ID bitwy: {battle['id']}\n", 1))
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

# Start the script.
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cb = CaseBattle(configData.bearer_token)
    cb.monitor_battles()