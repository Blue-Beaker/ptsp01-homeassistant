import telnetlib
import time
import threading

host='192.168.31.179'
port=23

class ptsp01:
    host:str
    port:int
    telnet:telnetlib.Telnet
    listener:threading.Thread
    password:str=""
    __logged_in:bool|None=None
    version:str=""
    name:str="SP01"
    states={'1':{},'2':{},'3':{}}
    def __init__(self,host:str,port:int=23,password:str=""):
        self.host=host
        self.port=port
        self.password=password
        self.telnet=telnetlib.Telnet()
        self.listener=threading.Thread(target=self.threaded_receiver,daemon=True)
    def connect(self):
        self.telnet.open(self.host,self.port)
        self.onConnect()
    def onConnect(self):
        message=self.telnet.read_until("root@(none):/# ".encode(),1000).decode()
        if not self.__logged_in:
            if message.endswith("root@(none):/# "):
                self.__logged_in=True
                for line in message.splitlines():
                    if line.startswith(" ATTITUDE ADJUSTMENT ("):
                        self.version=line.split("(")[1].split(")")[0]
                self.listener.start()
            elif message.find("(none) login: ")>=0:
                self.login()
            elif message.find("Login incorrect")>=0:
                print("Login incorrect")
                self.__logged_in=False
    def login(self):
        self.telnet.write(("root\n"+self.password+"\n").encode())
        self.onConnect()
    def waitForLogin(self):
        while(self.__logged_in==None):
            time.sleep(0.1)
        return self.__logged_in

    def switch(self,socket:int,switch:int):
        if self.__logged_in:
            command=f"qmibtree -s Device.SmartPlug.Socket.{socket}.Switch {switch}\n"
            self.telnet.write(command.encode())

    def getStatus(self):
        if self.__logged_in:
            command=f"qmibtree -p Device.SmartPlug.Socket.\n"
            self.telnet.write(command.encode())

    def readLine(self):
        return(self.telnet.read_until('\r\n'.encode(),100))

    def onMessage(self,message:str):
        #print(message)
        message=message.removeprefix(" ").removeprefix(" ").removeprefix(" ")
        if message.startswith("Device.SmartPlug.Socket."):
            self.parseStatus(message)
    def parseStatus(self,message):
            socket=message[24]
            pairstr=message[26:]
            pair=pairstr.split(') = ')
            key=pair[0].split(' (')
            if(key[1]=='int'):
                value=int(pair[1])
            else:
                value=pair[1]
            self.states[socket][key[0]]=value
            #print(key[0],key[1],pair[1])
    def onException(self,exception:Exception):
        pass
    def threaded_receiver(self):
        while(1):
            try:
                self.onMessage(self.readLine().decode().removesuffix('\r\n'))
            except Exception as e:
                self.onException(e)
    def close(self):
        self.telnet.close()
