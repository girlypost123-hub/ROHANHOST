import telebot
import subprocess
import os
import zipfile
import tempfile
import shutil
from telebot import types
import time
from datetime import datetime, timedelta
# Removed unused telegram.* imports as we are using telebot consistently
# from telegram import Update
# from telegram.ext import Updater, CommandHandler, CallbackContext
import psutil
import sqlite3
import json # Kept in case needed elsewhere, but not used in provided logic
import logging # Kept in case needed elsewhere
import signal # Kept in case needed elsewhere
import threading
import re # Added for regex matching in auto-install
import sys # Added for sys.executable
import atexit
import requests # For polling exceptions

import itertools as _itertools
import threading as _ethreading

# ─── Premium Emoji IDs (rotating per-call) ───────────────────
_PE = {
    "crown":    _itertools.cycle([5039727497143387500,5039539210072097557,5041792560368977040]),
    "star":     _itertools.cycle([5042176294222037888,5042061201983407048,5039555114335994885]),
    "gem":      _itertools.cycle([5042050649248760772,5039816072253932764,5041796412954641308]),
    "fire":     _itertools.cycle([5039644681583985437,5039690401510851397]),
    "bolt":     _itertools.cycle([5042334757040423886,5890847821728322055,5989800724312101453]),
    "check":    _itertools.cycle([5039793437776282663,5039844895779455925]),
    "cross":    _itertools.cycle([5040042498634810056,5042112436648281096]),
    "warn":     _itertools.cycle([5039665997506675838]),
    "pin":      _itertools.cycle([5039600026809009149,5039775669496579510,5967276872134824140]),
    "party":    _itertools.cycle([5039778134807806727,5039529134078821602,5989848973974704652]),
    "gift":     _itertools.cycle([5041975203853239332,5039823300683891773]),
    "eyes":     _itertools.cycle([5039623284056917259,5041784790773138608,5039984684080038649]),
    "brain":    _itertools.cycle([5040030395416969985]),
    "shield":   _itertools.cycle([5042328396193864923]),
    "chart":    _itertools.cycle([5042290883949495533]),
    "search":   _itertools.cycle([5039649904264217620]),
    "link":     _itertools.cycle([5042101437237036298]),
    "globe":    _itertools.cycle([5042186567783809934]),
    "bell":     _itertools.cycle([5042111805288089118,5039599902254957590]),
    "heart":    _itertools.cycle([5040072842578756396,5039643719511311434]),
    "sparkle":  _itertools.cycle([5040016479722931047,5039827436737397847,5987715818337603766]),
    "money":    _itertools.cycle([5039789890133296083,5040025580758631490]),
    "calendar": _itertools.cycle([5039534051816375152,5990174326337310665]),
    "wave":     _itertools.cycle([5040033797031070992,5042257262945502037]),
    "trash":    _itertools.cycle([5039614900280754969]),
    "refresh":  _itertools.cycle([5041837837914211014]),
    "green":    _itertools.cycle([5039928501612839813]),
    "red":      _itertools.cycle([5042042652019655612,5041801768778859296]),
    "announce": _itertools.cycle([5041888071851705019]),
    "moon":     _itertools.cycle([5041906342642582678,5042180842592404417]),
    "leaf":     _itertools.cycle([5042148333984941105]),
    "info":     _itertools.cycle([5041888071851705019]),  # FIXED: Added info emoji for premium use
    "bomb":     _itertools.cycle([5040025580758631490]),  # FIXED: Added bomb emoji for errors
}
_PLAIN = {
    "crown":"👑","star":"⭐","gem":"💎","fire":"🔥","bolt":"⚡",
    "check":"✅","cross":"❌","warn":"⚠️","pin":"📌","party":"🎉",
    "gift":"🎁","eyes":"👀","brain":"🧠","shield":"🛡️","chart":"📊",
    "search":"🔍","link":"🔗","globe":"🌐","bell":"🔔","heart":"❤️",
    "sparkle":"✨","money":"💰","calendar":"🗓️","wave":"👋","trash":"🗑️",  # FIXED: Fixed calendar emoji
    "refresh":"🔄","green":"🟢","red":"🔴","announce":"📣","moon":"🌙",
    "leaf":"🍃","info":"ℹ️","bomb":"💥","folder":"📁",  # FIXED: Added bomb and folder emojis
}
_pe_lock = _ethreading.Lock()

def E(key):
    """Return a rotating premium tg-emoji tag for use in HTML messages."""
    cyc = _PE.get(key)
    plain = _PLAIN.get(key, "✨")
    if not cyc:
        return plain
    with _pe_lock:
        eid = next(cyc)
    return f'<tg-emoji emoji-id="{eid}">{plain}</tg-emoji>'

def PE(key):
    """Return plain unicode emoji — use in button labels (buttons don't support HTML)."""
    return _PLAIN.get(key, "✨")


# --- Flask Keep Alive ---
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "ROHAN HOSTING BOT IS NOW RUNNING......................."
   
 

def run_flask():
  # Make sure to run on port provided by environment or default to 8080
  port = int(os.environ.get("PORT", 2828))
  app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True # Allows program to exit even if this thread is running
    t.start()
    print("Flask Keep-Alive server started.")
# --- End Flask Keep Alive ---

# --- Configuration ---
TOKEN = '8538853060:AAFKh-u2gDu6M7QMmeHpbHt_P6M3kQorZbo' # Replace with your actual token
OWNER_ID = '5994305183'# Replace with your Owner ID
ADMIN_ID = '5994305183' # Replace with your Admin ID (can be same as Owner)
YOUR_USERNAME = '@wasrohanxd' # Replace with your Telegram username (without the @)
UPDATE_CHANNEL = 'https://t.me/AutoHitterPy' # Replace with your update channel link

# --- Force Join Configuration ---
# Set FORCE_JOIN_CHANNEL to the channel/group username (e.g. '@MyChannel')
# or numeric chat ID (e.g. -1001234567890).
# Set to None to disable force-join.
FORCE_JOIN_CHANNEL = '@AutoHitterPy'  # <-- Change this to your channel/group
FORCE_JOIN_CHANNEL_LINK = UPDATE_CHANNEL  # Link shown to users who haven't joined

# Folder setup - using absolute paths
BASE_DIR = os.path.abspath(os.path.dirname(__file__)) # Get script's directory
UPLOAD_BOTS_DIR = os.path.join(BASE_DIR, 'upload_bots')
IROTECH_DIR = os.path.join(BASE_DIR, 'inf') # Assuming this name is intentional
DATABASE_PATH = os.path.join(IROTECH_DIR, 'bot_data.db')

# File upload limits
FREE_USER_LIMIT = 2
SUBSCRIBED_USER_LIMIT = 53 # Changed from 10 to 15
ADMIN_LIMIT = 9999    # Changed from 50 to 999
OWNER_LIMIT = float('inf') # Changed from 999 to infinity
# FREE_MODE_LIMIT = 3 # Removed as free_mode is removed

# Create necessary directories
os.makedirs(UPLOAD_BOTS_DIR, exist_ok=True)
os.makedirs(IROTECH_DIR, exist_ok=True)

# Initialize bot
bot = telebot.TeleBot(TOKEN)

# --- Data structures ---
bot_scripts = {} # Stores info about running scripts {script_key: info_dict}
user_subscriptions = {} # {user_id: {'expiry': datetime_object}}
user_files = {} # {user_id: [(file_name, file_type), ...]}
active_users = set() # Set of all user IDs that have interacted with the bot
admin_ids = {ADMIN_ID, OWNER_ID} # Set of admin IDs
bot_locked = False
BOT_START_TIME = datetime.now()   # tracks how long the bot has been running
# free_mode = False # Removed free_mode

# --- Logging Setup ---
# Configure basic logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Reply keyboard removed: using inline buttons only ---

# --- Database Setup ---
def init_db():
    """Initialize the database with required tables"""
    logger.info(f"Initializing database at: {DATABASE_PATH}")
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False) # Allow access from multiple threads
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS subscriptions
                     (user_id INTEGER PRIMARY KEY, expiry TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS user_files
                     (user_id INTEGER, file_name TEXT, file_type TEXT,
                      PRIMARY KEY (user_id, file_name))''')
        c.execute('''CREATE TABLE IF NOT EXISTS active_users
                     (user_id INTEGER PRIMARY KEY)''')
        c.execute('''CREATE TABLE IF NOT EXISTS admins
                     (user_id INTEGER PRIMARY KEY)''') # Added admins table
        # Ensure owner and initial admin are in admins table
        c.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (OWNER_ID,))
        if ADMIN_ID != OWNER_ID:
             c.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (ADMIN_ID,))
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"❌ Database initialization error: {e}", exc_info=True)

def load_data():
    """Load data from database into memory"""
    logger.info("Loading data from database...")
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()

        # Load subscriptions
        c.execute('SELECT user_id, expiry FROM subscriptions')
        for user_id, expiry in c.fetchall():
            try:
                user_subscriptions[user_id] = {'expiry': datetime.fromisoformat(expiry)}
            except ValueError:
                logger.warning(f"⚠️ Invalid expiry date format for user {user_id}: {expiry}. Skipping.")

        # Load user files
        c.execute('SELECT user_id, file_name, file_type FROM user_files')
        for user_id, file_name, file_type in c.fetchall():
            if user_id not in user_files:
                user_files[user_id] = []
            user_files[user_id].append((file_name, file_type))

        # Load active users
        c.execute('SELECT user_id FROM active_users')
        active_users.update(user_id for (user_id,) in c.fetchall())

        # Load admins
        c.execute('SELECT user_id FROM admins')
        admin_ids.update(user_id for (user_id,) in c.fetchall()) # Load admins into the set

        conn.close()
        logger.info(f"Data loaded: {len(active_users)} users, {len(user_subscriptions)} subscriptions, {len(admin_ids)} admins.")
    except Exception as e:
        logger.error(f"❌ Error loading data: {e}", exc_info=True)

# Initialize DB and Load Data at startup
init_db()
load_data()
# --- End Database Setup ---

# --- Helper Functions ---
def get_user_folder(user_id):
    """Get or create user's folder for storing files"""
    user_folder = os.path.join(UPLOAD_BOTS_DIR, str(user_id))
    os.makedirs(user_folder, exist_ok=True)
    return user_folder

def get_user_file_limit(user_id):
    """Get the file upload limit for a user"""
    # if free_mode: return FREE_MODE_LIMIT # Removed free_mode check
    if user_id == OWNER_ID: return OWNER_LIMIT
    if user_id in admin_ids: return ADMIN_LIMIT
    if user_id in user_subscriptions and user_subscriptions[user_id]['expiry'] > datetime.now():
        return SUBSCRIBED_USER_LIMIT
    return FREE_USER_LIMIT

def get_user_file_count(user_id):
    """Get the number of files uploaded by a user"""
    return len(user_files.get(user_id, []))

def is_bot_running(script_owner_id, file_name): # Parameter renamed for clarity
    """Check if a bot script is currently running for a specific user"""
    script_key = f"{script_owner_id}_{file_name}" # Key uses script_owner_id
    script_info = bot_scripts.get(script_key)
    if script_info and script_info.get('process'):
        try:
            proc = psutil.Process(script_info['process'].pid)
            is_running = proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
            if not is_running:
                logger.warning(f"Process {script_info['process'].pid} for {script_key} found in memory but not running/zombie. Cleaning up.")
                if 'log_file' in script_info and hasattr(script_info['log_file'], 'close') and not script_info['log_file'].closed:
                    try:
                        script_info['log_file'].close()
                    except Exception as log_e:
                        logger.error(f"Error closing log file during zombie cleanup {script_key}: {log_e}")
                if script_key in bot_scripts:
                    del bot_scripts[script_key]
            return is_running
        except psutil.NoSuchProcess:
            logger.warning(f"Process for {script_key} not found (NoSuchProcess). Cleaning up.")
            if 'log_file' in script_info and hasattr(script_info['log_file'], 'close') and not script_info['log_file'].closed:
                try:
                     script_info['log_file'].close()
                except Exception as log_e:
                     logger.error(f"Error closing log file during cleanup of non-existent process {script_key}: {log_e}")
            if script_key in bot_scripts:
                 del bot_scripts[script_key]
            return False
        except Exception as e:
            logger.error(f"Error checking process status for {script_key}: {e}", exc_info=True)
            return False
    return False


def kill_process_tree(process_info):
    """Kill a process and all its children, ensuring log file is closed."""
    pid = None
    log_file_closed = False
    script_key = process_info.get('script_key', 'N/A') 

    try:
        if 'log_file' in process_info and hasattr(process_info['log_file'], 'close') and not process_info['log_file'].closed:
            try:
                process_info['log_file'].close()
                log_file_closed = True
                logger.info(f"Closed log file for {script_key} (PID: {process_info.get('process', {}).get('pid', 'N/A')})")
            except Exception as log_e:
                logger.error(f"Error closing log file during kill for {script_key}: {log_e}")

        process = process_info.get('process')
        if process and hasattr(process, 'pid'):
           pid = process.pid
           if pid: 
                try:
                    parent = psutil.Process(pid)
                    children = parent.children(recursive=True)
                    logger.info(f"Attempting to kill process tree for {script_key} (PID: {pid}, Children: {[c.pid for c in children]})")

                    for child in children:
                        try:
                            child.terminate()
                            logger.info(f"Terminated child process {child.pid} for {script_key}")
                        except psutil.NoSuchProcess:
                            logger.warning(f"Child process {child.pid} for {script_key} already gone.")
                        except Exception as e:
                            logger.error(f"Error terminating child {child.pid} for {script_key}: {e}. Trying kill...")
                            try: child.kill(); logger.info(f"Killed child process {child.pid} for {script_key}")
                            except Exception as e2: logger.error(f"Failed to kill child {child.pid} for {script_key}: {e2}")

                    gone, alive = psutil.wait_procs(children, timeout=1)
                    for p in alive:
                        logger.warning(f"Child process {p.pid} for {script_key} still alive. Killing.")
                        try: p.kill()
                        except Exception as e: logger.error(f"Failed to kill child {p.pid} for {script_key} after wait: {e}")

                    try:
                        parent.terminate()
                        logger.info(f"Terminated parent process {pid} for {script_key}")
                        try: parent.wait(timeout=1)
                        except psutil.TimeoutExpired:
                            logger.warning(f"Parent process {pid} for {script_key} did not terminate. Killing.")
                            parent.kill()
                            logger.info(f"Killed parent process {pid} for {script_key}")
                    except psutil.NoSuchProcess:
                        logger.warning(f"Parent process {pid} for {script_key} already gone.")
                    except Exception as e:
                        logger.error(f"Error terminating parent {pid} for {script_key}: {e}. Trying kill...")
                        try: parent.kill(); logger.info(f"Killed parent process {pid} for {script_key}")
                        except Exception as e2: logger.error(f"Failed to kill parent {pid} for {script_key}: {e2}")

                except psutil.NoSuchProcess:
                    logger.warning(f"Process {pid or 'N/A'} for {script_key} not found during kill. Already terminated?")
           else: logger.error(f"Process PID is None for {script_key}.")
        elif log_file_closed: logger.warning(f"Process object missing for {script_key}, but log file closed.")
        else: logger.error(f"Process object missing for {script_key}, and no log file. Cannot kill.")
    except Exception as e:
        logger.error(f"❌ Unexpected error killing process tree for PID {pid or 'N/A'} ({script_key}): {e}", exc_info=True)

# --- Automatic Package Installation & Script Running ---

def attempt_install_pip(module_name, message):
    package_name = TELEGRAM_MODULES.get(module_name.lower(), module_name) 
    if package_name is None: 
        logger.info(f"Module '{module_name}' is core. Skipping pip install.")
        return False 
    try:
        bot.reply_to(message, f"{E('eyes')} Module <code>{module_name}</code> not found. Installing <code>{package_name}</code>...", parse_mode='HTML')
        command = [sys.executable, '-m', 'pip', 'install', package_name]
        logger.info(f"Running install: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True, check=False, encoding='utf-8', errors='ignore')
        if result.returncode == 0:
            logger.info(f"Installed {package_name}. Output:\n{result.stdout}")
            bot.reply_to(message, f"{E('check')} Package <code>{package_name}</code> installed.", parse_mode='HTML')
            return True
        else:
            error_msg = f"{E('cross')} Failed to install <code>{package_name}</code> for <code>{module_name}</code>.\nLog:\n``<code>\n{result.stderr or result.stdout}\n</code>``"
            logger.error(error_msg)
            if len(error_msg) > 4000: error_msg = error_msg[:4000] + "\n... (Log truncated)"
            bot.reply_to(message, error_msg, parse_mode='HTML')
            return False
    except Exception as e:
        error_msg = f"{E('cross')} Error installing <code>{package_name}</code>: {str(e)}"
        logger.error(error_msg, exc_info=True)
        bot.reply_to(message, error_msg)
        return False

def attempt_install_npm(module_name, user_folder, message):
    try:
        bot.reply_to(message, f"{E('eyes')} Node package <code>{module_name}</code> not found. Installing locally...", parse_mode='HTML')
        command = ['npm', 'install', module_name]
        logger.info(f"Running npm install: {' '.join(command)} in {user_folder}")
        result = subprocess.run(command, capture_output=True, text=True, check=False, cwd=user_folder, encoding='utf-8', errors='ignore')
        if result.returncode == 0:
            logger.info(f"Installed {module_name}. Output:\n{result.stdout}")
            bot.reply_to(message, f"{E('check')} Node package <code>{module_name}</code> installed locally.", parse_mode='HTML')
            return True
        else:
            error_msg = f"{E('cross')} Failed to install Node package <code>{module_name}</code>.\nLog:\n``<code>\n{result.stderr or result.stdout}\n</code>``"
            logger.error(error_msg)
            if len(error_msg) > 4000: error_msg = error_msg[:4000] + "\n... (Log truncated)"
            bot.reply_to(message, error_msg, parse_mode='HTML')
            return False
    except FileNotFoundError:
         error_msg = f"{E('cross')} Error: 'npm' not found. Ensure Node.js/npm are installed and in PATH."
         logger.error(error_msg)
         bot.reply_to(message, error_msg)
         return False
    except Exception as e:
        error_msg = f"{E('cross')} Error installing Node package <code>{module_name}</code>: {str(e)}"
        logger.error(error_msg, exc_info=True)
        bot.reply_to(message, error_msg)
        return False

def run_script(script_path, script_owner_id, user_folder, file_name, message_obj_for_reply, attempt=1):
    """Run Python script. script_owner_id is used for the script_key. message_obj_for_reply is for sending feedback."""
    max_attempts = 2 
    if attempt > max_attempts:
        bot.reply_to(message_obj_for_reply, f"{E('cross')} Failed to run '{file_name}' after {max_attempts} attempts. Check logs.")
        return

    script_key = f"{script_owner_id}_{file_name}"
    logger.info(f"Attempt {attempt} to run Python script: {script_path} (Key: {script_key}) for user {script_owner_id}")

    try:
        if not os.path.exists(script_path):
             bot.reply_to(message_obj_for_reply, f"{E('cross')} Error: Script '{file_name}' not found at '{script_path}'!")
             logger.error(f"Script not found: {script_path} for user {script_owner_id}")
             if script_owner_id in user_files:
                 user_files[script_owner_id] = [f for f in user_files.get(script_owner_id, []) if f[0] != file_name]
             remove_user_file_db(script_owner_id, file_name)
             return

        if attempt == 1:
            check_command = [sys.executable, script_path]
            logger.info(f"Running Python pre-check: {' '.join(check_command)}")
            check_proc = None
            try:
                check_proc = subprocess.Popen(check_command, cwd=user_folder, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore')
                stdout, stderr = check_proc.communicate(timeout=5)
                return_code = check_proc.returncode
                logger.info(f"Python Pre-check early. RC: {return_code}. Stderr: {stderr[:200]}...")
                if return_code != 0 and stderr:
                    match_py = re.search(r"ModuleNotFoundError: No module named '(.+?)'", stderr)
                    if match_py:
                        module_name = match_py.group(1).strip().strip("'\"")
                        logger.info(f"Detected missing Python module: {module_name}")
                        if attempt_install_pip(module_name, message_obj_for_reply):
                            logger.info(f"Install OK for {module_name}. Retrying run_script...")
                            bot.reply_to(message_obj_for_reply, f"{E('refresh')} Install successful. Retrying '{file_name}'...")
                            time.sleep(2)
                            threading.Thread(target=run_script, args=(script_path, script_owner_id, user_folder, file_name, message_obj_for_reply, attempt + 1)).start()
                            return
                        else:
                            bot.reply_to(message_obj_for_reply, f"{E('cross')} Install failed. Cannot run '{file_name}'.")
                            return
                    else:
                         error_summary = stderr[:500]
                         bot.reply_to(message_obj_for_reply, f"{E('cross')} Error in script pre-check for '{file_name}':\n``<code>\n{error_summary}\n</code>``\nFix the script.", parse_mode='HTML')
                         return
            except subprocess.TimeoutExpired:
                logger.info("Python Pre-check timed out (>5s), imports likely OK. Killing check process.")
                if check_proc and check_proc.poll() is None: check_proc.kill(); check_proc.communicate()
                logger.info("Python Check process killed. Proceeding to long run.")
            except FileNotFoundError:
                 logger.error(f"Python interpreter not found: {sys.executable}")
                 bot.reply_to(message_obj_for_reply, f"{E('cross')} Error: Python interpreter '{sys.executable}' not found.")
                 return
            except Exception as e:
                 logger.error(f"Error in Python pre-check for {script_key}: {e}", exc_info=True)
                 bot.reply_to(message_obj_for_reply, f"{E('cross')} Unexpected error in script pre-check for '{file_name}': {e}")
                 return
            finally:
                 if check_proc and check_proc.poll() is None:
                     logger.warning(f"Python Check process {check_proc.pid} still running. Killing.")
                     check_proc.kill(); check_proc.communicate()

        logger.info(f"Starting long-running Python process for {script_key}")
        log_file_path = os.path.join(user_folder, f"{os.path.splitext(file_name)[0]}.log")
        log_file = None; process = None
        try: log_file = open(log_file_path, 'w', encoding='utf-8', errors='ignore')
        except Exception as e:
             logger.error(f"Failed to open log file '{log_file_path}' for {script_key}: {e}", exc_info=True)
             bot.reply_to(message_obj_for_reply, f"{E('cross')} Failed to open log file '{log_file_path}': {e}")
             return
        try:
            startupinfo = None; creationflags = 0
            if os.name == 'nt':
                 startupinfo = subprocess.STARTUPINFO(); startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                 startupinfo.wShowWindow = subprocess.SW_HIDE
            process = subprocess.Popen(
                [sys.executable, script_path], cwd=user_folder, stdout=log_file, stderr=log_file,
                stdin=subprocess.PIPE, startupinfo=startupinfo, creationflags=creationflags,
                encoding='utf-8', errors='ignore'
            )
            logger.info(f"Started Python process {process.pid} for {script_key}")
            bot_scripts[script_key] = {
                'process': process, 'log_file': log_file, 'file_name': file_name,
                'chat_id': message_obj_for_reply.chat.id,
                'script_owner_id': script_owner_id,
                'start_time': datetime.now(), 'user_folder': user_folder, 'type': 'py', 'script_key': script_key
            }
            now_str = datetime.now().strftime("%d %b %Y  %H:%M:%S")
            hosted_markup = types.InlineKeyboardMarkup()
            hosted_markup.add(types.InlineKeyboardButton(
                f'{PE("bolt")} Manage File', callback_data=f'file_{script_owner_id}_{file_name}'))
            hosted_markup.add(types.InlineKeyboardButton(
                f'{PE("gem")} My Files', callback_data='check_files'),
                types.InlineKeyboardButton(f'{PE("heart")} Main Menu', callback_data='back_to_main'))
            bot.reply_to(message_obj_for_reply,
                f"{E('check')} <b>Script Hosted!</b>\n\n"
                f"┌◈────────────────────◈┐\n"
                f"│  {E('pin')}  𝐅𝐢𝐥𝐞   →  <code>{file_name}</code>\n"
                f"│  {E('bolt')}  𝐓𝐲𝐩𝐞   →  Python\n"
                f"│  {E('green')}  𝐒𝐭𝐚𝐭𝐮𝐬 →  Running\n"
                f"│  {E('eyes')}  𝐏𝐈𝐃   →  <code>{process.pid}</code>\n"
                f"│  {E('calendar')}  𝐒𝐭𝐚𝐫𝐭  →  <code>{now_str}</code>\n"
                f"└◈────────────────────◈┘\n\n"
                f"{E('check')}  𝐒𝐭𝐞𝐩 𝟒/𝟒 — 𝐋𝐢𝐯𝐞 & 𝐑𝐮𝐧𝐧𝐢𝐧𝐠!\n"
                f"▓▓▓▓▓▓▓▓▓▓  100%\n\n"
                f"{E('fire')}  Use the buttons below to manage your script.",
                parse_mode='HTML', reply_markup=hosted_markup)
        except FileNotFoundError:
             logger.error(f"Python interpreter {sys.executable} not found for long run {script_key}")
             bot.reply_to(message_obj_for_reply, f"{E('cross')} Error: Python interpreter '{sys.executable}' not found.")
             if log_file and not log_file.closed: log_file.close()
             if script_key in bot_scripts: del bot_scripts[script_key]
        except Exception as e:
            if log_file and not log_file.closed: log_file.close()
            error_msg = f"{E('cross')} Error starting Python script '{file_name}': {str(e)}"
            logger.error(error_msg, exc_info=True)
            bot.reply_to(message_obj_for_reply, error_msg)
            if process and process.poll() is None:
                 logger.warning(f"Killing potentially started Python process {process.pid} for {script_key}")
                 kill_process_tree({'process': process, 'log_file': log_file, 'script_key': script_key})
            if script_key in bot_scripts: del bot_scripts[script_key]
    except Exception as e:
        error_msg = f"{E('cross')} Unexpected error running Python script '{file_name}': {str(e)}"
        logger.error(error_msg, exc_info=True)
        bot.reply_to(message_obj_for_reply, error_msg)
        if script_key in bot_scripts:
             logger.warning(f"Cleaning up {script_key} due to error in run_script.")
             kill_process_tree(bot_scripts[script_key])
             del bot_scripts[script_key]

def run_js_script(script_path, script_owner_id, user_folder, file_name, message_obj_for_reply, attempt=1):
    """Run JS script. script_owner_id is used for the script_key. message_obj_for_reply is for sending feedback."""
    max_attempts = 2
    if attempt > max_attempts:
        bot.reply_to(message_obj_for_reply, f"{E('cross')} Failed to run '{file_name}' after {max_attempts} attempts. Check logs.")
        return

    script_key = f"{script_owner_id}_{file_name}"
    logger.info(f"Attempt {attempt} to run JS script: {script_path} (Key: {script_key}) for user {script_owner_id}")

    try:
        if not os.path.exists(script_path):
             bot.reply_to(message_obj_for_reply, f"{E('cross')} Error: Script '{file_name}' not found at '{script_path}'!")
             logger.error(f"JS Script not found: {script_path} for user {script_owner_id}")
             if script_owner_id in user_files:
                 user_files[script_owner_id] = [f for f in user_files.get(script_owner_id, []) if f[0] != file_name]
             remove_user_file_db(script_owner_id, file_name)
             return

        if attempt == 1:
            check_command = ['node', script_path]
            logger.info(f"Running JS pre-check: {' '.join(check_command)}")
            check_proc = None
            try:
                check_proc = subprocess.Popen(check_command, cwd=user_folder, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore')
                stdout, stderr = check_proc.communicate(timeout=5)
                return_code = check_proc.returncode
                logger.info(f"JS Pre-check early. RC: {return_code}. Stderr: {stderr[:200]}...")
                if return_code != 0 and stderr:
                    match_js = re.search(r"Cannot find module '(.+?)'", stderr)
                    if match_js:
                        module_name = match_js.group(1).strip().strip("'\"")
                        if not module_name.startswith('.') and not module_name.startswith('/'):
                             logger.info(f"Detected missing Node module: {module_name}")
                             if attempt_install_npm(module_name, user_folder, message_obj_for_reply):
                                 logger.info(f"NPM Install OK for {module_name}. Retrying run_js_script...")
                                 bot.reply_to(message_obj_for_reply, f"{E('refresh')} NPM Install successful. Retrying '{file_name}'...")
                                 time.sleep(2)
                                 threading.Thread(target=run_js_script, args=(script_path, script_owner_id, user_folder, file_name, message_obj_for_reply, attempt + 1)).start()
                                 return
                             else:
                                 bot.reply_to(message_obj_for_reply, f"{E('cross')} NPM Install failed. Cannot run '{file_name}'.")
                                 return
                        else: logger.info(f"Skipping npm install for relative/core: {module_name}")
                    error_summary = stderr[:500]
                    bot.reply_to(message_obj_for_reply, f"{E('cross')} Error in JS script pre-check for '{file_name}':\n``<code>\n{error_summary}\n</code>``\nFix script or install manually.", parse_mode='HTML')
                    return
            except subprocess.TimeoutExpired:
                logger.info("JS Pre-check timed out (>5s), imports likely OK. Killing check process.")
                if check_proc and check_proc.poll() is None: check_proc.kill(); check_proc.communicate()
                logger.info("JS Check process killed. Proceeding to long run.")
            except FileNotFoundError:
                 error_msg = f"{E('cross')} Error: 'node' not found. Ensure Node.js is installed for JS files."
                 logger.error(error_msg)
                 bot.reply_to(message_obj_for_reply, error_msg)
                 return
            except Exception as e:
                 logger.error(f"Error in JS pre-check for {script_key}: {e}", exc_info=True)
                 bot.reply_to(message_obj_for_reply, f"{E('cross')} Unexpected error in JS pre-check for '{file_name}': {e}")
                 return
            finally:
                 if check_proc and check_proc.poll() is None:
                     logger.warning(f"JS Check process {check_proc.pid} still running. Killing.")
                     check_proc.kill(); check_proc.communicate()

        logger.info(f"Starting long-running JS process for {script_key}")
        log_file_path = os.path.join(user_folder, f"{os.path.splitext(file_name)[0]}.log")
        log_file = None; process = None
        try: log_file = open(log_file_path, 'w', encoding='utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Failed to open log file '{log_file_path}' for JS script {script_key}: {e}", exc_info=True)
            bot.reply_to(message_obj_for_reply, f"{E('cross')} Failed to open log file '{log_file_path}': {e}")
            return
        try:
            startupinfo = None; creationflags = 0
            if os.name == 'nt':
                 startupinfo = subprocess.STARTUPINFO(); startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                 startupinfo.wShowWindow = subprocess.SW_HIDE
            process = subprocess.Popen(
                ['node', script_path], cwd=user_folder, stdout=log_file, stderr=log_file,
                stdin=subprocess.PIPE, startupinfo=startupinfo, creationflags=creationflags,
                encoding='utf-8', errors='ignore'
            )
            logger.info(f"Started JS process {process.pid} for {script_key}")
            bot_scripts[script_key] = {
                'process': process, 'log_file': log_file, 'file_name': file_name,
                'chat_id': message_obj_for_reply.chat.id,
                'script_owner_id': script_owner_id,
                'start_time': datetime.now(), 'user_folder': user_folder, 'type': 'js', 'script_key': script_key
            }
            now_str = datetime.now().strftime("%d %b %Y  %H:%M:%S")
            hosted_markup = types.InlineKeyboardMarkup()
            hosted_markup.add(types.InlineKeyboardButton(
                f'{PE("bolt")} Manage File', callback_data=f'file_{script_owner_id}_{file_name}'))
            hosted_markup.add(types.InlineKeyboardButton(
                f'{PE("gem")} My Files', callback_data='check_files'),
                types.InlineKeyboardButton(f'{PE("heart")} Main Menu', callback_data='back_to_main'))
            bot.reply_to(message_obj_for_reply,
                f"{E('check')} <b>Script Hosted!</b>\n\n"
                f"┌◈────────────────────◈┐\n"
                f"│  {E('pin')}  𝐅𝐢𝐥𝐞   →  <code>{file_name}</code>\n"
                f"│  {E('bolt')}  𝐓𝐲𝐩𝐞   →  JavaScript\n"
                f"│  {E('green')}  𝐒𝐭𝐚𝐭𝐮𝐬 →  Running\n"
                f"│  {E('eyes')}  𝐏𝐈𝐃   →  <code>{process.pid}</code>\n"
                f"│  {E('calendar')}  𝐒𝐭𝐚𝐫𝐭  →  <code>{now_str}</code>\n"
                f"└◈────────────────────◈┘\n\n"
                f"{E('check')}  𝐒𝐭𝐞𝐩 𝟒/𝟒 — 𝐋𝐢𝐯𝐞 & 𝐑𝐮𝐧𝐧𝐢𝐧𝐠!\n"
                f"▓▓▓▓▓▓▓▓▓▓  100%\n\n"
                f"{E('fire')}  Use the buttons below to manage your script.",
                parse_mode='HTML', reply_markup=hosted_markup)
        except FileNotFoundError:
             error_msg = f"{E('cross')} Error: 'node' not found for long run. Ensure Node.js is installed."
             logger.error(error_msg)
             if log_file and not log_file.closed: log_file.close()
             bot.reply_to(message_obj_for_reply, error_msg)
             if script_key in bot_scripts: del bot_scripts[script_key]
        except Exception as e:
            if log_file and not log_file.closed: log_file.close()
            error_msg = f"{E('cross')} Error starting JS script '{file_name}': {str(e)}"
            logger.error(error_msg, exc_info=True)
            bot.reply_to(message_obj_for_reply, error_msg)
            if process and process.poll() is None:
                 logger.warning(f"Killing potentially started JS process {process.pid} for {script_key}")
                 kill_process_tree({'process': process, 'log_file': log_file, 'script_key': script_key})
            if script_key in bot_scripts: del bot_scripts[script_key]
    except Exception as e:
        error_msg = f"{E('cross')} Unexpected error running JS script '{file_name}': {str(e)}"
        logger.error(error_msg, exc_info=True)
        bot.reply_to(message_obj_for_reply, error_msg)
        if script_key in bot_scripts:
             logger.warning(f"Cleaning up {script_key} due to error in run_js_script.")
             kill_process_tree(bot_scripts[script_key])
             del bot_scripts[script_key]

# --- Map Telegram import names to actual PyPI package names ---
TELEGRAM_MODULES = {
    # Main Bot Frameworks
    'telebot': 'pyTelegramBotAPI',
    'telegram': 'python-telegram-bot',
    'python_telegram_bot': 'python-telegram-bot',
    'aiogram': 'aiogram',
    'pyrogram': 'pyrogram',
    'telethon': 'telethon',
    'telethon.sync': 'telethon', # Handle specific imports
    'from telethon.sync import telegramclient': 'telethon', # Example

    # Additional Libraries (add more specific mappings if import name differs)
    'telepot': 'telepot',
    'pytg': 'pytg',
    'tgcrypto': 'tgcrypto',
    'telegram_upload': 'telegram-upload',
    'telegram_send': 'telegram-send',
    'telegram_text': 'telegram-text',

    # MTProto & Low-Level
    'mtproto': 'telegram-mtproto', # Example, check actual package name
    'tl': 'telethon',  # Part of Telethon, install 'telethon'

    # Utilities & Helpers (examples, verify package names)
    'telegram_utils': 'telegram-utils',
    'telegram_logger': 'telegram-logger',
    'telegram_handlers': 'python-telegram-handlers',

    # Database Integrations (examples)
    'telegram_redis': 'telegram-redis',
    'telegram_sqlalchemy': 'telegram-sqlalchemy',

    # Payment & E-commerce (examples)
    'telegram_payment': 'telegram-payment',
    'telegram_shop': 'telegram-shop-sdk',

    # Testing & Debugging (examples)
    'pytest_telegram': 'pytest-telegram',
    'telegram_debug': 'telegram-debug',

    # Scraping & Analytics (examples)
    'telegram_scraper': 'telegram-scraper',
    'telegram_analytics': 'telegram-analytics',

    # NLP & AI (examples)
    'telegram_nlp': 'telegram-nlp-toolkit',
    'telegram_ai': 'telegram-ai', # Assuming this exists

    # Web & API Integration (examples)
    'telegram_api': 'telegram-api-client',
    'telegram_web': 'telegram-web-integration',

    # Gaming & Interactive (examples)
    'telegram_games': 'telegram-games',
    'telegram_quiz': 'telegram-quiz-bot',

    # File & Media Handling (examples)
    'telegram_ffmpeg': 'telegram-ffmpeg',
    'telegram_media': 'telegram-media-utils',

    # Security & Encryption (examples)
    'telegram_2fa': 'telegram-twofa',
    'telegram_crypto': 'telegram-crypto-bot',

    # Localization & i18n (examples)
    'telegram_i18n': 'telegram-i18n',
    'telegram_translate': 'telegram-translate',

    # Common non-telegram examples
    'bs4': 'beautifulsoup4',
    'requests': 'requests',
    'pillow': 'Pillow', # Note the capitalization difference
    'cv2': 'opencv-python', # Common import name for OpenCV
    'yaml': 'PyYAML',
    'dotenv': 'python-dotenv',
    'dateutil': 'python-dateutil',
    'pandas': 'pandas',
    'numpy': 'numpy',
    'flask': 'Flask',
    'django': 'Django',
    'sqlalchemy': 'SQLAlchemy',
    'asyncio': None, # Core module, should not be installed
    'json': None,    # Core module
    'datetime': None,# Core module
    'os': None,      # Core module
    'sys': None,     # Core module
    're': None,      # Core module
    'time': None,    # Core module
    'math': None,    # Core module
    'random': None,  # Core module
    'logging': None, # Core module
    'threading': None,# Core module
    'subprocess':None,# Core module
    'zipfile':None,  # Core module
    'tempfile':None, # Core module
    'shutil':None,   # Core module
    'sqlite3':None,  # Core module
    'psutil': 'psutil',
    'atexit': None   # Core module

}
# --- End Automatic Package Installation & Script Running ---


# --- Force Join Helper ---
def check_force_join(user_id):
    """
    Returns True if the user has joined the required channel/group,
    or if FORCE_JOIN_CHANNEL is None (feature disabled).
    Admins and owner are always exempt.
    """
    if FORCE_JOIN_CHANNEL is None:
        return True
    if user_id == int(OWNER_ID) or str(user_id) == OWNER_ID:
        return True
    if user_id in admin_ids or str(user_id) in admin_ids:
        return True
    try:
        member = bot.get_chat_member(FORCE_JOIN_CHANNEL, user_id)
        return member.status in ('member', 'administrator', 'creator')
    except Exception as e:
        logger.warning(f"Force-join check failed for user {user_id}: {e}")
        # If we can't check (e.g. bot not admin in channel), allow through to avoid blocking users
        return True

def send_force_join_message(chat_id):
    """Send a message asking the user to join the required channel."""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f'{PE("link")} Join Channel / Group', url=FORCE_JOIN_CHANNEL_LINK))
    markup.add(types.InlineKeyboardButton(f'{PE("check")} I Have Joined — Verify', callback_data='verify_join'))
    bot.send_message(
        chat_id,
        f"{E('shield')} <b>Access Restricted</b>\n\n"
        f"{E('eyes')} To use this bot, join our channel first.\n\n"
        f"{E('bell')} Channel: <code>{FORCE_JOIN_CHANNEL}</code>\n\n"
        f"{E('link')} Join, then tap <b>Verify</b> below.",
        reply_markup=markup,
        parse_mode='HTML'
    )
# --- End Force Join Helper ---

# --- Database Operations ---
DB_LOCK = threading.Lock() 

def save_user_file(user_id, file_name, file_type='py'):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('INSERT OR REPLACE INTO user_files (user_id, file_name, file_type) VALUES (?, ?, ?)',
                      (user_id, file_name, file_type))
            conn.commit()
            if user_id not in user_files: user_files[user_id] = []
            user_files[user_id] = [(fn, ft) for fn, ft in user_files[user_id] if fn != file_name]
            user_files[user_id].append((file_name, file_type))
            logger.info(f"Saved file '{file_name}' ({file_type}) for user {user_id}")
        except sqlite3.Error as e: logger.error(f"❌ SQLite error saving file for user {user_id}, {file_name}: {e}")
        except Exception as e: logger.error(f"❌ Unexpected error saving file for {user_id}, {file_name}: {e}", exc_info=True)
        finally: conn.close()

def remove_user_file_db(user_id, file_name):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('DELETE FROM user_files WHERE user_id = ? AND file_name = ?', (user_id, file_name))
            conn.commit()
            if user_id in user_files:
                user_files[user_id] = [f for f in user_files[user_id] if f[0] != file_name]
                if not user_files[user_id]: del user_files[user_id]
            logger.info(f"Removed file '{file_name}' for user {user_id} from DB")
        except sqlite3.Error as e: logger.error(f"❌ SQLite error removing file for {user_id}, {file_name}: {e}")
        except Exception as e: logger.error(f"❌ Unexpected error removing file for {user_id}, {file_name}: {e}", exc_info=True)
        finally: conn.close()

def add_active_user(user_id):
    active_users.add(user_id) 
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('INSERT OR IGNORE INTO active_users (user_id) VALUES (?)', (user_id,))
            conn.commit()
            logger.info(f"Added/Confirmed active user {user_id} in DB")
        except sqlite3.Error as e: logger.error(f"❌ SQLite error adding active user {user_id}: {e}")
        except Exception as e: logger.error(f"❌ Unexpected error adding active user {user_id}: {e}", exc_info=True)
        finally: conn.close()

def save_subscription(user_id, expiry):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            expiry_str = expiry.isoformat()
            c.execute('INSERT OR REPLACE INTO subscriptions (user_id, expiry) VALUES (?, ?)', (user_id, expiry_str))
            conn.commit()
            user_subscriptions[user_id] = {'expiry': expiry}
            logger.info(f"Saved subscription for {user_id}, expiry {expiry_str}")
        except sqlite3.Error as e: logger.error(f"❌ SQLite error saving subscription for {user_id}: {e}")
        except Exception as e: logger.error(f"❌ Unexpected error saving subscription for {user_id}: {e}", exc_info=True)
        finally: conn.close()

def remove_subscription_db(user_id):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('DELETE FROM subscriptions WHERE user_id = ?', (user_id,))
            conn.commit()
            if user_id in user_subscriptions: del user_subscriptions[user_id]
            logger.info(f"Removed subscription for {user_id} from DB")
        except sqlite3.Error as e: logger.error(f"❌ SQLite error removing subscription for {user_id}: {e}")
        except Exception as e: logger.error(f"❌ Unexpected error removing subscription for {user_id}: {e}", exc_info=True)
        finally: conn.close()

def add_admin_db(admin_id):
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        try:
            c.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (admin_id,))
            conn.commit()
            admin_ids.add(admin_id) 
            logger.info(f"Added admin {admin_id} to DB")
        except sqlite3.Error as e: logger.error(f"❌ SQLite error adding admin {admin_id}: {e}")
        except Exception as e: logger.error(f"❌ Unexpected error adding admin {admin_id}: {e}", exc_info=True)
        finally: conn.close()

def remove_admin_db(admin_id):
    if admin_id == OWNER_ID:
        logger.warning("Attempted to remove OWNER_ID from admins.")
        return False 
    with DB_LOCK:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        c = conn.cursor()
        removed = False
        try:
            c.execute('SELECT 1 FROM admins WHERE user_id = ?', (admin_id,))
            if c.fetchone():
                c.execute('DELETE FROM admins WHERE user_id = ?', (admin_id,))
                conn.commit()
                removed = c.rowcount > 0 
                if removed: admin_ids.discard(admin_id); logger.info(f"Removed admin {admin_id} from DB")
                else: logger.warning(f"Admin {admin_id} found but delete affected 0 rows.")
            else:
                logger.warning(f"Admin {admin_id} not found in DB.")
                admin_ids.discard(admin_id)
            return removed
        except sqlite3.Error as e: logger.error(f"❌ SQLite error removing admin {admin_id}: {e}"); return False
        except Exception as e: logger.error(f"❌ Unexpected error removing admin {admin_id}: {e}", exc_info=True); return False
        finally: conn.close()
# --- End Database Operations ---

# --- Menu creation (Inline and ReplyKeyboards) ---
def create_main_menu_inline(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton(f'{PE("bell")} Updates Channel', url=UPDATE_CHANNEL),
        types.InlineKeyboardButton(f'{PE("sparkle")} Upload File', callback_data='upload'),
        types.InlineKeyboardButton(f'{PE("gem")} My Files', callback_data='check_files'),
        types.InlineKeyboardButton(f'{PE("bolt")} Bot Speed', callback_data='speed'),
        types.InlineKeyboardButton(f'{PE("crown")} Contact Owner', url=f'https://t.me/{YOUR_USERNAME.replace("@", "")}')
    ]

    if user_id in admin_ids:
        admin_buttons = [
            types.InlineKeyboardButton(f'{PE("money")} Subscriptions', callback_data='subscription'),
            types.InlineKeyboardButton(f'{PE("chart")} Statistics', callback_data='stats'),
            types.InlineKeyboardButton(f'{PE("shield")} Lock Bot' if not bot_locked else f'{PE("shield")} Unlock Bot',
                                     callback_data='lock_bot' if not bot_locked else 'unlock_bot'),
            types.InlineKeyboardButton(f'{PE("announce")} Broadcast', callback_data='broadcast'),
            types.InlineKeyboardButton(f'{PE("crown")} Admin Panel', callback_data='admin_panel'),
            types.InlineKeyboardButton(f'{PE("bolt")} Run All Code', callback_data='run_all_scripts')
        ]
        markup.add(buttons[0])
        markup.add(buttons[1], buttons[2])
        markup.add(buttons[3], admin_buttons[0])
        markup.add(admin_buttons[1], admin_buttons[3])
        markup.add(admin_buttons[2], admin_buttons[5])
        markup.add(admin_buttons[4])
        markup.add(buttons[4])
    else:
        markup.add(buttons[0])
        markup.add(buttons[1], buttons[2])
        markup.add(buttons[3])
        markup.add(types.InlineKeyboardButton(f'{PE("chart")} Statistics', callback_data='stats'))
        markup.add(buttons[4])
    return markup

def create_control_buttons(script_owner_id, file_name, is_running=True): # Parameter renamed
    markup = types.InlineKeyboardMarkup(row_width=2)
    # Callbacks use script_owner_id
    if is_running:
        markup.row(
            types.InlineKeyboardButton(f'{PE("red")} Stop', callback_data=f'stop_{script_owner_id}_{file_name}'),
            types.InlineKeyboardButton(f'{PE("refresh")} Restart', callback_data=f'restart_{script_owner_id}_{file_name}')
        )
        markup.row(
            types.InlineKeyboardButton(f'{PE("trash")} Delete', callback_data=f'delete_{script_owner_id}_{file_name}'),
            types.InlineKeyboardButton(f'{PE("search")} Logs', callback_data=f'logs_{script_owner_id}_{file_name}')
        )
    else:
        markup.row(
            types.InlineKeyboardButton(f'{PE("green")} Start', callback_data=f'start_{script_owner_id}_{file_name}'),
            types.InlineKeyboardButton(f'{PE("trash")} Delete', callback_data=f'delete_{script_owner_id}_{file_name}')
        )
        markup.row(
            types.InlineKeyboardButton(f'{PE("search")} View Logs', callback_data=f'logs_{script_owner_id}_{file_name}')
        )
    markup.add(types.InlineKeyboardButton(f'{PE("gem")} Back to Files', callback_data='check_files'))
    return markup

def create_admin_panel():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        types.InlineKeyboardButton(f'{PE("sparkle")} Add Admin', callback_data='add_admin'),
        types.InlineKeyboardButton(f'{PE("cross")} Remove Admin', callback_data='remove_admin')
    )
    markup.row(types.InlineKeyboardButton(f'{PE("crown")} List Admins', callback_data='list_admins'))
    markup.row(types.InlineKeyboardButton(f'{PE("heart")} Back to Main', callback_data='back_to_main'))
    return markup

def create_subscription_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        types.InlineKeyboardButton(f'{PE("party")} Add Subscription', callback_data='add_subscription'),
        types.InlineKeyboardButton(f'{PE("cross")} Remove Subscription', callback_data='remove_subscription')
    )
    markup.row(types.InlineKeyboardButton(f'{PE("search")} Check Subscription', callback_data='check_subscription'))
    markup.row(types.InlineKeyboardButton(f'{PE("heart")} Back to Main', callback_data='back_to_main'))
    return markup
# --- End Menu Creation ---

# --- File Handling ---
def handle_zip_file(downloaded_file_content, file_name_zip, message):
    user_id = message.from_user.id
    # chat_id = message.chat.id # script_owner_id (user_id here) will be used for script key context
    user_folder = get_user_folder(user_id)
    temp_dir = None 
    try:
        temp_dir = tempfile.mkdtemp(prefix=f"user_{user_id}_zip_")
        logger.info(f"Temp dir for zip: {temp_dir}")
        zip_path = os.path.join(temp_dir, file_name_zip)
        with open(zip_path, 'wb') as new_file: new_file.write(downloaded_file_content)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for member in zip_ref.infolist():
                member_path = os.path.abspath(os.path.join(temp_dir, member.filename))
                if not member_path.startswith(os.path.abspath(temp_dir)):
                    raise zipfile.BadZipFile(f"Zip has unsafe path: {member.filename}")
            zip_ref.extractall(temp_dir)
            logger.info(f"Extracted zip to {temp_dir}")

        extracted_items = os.listdir(temp_dir)
        py_files = [f for f in extracted_items if f.endswith('.py')]
        js_files = [f for f in extracted_items if f.endswith('.js')]
        req_file = 'requirements.txt' if 'requirements.txt' in extracted_items else None
        pkg_json = 'package.json' if 'package.json' in extracted_items else None

        if req_file:
            req_path = os.path.join(temp_dir, req_file)
            logger.info(f"requirements.txt found, installing: {req_path}")
            bot.reply_to(message, f"{E('refresh')} Installing Python deps from <code>{req_file}</code>...")
            try:
                command = [sys.executable, '-m', 'pip', 'install', '-r', req_path]
                result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore')
                logger.info(f"pip install from requirements.txt OK. Output:\n{result.stdout}")
                bot.reply_to(message, f"{E('check')} Python deps from <code>{req_file}</code> installed.")
            except subprocess.CalledProcessError as e:
                error_msg = f"{E('cross')} Failed to install Python deps from <code>{req_file}</code>.\nLog:\n``<code>\n{e.stderr or e.stdout}\n</code>``"
                logger.error(error_msg)
                if len(error_msg) > 4000: error_msg = error_msg[:4000] + "\n... (Log truncated)"
                bot.reply_to(message, error_msg, parse_mode='HTML'); return
            except Exception as e:
                 error_msg = f"{E('cross')} Unexpected error installing Python deps: {e}"
                 logger.error(error_msg, exc_info=True); bot.reply_to(message, error_msg); return

        if pkg_json:
            logger.info(f"package.json found, npm install in: {temp_dir}")
            bot.reply_to(message, f"{E('refresh')} Installing Node deps from <code>{pkg_json}</code>...")
            try:
                command = ['npm', 'install']
                result = subprocess.run(command, capture_output=True, text=True, check=True, cwd=temp_dir, encoding='utf-8', errors='ignore')
                logger.info(f"npm install OK. Output:\n{result.stdout}")
                bot.reply_to(message, f"{E('check')} Node deps from <code>{pkg_json}</code> installed.")
            except FileNotFoundError:
                bot.reply_to(message, f"{E('cross')} 'npm' not found. Cannot install Node deps."); return 
            except subprocess.CalledProcessError as e:
                error_msg = f"{E('cross')} Failed to install Node deps from <code>{pkg_json}</code>.\nLog:\n``<code>\n{e.stderr or e.stdout}\n</code>``"
                logger.error(error_msg)
                if len(error_msg) > 4000: error_msg = error_msg[:4000] + "\n... (Log truncated)"
                bot.reply_to(message, error_msg, parse_mode='HTML'); return
            except Exception as e:
                 error_msg = f"{E('cross')} Unexpected error installing Node deps: {e}"
                 logger.error(error_msg, exc_info=True); bot.reply_to(message, error_msg); return

        main_script_name = None; file_type = None
        preferred_py = ['main.py', 'bot.py', 'app.py']; preferred_js = ['index.js', 'main.js', 'bot.js', 'app.js']
        for p in preferred_py:
            if p in py_files: main_script_name = p; file_type = 'py'; break
        if not main_script_name:
             for p in preferred_js:
                 if p in js_files: main_script_name = p; file_type = 'js'; break
        if not main_script_name:
            if py_files: main_script_name = py_files[0]; file_type = 'py'
            elif js_files: main_script_name = js_files[0]; file_type = 'js'
        if not main_script_name:
            bot.reply_to(message, f"{E('cross')} No <code>.py</code> or <code>.js</code> script found in archive!"); return

        logger.info(f"Moving extracted files from {temp_dir} to {user_folder}")
        moved_count = 0
        for item_name in os.listdir(temp_dir):
            src_path = os.path.join(temp_dir, item_name)
            dest_path = os.path.join(user_folder, item_name)
            if os.path.isdir(dest_path): shutil.rmtree(dest_path)
            elif os.path.exists(dest_path): os.remove(dest_path)
            shutil.move(src_path, dest_path); moved_count +=1
        logger.info(f"Moved {moved_count} items to {user_folder}")

        save_user_file(user_id, main_script_name, file_type)
        logger.info(f"Saved main script '{main_script_name}' ({file_type}) for {user_id} from zip.")
        main_script_path = os.path.join(user_folder, main_script_name)
        bot.reply_to(message, f"{E('sparkle')} Files extracted. Starting <code>{main_script_name}</code>...", parse_mode='HTML')

        # Use user_id as script_owner_id for script key context
        if file_type == 'py':
             threading.Thread(target=run_script, args=(main_script_path, user_id, user_folder, main_script_name, message)).start()
        elif file_type == 'js':
             threading.Thread(target=run_js_script, args=(main_script_path, user_id, user_folder, main_script_name, message)).start()

    except zipfile.BadZipFile as e:
        logger.error(f"Bad zip file from {user_id}: {e}")
        bot.reply_to(message, f"{E('cross')} Error: Invalid/corrupted ZIP. {e}")
    except Exception as e:
        logger.error(f"❌ Error processing zip for {user_id}: {e}", exc_info=True)
        bot.reply_to(message, f"{E('cross')} Error processing zip: {str(e)}")
    finally:
        if temp_dir and os.path.exists(temp_dir):
            try: shutil.rmtree(temp_dir); logger.info(f"Cleaned temp dir: {temp_dir}")
            except Exception as e: logger.error(f"Failed to clean temp dir {temp_dir}: {e}", exc_info=True)

def handle_js_file(file_path, script_owner_id, user_folder, file_name, message):
    try:
        save_user_file(script_owner_id, file_name, 'js')
        threading.Thread(target=run_js_script, args=(file_path, script_owner_id, user_folder, file_name, message)).start()
    except Exception as e:
        logger.error(f"❌ Error processing JS file {file_name} for {script_owner_id}: {e}", exc_info=True)
        bot.reply_to(message, f"{E('cross')} Error processing JS file: {str(e)}")

def handle_py_file(file_path, script_owner_id, user_folder, file_name, message):
    try:
        save_user_file(script_owner_id, file_name, 'py')
        threading.Thread(target=run_script, args=(file_path, script_owner_id, user_folder, file_name, message)).start()
    except Exception as e:
        logger.error(f"❌ Error processing Python file {file_name} for {script_owner_id}: {e}", exc_info=True)
        bot.reply_to(message, f"{E('cross')} Error processing Python file: {str(e)}")
# --- End File Handling ---


# --- Logic Functions (called by commands and text handlers) ---
def _logic_send_welcome(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    user_name = message.from_user.first_name
    user_username = message.from_user.username

    logger.info(f"Welcome request from user_id: {user_id}, username: @{user_username}")

    try:
        dismiss = bot.send_message(chat_id, "ᅠ", reply_markup=types.ReplyKeyboardRemove())
        bot.delete_message(chat_id, dismiss.message_id)
    except Exception:
        pass

    if bot_locked and user_id not in admin_ids:
        bot.send_message(chat_id, f"{E('shield')} <b>Bot Locked!</b>\n\n{E('warn')} The bot is currently locked by admin.\n{E('moon')} Please try again later.", parse_mode='HTML')
        return

    # --- Force Join Check ---
    if not check_force_join(user_id):
        send_force_join_message(chat_id)
        return
    # --- End Force Join Check ---

    user_bio = "Could not fetch bio"; photo_file_id = None
    try: user_bio = bot.get_chat(user_id).bio or "No bio"
    except Exception: pass
    try:
        user_profile_photos = bot.get_user_profile_photos(user_id, limit=1)
        if user_profile_photos.photos: photo_file_id = user_profile_photos.photos[0][-1].file_id
    except Exception: pass

    if user_id not in active_users:
        add_active_user(user_id)
        try:
            owner_notification = (f"「 {E('party')} 𝐍𝐞𝐰 𝐔𝐬𝐞𝐫 𝐉𝐨𝐢𝐧𝐞𝐝! »\n\n"
                                  f"━━━━━━━━━━━━━━━━━━\n"
                                  f"{E('eyes')} *Name :* {user_name}\n"
                                  f"{E('star')} *Username :* @{user_username or 'N/A'}\n"
                                  f"🆔 *ID :* <code>{user_id}</code>\n"
                                  f"{E('pin')} *Bio :* {user_bio}\n"
                                  f"━━━━━━━━━━━━━━━━━━")
            bot.send_message(OWNER_ID, owner_notification, parse_mode='HTML')
            if photo_file_id: bot.send_photo(OWNER_ID, photo_file_id, caption=f"{E('eyes')} Profile pic of new user {user_id}")
        except Exception as e: logger.error(f"⚠️ Failed to notify owner about new user {user_id}: {e}")

    file_limit = get_user_file_limit(user_id)
    current_files = get_user_file_count(user_id)
    limit_str = str(file_limit) if file_limit != float('inf') else "Unlimited"
    expiry_info = ""
    if user_id == OWNER_ID: user_status = f"{E('crown')} Owner"
    elif user_id in admin_ids: user_status = f"{E('shield')} Admin"
    elif user_id in user_subscriptions:
        expiry_date = user_subscriptions[user_id].get('expiry')
        if expiry_date and expiry_date > datetime.now():
            user_status = "⭐ Premium"; days_left = (expiry_date - datetime.now()).days
            expiry_info = f"\n{E('calendar')} Subscription expires in: {days_left} days"
        else: user_status = "🆓 Free User (Expired Sub)"; remove_subscription_db(user_id) # Clean up expired
    else: user_status = "🆓 Free User"

    welcome_msg_text = (
        f"{E('boltf')} <b>HOSTING BOT</b> {E('bolt')}\n"
        f"{E('crownf')} Script Hosting & Manager {E('star')}\n\n"
        f"{E('wave')}  Hey {user_name}!\n\n"
        f"┌◈────────────────────◈┐\n"
        f"  {E('eyes')} ID      →  <code>{user_id}</code>\n"
        f"  {E('link')} User    →  @{user_username or 'Not set'}\n"
        f"  {E('star')} Status  →  {user_status}{expiry_info}\n"
        f"  {E('gem')} Files   →  <code>{current_files}</code> / <code>{limit_str}</code>\n"
        f"└◈────────────────────◈┘\n\n"
        f"{E('fire')}  Host .py · .js · .zip scripts\n"
        f"{E('sparkle')}  Upload, Run & Manage with ease\n\n"
        f"{E('pinf')} Tap a button below to continue {E('pin')}"
    )
    main_reply_markup = create_main_menu_inline(user_id)
    try:
        if photo_file_id: bot.send_photo(chat_id, photo_file_id)
        bot.send_message(chat_id, welcome_msg_text, reply_markup=main_reply_markup, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Error sending welcome to {user_id}: {e}", exc_info=True)
        try: bot.send_message(chat_id, welcome_msg_text, reply_markup=main_reply_markup, parse_mode='HTML')
        except Exception as fallback_e: logger.error(f"Fallback send_message failed for {user_id}: {fallback_e}")

def _logic_updates_channel(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f'{PE("bell")} Updates Channel', url=UPDATE_CHANNEL))
    bot.reply_to(message, f"{E('bellf')} <b>Updates Channel</b>\n\n{E('sparkle')}  Stay updated with the latest news!", reply_markup=markup, parse_mode='HTML')

def _logic_upload_file(message):
    user_id = message.from_user.id
    if bot_locked and user_id not in admin_ids:
        bot.reply_to(message, f"{E('warn')} Bot locked by admin, cannot accept files.")
        return

    # --- Force Join Check ---
    if not check_force_join(user_id):
        send_force_join_message(message.chat.id)
        return
    # --- End Force Join Check ---

    # Removed free_mode check, relies on get_user_file_limit and FREE_USER_LIMIT
    # Users need to be admin or subscribed to upload if FREE_USER_LIMIT is 0
    # For now, FREE_USER_LIMIT > 0, so free users can upload up to that limit.
    # If we want to restrict free users entirely, set FREE_USER_LIMIT to 0.
    # For this implementation, free users get FREE_USER_LIMIT.

    file_limit = get_user_file_limit(user_id)
    current_files = get_user_file_count(user_id)
    if current_files >= file_limit:
        limit_str = str(file_limit) if file_limit != float('inf') else "Unlimited"
        bot.reply_to(message, f"「 {E('warn')} 𝐅𝐢𝐥𝐞 𝐋𝐢𝐦𝐢𝐭 𝐑𝐞𝐚𝐜𝐡𝐞𝐝 »\n\n⬡  𝐘𝐨𝐮 𝐡𝐚𝐯𝐞 𝐫𝐞𝐚𝐜𝐡𝐞𝐝 𝐲𝐨𝐮𝐫 𝐥𝐢𝐦𝐢𝐭 <code>{current_files}/{limit_str}</code>. 𝐏𝐥𝐞𝐚𝐬𝐞 𝐝𝐞𝐥𝐞𝐭𝐞 𝐬𝐨𝐦𝐞 𝐟𝐢𝐥𝐞𝐬 𝐟𝐢𝐫𝐬𝐭.", parse_mode='HTML')
        return
    bot.reply_to(message, f"{E('sparklef')} <b>Upload Your Script</b>\n\n{E('pin')}  Send your .py Python, .js JS, or .zip ZIP file.", parse_mode='HTML')

def _logic_check_files(message):
    user_id = message.from_user.id
    # chat_id = message.chat.id # user_id will be used as script_owner_id for buttons
    user_files_list = user_files.get(user_id, [])
    if not user_files_list:
        bot.reply_to(message, f"{E('gemf')} <b>My Files</b>\n\n┌◈────────────────────◈┐\n  {E('moonf')}  No files uploaded yet.\n└◈────────────────────◈┘\n\n{E('sparkle')}  Upload a .py · .js · .zip to get started!", parse_mode='HTML')
        return
    markup = types.InlineKeyboardMarkup(row_width=1)
    for file_name, file_type in sorted(user_files_list):
        is_running = is_bot_running(user_id, file_name)
        status_icon = f"{E('green')} Running" if is_running else f"{E('red')} Stopped"
        btn_text = f"{file_name} ({file_type}) — {status_icon}"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f'file_{user_id}_{file_name}'))
    bot.reply_to(message, f"{E('gemf')} <b>My Files</b>\n\n{E('pin')}  Tap a file below to manage it:", reply_markup=markup, parse_mode='HTML')

def _logic_bot_speed(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    start_time_ping = time.time()
    wait_msg = bot.reply_to(message, "⬡  𝐓𝐞𝐬𝐭𝐢𝐧𝐠 𝐛𝐨𝐭 𝐬𝐩𝐞𝐞𝐝...", parse_mode='HTML')
    try:
        bot.send_chat_action(chat_id, 'typing')
        response_time = round((time.time() - start_time_ping) * 1000, 2)
        status = f"{E('check')} Unlocked" if not bot_locked else f"{E('shield')} Locked"
        # mode = "💰 Free Mode: ON" if free_mode else "💸 Free Mode: OFF" # Removed free_mode
        if user_id == OWNER_ID: user_level = f"{E('crown')} Owner"
        elif user_id in admin_ids: user_level = f"{E('shield')} Admin"
        elif user_id in user_subscriptions and user_subscriptions[user_id].get('expiry', datetime.min) > datetime.now(): user_level = "⭐ Premium"
        else: user_level = "🆓 Free User"
        speed_msg = (f"{E('bolt')} <b>Bot Speed & Status</b>\n\n"
                     f"╔─────────────────────────╗\n"
                     f"│  {E('sparkle')}  Ping   ➤  <code>{response_time} ms</code>\n"
                     f"│  {E('green')}  Status ➤  {status}\n"
                     f"│  {E('crown')}  Level  ➤  {user_level}\n"
                     f"╚─────────────────────────╝")
        bot.edit_message_text(speed_msg, chat_id, wait_msg.message_id, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Error during speed test (cmd): {e}", exc_info=True)
        bot.edit_message_text(f"{E('cross')} Error during speed test.", chat_id, wait_msg.message_id, parse_mode='HTML')

def _logic_contact_owner(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f'{PE("crown")} Contact Owner', url=f'https://t.me/{YOUR_USERNAME.replace("@", "")}'))
    bot.reply_to(message, f"{E('crownf')} <b>Contact Owner</b>\n\n{E('heart')}  Need help? Reach the owner directly!", reply_markup=markup, parse_mode='HTML')

# --- Admin Logic Functions ---
def _logic_subscriptions_panel(message):
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, f"{E('warn')} Admin permissions required.", parse_mode='HTML')
        return
    bot.reply_to(message, f"「 {E('money')} 𝐒𝐮𝐛𝐬𝐜𝐫𝐢𝐩𝐭𝐢𝐨𝐧 𝐌𝐚𝐧𝐚𝐠𝐞𝐦𝐞𝐧𝐭 »\n\n⬡  𝐒𝐞𝐥𝐞𝐜𝐭 𝐚𝐧 𝐚𝐜𝐭𝐢𝐨𝐧 𝐛𝐞𝐥𝐨𝐰:", reply_markup=create_subscription_menu(), parse_mode='HTML')

def _format_uptime(start_time):
    """Return a human-readable uptime string from a start datetime."""
    delta = datetime.now() - start_time
    total_seconds = int(delta.total_seconds())
    days    = total_seconds // 86400
    hours   = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    parts = []
    if days:    parts.append(f"{days}d")
    if hours:   parts.append(f"{hours}h")
    if minutes: parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    return " ".join(parts)

def _get_system_stats():
    """Return CPU%, RAM used/total, and disk used/total as strings."""
    try:
        cpu   = psutil.cpu_percent(interval=0.3)
        ram   = psutil.virtual_memory()
        disk  = psutil.disk_usage('/')
        ram_used  = round(ram.used  / (1024**3), 2)
        ram_total = round(ram.total / (1024**3), 2)
        disk_used  = round(disk.used  / (1024**3), 1)
        disk_total = round(disk.total / (1024**3), 1)
        return cpu, ram_used, ram_total, disk_used, disk_total
    except Exception:
        return 0, 0, 0, 0, 0

def _get_running_scripts_detail():
    """Return list of dicts with name, owner, uptime for all running scripts."""
    result = []
    for script_key, info in list(bot_scripts.items()):
        try:
            s_owner_id_str, _ = script_key.split('_', 1)
            s_owner_id = int(s_owner_id_str)
        except Exception:
            continue
        if is_bot_running(s_owner_id, info['file_name']):
            uptime_str = _format_uptime(info.get('start_time', datetime.now()))
            result.append({
                'file': info['file_name'],
                'owner': s_owner_id,
                'uptime': uptime_str,
                'type': info.get('type', '?'),
            })
    return result

def _logic_statistics(message):
    """Rich real-time statistics — different depth for users vs admins."""
    user_id = message.from_user.id
    now_str = datetime.now().strftime("%d %b %Y  %H:%M:%S")

    total_users       = len(active_users)
    total_files_all   = sum(len(f) for f in user_files.values())
    my_files          = len(user_files.get(user_id, []))
    running_detail    = _get_running_scripts_detail()
    running_total     = len(running_detail)
    my_running        = sum(1 for r in running_detail if r['owner'] == user_id)
    bot_uptime        = _format_uptime(BOT_START_TIME)
    total_subs        = len([uid for uid, info in user_subscriptions.items()
                             if info.get('expiry', datetime.min) > datetime.now()])

    # ── User section ──────────────────────────────────────────────
    msg = (
        f"{E('chart')} <b>Real-Time Stats</b>\n"
        f"{E('calendar')}  <code>{now_str}</code>\n\n"
        f"┌◈──────────────────────◈┐\n"
        f"│  {E('eyes')}  𝐓𝐨𝐭𝐚𝐥 𝐔𝐬𝐞𝐫𝐬      ➤  <code>{total_users}</code>\n"
        f"│  {E('gem')}  Total Files      ➤  <code>{total_files_all}</code>\n"
        f"│  {E('green')}  𝐑𝐮𝐧𝐧𝐢𝐧𝐠 𝐒𝐜𝐫𝐢𝐩𝐭𝐬  ➤  <code>{running_total}</code>\n"
        f"│  {E('star')}  Premium Users   ➤  <code>{total_subs}</code>\n"
        f"│  {E('fire')}  𝐁𝐨𝐭 𝐔𝐩𝐭𝐢𝐦𝐞      ➤  <code>{bot_uptime}</code>\n"
        f"└◈──────────────────────◈┘\n\n"
        f"{E('crown')} Your Info:\n"
        f"  {E('pin')}  My Files       ➤  <code>{my_files}</code>\n"
        f"  {E('bolt')}  My Running    ➤  <code>{my_running}</code>\n"
    )

    # Per-user running file details
    my_scripts = [r for r in running_detail if r['owner'] == user_id]
    if my_scripts:
        msg += f"\n{E('sparkle')} My Running Files:\n"
        for r in my_scripts:
            msg += f"  {E('green')} <code>{r['file']}</code> ({r['type']} — ⏱ {r['uptime']}\n"

    # ── Admin extra section ───────────────────────────────────────
    if user_id in admin_ids:
        cpu, ram_used, ram_total, disk_used, disk_total = _get_system_stats()
        msg += (
            f"\n┌◈──── {E('crown')} Admin Dashboard ────◈┐\n"
            f"│  {E('shield')}  Bot Lock     ➤  {E('red') + ' Locked' if bot_locked else E('green') + ' Unlocked'}\n"
            f"│  {E('brain')}  CPU          ➤  <code>{cpu}%</code>\n"
            f"│  {E('bolt')}  RAM          ➤  <code>{ram_used} / {ram_total} GB</code>\n"
            f"│  {E('gem')}  Disk         ➤  <code>{disk_used} / {disk_total} GB</code>\n"
            f"│  {E('crown')}  Admins       ➤  <code>{len(admin_ids)}</code>\n"
            f"└◈──────────────────────────◈┘\n"
        )
        # All running scripts list for admin
        if running_detail:
            msg += f"\n{E('fire')} All Running Scripts:\n"
            for r in running_detail:
                msg += f"  {E('green')} <code>{r['file']}</code> ({r['type']} | {E('eyes')}<code>{r['owner']}</code> | ⏱<code>{r['uptime']}</code>\n"
        else:
            msg += f"\n{E('moon')} No scripts currently running.\n"

    # Refresh button
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f'{PE("refresh")} Refresh Stats', callback_data='stats'))
    markup.add(types.InlineKeyboardButton(f'{PE("heart")} Back to Main',  callback_data='back_to_main'))
    bot.reply_to(message, msg, parse_mode='HTML', reply_markup=markup)


def _logic_broadcast_init(message):
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, f"{E('warn')} Admin permissions required.", parse_mode='HTML')
        return
    msg = bot.reply_to(message, "📣  𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 𝐌𝐞𝐬𝐬𝐚𝐠𝐞\n\n𝐒𝐞𝐧𝐝 𝐭𝐡𝐞 𝐦𝐞𝐬𝐬𝐚𝐠𝐞 𝐭𝐨 𝐛𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 𝐭𝐨 𝐚𝐥𝐥 𝐚𝐜𝐭𝐢𝐯𝐞 𝐮𝐬𝐞𝐫𝐬.\n\n/cancel to abort.", parse_mode='HTML')
    bot.register_next_step_handler(msg, process_broadcast_message)

def _logic_toggle_lock_bot(message):
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, f"{E('warn')} Admin permissions required.", parse_mode='HTML')
        return
    global bot_locked
    bot_locked = not bot_locked
    status = "locked" if bot_locked else "unlocked"
    logger.warning(f"Bot {status} by Admin {message.from_user.id} via command/button.")
    bot.reply_to(message, f"{E('shield')} <b>Bot Status</b>\n\n{E('check')} Bot has been {status}", parse_mode='HTML')

# def _logic_toggle_free_mode(message): # Removed
#     pass

def _logic_admin_panel(message):
    if message.from_user.id not in admin_ids:
        bot.reply_to(message, f"{E('warn')} Admin permissions required.", parse_mode='HTML')
        return
    bot.reply_to(message, f"{E('crownf')} <b>Admin Panel</b>\n\n{E('pin')}  Manage admins using the buttons below:",
                 reply_markup=create_admin_panel(), parse_mode='HTML')

def _logic_run_all_scripts(message_or_call):
    if isinstance(message_or_call, telebot.types.Message):
        admin_user_id = message_or_call.from_user.id
        admin_chat_id = message_or_call.chat.id
        reply_func = lambda text, *kwargs: bot.reply_to(message_or_call, text, *kwargs)
        admin_message_obj_for_script_runner = message_or_call
    elif isinstance(message_or_call, telebot.types.CallbackQuery):
        admin_user_id = message_or_call.from_user.id
        admin_chat_id = message_or_call.message.chat.id
        bot.answer_callback_query(message_or_call.id)
        reply_func = lambda text, *kwargs: bot.send_message(admin_chat_id, text, *kwargs)
        admin_message_obj_for_script_runner = message_or_call.message 
    else:
        logger.error("Invalid argument for _logic_run_all_scripts")
        return

    if admin_user_id not in admin_ids:
        reply_func(f"{E('warn')} Admin permissions required.")
        return

    reply_func(f"{E('boltf')} <b>Running All Scripts</b>\n\n{E('eyes')}  Starting all user scripts... Please wait.", parse_mode='HTML')
    logger.info(f"Admin {admin_user_id} initiated 'run all scripts' from chat {admin_chat_id}.")

    started_count = 0; attempted_users = 0; skipped_files = 0; error_files_details = []

    # Use a copy of user_files keys and values to avoid modification issues during iteration
    all_user_files_snapshot = dict(user_files)

    for target_user_id, files_for_user in all_user_files_snapshot.items():
        if not files_for_user: continue
        attempted_users += 1
        logger.info(f"Processing scripts for user {target_user_id}...")
        user_folder = get_user_folder(target_user_id)

        for file_name, file_type in files_for_user:
            # script_owner_id for key context is target_user_id
            if not is_bot_running(target_user_id, file_name):
                file_path = os.path.join(user_folder, file_name)
                if os.path.exists(file_path):
                    logger.info(f"Admin {admin_user_id} attempting to start '{file_name}' ({file_type}) for user {target_user_id}.")
                    try:
                        if file_type == 'py':
                            threading.Thread(target=run_script, args=(file_path, target_user_id, user_folder, file_name, admin_message_obj_for_script_runner)).start()
                            started_count += 1
                        elif file_type == 'js':
                            threading.Thread(target=run_js_script, args=(file_path, target_user_id, user_folder, file_name, admin_message_obj_for_script_runner)).start()
                            started_count += 1
                        else:
                            logger.warning(f"Unknown file type '{file_type}' for {file_name} (user {target_user_id}). Skipping.")
                            error_files_details.append(f"<code>{file_name}</code> (User {target_user_id}) - Unknown type")
                            skipped_files += 1
                        time.sleep(0.7) # Increased delay slightly
                    except Exception as e:
                        logger.error(f"Error queueing start for '{file_name}' (user {target_user_id}): {e}")
                        error_files_details.append(f"<code>{file_name}</code> (User {target_user_id}) - Start error")
                        skipped_files += 1
                else:
                    logger.warning(f"File '{file_name}' for user {target_user_id} not found at '{file_path}'. Skipping.")
                    error_files_details.append(f"<code>{file_name}</code> (User {target_user_id}) - File not found")
                    skipped_files += 1
            # else: logger.info(f"Script '{file_name}' for user {target_user_id} already running.")

    summary_msg = (f"「 {E('check')} 𝐑𝐮𝐧 𝐀𝐥𝐥 𝐒𝐜𝐫𝐢𝐩𝐭𝐬 — 𝐂𝐨𝐦𝐩𝐥𝐞𝐭𝐞 »\n\n"
                   f"┌◈────────────────────◈┐\n"
                   f"  {E('bolt')}  𝐒𝐭𝐚𝐫𝐭𝐞𝐝  →  {started_count} scripts\n"
                   f"  {E('eyes')}  𝐔𝐬𝐞𝐫𝐬    →  {attempted_users}\n"
                   f"└◈────────────────────◈┘\n")
    if skipped_files > 0:
        summary_msg += f"{E('warn')}  Skipped/Error  ➤  {skipped_files}\n"
        if error_files_details:
             summary_msg += f"{E('search')}  𝐃𝐞𝐭𝐚𝐢𝐥𝐬 (first 5):\n" + "\n".join([f"  ▸ {err}" for err in error_files_details[:5]])
             if len(error_files_details) > 5: summary_msg += "\n  ... and more (check logs)."

    reply_func(summary_msg, parse_mode='HTML')
    logger.info(f"Run all scripts finished. Admin: {admin_user_id}. Started: {started_count}. Skipped/Errors: {skipped_files}")


# --- Command Handlers & Text Handlers for ReplyKeyboard ---
@bot.message_handler(commands=['start', 'help'])
def command_send_welcome(message): _logic_send_welcome(message)

@bot.message_handler(commands=['status']) # Kept for direct command
def command_show_status(message): _logic_statistics(message) # Changed to call _logic_statistics


BUTTON_TEXT_TO_LOGIC = {
    "🔔 Updates Channel": _logic_updates_channel,
    "✨ Upload File": _logic_upload_file,
    "💎 My Files": _logic_check_files,
    "⚡ Bot Speed": _logic_bot_speed,
    f"{E('crown')} Contact Owner": _logic_contact_owner,
    "📊 Statistics": _logic_statistics,
    "💰 Subscriptions": _logic_subscriptions_panel,
    "📣 Broadcast": _logic_broadcast_init,
    f"{E('shield')} Lock Bot": _logic_toggle_lock_bot,
    "⚡ Run All Code": _logic_run_all_scripts,
    f"{E('crown')} Admin Panel": _logic_admin_panel,
}

@bot.message_handler(func=lambda message: message.text in BUTTON_TEXT_TO_LOGIC)
def handle_button_text(message):
    logic_func = BUTTON_TEXT_TO_LOGIC.get(message.text)
    if logic_func: logic_func(message)
    else: logger.warning(f"Button text '{message.text}' matched but no logic func.")

@bot.message_handler(commands=['updateschannel'])
def command_updates_channel(message): _logic_updates_channel(message)
@bot.message_handler(commands=['uploadfile'])
def command_upload_file(message): _logic_upload_file(message)
@bot.message_handler(commands=['checkfiles'])
def command_check_files(message): _logic_check_files(message)
@bot.message_handler(commands=['botspeed'])
def command_bot_speed(message): _logic_bot_speed(message)
@bot.message_handler(commands=['contactowner'])
def command_contact_owner(message): _logic_contact_owner(message)
@bot.message_handler(commands=['subscriptions'])
def command_subscriptions(message): _logic_subscriptions_panel(message)
@bot.message_handler(commands=['statistics']) # Alias for /status
def command_statistics(message): _logic_statistics(message)
@bot.message_handler(commands=['broadcast'])
def command_broadcast(message): _logic_broadcast_init(message)
@bot.message_handler(commands=['lockbot']) 
def command_lock_bot(message): _logic_toggle_lock_bot(message)
# @bot.message_handler(commands=['freemode']) # Removed
# def command_free_mode(message): _logic_toggle_free_mode(message)
@bot.message_handler(commands=['adminpanel'])
def command_admin_panel(message): _logic_admin_panel(message)
@bot.message_handler(commands=['runningallcode']) # Added
def command_run_all_code(message): _logic_run_all_scripts(message)


@bot.message_handler(commands=['ping'])
def ping(message):
    start_ping_time = time.time() 
    msg = bot.reply_to(message, "Pong!")
    latency = round((time.time() - start_ping_time) * 1000, 2)
    bot.edit_message_text(f"Pong! Latency: {latency} ms", message.chat.id, msg.message_id)


# --- Document (File) Handler ---
@bot.message_handler(content_types=['document'])
def handle_file_upload_doc(message): # Renamed
    user_id = message.from_user.id
    chat_id = message.chat.id # Used for replies, script context uses user_id
    doc = message.document
    logger.info(f"Doc from {user_id}: {doc.file_name} ({doc.mime_type}), Size: {doc.file_size}")

    if bot_locked and user_id not in admin_ids:
        bot.reply_to(message, f"{E('warn')} Bot locked, cannot accept files.")
        return

    # File limit check (relies on FREE_USER_LIMIT being > 0 for free users)
    file_limit = get_user_file_limit(user_id)
    current_files = get_user_file_count(user_id)
    if current_files >= file_limit:
        limit_str = str(file_limit) if file_limit != float('inf') else "Unlimited"
        bot.reply_to(message, f"{E('warn')} File limit ({current_files}/{limit_str}) reached. Delete files via /checkfiles.")
        return

    file_name = doc.file_name
    if not file_name: bot.reply_to(message, f"{E('warn')} No file name. Ensure file has a name."); return
    file_ext = os.path.splitext(file_name)[1].lower()
    if file_ext not in ['.py', '.js', '.zip']:
        bot.reply_to(message, f"{E('warn')} Unsupported type! Only <code>.py</code>, <code>.js</code>, <code>.zip</code> allowed.")
        return
    max_file_size = 20 * 1024 * 1024 # 20 MB
    if doc.file_size > max_file_size:
        bot.reply_to(message, f"{E('warn')} File too large (Max: {max_file_size // 1024 // 1024} MB)."); return

    try:
        try:
            bot.forward_message(OWNER_ID, chat_id, message.message_id)
            bot.send_message(OWNER_ID, f"{E('bell')} File <code>{file_name}</code> from {message.from_user.first_name} (<code>{user_id}</code>)", parse_mode='HTML')
        except Exception as e: logger.error(f"Failed to forward uploaded file to OWNER_ID {OWNER_ID}: {e}")

        # ── Step 1: Received ──────────────────────────────────────
        fsize_kb = round(doc.file_size / 1024, 1)
        status_msg = bot.reply_to(message,
            f"{E('bell')} <b>File Received</b>\n\n"
            f"┌◈────────────────────◈┐\n"
            f"│  {E('pin')}  <code>{file_name}</code>\n"
            f"│  {E('brain')}  {fsize_kb} KB  •  {file_ext.upper()[1:]}\n"
            f"└◈────────────────────◈┘\n\n"
            f"{E('eyes')}  Step 1/4 — Downloading from Telegram...\n"
            f"▓░░░░░░░░░  10%",
            parse_mode='HTML')

        # ── Step 2: Download ──────────────────────────────────────
        file_info_tg_doc = bot.get_file(doc.file_id)
        downloaded_file_content = bot.download_file(file_info_tg_doc.file_path)
        bot.edit_message_text(
            f"{E('bell')} <b>File Received</b>\n\n"
            f"┌◈────────────────────◈┐\n"
            f"│  {E('pin')}  <code>{file_name}</code>\n"
            f"│  {E('brain')}  {fsize_kb} KB  •  {file_ext.upper()[1:]}\n"
            f"└◈────────────────────◈┘\n\n"
            f"{E('check')}  𝐒𝐭𝐞𝐩 𝟏/𝟒 — 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝𝐞𝐝\n"
            f"{E('eyes')}  𝐒𝐭𝐞𝐩 𝟐/𝟒 — 𝐒𝐚𝐯𝐢𝐧𝐠 𝐭𝐨 𝐬𝐞𝐫𝐯𝐞𝐫...\n"
            f"▓▓▓░░░░░░░  30%",
            chat_id, status_msg.message_id, parse_mode='HTML')
        logger.info(f"Downloaded {file_name} for user {user_id}")
        user_folder = get_user_folder(user_id)

        # ── Step 3: Save / extract ────────────────────────────────
        bot.edit_message_text(
            f"{E('bell')} <b>File Received</b>\n\n"
            f"┌◈────────────────────◈┐\n"
            f"│  {E('pin')}  <code>{file_name}</code>\n"
            f"│  {E('brain')}  {fsize_kb} KB  •  {file_ext.upper()[1:]}\n"
            f"└◈────────────────────◈┘\n\n"
            f"{E('check')}  𝐒𝐭𝐞𝐩 𝟏/𝟒 — 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝𝐞𝐝\n"
            f"{E('check')}  𝐒𝐭𝐞𝐩 𝟐/𝟒 — 𝐒𝐚𝐯𝐞𝐝\n"
            f"{E('eyes')}  𝐒𝐭𝐞𝐩 𝟑/𝟒 — {'𝐄𝐱𝐭𝐫𝐚𝐜𝐭𝐢𝐧𝐠 𝐙𝐈𝐏...' if file_ext == '.zip' else '𝐂𝐡𝐞𝐜𝐤𝐢𝐧𝐠 𝐝𝐞𝐩𝐞𝐧𝐝𝐞𝐧𝐜𝐢𝐞𝐬...'}\n"
            f"▓▓▓▓▓▓░░░░  60%",
            chat_id, status_msg.message_id, parse_mode='HTML')

        if file_ext == '.zip':
            handle_zip_file(downloaded_file_content, file_name, message)
        else:
            file_path = os.path.join(user_folder, file_name)
            with open(file_path, 'wb') as f: f.write(downloaded_file_content)
            logger.info(f"Saved single file to {file_path}")

            # ── Step 4: Starting ──────────────────────────────────
            bot.edit_message_text(
                f"{E('bell')} <b>File Received</b>\n\n"
                f"┌◈────────────────────◈┐\n"
                f"│  {E('pin')}  <code>{file_name}</code>\n"
                f"│  {E('brain')}  {fsize_kb} KB  •  {file_ext.upper()[1:]}\n"
                f"└◈────────────────────◈┘\n\n"
                f"{E('check')}  𝐒𝐭𝐞𝐩 𝟏/𝟒 — 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝𝐞𝐝\n"
                f"{E('check')}  𝐒𝐭𝐞𝐩 𝟐/𝟒 — 𝐒𝐚𝐯𝐞𝐝\n"
                f"{E('check')}  𝐒𝐭𝐞𝐩 𝟑/𝟒 — 𝐃𝐞𝐩𝐬 𝐂𝐡𝐞𝐜𝐤𝐞𝐝\n"
                f"{E('eyes')}  𝐒𝐭𝐞𝐩 𝟒/𝟒 — 𝐋𝐚𝐮𝐧𝐜𝐡𝐢𝐧𝐠 𝐬𝐜𝐫𝐢𝐩𝐭...\n"
                f"▓▓▓▓▓▓▓▓░░  80%",
                chat_id, status_msg.message_id, parse_mode='HTML')

            if file_ext == '.js': handle_js_file(file_path, user_id, user_folder, file_name, message)
            elif file_ext == '.py': handle_py_file(file_path, user_id, user_folder, file_name, message)

    except telebot.apihelper.ApiTelegramException as e:
         logger.error(f"Telegram API Error handling file for {user_id}: {e}", exc_info=True)
         if "file is too big" in str(e).lower():
              bot.reply_to(message, f"{E('cross')} Telegram API Error: File too large to download (~20MB limit).")
         else: bot.reply_to(message, f"{E('cross')} Telegram API Error: {str(e)}. Try later.")
    except Exception as e:
        logger.error(f"❌ General error handling file for {user_id}: {e}", exc_info=True)
        bot.reply_to(message, f"{E('cross')} Unexpected error: {str(e)}")
# --- End Document Handler ---


# --- Callback Query Handlers (for Inline Buttons) ---
@bot.callback_query_handler(func=lambda call: True) 
def handle_callbacks(call):
    user_id = call.from_user.id
    data = call.data
    logger.info(f"Callback: User={user_id}, Data='{data}'")

    if bot_locked and user_id not in admin_ids and data not in ['back_to_main', 'speed', 'stats']: # Allow stats
        bot.answer_callback_query(call.id, "⚠️ Bot locked by admin.", show_alert=True)
        return
    try:
        if data == 'upload': upload_callback(call)
        elif data == 'verify_join': verify_join_callback(call)
        elif data == 'check_files': check_files_callback(call)
        elif data.startswith('file_'): file_control_callback(call)
        elif data.startswith('start_'): start_bot_callback(call)
        elif data.startswith('stop_'): stop_bot_callback(call)
        elif data.startswith('restart_'): restart_bot_callback(call)
        elif data.startswith('delete_'): delete_bot_callback(call)
        elif data.startswith('logs_'): logs_bot_callback(call)
        elif data == 'speed': speed_callback(call)
        elif data == 'back_to_main': back_to_main_callback(call)
        elif data.startswith('confirm_broadcast_'): handle_confirm_broadcast(call)
        elif data == 'cancel_broadcast': handle_cancel_broadcast(call)
        # --- Admin Callbacks ---
        elif data == 'subscription': admin_required_callback(call, subscription_management_callback)
        elif data == 'stats': stats_callback(call) # No admin check here, handled in func
        elif data == 'lock_bot': admin_required_callback(call, lock_bot_callback)
        elif data == 'unlock_bot': admin_required_callback(call, unlock_bot_callback)
        # elif data == 'free_mode': admin_required_callback(call, toggle_free_mode_callback) # Removed
        elif data == 'run_all_scripts': admin_required_callback(call, run_all_scripts_callback) # Added
        elif data == 'broadcast': admin_required_callback(call, broadcast_init_callback) 
        elif data == 'admin_panel': admin_required_callback(call, admin_panel_callback)
        elif data == 'add_admin': owner_required_callback(call, add_admin_init_callback) 
        elif data == 'remove_admin': owner_required_callback(call, remove_admin_init_callback) 
        elif data == 'list_admins': admin_required_callback(call, list_admins_callback)
        elif data == 'add_subscription': admin_required_callback(call, add_subscription_init_callback) 
        elif data == 'remove_subscription': admin_required_callback(call, remove_subscription_init_callback) 
        elif data == 'check_subscription': admin_required_callback(call, check_subscription_init_callback) 
        else:
            bot.answer_callback_query(call.id, "Unknown action.")
            logger.warning(f"Unhandled callback data: {data} from user {user_id}")
    except Exception as e:
        logger.error(f"Error handling callback '{data}' for {user_id}: {e}", exc_info=True)
        try: bot.answer_callback_query(call.id, "Error processing request.", show_alert=True)
        except Exception as e_ans: logger.error(f"Failed to answer callback after error: {e_ans}")

def admin_required_callback(call, func_to_run):
    if call.from_user.id not in admin_ids:
        bot.answer_callback_query(call.id, "⚠️ Admin permissions required.", show_alert=True)
        return
    func_to_run(call) 

def owner_required_callback(call, func_to_run):
    if call.from_user.id != OWNER_ID:
        bot.answer_callback_query(call.id, "⚠️ Owner permissions required.", show_alert=True)
        return
    func_to_run(call)

def verify_join_callback(call):
    """Called when user taps 'I Have Joined — Verify' button."""
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    if check_force_join(user_id):
        bot.answer_callback_query(call.id, "Verified! Welcome!", show_alert=True)
        try: bot.delete_message(chat_id, call.message.message_id)
        except Exception: pass
        # Trigger the welcome flow
        _logic_send_welcome(call.message)
    else:
        bot.answer_callback_query(
            call.id,
            f"{E('cross')} You have not joined yet!\nPlease join the channel first, then tap Verify again.",
            show_alert=True
        )

def upload_callback(call):
    user_id = call.from_user.id
    # --- Force Join Check ---
    if not check_force_join(user_id):
        bot.answer_callback_query(call.id)
        send_force_join_message(call.message.chat.id)
        return
    # --- End Force Join Check ---
    # Removed free_mode check
    file_limit = get_user_file_limit(user_id)
    current_files = get_user_file_count(user_id)
    if current_files >= file_limit:
        limit_str = str(file_limit) if file_limit != float('inf') else "Unlimited"
        bot.answer_callback_query(call.id, f"⚠️ File limit ({current_files}/{limit_str}) reached.", show_alert=True)
        return
    bot.answer_callback_query(call.id) 
    bot.send_message(call.message.chat.id, f"{E('sparklef')} <b>Upload Your Script</b>\n\n{E('pin')}  Send your .py Python, .js JS, or .zip ZIP file.", parse_mode='HTML')

def check_files_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    user_files_list = user_files.get(user_id, [])
    now_str = datetime.now().strftime("%H:%M:%S")
    if not user_files_list:
        bot.answer_callback_query(call.id, "⚠️ No files uploaded.", show_alert=True)
        try:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(f'{PE("heart")} Back to Main', callback_data='back_to_main'))
            bot.edit_message_text(
                "「 💎 𝐌𝐲 𝐅𝐢𝐥𝐞𝐬 »\n\n┌◈────────────────────◈┐\n  📂  𝐍𝐨 𝐟𝐢𝐥𝐞𝐬 𝐮𝐩𝐥𝐨𝐚𝐝𝐞𝐝 𝐲𝐞𝐭.\n└◈────────────────────◈┘\n\n⬡  𝐔𝐩𝐥𝐨𝐚𝐝 𝐚 <code>.py</code> · <code>.js</code> · <code>.zip</code> 𝐭𝐨 𝐠𝐞𝐭 𝐬𝐭𝐚𝐫𝐭𝐞𝐝!",
                chat_id, call.message.message_id, reply_markup=markup, parse_mode='HTML')
        except Exception as e: logger.error(f"Error editing msg for empty file list: {e}")
        return

    bot.answer_callback_query(call.id)
    running_count  = sum(1 for fn, _ in user_files_list if is_bot_running(user_id, fn))
    stopped_count  = len(user_files_list) - running_count
    header = (
        f"{E('gemf')} <b>My Files</b>  {E('calendar')} <code>{now_str}</code>\n\n"
        f"  {E('green')} Running: <code>{running_count}</code>   {E('red')} Stopped: <code>{stopped_count}</code>\n\n"
        f"⬡  𝐓𝐚𝐩 𝐚 𝐟𝐢𝐥𝐞 𝐭𝐨 𝐬𝐞𝐞 𝐝𝐞𝐭𝐚𝐢𝐥𝐬 & 𝐜𝐨𝐧𝐭𝐫𝐨𝐥𝐬:"
    )
    markup = types.InlineKeyboardMarkup(row_width=1)
    for file_name, file_type in sorted(user_files_list):
        is_running = is_bot_running(user_id, file_name)
        if is_running:
            script_key = f"{user_id}_{file_name}"
            info = bot_scripts.get(script_key, {})
            uptime_str = _format_uptime(info.get('start_time', datetime.now())) if info else ""
            btn_text = f"{PE('green')} {file_name} ({file_type}) ⏱{uptime_str}"
        else:
            btn_text = f"{PE('red')} {file_name} ({file_type})"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f'file_{user_id}_{file_name}'))
    markup.add(types.InlineKeyboardButton(f'{PE("refresh")} Refresh', callback_data='check_files'))
    markup.add(types.InlineKeyboardButton(f'{PE("heart")} Back to Main', callback_data='back_to_main'))
    try:
        bot.edit_message_text(header, chat_id, call.message.message_id,
                              reply_markup=markup, parse_mode='HTML')
    except telebot.apihelper.ApiTelegramException as e:
        if "message is not modified" in str(e): logger.warning("Msg not modified (files).")
        else: logger.error(f"Error editing msg for file list: {e}")
    except Exception as e: logger.error(f"Unexpected error editing msg for file list: {e}", exc_info=True)

def _build_file_status_card(script_owner_id, file_name, file_type):
    """Build a rich real-time status card string for a single hosted file."""
    is_running = is_bot_running(script_owner_id, file_name)
    status_icon = f"{E('green')} Running" if is_running else f"{E('red')} Stopped"
    now_str = datetime.now().strftime("%d %b %Y  %H:%M:%S")

    # File size on disk
    user_folder = get_user_folder(script_owner_id)
    file_path = os.path.join(user_folder, file_name)
    try:
        fsize = os.path.getsize(file_path)
        fsize_str = f"{fsize / 1024:.1f} KB" if fsize < 1_048_576 else f"{fsize / 1_048_576:.2f} MB"
    except Exception:
        fsize_str = "N/A"

    card = (
        f"{E('bolt')} <b>File Status</b>\n"
        f"{E('calendar')}  <code>{now_str}</code>\n\n"
        f"┌◈────────────────────◈┐\n"
        f"│  {E('pin')}  𝐍𝐚𝐦𝐞     ➤  <code>{file_name}</code>\n"
        f"│  {E('bolt')}  𝐓𝐲𝐩𝐞     ➤  <code>{file_type.upper()}</code>\n"
        f"│  {E('brain')}  𝐒𝐢𝐳𝐞     ➤  <code>{fsize_str}</code>\n"
        f"│  {E('green')}  𝐒𝐭𝐚𝐭𝐮𝐬   ➤  {status_icon}\n"
    )

    if is_running:
        script_key = f"{script_owner_id}_{file_name}"
        info = bot_scripts.get(script_key, {})
        uptime_str = _format_uptime(info.get('start_time', datetime.now())) if info else "N/A"
        card += f"│  {E('fire')}  𝐔𝐩𝐭𝐢𝐦𝐞   ➤  <code>{uptime_str}</code>\n"
        # Memory usage of the process
        try:
            proc = psutil.Process(info['process'].pid)
            mem_mb = round(proc.memory_info().rss / (1024**2), 2)
            cpu_p  = proc.cpu_percent(interval=0.2)
            card += f"│  {E('brain')}  Memory  ➤  <code>{mem_mb} MB</code>\n"
            card += f"│  {E('bolt')}  CPU     ➤  <code>{cpu_p}%</code>\n"
            card += f"│  {E('eyes')}  PID     ➤  <code>{proc.pid}</code>\n"
        except Exception:
            pass
    card += f"└◈────────────────────◈┘\n"
    return card, is_running

def file_control_callback(call):
    try:
        _, script_owner_id_str, file_name = call.data.split('_', 2)
        script_owner_id = int(script_owner_id_str)
        requesting_user_id = call.from_user.id

        if not (requesting_user_id == script_owner_id or requesting_user_id in admin_ids):
            logger.warning(f"User {requesting_user_id} tried to access file '{file_name}' of user {script_owner_id} without permission.")
            bot.answer_callback_query(call.id, "⚠️ You can only manage your own files.", show_alert=True)
            check_files_callback(call)
            return

        user_files_list = user_files.get(script_owner_id, [])
        if not any(f[0] == file_name for f in user_files_list):
            bot.answer_callback_query(call.id, "⚠️ File not found.", show_alert=True)
            check_files_callback(call)
            return

        bot.answer_callback_query(call.id)
        file_type = next((f[1] for f in user_files_list if f[0] == file_name), '?')
        card, is_running = _build_file_status_card(script_owner_id, file_name, file_type)

        # Add a "🔄 Refresh" button to re-open this same card
        ctrl_markup = create_control_buttons(script_owner_id, file_name, is_running)
        ctrl_markup.add(types.InlineKeyboardButton(
f'{PE("refresh")} Refresh Status', callback_data=f'file_{script_owner_id}_{file_name}'))
        try:
            bot.edit_message_text(card, call.message.chat.id, call.message.message_id,
                                  reply_markup=ctrl_markup, parse_mode='HTML')
        except telebot.apihelper.ApiTelegramException as e:
            if "message is not modified" in str(e):
                logger.warning(f"Msg not modified (controls for {file_name})")
            else: raise
    except (ValueError, IndexError) as ve:
        logger.error(f"Error parsing file control callback: {ve}. Data: '{call.data}'")
        bot.answer_callback_query(call.id, "Error: Invalid action data.", show_alert=True)
    except Exception as e:
        logger.error(f"Error in file_control_callback for data '{call.data}': {e}", exc_info=True)
        bot.answer_callback_query(call.id, "An error occurred.", show_alert=True)

def start_bot_callback(call):
    try:
        _, script_owner_id_str, file_name = call.data.split('_', 2)
        script_owner_id = int(script_owner_id_str)
        requesting_user_id = call.from_user.id
        chat_id_for_reply = call.message.chat.id # Where the admin/user gets the reply

        logger.info(f"Start request: Requester={requesting_user_id}, Owner={script_owner_id}, File='{file_name}'")

        if not (requesting_user_id == script_owner_id or requesting_user_id in admin_ids):
            bot.answer_callback_query(call.id, "⚠️ Permission denied to start this script.", show_alert=True); return

        user_files_list = user_files.get(script_owner_id, [])
        file_info = next((f for f in user_files_list if f[0] == file_name), None)
        if not file_info:
            bot.answer_callback_query(call.id, "⚠️ File not found.", show_alert=True); check_files_callback(call); return

        file_type = file_info[1]
        user_folder = get_user_folder(script_owner_id)
        file_path = os.path.join(user_folder, file_name)

        if not os.path.exists(file_path):
            bot.answer_callback_query(call.id, f"⚠️ Error: File <code>{file_name}</code> missing! Re-upload.", show_alert=True)
            remove_user_file_db(script_owner_id, file_name); check_files_callback(call); return

        if is_bot_running(script_owner_id, file_name):
            bot.answer_callback_query(call.id, f"⚠️ Script '{file_name}' already running.", show_alert=True)
            try: bot.edit_message_reply_markup(chat_id_for_reply, call.message.message_id, reply_markup=create_control_buttons(script_owner_id, file_name, True))
            except Exception as e: logger.error(f"Error updating buttons (already running): {e}")
            return

        bot.answer_callback_query(call.id, f"Starting {file_name} for user {script_owner_id}...")

        # Pass call.message as message_obj_for_reply so feedback goes to the person who clicked
        if file_type == 'py':
            threading.Thread(target=run_script, args=(file_path, script_owner_id, user_folder, file_name, call.message)).start()
        elif file_type == 'js':
            threading.Thread(target=run_js_script, args=(file_path, script_owner_id, user_folder, file_name, call.message)).start()
        else:
             bot.send_message(chat_id_for_reply, f"{E('cross')} Error: Unknown file type '{file_type}' for '{file_name}'."); return 

        time.sleep(1.5) # Give script time to actually start or fail early
        is_now_running = is_bot_running(script_owner_id, file_name)
        card, _ = _build_file_status_card(script_owner_id, file_name, file_type)
        ctrl_markup = create_control_buttons(script_owner_id, file_name, is_now_running)
        ctrl_markup.add(types.InlineKeyboardButton(f'{PE("refresh")} Refresh Status', callback_data=f'file_{script_owner_id}_{file_name}'))
        try:
            bot.edit_message_text(card, chat_id_for_reply, call.message.message_id,
                                  reply_markup=ctrl_markup, parse_mode='HTML')
        except telebot.apihelper.ApiTelegramException as e:
             if "message is not modified" in str(e): logger.warning(f"Msg not modified after starting {file_name}")
             else: raise
    except (ValueError, IndexError) as e:
        logger.error(f"Error parsing start callback '{call.data}': {e}")
        bot.answer_callback_query(call.id, "Error: Invalid start command.", show_alert=True)
    except Exception as e:
        logger.error(f"Error in start_bot_callback for '{call.data}': {e}", exc_info=True)
        bot.answer_callback_query(call.id, "Error starting script.", show_alert=True)
        try: # Attempt to reset buttons to 'stopped' state on error
            _, script_owner_id_err_str, file_name_err = call.data.split('_', 2)
            script_owner_id_err = int(script_owner_id_err_str)
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=create_control_buttons(script_owner_id_err, file_name_err, False))
        except Exception as e_btn: logger.error(f"Failed to update buttons after start error: {e_btn}")

def stop_bot_callback(call):
    try:
        _, script_owner_id_str, file_name = call.data.split('_', 2)
        script_owner_id = int(script_owner_id_str)
        requesting_user_id = call.from_user.id
        chat_id_for_reply = call.message.chat.id

        logger.info(f"Stop request: Requester={requesting_user_id}, Owner={script_owner_id}, File='{file_name}'")
        if not (requesting_user_id == script_owner_id or requesting_user_id in admin_ids):
            bot.answer_callback_query(call.id, "⚠️ Permission denied.", show_alert=True); return

        user_files_list = user_files.get(script_owner_id, [])
        file_info = next((f for f in user_files_list if f[0] == file_name), None)
        if not file_info:
            bot.answer_callback_query(call.id, "⚠️ File not found.", show_alert=True); check_files_callback(call); return

        file_type = file_info[1] 
        script_key = f"{script_owner_id}_{file_name}"

        if not is_bot_running(script_owner_id, file_name): 
            bot.answer_callback_query(call.id, f"⚠️ Script '{file_name}' already stopped.", show_alert=True)
            try:
                card, _ = _build_file_status_card(script_owner_id, file_name, file_type)
                ctrl_markup = create_control_buttons(script_owner_id, file_name, False)
                ctrl_markup.add(types.InlineKeyboardButton(f'{PE("refresh")} Refresh Status', callback_data=f'file_{script_owner_id}_{file_name}'))
                bot.edit_message_text(card, chat_id_for_reply, call.message.message_id,
                                      reply_markup=ctrl_markup, parse_mode='HTML')
            except Exception as e: logger.error(f"Error updating buttons (already stopped): {e}")
            return

        bot.answer_callback_query(call.id, f"Stopping {file_name} for user {script_owner_id}...")
        process_info = bot_scripts.get(script_key)
        if process_info:
            kill_process_tree(process_info)
            if script_key in bot_scripts: del bot_scripts[script_key]; logger.info(f"Removed {script_key} from running after stop.")
        else: logger.warning(f"Script {script_key} running by psutil but not in bot_scripts dict.")

        try:
            card, _ = _build_file_status_card(script_owner_id, file_name, file_type)
            ctrl_markup = create_control_buttons(script_owner_id, file_name, False)
            ctrl_markup.add(types.InlineKeyboardButton(f'{PE("refresh")} Refresh Status', callback_data=f'file_{script_owner_id}_{file_name}'))
            bot.edit_message_text(card, chat_id_for_reply, call.message.message_id,
                                  reply_markup=ctrl_markup, parse_mode='HTML')
        except telebot.apihelper.ApiTelegramException as e:
             if "message is not modified" in str(e): logger.warning(f"Msg not modified after stopping {file_name}")
             else: raise
    except (ValueError, IndexError) as e:
        logger.error(f"Error parsing stop callback '{call.data}': {e}")
        bot.answer_callback_query(call.id, "Error: Invalid stop command.", show_alert=True)
    except Exception as e:
        logger.error(f"Error in stop_bot_callback for '{call.data}': {e}", exc_info=True)
        bot.answer_callback_query(call.id, "Error stopping script.", show_alert=True)

def restart_bot_callback(call):
    try:
        _, script_owner_id_str, file_name = call.data.split('_', 2)
        script_owner_id = int(script_owner_id_str)
        requesting_user_id = call.from_user.id
        chat_id_for_reply = call.message.chat.id

        logger.info(f"Restart: Requester={requesting_user_id}, Owner={script_owner_id}, File='{file_name}'")
        if not (requesting_user_id == script_owner_id or requesting_user_id in admin_ids):
            bot.answer_callback_query(call.id, "⚠️ Permission denied.", show_alert=True); return

        user_files_list = user_files.get(script_owner_id, [])
        file_info = next((f for f in user_files_list if f[0] == file_name), None)
        if not file_info:
            bot.answer_callback_query(call.id, "⚠️ File not found.", show_alert=True); check_files_callback(call); return

        file_type = file_info[1]; user_folder = get_user_folder(script_owner_id)
        file_path = os.path.join(user_folder, file_name); script_key = f"{script_owner_id}_{file_name}"

        if not os.path.exists(file_path):
            bot.answer_callback_query(call.id, f"⚠️ Error: File <code>{file_name}</code> missing! Re-upload.", show_alert=True)
            remove_user_file_db(script_owner_id, file_name)
            if script_key in bot_scripts: del bot_scripts[script_key]
            check_files_callback(call); return

        bot.answer_callback_query(call.id, f"Restarting {file_name} for user {script_owner_id}...")
        if is_bot_running(script_owner_id, file_name):
            logger.info(f"Restart: Stopping existing {script_key}...")
            process_info = bot_scripts.get(script_key)
            if process_info: kill_process_tree(process_info)
            if script_key in bot_scripts: del bot_scripts[script_key]
            time.sleep(1.5) 

        logger.info(f"Restart: Starting script {script_key}...")
        if file_type == 'py':
            threading.Thread(target=run_script, args=(file_path, script_owner_id, user_folder, file_name, call.message)).start()
        elif file_type == 'js':
            threading.Thread(target=run_js_script, args=(file_path, script_owner_id, user_folder, file_name, call.message)).start()
        else:
             bot.send_message(chat_id_for_reply, f"{E('cross')} Unknown type '{file_type}' for '{file_name}'."); return

        time.sleep(1.5)
        is_now_running = is_bot_running(script_owner_id, file_name)
        card, _ = _build_file_status_card(script_owner_id, file_name, file_type)
        ctrl_markup = create_control_buttons(script_owner_id, file_name, is_now_running)
        ctrl_markup.add(types.InlineKeyboardButton(f'{PE("refresh")} Refresh Status', callback_data=f'file_{script_owner_id}_{file_name}'))
        try:
            bot.edit_message_text(card, chat_id_for_reply, call.message.message_id,
                                  reply_markup=ctrl_markup, parse_mode='HTML')
        except telebot.apihelper.ApiTelegramException as e:
             if "message is not modified" in str(e): logger.warning(f"Msg not modified (restart {file_name})")
             else: raise
    except (ValueError, IndexError) as e:
        logger.error(f"Error parsing restart callback '{call.data}': {e}")
        bot.answer_callback_query(call.id, "Error: Invalid restart command.", show_alert=True)
    except Exception as e:
        logger.error(f"Error in restart_bot_callback for '{call.data}': {e}", exc_info=True)
        bot.answer_callback_query(call.id, "Error restarting.", show_alert=True)
        try:
            _, script_owner_id_err_str, file_name_err = call.data.split('_', 2)
            script_owner_id_err = int(script_owner_id_err_str)
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=create_control_buttons(script_owner_id_err, file_name_err, False))
        except Exception as e_btn: logger.error(f"Failed to update buttons after restart error: {e_btn}")


def delete_bot_callback(call):
    try:
        _, script_owner_id_str, file_name = call.data.split('_', 2)
        script_owner_id = int(script_owner_id_str)
        requesting_user_id = call.from_user.id
        chat_id_for_reply = call.message.chat.id

        logger.info(f"Delete: Requester={requesting_user_id}, Owner={script_owner_id}, File='{file_name}'")
        if not (requesting_user_id == script_owner_id or requesting_user_id in admin_ids):
            bot.answer_callback_query(call.id, "⚠️ Permission denied.", show_alert=True); return

        user_files_list = user_files.get(script_owner_id, [])
        if not any(f[0] == file_name for f in user_files_list):
            bot.answer_callback_query(call.id, "⚠️ File not found.", show_alert=True); check_files_callback(call); return

        bot.answer_callback_query(call.id, f"Deleting {file_name} for user {script_owner_id}...")
        script_key = f"{script_owner_id}_{file_name}"
        if is_bot_running(script_owner_id, file_name):
            logger.info(f"Delete: Stopping {script_key}...")
            process_info = bot_scripts.get(script_key)
            if process_info: kill_process_tree(process_info)
            if script_key in bot_scripts: del bot_scripts[script_key]
            time.sleep(0.5) 

        user_folder = get_user_folder(script_owner_id)
        file_path = os.path.join(user_folder, file_name)
        log_path = os.path.join(user_folder, f"{os.path.splitext(file_name)[0]}.log")
        deleted_disk = []
        if os.path.exists(file_path):
            try: os.remove(file_path); deleted_disk.append(file_name); logger.info(f"Deleted file: {file_path}")
            except OSError as e: logger.error(f"Error deleting {file_path}: {e}")
        if os.path.exists(log_path):
            try: os.remove(log_path); deleted_disk.append(os.path.basename(log_path)); logger.info(f"Deleted log: {log_path}")
            except OSError as e: logger.error(f"Error deleting log {log_path}: {e}")

        remove_user_file_db(script_owner_id, file_name)
        back_markup = types.InlineKeyboardMarkup()
        back_markup.add(types.InlineKeyboardButton(f'{PE("gem")} My Files', callback_data='check_files'),
                        types.InlineKeyboardButton(f'{PE("heart")} Main Menu', callback_data='back_to_main'))
        try:
            bot.edit_message_text(
                f"{E('trash')} <b>File Deleted</b>\n\n"
                f"┌◈────────────────────◈┐\n"
                f"│  {E('pin')}  <code>{file_name}</code>\n"
                f"│  {E('eyes')}  User <code>{script_owner_id}</code>\n"
                f"│  {E('red')}  Status → Removed\n"
                f"└◈────────────────────◈┘\n\n"
                f"{E('check')}  Script stopped & all files cleaned up.",
                chat_id_for_reply, call.message.message_id,
                reply_markup=back_markup, parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Error editing msg after delete: {e}")
            bot.send_message(chat_id_for_reply, f"🗑️ <code>{file_name}</code> deleted.", reply_markup=back_markup, parse_mode='HTML')
    except (ValueError, IndexError) as e:
        logger.error(f"Error parsing delete callback '{call.data}': {e}")
        bot.answer_callback_query(call.id, "Error: Invalid delete command.", show_alert=True)
    except Exception as e:
        logger.error(f"Error in delete_bot_callback for '{call.data}': {e}", exc_info=True)
        bot.answer_callback_query(call.id, "Error deleting.", show_alert=True)

def logs_bot_callback(call):
    try:
        _, script_owner_id_str, file_name = call.data.split('_', 2)
        script_owner_id = int(script_owner_id_str)
        requesting_user_id = call.from_user.id
        chat_id_for_reply = call.message.chat.id

        logger.info(f"Logs: Requester={requesting_user_id}, Owner={script_owner_id}, File='{file_name}'")
        if not (requesting_user_id == script_owner_id or requesting_user_id in admin_ids):
            bot.answer_callback_query(call.id, "⚠️ Permission denied.", show_alert=True); return

        user_files_list = user_files.get(script_owner_id, [])
        if not any(f[0] == file_name for f in user_files_list):
            bot.answer_callback_query(call.id, "⚠️ File not found.", show_alert=True); check_files_callback(call); return

        user_folder = get_user_folder(script_owner_id)
        log_path = os.path.join(user_folder, f"{os.path.splitext(file_name)[0]}.log")
        if not os.path.exists(log_path):
            bot.answer_callback_query(call.id, f"⚠️ No logs for '{file_name}'.", show_alert=True); return

        bot.answer_callback_query(call.id) 
        try:
            log_content = ""; file_size = os.path.getsize(log_path)
            max_log_kb = 100; max_tg_msg = 4096
            if file_size == 0: log_content = "(Log empty)"
            elif file_size > max_log_kb * 1024:
                 with open(log_path, 'rb') as f: f.seek(-max_log_kb * 1024, os.SEEK_END); log_bytes = f.read()
                 log_content = log_bytes.decode('utf-8', errors='ignore')
                 log_content = f"(Last {max_log_kb} KB)\n...\n" + log_content
            else:
                 with open(log_path, 'r', encoding='utf-8', errors='ignore') as f: log_content = f.read()

            if len(log_content) > max_tg_msg:
                log_content = log_content[-max_tg_msg:]
                first_nl = log_content.find('\n')
                if first_nl != -1: log_content = "...\n" + log_content[first_nl+1:]
                else: log_content = "...\n" + log_content 
            if not log_content.strip(): log_content = "(No visible content)"

            log_markup = types.InlineKeyboardMarkup()
            log_markup.add(types.InlineKeyboardButton(
                f'{PE("bolt")} Back to File', callback_data=f'file_{script_owner_id}_{file_name}'))
            log_markup.add(types.InlineKeyboardButton(
                f'{PE("gem")} My Files', callback_data='check_files'),
                types.InlineKeyboardButton(f'{PE("heart")} Main Menu', callback_data='back_to_main'))
            bot.send_message(chat_id_for_reply,
                f"{E('search')} <b>Logs — <code>{file_name}</code></b>\n<code>\n{log_content}\n</code>",
                parse_mode='HTML', reply_markup=log_markup)
        except Exception as e:
            logger.error(f"Error reading/sending log {log_path}: {e}", exc_info=True)
            bot.send_message(chat_id_for_reply, f"{E('cross')} Error reading log for <code>{file_name}</code>.")
    except (ValueError, IndexError) as e:
        logger.error(f"Error parsing logs callback '{call.data}': {e}")
        bot.answer_callback_query(call.id, "Error: Invalid logs command.", show_alert=True)
    except Exception as e:
        logger.error(f"Error in logs_bot_callback for '{call.data}': {e}", exc_info=True)
        bot.answer_callback_query(call.id, "Error fetching logs.", show_alert=True)

def speed_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    start_cb_ping_time = time.time()
    try:
        bot.edit_message_text("⬡  𝐓𝐞𝐬𝐭𝐢𝐧𝐠 𝐛𝐨𝐭 𝐬𝐩𝐞𝐞𝐝...", chat_id, call.message.message_id, parse_mode='HTML')
        bot.send_chat_action(chat_id, 'typing')
        response_time = round((time.time() - start_cb_ping_time) * 1000, 2)
        status = f"{E('check')} Unlocked" if not bot_locked else f"{E('shield')} Locked"
        if user_id == OWNER_ID: user_level = f"{E('crown')} Owner"
        elif user_id in admin_ids: user_level = f"{E('shield')} Admin"
        elif user_id in user_subscriptions and user_subscriptions[user_id].get('expiry', datetime.min) > datetime.now(): user_level = "⭐ Premium"
        else: user_level = "🆓 Free User"
        ping_quality = f"{E('green')} Excellent" if response_time < 300 else (f"{E('starf')} Good" if response_time < 800 else f"{E('red')} Slow")
        bot_uptime = _format_uptime(BOT_START_TIME)
        now_str = datetime.now().strftime("%d %b %Y  %H:%M:%S")
        speed_msg = (
            f"{E('bolt')} <b>Bot Speed & Status</b>\n"
            f"{E('calendar')}  <code>{now_str}</code>\n\n"
            f"┌◈────────────────────◈┐\n"
            f"│  {E('fire')}  𝐏𝐢𝐧𝐠    ➤  <code>{response_time} ms</code>\n"
            f"│  {E('chart')}  𝐐𝐮𝐚𝐥𝐢𝐭𝐲 ➤  {ping_quality}\n"
            f"│  {E('green')}  𝐒𝐭𝐚𝐭𝐮𝐬  ➤  {status}\n"
            f"│  {E('eyes')}  𝐋𝐞𝐯𝐞𝐥   ➤  {user_level}\n"
            f"│  {E('eyes')}  𝐔𝐩𝐭𝐢𝐦𝐞  ➤  <code>{bot_uptime}</code>\n"
            f"└◈────────────────────◈┘"
        )
        speed_markup = types.InlineKeyboardMarkup()
        speed_markup.add(types.InlineKeyboardButton(f'{PE("refresh")} Refresh', callback_data='speed'))
        speed_markup.add(types.InlineKeyboardButton(f'{PE("chart")} Statistics', callback_data='stats'),
                         types.InlineKeyboardButton(f'{PE("heart")} Main Menu', callback_data='back_to_main'))
        bot.answer_callback_query(call.id)
        bot.edit_message_text(speed_msg, chat_id, call.message.message_id,
                              reply_markup=speed_markup, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Error during speed test (cb): {e}", exc_info=True)
        bot.answer_callback_query(call.id, "Error in speed test.", show_alert=True)
        try: bot.edit_message_text(f"{E('heart')} <b>Main Menu</b>", chat_id, call.message.message_id,
                                   reply_markup=create_main_menu_inline(user_id), parse_mode='HTML')
        except Exception: pass

def back_to_main_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    file_limit = get_user_file_limit(user_id)
    current_files = get_user_file_count(user_id)
    limit_str = str(file_limit) if file_limit != float('inf') else "Unlimited"
    expiry_info = ""
    if user_id == OWNER_ID: user_status = f"{E('crown')} Owner"
    elif user_id in admin_ids: user_status = f"{E('shield')} Admin"
    elif user_id in user_subscriptions:
        expiry_date = user_subscriptions[user_id].get('expiry')
        if expiry_date and expiry_date > datetime.now():
            user_status = "⭐ Premium"; days_left = (expiry_date - datetime.now()).days
            expiry_info = f"\n{E('calendar')} Subscription expires in: {days_left} days"
        else: user_status = "🆓 Free User (Expired Sub)" # Will be cleaned up by welcome if not already
    else: user_status = "🆓 Free User"
    main_menu_text = (
        f"{E('boltf')} <b>HOSTING BOT</b> {E('bolt')}\n"
        f"{E('crownf')} Script Hosting & Manager {E('star')}\n\n"
        f"{E('wave')}  Welcome back, {call.from_user.first_name}!\n\n"
        f"┌◈────────────────────◈┐\n"
        f"  {E('eyes')} ID      →  <code>{user_id}</code>\n"
        f"  {E('star')} Status  →  {user_status}{expiry_info}\n"
        f"  {E('gem')} Files   →  <code>{current_files}</code> / <code>{limit_str}</code>\n"
        f"└◈────────────────────◈┘\n\n"
        f"{E('pinf')} Tap a button below to continue {E('pin')}"
    )
    try:
        bot.answer_callback_query(call.id)
        bot.edit_message_text(main_menu_text, chat_id, call.message.message_id,
                              reply_markup=create_main_menu_inline(user_id), parse_mode='HTML')
    except telebot.apihelper.ApiTelegramException as e:
         if "message is not modified" in str(e): logger.warning("Msg not modified (back_to_main).")
         else: logger.error(f"API error on back_to_main: {e}")
    except Exception as e: logger.error(f"Error handling back_to_main: {e}", exc_info=True)

# --- Admin Callback Implementations (for Inline Buttons) ---
def subscription_management_callback(call):
    bot.answer_callback_query(call.id)
    try:
        bot.edit_message_text(f"{E('moneyf')} <b>Subscription Management</b>\n\n{E('pin')}  Select an action below:",
                              call.message.chat.id, call.message.message_id, reply_markup=create_subscription_menu(), parse_mode='HTML')
    except Exception as e: logger.error(f"Error showing sub menu: {e}")

def stats_callback(call):
    bot.answer_callback_query(call.id, "Refreshing...")
    user_id = call.from_user.id
    now_str = datetime.now().strftime("%d %b %Y  %H:%M:%S")

    total_users     = len(active_users)
    total_files_all = sum(len(f) for f in user_files.values())
    my_files        = len(user_files.get(user_id, []))
    running_detail  = _get_running_scripts_detail()
    running_total   = len(running_detail)
    my_running      = sum(1 for r in running_detail if r['owner'] == user_id)
    bot_uptime      = _format_uptime(BOT_START_TIME)
    total_subs      = len([uid for uid, info in user_subscriptions.items()
                           if info.get('expiry', datetime.min) > datetime.now()])

    msg = (
        f"{E('chart')} <b>Real-Time Stats</b>\n"
        f"{E('calendar')}  <code>{now_str}</code>\n\n"
        f"┌◈──────────────────────◈┐\n"
        f"│  {E('eyes')}  𝐓𝐨𝐭𝐚𝐥 𝐔𝐬𝐞𝐫𝐬      ➤  <code>{total_users}</code>\n"
        f"│  {E('gem')}  Total Files      ➤  <code>{total_files_all}</code>\n"
        f"│  {E('green')}  𝐑𝐮𝐧𝐧𝐢𝐧𝐠 𝐒𝐜𝐫𝐢𝐩𝐭𝐬  ➤  <code>{running_total}</code>\n"
        f"│  {E('star')}  Premium Users   ➤  <code>{total_subs}</code>\n"
        f"│  {E('fire')}  𝐁𝐨𝐭 𝐔𝐩𝐭𝐢𝐦𝐞      ➤  <code>{bot_uptime}</code>\n"
        f"└◈──────────────────────◈┘\n\n"
        f"{E('crown')} Your Info:\n"
        f"  {E('pin')}  My Files       ➤  <code>{my_files}</code>\n"
        f"  {E('bolt')}  My Running    ➤  <code>{my_running}</code>\n"
    )

    my_scripts = [r for r in running_detail if r['owner'] == user_id]
    if my_scripts:
        msg += f"\n{E('sparkle')} My Running Files:\n"
        for r in my_scripts:
            msg += f"  {E('green')} <code>{r['file']}</code> ({r['type']} — ⏱ {r['uptime']}\n"

    if user_id in admin_ids:
        cpu, ram_used, ram_total, disk_used, disk_total = _get_system_stats()
        msg += (
            f"\n┌◈──── {E('crown')} Admin Dashboard ────◈┐\n"
            f"│  {E('shield')}  Bot Lock     ➤  {E('red') + ' Locked' if bot_locked else E('green') + ' Unlocked'}\n"
            f"│  {E('brain')}  CPU          ➤  <code>{cpu}%</code>\n"
            f"│  {E('bolt')}  RAM          ➤  <code>{ram_used} / {ram_total} GB</code>\n"
            f"│  {E('gem')}  Disk         ➤  <code>{disk_used} / {disk_total} GB</code>\n"
            f"│  {E('crown')}  Admins       ➤  <code>{len(admin_ids)}</code>\n"
            f"└◈──────────────────────────◈┘\n"
        )
        if running_detail:
            msg += f"\n{E('fire')} All Running Scripts:\n"
            for r in running_detail:
                msg += f"  {E('green')} <code>{r['file']}</code> ({r['type']} | {E('eyes')}<code>{r['owner']}</code> | ⏱<code>{r['uptime']}</code>\n"
        else:
            msg += f"\n{E('moon')} No scripts currently running.\n"

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f'{PE("refresh")} Refresh Stats', callback_data='stats'))
    markup.add(types.InlineKeyboardButton(f'{PE("heart")} Back to Main',  callback_data='back_to_main'))
    try:
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id,
                              reply_markup=markup, parse_mode='HTML')
    except telebot.apihelper.ApiTelegramException as e:
        if "message is not modified" not in str(e):
            logger.error(f"Error updating stats message: {e}")


def lock_bot_callback(call):
    global bot_locked; bot_locked = True
    logger.warning(f"Bot locked by Admin {call.from_user.id}")
    bot.answer_callback_query(call.id, "Bot locked.")
    try: bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=create_main_menu_inline(call.from_user.id))
    except Exception as e: logger.error(f"Error updating menu (lock): {e}")

def unlock_bot_callback(call):
    global bot_locked; bot_locked = False
    logger.warning(f"Bot unlocked by Admin {call.from_user.id}")
    bot.answer_callback_query(call.id, "Bot unlocked.")
    try: bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=create_main_menu_inline(call.from_user.id))
    except Exception as e: logger.error(f"Error updating menu (unlock): {e}")

# def toggle_free_mode_callback(call): # Removed
#     pass

def run_all_scripts_callback(call): # Added
    _logic_run_all_scripts(call) # Pass the call object


def broadcast_init_callback(call):
    bot.answer_callback_query(call.id)
    cancel_markup = types.InlineKeyboardMarkup()
    cancel_markup.add(types.InlineKeyboardButton(f'{PE("heart")} Back to Main Menu', callback_data='back_to_main'))
    msg = bot.send_message(call.message.chat.id,
        f"{E('announce')} <b>Broadcast Message</b>\n\n"
        "⬡  𝐒𝐞𝐧𝐝 𝐭𝐡𝐞 𝐦𝐞𝐬𝐬𝐚𝐠𝐞 𝐭𝐨 𝐛𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 𝐭𝐨 𝐚𝐥𝐥 𝐮𝐬𝐞𝐫𝐬.\n"
        "⬡  𝐒𝐞𝐧𝐝 /cancel 𝐭𝐨 𝐚𝐛𝐨𝐫𝐭.",
        reply_markup=cancel_markup)
    bot.register_next_step_handler(msg, process_broadcast_message)

def process_broadcast_message(message):
    user_id = message.from_user.id
    if user_id not in admin_ids: bot.reply_to(message, f"{E('warn')} Not authorized."); return
    if message.text and message.text.lower() == '/cancel': bot.reply_to(message, "𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 𝐜𝐚𝐧𝐜𝐞𝐥𝐥𝐞𝐝."); return

    broadcast_content = message.text # Can also handle photos, videos etc. if message.content_type is checked
    if not broadcast_content and not (message.photo or message.video or message.document or message.sticker or message.voice or message.audio): # If no text and no other media
         bot.reply_to(message, f"{E('warn')} Cannot broadcast empty message. Send text or media, or /cancel.")
         msg = bot.send_message(message.chat.id, "𝐒𝐞𝐧𝐝 𝐲𝐨𝐮𝐫 𝐛𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 𝐦𝐞𝐬𝐬𝐚𝐠𝐞, 𝐨𝐫 /cancel.")
         bot.register_next_step_handler(msg, process_broadcast_message)
         return

    target_count = len(active_users)
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton(f'{PE("check")} Confirm & Send', callback_data=f"confirm_broadcast_{message.message_id}"),
               types.InlineKeyboardButton(f'{PE("cross")} Cancel', callback_data="cancel_broadcast"))

    preview_text = broadcast_content[:1000].strip() if broadcast_content else "(Media message)"
    bot.reply_to(message, f"{E('warn')} Confirm Broadcast:\n\n``<code>\n{preview_text}\n</code>``\n" 
                          f"To *{target_count}* users. Sure?", reply_markup=markup, parse_mode='HTML')

def handle_confirm_broadcast(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    if user_id not in admin_ids: bot.answer_callback_query(call.id, "⚠️ Admin only.", show_alert=True); return
    try:
        original_message = call.message.reply_to_message
        if not original_message: raise ValueError("Could not retrieve original message.")

        # Check content type and get content
        broadcast_text = None
        broadcast_photo_id = None
        broadcast_video_id = None
        # Add other types as needed: document, sticker, voice, audio

        if original_message.text:
            broadcast_text = original_message.text
        elif original_message.photo:
            broadcast_photo_id = original_message.photo[-1].file_id # Get highest quality
        elif original_message.video:
            broadcast_video_id = original_message.video.file_id
        # Add more elif for other content types
        else:
            raise ValueError("Message has no text or supported media for broadcast.")

        bot.answer_callback_query(call.id, "Starting broadcast...")
        bot.edit_message_text(f"{E('announce')} <b>Broadcasting...</b>  Sending to {len(active_users)} users",
                              chat_id, call.message.message_id, reply_markup=None)
        # Pass all potential content types to execute_broadcast
        thread = threading.Thread(target=execute_broadcast, args=(
            broadcast_text, broadcast_photo_id, broadcast_video_id, 
            original_message.caption if (broadcast_photo_id or broadcast_video_id) else None, # Pass caption
            chat_id))
        thread.start()
    except ValueError as ve: 
        logger.error(f"Error retrieving msg for broadcast confirm: {ve}")
        bot.edit_message_text(f"{E('cross')} Error starting broadcast: {ve}", chat_id, call.message.message_id, reply_markup=None)
    except Exception as e:
        logger.error(f"Error in handle_confirm_broadcast: {e}", exc_info=True)
        bot.edit_message_text(f"{E('cross')} Unexpected error during broadcast confirm.", chat_id, call.message.message_id, reply_markup=None)

def handle_cancel_broadcast(call):
    bot.answer_callback_query(call.id, "𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 𝐜𝐚𝐧𝐜𝐞𝐥𝐥𝐞𝐝.")
    bot.delete_message(call.message.chat.id, call.message.message_id)
    # Optionally delete the original message too if call.message.reply_to_message exists
    if call.message.reply_to_message:
        try: bot.delete_message(call.message.chat.id, call.message.reply_to_message.message_id)
        except: pass


def execute_broadcast(broadcast_text, photo_id, video_id, caption, admin_chat_id):
    sent_count = 0; failed_count = 0; blocked_count = 0
    start_exec_time = time.time() 
    users_to_broadcast = list(active_users); total_users = len(users_to_broadcast)
    logger.info(f"Executing broadcast to {total_users} users.")
    batch_size = 25; delay_batches = 1.5

    for i, user_id_bc in enumerate(users_to_broadcast): # Renamed
        try:
            if broadcast_text:
                bot.send_message(user_id_bc, broadcast_text, parse_mode='HTML')
            elif photo_id:
                bot.send_photo(user_id_bc, photo_id, caption=caption, parse_mode='HTML' if caption else None)
            elif video_id:
                bot.send_video(user_id_bc, video_id, caption=caption, parse_mode='HTML' if caption else None)
            # Add other send methods for other types
            sent_count += 1
        except telebot.apihelper.ApiTelegramException as e:
            err_desc = str(e).lower()
            if any(s in err_desc for s in ["bot was blocked", "user is deactivated", "chat not found", "kicked from", "restricted"]): 
                logger.warning(f"Broadcast failed to {user_id_bc}: User blocked/inactive.")
                blocked_count += 1
            elif "flood control" in err_desc or "too many requests" in err_desc:
                retry_after = 5; match = re.search(r"retry after (\d+)", err_desc)
                if match: retry_after = int(match.group(1)) + 1 
                logger.warning(f"Flood control. Sleeping {retry_after}s...")
                time.sleep(retry_after)
                try: # Retry once
                    if broadcast_text: bot.send_message(user_id_bc, broadcast_text, parse_mode='HTML')
                    elif photo_id: bot.send_photo(user_id_bc, photo_id, caption=caption, parse_mode='HTML' if caption else None)
                    elif video_id: bot.send_video(user_id_bc, video_id, caption=caption, parse_mode='HTML' if caption else None)
                    sent_count += 1
                except Exception as e_retry: logger.error(f"Broadcast retry failed to {user_id_bc}: {e_retry}"); failed_count +=1
            else: logger.error(f"Broadcast failed to {user_id_bc}: {e}"); failed_count += 1
        except Exception as e: logger.error(f"Unexpected error broadcasting to {user_id_bc}: {e}"); failed_count += 1

        if (i + 1) % batch_size == 0 and i < total_users - 1:
            logger.info(f"Broadcast batch {i//batch_size + 1} sent. Sleeping {delay_batches}s...")
            time.sleep(delay_batches)
        elif i % 5 == 0: time.sleep(0.2) 

    duration = round(time.time() - start_exec_time, 2)
    result_msg = (f"{E('announcef')} Broadcast Complete!\n\n{E('check')} Sent: {sent_count}\n{E('cross')} Failed: {failed_count}\n"
                  f"{E('shield')} Blocked/Inactive: {blocked_count}\n{E('eyesf')} Targets: {total_users}\n{E('fire')} Duration: {duration}s")
    logger.info(result_msg)
    try: bot.send_message(admin_chat_id, result_msg)
    except Exception as e: logger.error(f"Failed to send broadcast result to admin {admin_chat_id}: {e}")

def admin_panel_callback(call):
    bot.answer_callback_query(call.id)
    try:
        bot.edit_message_text(f"{E('crownf')} <b>Admin Panel</b>\n\n{E('pin')}  Manage admins using the buttons below:",
                              call.message.chat.id, call.message.message_id, reply_markup=create_admin_panel())
    except Exception as e: logger.error(f"Error showing admin panel: {e}")

def add_admin_init_callback(call):
    bot.answer_callback_query(call.id)
    back_mk = types.InlineKeyboardMarkup()
    back_mk.add(types.InlineKeyboardButton(f"{PE('heart')} Back to Admin Panel", callback_data='admin_panel'))
    msg = bot.send_message(call.message.chat.id,
        f"「 {E('crown')} 𝐀𝐝𝐝 𝐀𝐝𝐦𝐢𝐧 »\n\n⬡  𝐄𝐧𝐭𝐞𝐫 𝐭𝐡𝐞 𝐔𝐬𝐞𝐫 𝐈𝐃 𝐭𝐨 𝐩𝐫𝐨𝐦𝐨𝐭𝐞.\n/cancel to abort.",
        reply_markup=back_mk)
    bot.register_next_step_handler(msg, process_add_admin_id)

def process_add_admin_id(message):
    owner_id_check = message.from_user.id 
    if owner_id_check != OWNER_ID: bot.reply_to(message, f"{E('warn')} Owner only."); return
    if message.text.lower() == '/cancel': bot.reply_to(message, "𝐀𝐝𝐦𝐢𝐧 𝐩𝐫𝐨𝐦𝐨𝐭𝐢𝐨𝐧 𝐜𝐚𝐧𝐜𝐞𝐥𝐥𝐞𝐝."); return
    try:
        new_admin_id = int(message.text.strip())
        if new_admin_id <= 0: raise ValueError("ID must be positive")
        if new_admin_id == OWNER_ID: bot.reply_to(message, f"{E('warn')} Owner is already Owner."); return
        if new_admin_id in admin_ids: bot.reply_to(message, f"{E('warn')} User <code>{new_admin_id}</code> already Admin."); return
        add_admin_db(new_admin_id) 
        logger.warning(f"Admin {new_admin_id} added by Owner {owner_id_check}.")
        bot.reply_to(message, f"{E('check')} User <code>{new_admin_id}</code> promoted to Admin.", parse_mode='HTML')
        try: bot.send_message(new_admin_id, f"{E('party')} Congrats! You are now an Admin.", parse_mode='HTML')
        except Exception as e: logger.error(f"Failed to notify new admin {new_admin_id}: {e}")
    except ValueError:
        bot.reply_to(message, f"{E('warn')} Invalid ID. Send numerical ID or /cancel.")
        msg = bot.send_message(message.chat.id, "𝐄𝐧𝐭𝐞𝐫 𝐔𝐬𝐞𝐫 𝐈𝐃 𝐭𝐨 𝐩𝐫𝐨𝐦𝐨𝐭𝐞, 𝐨𝐫 /cancel.")
        bot.register_next_step_handler(msg, process_add_admin_id)
    except Exception as e: logger.error(f"Error processing add admin: {e}", exc_info=True); bot.reply_to(message, "Error.")

def remove_admin_init_callback(call):
    bot.answer_callback_query(call.id)
    back_mk = types.InlineKeyboardMarkup()
    back_mk.add(types.InlineKeyboardButton(f"{PE('heart')} Back to Admin Panel", callback_data='admin_panel'))
    msg = bot.send_message(call.message.chat.id,
        f"「 {E('crown')} 𝐑𝐞𝐦𝐨𝐯𝐞 𝐀𝐝𝐦𝐢𝐧 »\n\n⬡  𝐄𝐧𝐭𝐞𝐫 𝐭𝐡𝐞 𝐀𝐝𝐦𝐢𝐧 𝐔𝐬𝐞𝐫 𝐈𝐃 𝐭𝐨 𝐫𝐞𝐦𝐨𝐯𝐞.\n/cancel to abort.",
        reply_markup=back_mk)
    bot.register_next_step_handler(msg, process_remove_admin_id)

def process_remove_admin_id(message):
    owner_id_check = message.from_user.id
    if owner_id_check != OWNER_ID: bot.reply_to(message, f"{E('warn')} Owner only."); return
    if message.text.lower() == '/cancel': bot.reply_to(message, "𝐀𝐝𝐦𝐢𝐧 𝐫𝐞𝐦𝐨𝐯𝐚𝐥 𝐜𝐚𝐧𝐜𝐞𝐥𝐥𝐞𝐝."); return
    try:
        admin_id_remove = int(message.text.strip()) # Renamed
        if admin_id_remove <= 0: raise ValueError("ID must be positive")
        if admin_id_remove == OWNER_ID: bot.reply_to(message, f"{E('warn')} Owner cannot remove self."); return
        if admin_id_remove not in admin_ids: bot.reply_to(message, f"{E('warn')} User <code>{admin_id_remove}</code> not Admin."); return
        if remove_admin_db(admin_id_remove): 
            logger.warning(f"Admin {admin_id_remove} removed by Owner {owner_id_check}.")
            bot.reply_to(message, f"{E('check')} Admin <code>{admin_id_remove}</code> removed.", parse_mode='HTML')
            try: bot.send_message(admin_id_remove, f"{E('warn')} You are no longer an Admin.", parse_mode='HTML')
            except Exception as e: logger.error(f"Failed to notify removed admin {admin_id_remove}: {e}")
        else: bot.reply_to(message, f"{E('cross')} Failed to remove admin <code>{admin_id_remove}</code>. Check logs.")
    except ValueError:
        bot.reply_to(message, f"{E('warn')} Invalid ID. Send numerical ID or /cancel.")
        msg = bot.send_message(message.chat.id, f"{E('crown')} Enter Admin ID to remove or /cancel.")
        bot.register_next_step_handler(msg, process_remove_admin_id)
    except Exception as e: logger.error(f"Error processing remove admin: {e}", exc_info=True); bot.reply_to(message, "Error.")

def list_admins_callback(call):
    bot.answer_callback_query(call.id)
    try:
        admin_list_str = "\n".join(f"- <code>{aid}</code> {'(Owner)' if aid == OWNER_ID else ''}" for aid in sorted(list(admin_ids)))
        if not admin_list_str: admin_list_str = "(No Owner/Admins configured!)"
        bot.edit_message_text(f"{E('crown')} <b>Current Admins</b>:\n\n{admin_list_str}", call.message.chat.id,
                              call.message.message_id, reply_markup=create_admin_panel(), parse_mode='HTML')
    except Exception as e: logger.error(f"Error listing admins: {e}")

def add_subscription_init_callback(call):
    bot.answer_callback_query(call.id)
    back_mk = types.InlineKeyboardMarkup()
    back_mk.add(types.InlineKeyboardButton(f"{PE('heart')} Back to Subscriptions", callback_data='subscription'))
    msg = bot.send_message(call.message.chat.id,
        f"「 {E('money')} 𝐀𝐝𝐝 𝐒𝐮𝐛𝐬𝐜𝐫𝐢𝐩𝐭𝐢𝐨𝐧 »\n\n⬡  𝐄𝐧𝐭𝐞𝐫 𝐔𝐬𝐞𝐫 𝐈𝐃 & 𝐝𝐚𝐲𝐬 (e.g. <code>12345678 30</code>).\n/cancel to abort.",
        reply_markup=back_mk, parse_mode='HTML')
    bot.register_next_step_handler(msg, process_add_subscription_details)

def process_add_subscription_details(message):
    admin_id_check = message.from_user.id 
    if admin_id_check not in admin_ids: bot.reply_to(message, f"{E('warn')} Not authorized."); return
    if message.text.lower() == '/cancel': bot.reply_to(message, "Sub add cancelled."); return
    try:
        parts = message.text.split();
        if len(parts) != 2: raise ValueError("Incorrect format")
        sub_user_id = int(parts[0].strip()); days = int(parts[1].strip())
        if sub_user_id <= 0 or days <= 0: raise ValueError("User ID/days must be positive")

        current_expiry = user_subscriptions.get(sub_user_id, {}).get('expiry')
        start_date_new_sub = datetime.now() # Renamed
        if current_expiry and current_expiry > start_date_new_sub: start_date_new_sub = current_expiry
        new_expiry = start_date_new_sub + timedelta(days=days)
        save_subscription(sub_user_id, new_expiry)

        logger.info(f"Sub for {sub_user_id} by admin {admin_id_check}. Expiry: {new_expiry:%Y-%m-%d}")
        bot.reply_to(message, f"{E('check')} Sub for <code>{sub_user_id}</code> by {days} days.\nNew expiry: {new_expiry:%Y-%m-%d}")
        try: bot.send_message(sub_user_id, f"{E('party')} Sub activated/extended by {days} days! Expires: {new_expiry:%Y-%m-%d}.")
        except Exception as e: logger.error(f"Failed to notify {sub_user_id} of new sub: {e}")
    except ValueError as e:
        bot.reply_to(message, f"{E('warn')} Invalid: {e}. Format: <code>ID days</code> or /cancel.")
        msg = bot.send_message(message.chat.id, f"{E('money')} Enter User ID & days, or /cancel.")
        bot.register_next_step_handler(msg, process_add_subscription_details)
    except Exception as e: logger.error(f"Error processing add sub: {e}", exc_info=True); bot.reply_to(message, "Error.")

def remove_subscription_init_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, f"{E('money')} Enter User ID to remove sub.\n/cancel to abort.")
    bot.register_next_step_handler(msg, process_remove_subscription_id)

def process_remove_subscription_id(message):
    admin_id_check = message.from_user.id
    if admin_id_check not in admin_ids: bot.reply_to(message, f"{E('warn')} Not authorized."); return
    if message.text.lower() == '/cancel': bot.reply_to(message, "Sub removal cancelled."); return
    try:
        sub_user_id_remove = int(message.text.strip()) # Renamed
        if sub_user_id_remove <= 0: raise ValueError("ID must be positive")
        if sub_user_id_remove not in user_subscriptions:
            bot.reply_to(message, f"{E('warn')} User <code>{sub_user_id_remove}</code> no active sub in memory."); return
        remove_subscription_db(sub_user_id_remove) 
        logger.warning(f"Sub removed for {sub_user_id_remove} by admin {admin_id_check}.")
        bot.reply_to(message, f"{E('check')} Subscription for <code>{sub_user_id_remove}</code> removed.", parse_mode='HTML')
        try: bot.send_message(sub_user_id_remove, f"{E('warn')} Your subscription was removed by admin.", parse_mode='HTML')
        except Exception as e: logger.error(f"Failed to notify {sub_user_id_remove} of sub removal: {e}")
    except ValueError:
        bot.reply_to(message, f"{E('warn')} Invalid ID. Send numerical ID or /cancel.")
        msg = bot.send_message(message.chat.id, f"{E('money')} Enter User ID to remove sub from, or /cancel.")
        bot.register_next_step_handler(msg, process_remove_subscription_id)
    except Exception as e: logger.error(f"Error processing remove sub: {e}", exc_info=True); bot.reply_to(message, "Error.")

def check_subscription_init_callback(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, f"{E('money')} Enter User ID to check sub.\n/cancel to abort.")
    bot.register_next_step_handler(msg, process_check_subscription_id)

def process_check_subscription_id(message):
    admin_id_check = message.from_user.id
    if admin_id_check not in admin_ids: bot.reply_to(message, f"{E('warn')} Not authorized."); return
    if message.text.lower() == '/cancel': bot.reply_to(message, "Sub check cancelled."); return
    try:
        sub_user_id_check = int(message.text.strip()) # Renamed
        if sub_user_id_check <= 0: raise ValueError("ID must be positive")
        if sub_user_id_check in user_subscriptions:
            expiry_dt = user_subscriptions[sub_user_id_check].get('expiry')
            if expiry_dt:
                if expiry_dt > datetime.now():
                    days_left = (expiry_dt - datetime.now()).days
                    bot.reply_to(message, f"{E('check')} User <code>{sub_user_id_check}</code> active sub.\nExpires: {expiry_dt:%Y-%m-%d %H:%M:%S} ({days_left} days left).")
                else:
                    bot.reply_to(message, f"{E('warn')} User <code>{sub_user_id_check}</code> expired sub (On: {expiry_dt:%Y-%m-%d %H:%M:%S}).")
                    remove_subscription_db(sub_user_id_check) # Clean up
            else: bot.reply_to(message, f"{E('warn')} User <code>{sub_user_id_check}</code> in sub list, but expiry missing. Re-add if needed.")
        else: bot.reply_to(message, f"{E('info')} User <code>{sub_user_id_check}</code> no active sub record.", parse_mode='HTML')
    except ValueError:
        bot.reply_to(message, f"{E('warn')} Invalid ID. Send numerical ID or /cancel.")
        msg = bot.send_message(message.chat.id, f"{E('money')} Enter User ID to check, or /cancel.")
        bot.register_next_step_handler(msg, process_check_subscription_id)
    except Exception as e: logger.error(f"Error processing check sub: {e}", exc_info=True); bot.reply_to(message, "Error.")

# --- End Callback Query Handlers ---

# --- Cleanup Function ---
def cleanup():
    logger.warning("Shutdown. Cleaning up processes...")
    script_keys_to_stop = list(bot_scripts.keys()) 
    if not script_keys_to_stop: logger.info("No scripts running. Exiting."); return
    logger.info(f"Stopping {len(script_keys_to_stop)} scripts...")
    for key in script_keys_to_stop:
        if key in bot_scripts: logger.info(f"Stopping: {key}"); kill_process_tree(bot_scripts[key])
        else: logger.info(f"Script {key} already removed.")
    logger.warning("Cleanup finished.")
atexit.register(cleanup)

# --- Main Execution ---
if __name__ == '__main__':
    logger.info("="*40 + "\nBot Starting Up...\n" + f"Python: {sys.version.split()[0]}\n" +
                f"{PE('bolt')} Base Dir: {BASE_DIR}\n{PE('folder')} Upload Dir: {UPLOAD_BOTS_DIR}\n" +
                f"Data Dir: {IROTECH_DIR}\nOwner ID: {OWNER_ID}\nAdmins: {admin_ids}\n" + "="*40)
    keep_alive()
    logger.info("Starting polling...")
    while True:
        try:
            bot.infinity_polling(logger_level=logging.INFO, timeout=60, long_polling_timeout=30)
        except requests.exceptions.ReadTimeout: logger.warning("Polling ReadTimeout. Restarting in 5s..."); time.sleep(5)
        except requests.exceptions.ConnectionError as ce: logger.error(f"Polling ConnectionError: {ce}. Retrying in 15s..."); time.sleep(15)
        except Exception as e:
            logger.critical(f"{PE('bomb')} Unrecoverable polling error: {e}", exc_info=True)
            logger.info("Restarting polling in 30s due to critical error..."); time.sleep(30)
        finally: logger.warning("Polling attempt finished. Will restart if in loop."); time.sleep(1)

