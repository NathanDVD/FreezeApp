import psutil
import json
import os
import time
import ctypes
import keyboard#Global hotkeys library

CONFIG_PATH = "config.json"

#Load or create config
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r") as config_file:
        try:
            config = json.load(config_file)
        except json.JSONDecodeError:
            config = {}
else:
    config = {}

#Get or ask for process name
if "process_name" not in config or not config["process_name"]:
    process_name = input("Enter the process name to manage (e.g. roblox): ").strip()
    config["process_name"] = process_name
    with open(CONFIG_PATH, "w") as config_file:
        json.dump(config, config_file)
else:
    process_name = config["process_name"]


#Get the necessary constants
THREAD_SUSPEND_RESUME = 0x0002
OpenThread = ctypes.windll.kernel32.OpenThread
SuspendThread = ctypes.windll.kernel32.SuspendThread
ResumeThread = ctypes.windll.kernel32.ResumeThread
CloseHandle = ctypes.windll.kernel32.CloseHandle

paused_pids = set()

def suspend_process_threads(pid):
    try:
        proc = psutil.Process(pid)
        for thread in proc.threads():
            try:
                tid = thread.id
                h_thread = OpenThread(THREAD_SUSPEND_RESUME, False, tid)
                if h_thread:
                    SuspendThread(h_thread)
                    CloseHandle(h_thread)
            except Exception:
                pass
    except psutil.NoSuchProcess:
        pass

def resume_process_threads(pid):
    try:
        proc = psutil.Process(pid)
        for thread in proc.threads():
            try:
                tid = thread.id
                h_thread = OpenThread(THREAD_SUSPEND_RESUME, False, tid)
                if h_thread:
                    ResumeThread(h_thread)
                    CloseHandle(h_thread)
            except Exception:
                pass
    except psutil.NoSuchProcess:
        pass

def find_processes_by_name(name):
    return [p for p in psutil.process_iter(['pid', 'name']) if p.info['name'] and name.lower() in p.info['name'].lower()]

def toggle_pause():
    global paused_pids
    procs = find_processes_by_name(process_name)

    if not procs:
        print("No matching processes found.")
        return

    for proc in procs:
        if proc.pid not in paused_pids:
            print(f"[HOTKEY] Suspending {proc.name()} (PID {proc.pid})")
            suspend_process_threads(proc.pid)
            paused_pids.add(proc.pid)
        else:
            print(f"[HOTKEY] Resuming {proc.name()} (PID {proc.pid})")
            resume_process_threads(proc.pid)
            paused_pids.remove(proc.pid)


#Hotkey setup
keyboard.add_hotkey('f1', toggle_pause)

print("To change the process to freeze, either edit the config file to add the proper process name, or just delete it.")
print(f"Monitoring for process: {process_name}")
print("Press F1 to pause/resume process, F3 to exit.")


def resume_all_paused_processes():
    for pid in list(paused_pids):
        try:
            proc = psutil.Process(pid)
            print(f"[EXIT] Resuming {proc.name()} (PID {pid})")
            resume_process_threads(pid)
            paused_pids.remove(pid)
        except psutil.NoSuchProcess:
            pass

def exit_program():
    print("\nExiting... Resuming paused processes.")
    resume_all_paused_processes()
    time.sleep(0.5)
    os._exit(0)

keyboard.add_hotkey('f3', exit_program)
keyboard.wait()
