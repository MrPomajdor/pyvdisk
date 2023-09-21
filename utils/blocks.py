
import re
from utils import logger
from utils.directory_utils import File

import base64

#CIRCULAR IMPOOOORT
from disk import MFT

def decode_base64(data, altchars=b'+/'):
    """Decode base64, padding being optional.

    :param data: Base64 data as an ASCII byte string
    :returns: The decoded byte string.

    """
    data = re.sub(rb'[^a-zA-Z0-9%s]+' % altchars, b'', data)  # normalize
    missing_padding = len(data) % 4
    if missing_padding:
        data += b'='* (4 - missing_padding)
    return base64.b64decode(data, altchars)


def Compress(s:bytes) -> bytes:
    index = 0
    compressed = b""
    l = len(s)
    while index != l:
        count = 1
        while (index<l-1) and (s[index]==s[index+1]):
            count += 1
            index += 1
        if count == 1:
            compressed += chr(s[index]).encode()
        else:
            compressed += chr(s[index]).encode()+b"\\c"+bytes(str(count).encode()+b";")
        index += 1
    return compressed

def Decompress(s:bytes) -> bytes:
    index = 0
    decompressed = b""
    l = len(s)
    #print("Decompressing",s)
    while index != l:
        if chr(s[index])=="\\" and chr(s[index+1])=="c":
            index+=1
            i=1
            am = ""
            while 1:
                if chr(s[index+i]) != ";":
                    am+=chr(s[index+i])
                else:
                    break
                i+=1

            decompressed += chr(s[index-2]).encode()*(int(am)-1)
            index += len(am)+1

        else:
            decompressed +=chr(s[index]).encode()
        index += 1
    return decompressed


def SplitToChunks(str,n):
    chunks = [str[i:i+n] for i in range(0, len(str), n)]
    return chunks

def GenEmpty(size:int):
    return b'0'*size

def ReadBlock(path,block:int) -> bytes:
    logger.Log.debug(f"Reading block {block}")
    with open(path,"rb") as f:
        f.seek(block*512)
        data = f.read(512)
        if b"\c" in data:
            data = Decompress(data)
        return data
    
def ReadBlocks(path,start:int,decompress:bool=True) -> bytes:
    with open(path,"rb") as f:
        cur_addr = start
        file = b""
        fileSize = int(re.search(b"\\\\l\\d{1,}",ReadBlock(path,cur_addr)).group(0).replace(b"\\l",b""))
        while 1:
            curr_block = ReadBlock(path,cur_addr)
            pureData = re.sub(b"\\\\\\w+\\d{0,};0{0,}",b'',curr_block.replace(b"\\\\",b"\\"))
            file+=pureData
            if b"\\nbl" in curr_block:
                temp = re.compile(b"\\\\nbl\\d{0,};")
                found = temp.findall(curr_block)
                cur_addr = int(found[0].strip(b';').replace(b'\\nbl',b''))
                logger.Log.debug(f"Next block is at {cur_addr}")
            
            if b"\\e;" in curr_block:
                logger.Log.debug(f"End block at {cur_addr}")
                if not fileSize == len(file):
                    logger.Log.warning(f"Final filesize and size header mismatch! (header: {fileSize}, actual length: {len(file)}) (start block {start})")
                if decompress:
                    file = Decompress(file)
                return base64.b64decode(file.rstrip(b'0'))


def IsBlockEmpty(path,block:int) -> bool:
    js = MFT.Read.Read(path)
    sj = str(js)
    r= re.compile("'address': {0,}\d{1,}")
    l = r.findall(sj)
    
    if block<=10:
        return False
    if len(l) == 0:
        return True
    occ_blocks = []
    for ad in l:
        address = int(ad.split(":")[1])
        if block == address:
            return False
        block = ReadBlock(path,address)
        if b"\\eb" in block:
            endBlock= int(re.search(b"\\\\eb\\d{1,}",block).group(0).replace(b"\\eb",b""))
            occ_blocks.extend(range(address, endBlock + 1))
    if block in occ_blocks:
        return False
    else:
        return True

def WriteBlocks(path,content:bytes,block:int,force:bool=False,compress:bool=False) -> bool:
        if type(content) != bytes:
            logger.Log.error(f"WriteBlocks only accepts BYTES not {type(content)} as content")
            return
        l = len(content)
        l2 = len(content.rstrip(b'0'))
        content = base64.b64encode(content.rstrip(b'0'))
        content+=b'0'*(l-l2)
        sizeFlag = b''
        if compress:
            content = Compress(content)
        
        sizeFlag += bytes('\\l'+str(len(sizeFlag+content))+';',"utf-8")
        chunks = SplitToChunks(b"0"*20+content,490)
        endBl = block+len(chunks)-1
        if compress:
            sizeFlag+=b'\\c'+str(endBl).encode()+b';'
        sizeFlag += bytes('\\eb'+str(endBl)+';',"utf-8")

        sizeFlag = sizeFlag+((20-len(sizeFlag)))*b'0'
        last_pr = -1
        with open(path,"rb+") as f:
            if len(sizeFlag+content)-1 > 512:
                chunks = SplitToChunks(sizeFlag+content,480)
                blocksAmount = len(chunks)-1
                cutStr = ""
                for a in range(blocksAmount+1):
                    if a != 0:
                        pr = int((a/blocksAmount)*100)
                        if pr%10==0 and pr!=last_pr:
                            logger.Log.debug(f"Writing {pr}%")
                            last_pr = pr
                    else:
                        logger.Log.debug(f"Writing 0%")


                    f.seek(0,1)
                    blockOffset = block
                    if a != blocksAmount:
                        if force or IsBlockEmpty(path,block+1):
                            f.seek((block+a)*512,0)
                            logger.Log.debug(f"seeking {block*512+(a*512)+blockOffset}")
                            nextBlockFlag = f"\\nbl{blockOffset+a+1};".encode()
                            nextBlockFlag += b'0'*(512-len(chunks[a]+nextBlockFlag))
                            f.write(chunks[a]+nextBlockFlag)
                            logger.Log.debug(f"Writing chunk {a} at posision {blockOffset+a}")
                        else:
                            nextBlock = FindEmpty(path)
                            blockOffset = nextBlock
                            nextBlockFlag = f"\\nbl{a+nextBlock};".encode()
                            nextBlockFlag += b'0'*(512-len(chunks[a]+nextBlockFlag))
                            f.seek((block+a)*512,0)
                            f.write(chunks[a]+nextBlockFlag)
                            logger.Log.debug(f"Writing chunk {a} at posision {blockOffset+a} (next one was not empty)")
                    else:
                        f.seek((block+a)*512,0)
                        logger.Log.debug(f"seeking {block+(a*512)+blockOffset}")
                        endFlag = bytes("\\e;","utf-8")
                        endFlag += b'0'*(512-len(chunks[a]+endFlag))
                        f.write(chunks[a]+endFlag)
                        logger.Log.debug(f"Writing last chunk {a} at posision {blockOffset+a}")
                return True
                
            else:
                if force or IsBlockEmpty(path,block):
                    f.seek(block*512,0)
                    endFlag = b"\\e;"
                    flcontent = sizeFlag + content + endFlag
                    f.write(flcontent+(b'0'*(512-len(flcontent)-1)))
                    logger.Log.debug(f"Writing block {block}")
                    return True
                else:
                    logger.Log.error(f"Block you are trying to write ({block}) is not empty! Use force argument to overwrite it.")
                    return False

def FindEmpty(path) -> int:
    with open(path,"rb+") as f:
        curr_block = 10
        while 1:
            if IsBlockEmpty(path,curr_block):
                return curr_block
            curr_block += 1
        