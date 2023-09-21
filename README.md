#  Virtual Disk in Python!!!!!!!1
to be honest its slow and doesnt always makes sense how it stores data and reads it, but its a hobby project not an actual piece of code that should work in a production enviroment. 

**Maybe some day ill make this good enough for production** 
*as I said this is a hobby project that serves no purpouse for anyone. It exists because I wanted to do it*

## How it stores data
first 10 blocks (512 character long segments) is reserved for a Master File Table that stores what addres a file is stored at. Address meaning what block it starts.

First 20 characters in a FIRST block is reserverved for headers like `\lx;` where x is the lenght of the content. Here are all the headers:

    \lx; - where x is lenght of the content
    \cx; - where x is the uncompressed lenght of the file (yes it supports compression but its really not that great.)
    \ebx; - where x is the last block that data for this file is stored 

There are "headers" in the last 20 characters of the block too:

    \e; - for indicating the end block of the file

**Oh and data is stored using Base64 encoding**


