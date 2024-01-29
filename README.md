# PTSP01-Hass
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)  
用于邦讯玩儿插排（PTSP01）的Homeassistant自定义集成.  
目前，它只能连接到无密码的插排。  
可通过在主板串口连接单片机，使其在收到`Press the [f] key and hit [enter] to enter failsafe mode`后写入 `f\r/etc/init.d/rcS S boot\r`进入failsafe模式并继续启动来绕过密码。  

功能:
- 通过telnet连接
- 将每个插孔当作一个设备
- 读取/控制开关
- 读取电压、电流、功率、能耗

This is a custom homeassistant integration for boomsense ptsp01 powerstrip.  
For now, it only works with powerstrips with no password.   
A MCU can be attached to onboard serial, make it write `f\r/etc/init.d/rcS S boot\r` after reading `Press the [f] key and hit [enter] to enter failsafe mode` , then the powerstrip will be booted into failsafe mode and continue with no password needed.  

Features:
- Connects via telnet
- Represents every socket as a device
- Access to switch
- Read Voltage, Current, Power and Energy

