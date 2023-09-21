import os
import re

from utils import blocks
from utils import logger



class MFT:
    def parse(s_:bytes):
        s = s_.rstrip(b"0").decode()
        if s == "/:;":
            return {"/":{"type":"folder","name":"/","content":[]}}
        dic = {}
        folders = s.split(";")
        for element in folders:
            if element == '':
                continue
            folderName = element.split(":")[0]
            content = element.split(":")[1]
            folderContent = content.split(",")

            dic[folderName] = {"type":"folder","name":folderName,"content":[]}
            if content == '':
                continue
            for file in folderContent:
                if file.endswith('/'):
                    dic[folderName]["content"].append({"type":"folder","name":file})
                else:
                    fInfo = file.split("-")
                    address = int(fInfo[-1])
                    fInfo.pop()
                    filename = "-".join(fInfo)
                    dic[folderName]["content"].append({"type":"file","name":filename,"address":address})

        return dic

    def assemble(s:dict):
        res = ""
        for folder in s:
            res+=folder+":"
            #print(s[folder]["content"])
            if len(s[folder]["content"]) > 0:
                last = s[folder]["content"][-1]
                for file in s[folder]["content"]:
                    if file["type"] == "file":
                        res+=f"{file['name']}-{file['address']}"
                    else:
                        res+=f"{file['name']}"
                    if file != last:
                        res+=","
                    
            res+=";"
        return res.encode()
    class Read:
        def Read(diskpath):
            curr = blocks.ReadBlocks(diskpath,0)
            curr.rstrip(b'0')
            js = MFT.parse(curr)
            return js
        def ReadAt(diskpath,path):
            curr = blocks.ReadBlocks(diskpath,0)
            curr.rstrip(b'0')
            js = MFT.parse(curr)
            if js.get(path):
                return js[path]["content"]
            else:
                logger.Log.error(f"Directory {path} not found!")


    class Write:
        #{"name":"/","type":"folder","content":[{"name":"xd","type":"file","address":11}]}
        def Add(diskpath:str,filename:bytes,directory:bytes,address:int=0,file=False):
            """Adds a File to Master File Table (first 10 blocks of the vdisk)"""
            # This can be a little bit inefficient but it gets all MFT data, changes is then writes it again.
            # Later on i want to implement a data shift function where it shifts all data 1 block forward if space runs out.
            # For now 10 blocks should be more than enough
            curr = blocks.ReadBlocks(diskpath,0)
            curr.rstrip(b'0')
            js = MFT.parse(curr)

            if not directory in js:
                logger.Log.error(f"Directory {directory} not found!")
                return
            
            if file:
                js[directory]["content"].append({"type":"file","name":f"{filename}","address":address})
            else:
                js[directory]["content"].append({"type":"folder","name":f"{filename}/"})
                js[f"{directory}{filename}/"]={"type":"folder","name":f"{directory}{filename}/"}
                js[f"{directory}{filename}/"]["content"] = []
            res = MFT.assemble(js)
            blocks.WriteBlocks(diskpath,res,0,force=True,compress=False)

        def Remove(diskpath:str,filename:bytes,directory:bytes,file:bool):
            curr = blocks.ReadBlocks(diskpath,0)
            curr.rstrip(b'0')
            js = MFT.parse(curr)
            if not directory in js:
                logger.Log.error(f"Directory {directory} not found!")
                return
            
            if file:
                temp_list = js[directory]["content"]
                temp_list = [item for item in temp_list if item["name"] != filename]
                js[directory]["content"]=temp_list
            else:
                del js[directory]
            res = MFT.assemble(js)
            blocks.WriteBlocks(diskpath,res,0,force=True,compress=False)


            
            



    def CreateBlocks(diskpath:str):
        """
        WARNING : 
        
        This function when called will OVERWRITE firs 10 blocks of disk file!\n
        Call this function only ONE time when the vdisk is initialized!
        """
        #OVERWRITING FIRST 10 BLOCKS!
        logger.Log.warning("Creating MFT blocks.")
        emp = {"/":{"type":"folder","name":"/","content":[]}}
        parsed = MFT.assemble(emp)
        blocks.WriteBlocks(diskpath,parsed+blocks.GenEmpty((512*10)-len(parsed)),0,force=True,compress=False)
        logger.Log.warning("Done creating MFT blocks.")
        


        
class Disk:
    def __init__(self,path:str) -> None:
        if not os.path.exists(path):
            with open(path,"wb") as d:
                d.write(b'0'*2048)
            MFT.CreateBlocks(path)
        self.path = path 
        #blocks.WriteBlock(self.stream,b'.'*1024,0)

    def GetData(self):
        with open(self.path) as f:
            pos = f.tell()
            data = f.read() 
            f.seek(pos)
            return data
    
    def ListFiles(self,directory):
        files = []
        mfiles = MFT.Read.ReadAt(self.path,directory)
        for file in mfiles:
            files.append(file.get("name","FILENAME"))
        return files
    
    def StoreFile(self,path:str,content:bytes):
        if "\\" in path:
            logger.Log.error("There cant be a \\ in the filename!")
            return
        if path.endswith("/"):
            logger.Log.error("You cant store a file as a folder!")
            return
        eBlock = blocks.FindEmpty(self.path)
        logger.Log.debug(f"Writing starts at address {eBlock}")
        blocks.WriteBlocks(self.path,content,eBlock)
        dir_ = path.split("/")
        dir_.pop()
        directory = "/".join(dir_)+"/"
        MFT.Write.Add(self.path,path.split("/")[-1],directory,eBlock,True)
    def CreateFolder(self,path:str):
        if "\\" in path:
            logger.Log.error("There cant be a \\ in the foldername!")
            return

        dir_ = path.split("/")
        dir_.pop()
        directory = "/".join(dir_)+"/"
        MFT.Write.Add(self.path,path.split("/")[-1],directory,file=False)
    def GetFile(self,filename,directory):
        fls = MFT.Read.ReadAt(self.path,directory)
        fls_l = []
        for f in fls:
            fls_l.append(f["name"])
        if filename in fls_l:
            for files in MFT.Read.ReadAt(self.path,directory):
                if files["name"] == filename:
                    return blocks.ReadBlocks(self.path,files["address"])
        else:  
            logger.Log.error(f"File {filename} in directory {directory} not found!")
    def RemoveFile(self,filename:str,directory:str):
        fls = MFT.Read.ReadAt(self.path,directory)
        fls_l = []
        for f in fls:
            fls_l.append(f["name"])
        if not filename in fls_l:
            return
        MFT.Write.Remove(self.path,filename,directory,True)
    def RemoveFolder(self,filename:str,directory:str):
        fls = MFT.Read.ReadAt(self.path,directory)
        fls_l = []
        for f in fls:
            fls_l.append(f["name"])
        if not filename in fls_l:
            return
        MFT.Write.Remove(self.path,filename,directory,False)

        
