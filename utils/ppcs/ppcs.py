#version: 1.0.2
#truongbv

import ctypes
import logging
import socket
import struct
import json
import sys

#log: .debug, .info, .critical, .error 
#DEBUG < INFO < WARNING < ERROR < CRITICAL
logger = logging.getLogger(__name__)
log_formatter = logging.Formatter('%(levelname)-8s [%(filename)-10s:%(funcName)-12s] %(message)s')
log_handler = logging.StreamHandler()
log_handler.setFormatter(log_formatter)
logger.addHandler(log_handler)
logger.setLevel(logging.DEBUG)
####

MAX_PK_SIZE = 1024 * 2048
HEADER_SIZE = 8
PACKET_SIZE = 1024

## struct 
class PPCS_NetInfo(ctypes.Structure):
    _fields_ = [
        ('FlagInternet',    ctypes.c_char),
        ('FlagHostResolved',ctypes.c_char),
        ('FlagServerHello', ctypes.c_char),
        ('NAT_Type',        ctypes.c_char),
        ('MyLanIP',         ctypes.c_char * 16),
        ('MyWanIP',         ctypes.c_char * 16)
    ]

class in_addr(ctypes.Structure):
    _fields_ = [
        ('s_addr', ctypes.c_uint)
    ]

class sockaddr_in(ctypes.Structure):
    _fields_ = [
        ('sin_family',  ctypes.c_ushort),
        ('sin_port',    ctypes.c_ushort),
        ('sin_addr',    in_addr),
        ('sin_zero',    ctypes.c_char * 8)
    ]

class PPCS_Session(ctypes.Structure):
    _fields_ = [
        ('Skt',         ctypes.c_int),
        ('RemoteAddr',  sockaddr_in),
        ('MyLocalAddr', sockaddr_in),
        ('MyWanAddr',   sockaddr_in),
        ('ConnectTime', ctypes.c_int),
        ('DID',         ctypes.c_char * 24),
        ('bCorD',       ctypes.c_char),
        ('bMode',       ctypes.c_char),
        ('Reserved',    ctypes.c_char * 2)
    ]
####

####
# ERROR CODE LOCAL
ERROR_PPCS_CONFIGS    = -1000
ERROR_PPCS_READ_SIZE  = -1001
ERROR_PPCS_READ_MASK  = -1002
ERROR_PPCS_READ_MSGID = -1003

P2P_LIB_DLL_PATH     = "utils/ppcs/libs/lib_ppcs_api.dll"
P2P_LIB_SO_PATH      = "utils/ppcs/libs/lib_ppcs_api.so"
#
class LibPPCS:
    def __init__(self):
        ppcs_lib_path = P2P_LIB_SO_PATH if sys.platform == "linux" else P2P_LIB_DLL_PATH
        self.lib = ctypes.cdll.LoadLibrary(ppcs_lib_path)
        self.init_string    = ""
        self.device_id      = ""
        self.session_id     = 0
        self.p2p_channel    = 0
        self.path_api_list  = ""
        self.max_pk_size = MAX_PK_SIZE
        self.header_size = HEADER_SIZE
        self.packet_size = PACKET_SIZE
        logger.info("Init class PPCS done")

    def check_configs(self):
        if self.init_string == "" or self.device_id == "":
            logger.error("Error InitString or DID is None!")
            return -1
        return 0
    
    def PPCS_Initialize(self):
        if self.check_configs() < 0:
            logger.error("config failed")
            return ERROR_PPCS_CONFIGS
        self.lib.PPCS_Initialize.argtypes = [ctypes.c_char_p]
        self.lib.PPCS_Initialize.restype = ctypes.c_int
        ret = self.lib.PPCS_Initialize(str.encode(self.init_string))
        logger.info(f"Done: {ret}")
        return ret
    
    def PPCS_DeInitialize(self):
        self.lib.PPCS_DeInitialize.argtypes = []
        res = self.lib.PPCS_DeInitialize()
        logger.info(f"Done: {res}")
        return res
    
    def PPCS_GetAPIInformation(self):
        self.lib.PPCS_GetAPIInformation.restype = ctypes.c_char_p
        res = self.lib.PPCS_GetAPIInformation()
        logger.info(f"Done: {res}")
        return res
    
    def PPCS_Close(self):
        self.lib.PPCS_Close.argtypes = [ctypes.c_int]
        res = self.lib.PPCS_Close(self.session_id)
        logger.info(f"Done: {res}")
        return res
    
    def PPCS_NetworkDetect(self):
        NetInfo = PPCS_NetInfo()
        self.lib.PPCS_NetworkDetect.argtypes = [ctypes.POINTER(PPCS_NetInfo), ctypes.c_int]
        ret = self.lib.PPCS_NetworkDetect(NetInfo, 0)
        logger.debug(f"FlagHostResolved:   0x{ord(NetInfo.FlagHostResolved):02x}")
        logger.debug(f"FlagInternet:       0x{ord(NetInfo.FlagInternet):02x}")
        logger.debug(f"FlagServerHello:    0x{ord(NetInfo.FlagServerHello):02x}")
        logger.debug(f"NAT_Type:           0x{ord(NetInfo.NAT_Type):02x}")
        logger.debug(f"MyLanIP:            {NetInfo.MyLanIP}")
        logger.debug(f"MyWanIP:            {NetInfo.MyWanIP}")
        logger.info(f"Done: {ret}")
        return ret
    
    def PPCS_Connect(self, EnableLanSearch, UDP_Port):
        if self.check_configs() < 0:
            logger.error(f"PPCS_DID: {ERROR_PPCS_CONFIGS}")
            return ERROR_PPCS_CONFIGS
        self.lib.PPCS_Connect.argtypes = [ctypes.c_char_p, ctypes.c_char, ctypes.c_int]
        self.lib.PPCS_Connect.restype = ctypes.c_int
        ret = self.lib.PPCS_Connect(str.encode(self.device_id), ctypes.c_char(str.encode(EnableLanSearch)), int(UDP_Port))
        logger.debug(f"EnableLanSearch: {str.encode(EnableLanSearch)}")
        logger.info(f"Done: {ret}")
        self.session_id = ret
        return ret
    
    def PPCS_Check(self):
        Session = PPCS_Session()
        self.lib.PPCS_Check.argtypes = [ctypes.c_int, ctypes.POINTER(PPCS_Session)]
        self.lib.PPCS_Check.restype = ctypes.c_int
        ret = self.lib.PPCS_Check(self.session_id, Session)
        logger.info(f"Done: {ret}")
        if ret < 0:
            logger.error("Check failed")
            return ret
        logger.debug(f"Skt:         {Session.Skt}")
        logger.debug(f"RemoteAddr:  {socket.inet_ntoa(struct.pack('I', Session.RemoteAddr.sin_addr.s_addr))}:{Session.RemoteAddr.sin_port}")
        logger.debug(f"MyLocalAddr: {socket.inet_ntoa(struct.pack('I', Session.MyLocalAddr.sin_addr.s_addr))}:{Session.MyLocalAddr.sin_port}")
        logger.debug(f"MyWanAddr:   {socket.inet_ntoa(struct.pack('I', Session.MyWanAddr.sin_addr.s_addr))}:{Session.MyWanAddr.sin_port}")
        logger.debug(f"ConnectTime: {Session.ConnectTime}")
        logger.debug(f"DID:         {Session.DID}")
        logger.debug(f"bCorD:       0x{ord(Session.bCorD):02x}")
        logger.debug(f"bMode:       0x{ord(Session.bMode):02x}")
        return ret
    
    def PPCS_Read(self, Channel, MsgID, TimeOut_ms):        
        TimeOut_ms_1 = 500
        Retry = int(TimeOut_ms / 100)

        DataSize = ctypes.c_int(self.max_pk_size)
        DataBuf = (ctypes.c_char * self.max_pk_size)()   
        self.lib.PPCS_Read.argtypes = [
            ctypes.c_int, 
            ctypes.c_char, 
            ctypes.POINTER(ctypes.c_char), 
            ctypes.POINTER(ctypes.c_int), 
            ctypes.c_uint
        ]
        self.lib.PPCS_Read.restype = ctypes.c_int

        for k in range(Retry):
            DataSize = ctypes.c_int(self.max_pk_size)
            ret = self.lib.PPCS_Read(
                ctypes.c_int(self.session_id), 
                ctypes.c_char(int(Channel)), 
                ctypes.POINTER(ctypes.c_char)(DataBuf), 
                ctypes.POINTER(ctypes.c_int)(DataSize), 
                ctypes.c_uint(int(TimeOut_ms_1))
            )
            if DataSize.value < 8:
                logger.warn(f"Wrong size of read. Try again {k}")
            if DataSize.value >= 8:
                break

        MsgLen = (ord(DataBuf[2]) << 8) + ord(DataBuf[3])       
        MsgIDRead = (ord(DataBuf[4]) << 8) + ord(DataBuf[5])
        Msgsession_id = (ord(DataBuf[6]) << 8) + ord(DataBuf[7])
        
        #debug
        logger.info(f"TimeOut_ms:      {TimeOut_ms}")
        logger.info(f"TimeOut_ms_1:    {TimeOut_ms_1}")
        logger.info(f"Retry:           {Retry}")
        logger.info(f"Channel:         {Channel}")
        logger.info(f"SessionID:       {self.session_id}")
        logger.info(f"DataSize:        {DataSize.value}")
        logger.info(f"DataBuf:         {DataBuf}")
        logger.info(f"PPCS_Read:       {ret}")
        # logger.debug(f"MsgLen:       {MsgLen}")
        # logger.debug(f"MsgIDRead:    {MsgIDRead}")
        # logger.debug(f"SessionID:    {MsgSessionID}")
        # if DataSize.value < 8:
        #     logger.error("Wrong size of read")
        #     return ERROR_PPCS_READ_SIZE
        if ord(DataBuf[0]) != 0xEF or ord(DataBuf[1]) != 0xEF:
            logger.error("Wrong Mask Number")
            return ERROR_PPCS_READ_MASK
        if MsgIDRead != int(MsgID):
            logger.error("Wrong Msg Id")
            return ERROR_PPCS_READ_MSGID
        
        res = (ctypes.c_char * (int(DataSize.value) - 8))()
        i = 8
        while (ord(DataBuf[i]) > 0x00  and ord(DataBuf[i]) < 0x7f):
            res[i - 8] = ord(DataBuf[i])
            i += 1
        logger.info(f"Buffer: {res.value}, Length: {len(res)}")
        return res.value
    

    def PPCS_Write(self, Channel, MsgID, MsgBody=""):
        if MsgBody == "":
            logger.error("msg is null")
            return -1
        logger.info(f"MsgID Body:\n{MsgBody}")
        try:
            json.loads(MsgBody)
        except ValueError:
            logger.error("MsgID body not a json")
            return -1
        
        MsgLen = len(MsgBody)
        DataSize = MsgLen + self.header_size
        DataBuf = (ctypes.c_char * DataSize)()
        DataBuf[0] = 0xEF
        DataBuf[1] = 0xEF
        DataBuf[2] = (MsgLen >> 8) & 0xFF
        DataBuf[3] = MsgLen & 0xFF
        DataBuf[4] = (int(MsgID)) >> 8 & 0xFF
        DataBuf[5] = int(MsgID) & 0xFF
        DataBuf[6] = (int(self.session_id) >> 8) & 0xFF
        DataBuf[7] = int(self.session_id) & 0xFF
        for i in range(MsgLen):
            DataBuf[8 + i] = ord(MsgBody[i])
        self.lib.PPCS_Write.argtypes = [
            ctypes.c_int, 
            ctypes.c_char, 
            ctypes.POINTER(ctypes.c_char), 
            ctypes.c_int
        ]        
        self.lib.PPCS_Write.restype = ctypes.c_int

        ret = self.lib.PPCS_Write(
            ctypes.c_int(self.session_id), 
            ctypes.c_char(int(Channel)), 
            ctypes.POINTER(ctypes.c_char)(DataBuf), 
            ctypes.c_int(DataSize)
        )

        logger.info(f"Done: {ret}")
        return ret
    
#############################################################

    def ppcs_init_api(self):
        ret = self.PPCS_GetAPIInformation()        
        ret = self.PPCS_Initialize()
        ret = self.PPCS_NetworkDetect()
        if ret < 0:
            logger.error("PPCS_NetworkDetect failed")
            return ret
        
        ret = self.PPCS_Connect('z', 0)
        if ret < 0:
            logger.error("PPCS_Connect failed")
            return ret
        
        ret = self.PPCS_Check()
        if ret < 0:
            logger.error("PPCS_Check failed")
            return ret
        logger.info("INIT P2P done")
        return 0
    
    def ppcs_deinit_api(self):
        ret = self.PPCS_Close()
        if ret < 0:
            logger.error("PPCS_Close failed")
            return ret
        
        ret = self.PPCS_DeInitialize()
        if ret < 0:
            logger.error("PPCS_DeInitialize failed")
            return ret
        logger.info("DEINIT P2P done")
        return 0
    
    def ppcs_set_get_api(self, MsgID=1050, inMsgBody="", outMsgBody=False, timeout=3000):
        ret = self.PPCS_Write(self.p2p_channel, MsgID, inMsgBody)
        if ret < 0:
            logger.error("PPCS_Write failed")
            return ret
        
        msg_byte_str = self.PPCS_Read(self.p2p_channel, MsgID, timeout)
        msg_json = dict
        try:
            # msg_byte_str = str(msg_byte_str)
            msg_str = msg_byte_str.decode('utf-8')
            msg_json = json.loads(msg_str)
            ret = msg_json['status']
            logger.info(f"===> Result API {MsgID}: {ret}")
        except ValueError:
            ret = -1

        if outMsgBody == True and ret >= 0:
            ret = msg_json
        return ret
    





    
#####################################################################################
    # def PPCS_Read_Byte(self, Channel, TimeOut_ms):
    #     DataSize = ctypes.c_int(1)
    #     DataBuf = (ctypes.c_char * 1)()
    #     TimeOut_ms_1 = int(int(TimeOut_ms) / 10)
    #     logger.info(f"TimeOut_ms_1: {TimeOut_ms_1}")
    #     self.Lib.PPCS_Read.argtypes = [
    #         ctypes.c_int, 
    #         ctypes.c_char, 
    #         ctypes.POINTER(ctypes.c_char), 
    #         ctypes.POINTER(ctypes.c_int), 
    #         ctypes.c_uint
    #     ]
    #     for k in range(50):
    #         ret = self.Lib.PPCS_Read(
    #             ctypes.c_int(self.session_id), 
    #             ctypes.c_char(int(Channel)), 
    #             ctypes.POINTER(ctypes.c_char)(DataBuf), 
    #             ctypes.POINTER(ctypes.c_int)(DataSize), 
    #             ctypes.c_uint(int(TimeOut_ms_1))
    #         )
    #         if DataSize.value > 0:
    #             break
    #     logger.info(f"DataBuf:     {DataBuf}")
    #     logger.info(f"DataSize:    {DataSize.value}")
    #     logger.info(f"Read_Byte:   {ret}")
    #     return ret

    # def PY_PPCS_PktRecv(self, Channel, MsgID, TimeOut_ms):
    #     PktSize = ctypes.c_int(PACKET_SIZE)
    #     PktBuf = (ctypes.c_char * PACKET_SIZE)()
    #     TimeOut_ms_1 = int(TimeOut_ms) / 10
    #     TimeOut_s_1 = int(TimeOut_ms) / 10000
    #     self.Lib.PPCS_PktRecv.argtypes = [
    #         ctypes.c_int, 
    #         ctypes.c_char, 
    #         ctypes.POINTER(ctypes.c_char), 
    #         ctypes.POINTER(ctypes.c_int), 
    #         ctypes.c_uint
    #     ]
    #     self.Lib.PPCS_PktRecv.restype = ctypes.c_int

    #     # for k in range(50):
    #     ret = self.Lib.PPCS_PktRecv(
    #         self.SessionID, 
    #         ctypes.c_char(int(Channel)), 
    #         ctypes.POINTER(ctypes.c_char)(PktBuf), 
    #         ctypes.POINTER(ctypes.c_int)(PktSize), 
    #         int(TimeOut_ms)
    #     )
    #     #     if PktSize.value > 0:
    #     #         break
    #     MsgLen = (ord(PktBuf[2]) << 8) + ord(PktBuf[3])        
    #     MsgIDRead = (ord(PktBuf[4]) << 8) + ord(PktBuf[5])
    #     MsgSessionID = (ord(PktBuf[6]) << 8) + ord(PktBuf[7])

    #     logger.info(f"TimeOut_ms_1: {TimeOut_ms_1}")
    #     logger.info(f"TimeOut_s_1:  {TimeOut_s_1}")
    #     logger.info(f"PktSize:      {PktSize.value}")
    #     logger.info(f"PktBuf:       {PktBuf}")
    #     logger.info(f"PPCS_PktRecv: {ret}")
    #     logger.info(f"MsgLen:       {MsgLen}")
    #     logger.info(f"MsgIDRead:    {MsgIDRead}")
    #     logger.info(f"SessionID:    {MsgSessionID}")
    #     if PktSize.value < 8:
    #         logger.error("Wrong size of read")
    #         return ERROR_PPCS_READ_SIZE
        
    #     if ord(PktBuf[0]) != 0xEF or ord(PktBuf[1]) != 0xEF:
    #         logger.error("Wrong Mask Number")
    #         return ERROR_PPCS_READ_MASK
        
    #     if MsgIDRead != int(MsgID):
    #         logger.error("Wrong Msg Id")
    #         return ERROR_PPCS_READ_MSGID
        
    #     res = (ctypes.c_char * (int(PktSize.value) - 8))()
    #     i = 8
    #     while ord(PktBuf[i]) > 0x00 and ord(PktBuf[i]) < 0x7f:
    #         res[i - 8] = ord(PktBuf[i])
    #         i += 1
    #     logger.info("res: {0}, Length: {1}".format(res.value, len(res)))
    #     return res.value
    
    # def PY_PPCS_PktSend(self, Channel, MsgID, subMsgID=-1):
    #     pathMsgIDFile = self.path_api_list + "/" + str(MsgID)
    #     if subMsgID != -1:
    #         pathMsgIDFile = pathMsgIDFile + '_' + str(subMsgID)
    #     fd = open(pathMsgIDFile, 'r')
    #     MsgBody = fd.read()
    #     fd.close()
    #     logger.info(f"MsgID Body:\n{MsgBody}")
    #     try:
    #         json.loads(MsgBody)
    #     except ValueError:
    #         logger.error("MsgID body not a json")
    #         return -1
        
    #     MsgLen = len(MsgBody)
    #     PktSize = MsgLen + HEADER_SIZE
    #     PktBuf = (ctypes.c_char * PktSize)()
    #     PktBuf[0] = 0xEF
    #     PktBuf[1] = 0xEF
    #     PktBuf[2] = (MsgLen >> 8) & 0xFF
    #     PktBuf[3] = MsgLen & 0xFF
    #     PktBuf[4] = (int(MsgID)) >> 8 & 0xFF
    #     PktBuf[5] = int(MsgID) & 0xFF
    #     PktBuf[6] = (int(self.SessionID) >> 8) & 0xFF
    #     PktBuf[7] = int(self.SessionID) & 0xFF
    #     for i in range(MsgLen):
    #         PktBuf[8 + i] = ord(MsgBody[i])
    #     # for i in range(8 + MsgLen, PACKET_SIZE):
    #     #     PktBuf[i] = 0x00
    #     self.Lib.PPCS_PktSend.argtypes = [
    #         ctypes.c_int, 
    #         ctypes.c_char, 
    #         ctypes.POINTER(ctypes.c_char), 
    #         ctypes.c_int
    #     ]
    #     self.Lib.PPCS_PktSend.restype = ctypes.c_int
    #     ret = self.Lib.PPCS_PktSend(
    #         self.SessionID, 
    #         ctypes.c_char(int(Channel)), 
    #         ctypes.POINTER(ctypes.c_char)(PktBuf), 
    #         ctypes.c_int(PktSize)
    #     )
    #     logger.info(f"Done: {ret}")
    #     return ret