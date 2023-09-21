import random
import string

from utils.blocks import *
from disk import *

d = Disk("disk.bin")

def get_random_string(length):
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str



print("Files in / :",d.ListFiles("/"))
print("Creating folder")
d.CreateFolder("/folder")
print("Creating a file in folder")
d.StoreFile("/folder/text.txt",get_random_string(1000).encode())
print("Files in / :",d.ListFiles("/"),"Files in /folder/ :",d.ListFiles("/folder/"))


