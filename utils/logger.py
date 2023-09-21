from termcolor import colored
from datetime import datetime

Standard = 0
Warning = 1
Error= 2
Debug = 3

debug = False
with open("log.txt","a") as logf:
    logf.write(f"\n\n--- LOG {datetime.now()} ---\n")

class Log:
    def close():
        logf.close()
    
    def log(message):
                print(f"[i] {message}")
                with open("log.txt","a+") as f: f.write(f"[i] {message}\n")
    def warning(message):
                print(colored(f"[W] {message}",'yellow')) 
                with open("log.txt","a+") as f: f.write(f"[W] {message}\n")
    def error(message):
                print(colored(f"[Error] {message}",'red')) 
                with open("log.txt","a+") as f: f.write(f"[Error] {message}\n")
    def debug(message):
                if not debug:
                        return
                print(colored(f"[Debug] {message}",'green')) 
                with open("log.txt","a+") as f: f.write(f"[Debug] {message}\n")
