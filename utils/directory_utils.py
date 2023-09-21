class Path:
    def __init__(self,path) -> None:
        self.path = path
    def __str__(self) -> str:
        return self.path

class File:
    def __init__(self,filename:str,content:bytes,address:int) -> None:
        self.filename = filename
        self.address = address
        self.content = content
        
    def __str__(self) -> str:
        try:
            return self.content.decode()
        except:
            return ""
    def bytes(self) -> bytes:
        return self.content