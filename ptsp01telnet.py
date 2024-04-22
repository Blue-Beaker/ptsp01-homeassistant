import json
import telnetlib
import time
import threading

NAN = float("nan")
class Socket:
    def __init__(self) -> None:
        pass
    def __str__(self) -> str:
        return f"{self.switch},U={self.voltage},I={self.current},P={self.power},W={self.energy}/{self.energy_meter}"
    switch=False
    voltage:float=NAN
    current:float=NAN
    power:float=NAN
    energy:float=NAN
    energy_meter:float=NAN
class ptsp01:
    host:str
    port:int
    telnet:telnetlib.Telnet
    receiver_thread:threading.Thread
    __poller:threading.Thread
    __polling:bool=False
    password:str=""
    __logged_in:bool|None=None
    __version:str=""
    update_interval:int=10
    __stored_message:str=""
    @property
    def version(self):
        return self.__version
    __states={1:Socket(),2:Socket(),3:Socket()}
    @property
    def states(self):
        return self.__states
    def __init__(self,host:str,port:int=23,password:str=""):
        self.host=host
        self.port=port
        self.password=password
        self.telnet=telnetlib.Telnet()
        self.receiver_thread=threading.Thread(target=self.threaded_receiver,daemon=True)
        self.__poller=threading.Thread(target=self.pollingStatus,daemon=True)
    def connect(self):
        self.telnet.open(self.host,self.port)
        self.onConnect()
        if not self.receiver_thread.is_alive():
            self.receiver_thread.start()
    def onConnect(self):
        message=self.telnet.read_until("root@(none):/# ".encode(),3000).decode()
        if not self.__logged_in:
            if message.endswith("root@(none):/# "):
                self.__logged_in=True
                self.__stored_message=message
                for line in message.splitlines():
                    if line.startswith(" ATTITUDE ADJUSTMENT ("):
                        self.__version=line.split("(")[1].split(")")[0]
                self.putReadStatesShellScript()
            elif message.find("(none) login: ")>=0:
                self.login()
            elif message.find("Login incorrect")>=0:
                print("Login incorrect")
                self.__logged_in=False
                self.onLoginFailure()
    def login(self):
        self.telnet.write(("root\n"+self.password+"\n").encode())
        self.onConnect()
    def onLoginFailure(self):
        pass
    def putReadStatesShellScript(self):
        if self.__logged_in:
            command="tee /tmp/readStates.sh <<EOF\n"
            for socket in range(1,4):
                for item in ["Switch","Voltage","Current","Power","Energy","EnergyMeter.SingleCount"]:
                    command=command+f"qmibtree -g Device.SmartPlug.Socket.{socket}.{item}\n"
            command=command+"EOF\n"
            self.telnet.write(command.encode())
            
    def isLoggedin(self):
        return self.__logged_in
    def waitForLogin(self):
        while(self.__logged_in==None):
            time.sleep(0.1)
        return self.__logged_in

    def getSwitch(self,socket:int):
        self.telnet.write(f"qmibtree -g Device.SmartPlug.Socket.{socket}.Switch\n".encode())
    def switch(self,socket:int,switch:int):
        if self.__logged_in:
            command=f"qmibtree -s Device.SmartPlug.Socket.{socket}.Switch {switch}\n"
            self.telnet.write(command.encode())
            
    def getVoltage(self,socket:int):
        return self.__states[socket].voltage
    def getCurrent(self,socket:int):
        return self.__states[socket].current
    def getPower(self,socket:int):
        return self.__states[socket].power
    def getEnergy(self,socket:int):
        return max(self.__states[socket].energy,self.__states[socket].energy_meter)
    def getStatus(self):
        if self.__logged_in:
            self.telnet.write("sh /tmp/readStates.sh\n".encode())
    def getStatusSingle(self,path):
        if self.__logged_in:
            command=f"qmibtree -g {path}\n"
            self.telnet.write(command.encode())
    def pollingStatus(self):
        while(self.__polling):
            while(not self.__stored_message.endswith("root@(none):/# ")):   # only send commands when ready
                time.sleep(0.1)
            self.getStatus()
            time.sleep(self.update_interval)
    def onMessage(self,message:str):
        message=message.replace(" ","")
        if message.startswith("Device.SmartPlug.Socket."):
            self.parseStatus(message)
    # Deprecated. Use read() and getMsg() instead.
    def readLine(self):
        return(self.telnet.read_until('\r\n'.encode(),100)).decode()
    
    def read(self):
        self.__stored_message=self.__stored_message+self.telnet.read_very_eager().decode()
    def getMsg(self):
        if self.__stored_message.find("\r\n")>-1:
            spl=self.__stored_message.split("\r\n")
            msg=spl[0:-1]
            self.__stored_message=spl[-1]
            return msg
    # def onMessageBlock(self,messages:str):
    #     lines=messages.split("\r\n")
    #     update=False
    #     for line in lines:
    #         line=line.replace(" ","")
    #         if line.startswith("Device.SmartPlug.Socket."):
    #             self.parseStatus(line)
    #             update=True
    #     if update:
    #         self.onStatusUpdate()

    def parseStatus(self,message):  #spaces are removed from message
            socket=int(message[24])
            pairstr=message[26:]
            pair:str=pairstr.split('=')
            if pair.__len__()<2:
                return
            value=pair[1]
            key=pair[0].split("(")[0]
            if key==("Switch"):
                self.__states[socket].switch=value=="1"
            elif key==("Voltage"):
                self.__states[socket].voltage=float(value)
            elif key==("Current"):
                self.__states[socket].current=float(value)
            elif key==("Power"):
                self.__states[socket].power=float(value)
            elif key==("Energy"):
                self.__states[socket].energy=float(value)
            elif key==("EnergyMeter.SingleCount"):
                data=json.loads(value.replace("'",'"'))
                energy=float(data["peakenergy"])+float(data["valleyenergy"])
                self.__states[socket].energy_meter=energy
            self.onStatusUpdate(socket,key)
    def start_polling(self):
        self.__polling=True
        self.__poller.start()
    def stop_polling(self):
        self.__polling=False
    @property
    def is_updating(self):
        return self.__polling
    def onStatusUpdate(self,socket:int,key:str):
        pass
    def onConnectionFailure(self,e):
        self.close()
    def onException(self,exception:Exception):
        pass
    def threaded_receiver(self):
        while(self.__logged_in):
            try:
                # msg = self.readLine.removesuffix('\r\n')
                self.read()
                msg = self.getMsg()
                if msg:
                    for message in msg:
                        self.onMessage(message)
            except (EOFError,OSError,ConnectionError,ConnectionResetError,BrokenPipeError) as e:
                self.onConnectionFailure(e)
                self.__logged_in=False
            except Exception as e:
                self.onException(e)
            time.sleep(0.5)
    def close(self):
        self.__logged_in=False
        self.telnet.close()
    def logMessage(self,*values):
        print(*values)