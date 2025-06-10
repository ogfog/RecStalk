import requests
import json
import time
from datetime import datetime
import os
import random
import ctypes
import sys
import shutil


#thank fog for this

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

WEBHOOK_URL = config['webhook_url']
BEARER_TOKEN = config['bearer_token']
GLITCH_INTENSITY = config['glitch_intensity']
BLUR_CHANCE = config['blur_chance']

last_room_data = None

def set_title():
    ctypes.windll.kernel32.SetConsoleTitleW("RecStalk (free) discord.gg/merch")

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def center_text(text):
    terminal_width = shutil.get_terminal_size().columns
    lines = text.split('\n')
    return '\n'.join(line.center(terminal_width) for line in lines)

class Colors:
    PINK = '\033[95m'
    PURPLE = '\033[35m'
    MAGENTA = '\033[38;5;200m'
    RESET = '\033[0m'
    BLUR = '\033[2m'

ASCII_ART = """
██████████████████████████████████████████████████████████████████████
█▄─▄▄▀█▄─▄▄─█─▄▄▄─█─▄▄▄▄█─▄─▄─██▀▄─██▄─▄███▄─█─▄███▄─█─▄█─▄▄─█████▀░██
██─▄─▄██─▄█▀█─███▀█▄▄▄▄─███─████─▀─███─██▀██─▄▀█████▄▀▄██─██─█░░███░██
▀▄▄▀▄▄▀▄▄▄▄▄▀▄▄▄▄▄▀▄▄▄▄▄▀▀▄▄▄▀▀▄▄▀▄▄▀▄▄▄▄▄▀▄▄▀▄▄▀▀▀▀▀▄▀▀▀▄▄▄▄▀▄▄▀▀▄▄▄▀
"""

def blur_effect(text):
    blur_chars = "░▒▓"
    result = ""
    for char in text:
        if char != " " and random.random() < BLUR_CHANCE:
            result += random.choice(blur_chars)
        else:
            result += char
    return result

def glitch_display(checks_count, demo_mode=False):
    colors = [Colors.PINK, Colors.PURPLE]
    clear()
    
    offset = random.randint(-2, 2)
    glitched_art = ''
    
    for line in ASCII_ART.splitlines():
        if line:
            color = random.choice(colors)
            
            if random.random() < GLITCH_INTENSITY:
                line = blur_effect(line)
                
            if offset > 0:
                line = " " * offset + line
            elif offset < 0:
                line = line[-offset:]
            
            if random.random() < GLITCH_INTENSITY:
                pos = random.randint(0, len(line)-1)
                chars = "█▀▄▌▐░▒▓"
                line = line[:pos] + random.choice(chars) + line[pos+1:]
            
            glitched_art += color + line + Colors.RESET + '\n'
    
    print('\n' * 2)
    print(center_text(glitched_art))
    if not demo_mode:
        color = random.choice(colors)
        print('\n')
        print(center_text(color + f"Status Checks: {checks_count}" + Colors.RESET))
        print('\n' * 3)
        time.sleep(0.05)

def get_player_data(player_id):
    url = f"https://match.rec.net/player?id={player_id}"
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    try:
        response = requests.get(url, headers=headers)
        return response.json()[0] if response.json() else None
    except:
        return None

def get_user_info():
    print(Colors.PINK + "Provide me a username: " + Colors.RESET, end='')
    username = input().strip()
    print(Colors.PINK + "Monitor room capacity? (y/n): " + Colors.RESET, end='').strip().lower() == 'y'
    url = f"https://apim.rec.net/accounts/account?username={username}"
    try:
        response = requests.get(url)
        data = response.json()
        return data.get("accountId"), username, monitor_capacity
    except:
        return None, None, False

def create_embed(data, username):
    global last_room_data
    
    if not data:
        return {
            "embeds": [{
                "title": "❌ Error fetching player data",
                "color": 16711680
            }]
        }

    color = 65280 if data["isOnline"] else 16711680
    
    embed = {
        "embeds": [{
            "title": f"**👓 Stalking - {username}**",
            "color": color,
            "image": {
                "url": config['embed_image']
            },
            "fields": [],
            "timestamp": datetime.utcnow().isoformat()
        }]
    }

    embed["embeds"][0]["fields"].append({
        "name": "Username",
        "value": username,
        "inline": True
    })

    status = "🟢 Online" if data["isOnline"] else "🔴 Offline"
    embed["embeds"][0]["fields"].append({
        "name": "Status",
        "value": status,
        "inline": True
    })

    embed["embeds"][0]["fields"].append({
        "name": "Last Online",
        "value": data["lastOnline"].replace("T", " ").replace("Z", " UTC"),
        "inline": True
    })

    vr_modes = {0: "Walk", 1: "Teleport", 2: "Hybrid"}
    embed["embeds"][0]["fields"].append({
        "name": "VR Movement",
        "value": vr_modes.get(data["vrMovementMode"], "Unknown"),
        "inline": True
    })

    if data["isOnline"] and data["roomInstance"]:
        room = data["roomInstance"]
        room_info = []
        
        privacy = "🔒 PRIVATE" if room["roomInstanceType"] == 2 else "🔓 PUBLIC"
        room_info.append(f"**Room Name:** {room['name']}")
        room_info.append(f"**Privacy:** {privacy}")
        room_info.append(f"**Capacity:** {room['maxCapacity']}")
        
        if room.get("voiceServerId"):
            room_info.append(f"**Voice Server:** {room['voiceServerId']}")
        if room.get("voiceAuthId"):
            room_info.append(f"**Voice Auth:** {room['voiceAuthId']}")

        embed["embeds"][0]["fields"].append({
            "name": "Room Information",
            "value": "\n".join(room_info),
            "inline": False
        })

        if last_room_data != room:
            embed["embeds"][0]["fields"].append({
                "name": "🔄 Room Change Detected",
                "value": f"Player moved to: {room['name']}",
                "inline": False
            })
            last_room_data = room

    return embed

def check_auth():
    try:
        response = requests.get("https://match.rec.net/player?id=1", 
                              headers={"Authorization": f"Bearer {BEARER_TOKEN}"})
        return response.status_code != 401
    except:
        return False

def startup_demo():
    start_time = time.time()
    while time.time() - start_time < config['demo_duration']:
        glitch_display(0, demo_mode=True)
        time.sleep(random.uniform(0.05, 0.2))

def create_room_status_embed(is_full, room_name):
    return {
        "embeds": [{
            "title": "Room Full" if is_full else "Room Open",
            "description": f"Room: {room_name}",
            "color": 16711680 if is_full else 65280
        }]
    }

def get_user_info():
    print(Colors.PINK + "Provide me a username: " + Colors.RESET, end='')
    username = input().strip()
    print(Colors.PINK + "Monitor room capacity? (y/n): " + Colors.RESET, end='')
    monitor_capacity = input().strip().lower() == 'y'
    url = f"https://apim.rec.net/accounts/account?username={username}"
    try:
        response = requests.get(url)
        data = response.json()
        return data.get("accountId"), username, monitor_capacity
    except:
        return None, None, False

def get_room_signature(room):
    return f"{room.get('name', '')}-{room.get('voiceServerId', '')}-{room.get('voiceAuthId', '')}"

def monitor_player():
    interval = config['check_interval']
    set_title()
    startup_demo()

    account_id, username, monitor_capacity = get_user_info()
    if not account_id:
        print("\nFailed to fetch account information!")
        return
    
    if not check_auth():
        clear()
        print(center_text(ASCII_ART))
        print(center_text("\nAuthorization Expired - Grab a New One!"))
        return
        
    checks_count = 0
    last_online_state = None
    last_room_signature = None
    last_room_full_state = None
    last_check_time = 0
    
    while True:
        try:
            current_time = time.time()
            
            if current_time - last_check_time >= interval:
                checks_count += 1
                last_check_time = current_time
                
                data = get_player_data(account_id)
                if not data:
                    clear()
                    print(center_text(ASCII_ART))
                    print(center_text("\nAuthorization Expired - Grab a New One!"))
                    break
                    
                current_online_state = data["isOnline"]

                if data["isOnline"] and data["roomInstance"]:
                    current_room = data["roomInstance"]
                    current_room_signature = get_room_signature(current_room)

                    if current_room_signature != last_room_signature:
                        privacy = "🔒 PRIVATE" if current_room["roomInstanceType"] == 2 else "🔓 PUBLIC"
                        room_change_embed = {
                            "embeds": [{
                                "title": f"Room Change - {username}",
                                "description": f"Moved to: {current_room['name']}\nPrivacy: {privacy}\nCapacity: {current_room['maxCapacity']}\nVoice Server: {current_room.get('voiceServerId', 'None')}\nVoice Auth: {current_room.get('voiceAuthId', 'None')}",
                                "color": 7506394
                            }]
                        }
                        requests.post(WEBHOOK_URL, json=room_change_embed)
                        last_room_signature = current_room_signature
                        
                    if monitor_capacity:
                        current_room_full = current_room["isFull"]
                        if current_room_full != last_room_full_state:
                            room_status_embed = {
                                "embeds": [{
                                    "title": "Room Full" if current_room_full else "Room Open",
                                    "description": f"User: {username}",
                                    "color": 16711680 if current_room_full else 65280
                                }]
                            }
                            requests.post(WEBHOOK_URL, json=room_status_embed)
                            last_room_full_state = current_room_full

                if current_online_state != last_online_state:
                    embed = create_embed(data, username)
                    requests.post(WEBHOOK_URL, json=embed)
                    last_online_state = current_online_state
            
            glitch_display(checks_count)
            time.sleep(0.05)
            
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(interval)
    
    if not check_auth():
        clear()
        print(center_text(ASCII_ART))
        print(center_text("\nAuthorization Expired - Grab a New One!"))
        return
        
    checks_count = 0
    last_online_state = None
    last_room_state = None
    last_room_full_state = None
    last_check_time = 0
    
    while True:
        try:
            current_time = time.time()
            
            if current_time - last_check_time >= interval:
                checks_count += 1
                last_check_time = current_time
                
                data = get_player_data(account_id)
                if not data:
                    clear()
                    print(center_text(ASCII_ART))
                    print(center_text("\nAuthorization Expired - Grab a New One!"))
                    break
                    
                current_online_state = data["isOnline"]
                current_room_state = json.dumps(data.get("roomInstance", {}), sort_keys=True)
                
                if data["isOnline"] and data["roomInstance"]:
                    current_room = data["roomInstance"]
                    current_room_name = current_room["name"]
                    current_voice_server = current_room.get("voiceServerId", "")
                    current_voice_auth = current_room.get("voiceAuthId", "")
                    
                    last_room = json.loads(last_room_state) if last_room_state else {}
                    last_voice_server = last_room.get("voiceServerId", "")
                    last_voice_auth = last_room.get("voiceAuthId", "")
                    
                    if (current_room_name != last_room.get("name", "") or 
                        current_voice_server != last_voice_server or 
                        current_voice_auth != last_voice_auth):
                        
                        privacy = "🔒 PRIVATE" if current_room["roomInstanceType"] == 2 else "🔓 PUBLIC"
                        room_change_embed = {
                            "embeds": [{
                                "title": f"Room Change - {username}",
                                "description": f"Moved to: {current_room_name}\nPrivacy: {privacy}\nCapacity: {current_room['maxCapacity']}",
                                "color": 7506394
                            }]
                        }
                        requests.post(WEBHOOK_URL, json=room_change_embed)

                    if monitor_capacity:
                        current_room_full = current_room["isFull"]
                        if current_room_full != last_room_full_state:
                            room_status_embed = {
                                "embeds": [{
                                    "title": "Room Full" if current_room_full else "Room Open",
                                    "description": f"User: {username}",
                                    "color": 16711680 if current_room_full else 65280
                                }]
                            }
                            requests.post(WEBHOOK_URL, json=room_status_embed)
                            last_room_full_state = current_room_full

                if current_online_state != last_online_state:
                    embed = create_embed(data, username)
                    requests.post(WEBHOOK_URL, json=embed)
                
                last_online_state = current_online_state
                last_room_state = current_room_state
            
            glitch_display(checks_count)
            time.sleep(0.05)
            
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(interval)

if __name__ == "__main__":
    monitor_player()
