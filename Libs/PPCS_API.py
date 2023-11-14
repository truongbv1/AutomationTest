import ctypes
import logging
import socket
import struct
import json

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

#log: .debug, .info, .critical, .error
logging.basicConfig(
    format="%(levelname)-8s [%(filename)s:%(lineno)d] %(message)s", 
    level=logging.DEBUG
)
log = logging.getLogger(__name__)
####
class PPCSAPI:
    def __init__(self, libPath="PPCS_API.dll"):
        self.Lib = ctypes.cdll.LoadLibrary(libPath)
        self.InitString = ""
        self.DID        = ""
        self.SessionID  = 0
        self.pathAPIList = ""
        self.max_pk_size = MAX_PK_SIZE
        self.header_size = HEADER_SIZE
        self.packet_size = PACKET_SIZE
        log.info("Init class PPCS done")

    def check_configs(self):
        if self.InitString == None or self.DID == None:
            log.error("Error InitString or DID is None!")
            return -1
        return 0


    def PY_PPCS_Initialize(self):
        if self.check_configs() < 0:
            log.error(f"PPCS_Initialize: {ERROR_PPCS_CONFIGS}")
            return ERROR_PPCS_CONFIGS
        self.Lib.PPCS_Initialize.argtypes = [ctypes.c_char_p]
        self.Lib.PPCS_Initialize.restype = ctypes.c_int
        ret = self.Lib.PPCS_Initialize(str.encode(self.InitString))
        log.info(f"PPCS_Initialize: {ret}")
        return ret
    
    def PY_PPCS_DeInitialize(self):
        self.Lib.PPCS_DeInitialize.argtypes = []
        res = self.Lib.PPCS_DeInitialize()
        log.info(f"PPCS_DeInitialize: {res}")
        return res
    
    def PY_PPCS_GetAPIInformation(self):
        self.Lib.PPCS_GetAPIInformation.restype = ctypes.c_char_p
        res = self.Lib.PPCS_GetAPIInformation()
        log.info(f"PPCS_GetAPIInformation: {res}")
        return res

    def PY_PPCS_ForceClose(self):
        self.Lib.PPCS_ForceClose.argtypes = [ctypes.c_int]
        res = self.Lib.PPCS_ForceClose(self.SessionID)
        log.info(f"PPCS_ForceClose: {res}")
        return res

    def PY_PPCS_Close(self):
        self.Lib.PPCS_Close.argtypes = [ctypes.c_int]
        res = self.Lib.PPCS_Close(self.SessionID)
        log.info(f"PPCS_Close: {res}")
        return res
    
    def PY_PPCS_NetworkDetect(self):
        NetInfo = PPCS_NetInfo()
        self.Lib.PPCS_NetworkDetect.argtypes = [ctypes.POINTER(PPCS_NetInfo), ctypes.c_int]
        ret = self.Lib.PPCS_NetworkDetect(NetInfo, 0)
        log.info(f"FlagHostResolved:   0x{ord(NetInfo.FlagHostResolved):02x}")
        log.info(f"FlagInternet:       0x{ord(NetInfo.FlagInternet):02x}")
        log.info(f"FlagServerHello:    0x{ord(NetInfo.FlagServerHello):02x}")
        log.info(f"NAT_Type:           0x{ord(NetInfo.NAT_Type):02x}")
        log.info(f"MyLanIP:            {NetInfo.MyLanIP}")
        log.info(f"MyWanIP:            {NetInfo.MyWanIP}")
        log.info(f"PPCS_NetworkDetect: {ret}")
        return ret
    
    def PY_PPCS_Connect(self, EnableLanSearch, UDP_Port):
        if self.check_configs() < 0:
            log.error(f"PPCS_DID: {ERROR_PPCS_CONFIGS}")
            return ERROR_PPCS_CONFIGS
        self.Lib.PPCS_Connect.argtypes = [ctypes.c_char_p, ctypes.c_char, ctypes.c_int]
        self.Lib.PPCS_Connect.restype = ctypes.c_int
        ret = self.Lib.PPCS_Connect(str.encode(self.DID), ctypes.c_char(str.encode(EnableLanSearch)), int(UDP_Port))
        log.info(f"EnableLanSearch: {str.encode(EnableLanSearch)}")
        log.info(f"PPCS_Connect: {ret}")
        self.SessionID = ret
        return ret
    
    def PY_PPCS_Check(self):
        Session = PPCS_Session()
        self.Lib.PPCS_Check.argtypes = [ctypes.c_int, ctypes.POINTER(PPCS_Session)]
        self.Lib.PPCS_Check.restype = ctypes.c_int
        ret = self.Lib.PPCS_Check(self.SessionID, Session)
        log.info(f"PPCS_Check: {ret}")
        if ret < 0:
            log.error("Check failed")
            return ret
        log.info(f"Skt:         {Session.Skt}")
        log.info(f"RemoteAddr:  {socket.inet_ntoa(struct.pack('I', Session.RemoteAddr.sin_addr.s_addr))}:{Session.RemoteAddr.sin_port}")
        log.info(f"MyLocalAddr: {socket.inet_ntoa(struct.pack('I', Session.MyLocalAddr.sin_addr.s_addr))}:{Session.MyLocalAddr.sin_port}")
        log.info(f"MyWanAddr:   {socket.inet_ntoa(struct.pack('I', Session.MyWanAddr.sin_addr.s_addr))}:{Session.MyWanAddr.sin_port}")
        log.info(f"ConnectTime: {Session.ConnectTime}")
        log.info(f"DID:         {Session.DID}")
        log.info(f"bCorD:       0x{ord(Session.bCorD):02x}")
        log.info(f"bMode:       0x{ord(Session.bMode):02x}")
        return ret
    
    def PY_PPCS_Read_Byte(self, Channel, TimeOut_ms):
        DataSize = ctypes.c_int(1)
        DataBuf = (ctypes.c_char * 1)()
        TimeOut_ms_1 = int(int(TimeOut_ms) / 10)
        log.info(f"TimeOut_ms_1: {TimeOut_ms_1}")
        self.Lib.PPCS_Read.argtypes = [
            ctypes.c_int, 
            ctypes.c_char, 
            ctypes.POINTER(ctypes.c_char), 
            ctypes.POINTER(ctypes.c_int), 
            ctypes.c_uint
        ]
        for k in range(50):
            ret = self.Lib.PPCS_Read(
                ctypes.c_int(self.SessionID), 
                ctypes.c_char(int(Channel)), 
                ctypes.POINTER(ctypes.c_char)(DataBuf), 
                ctypes.POINTER(ctypes.c_int)(DataSize), 
                ctypes.c_uint(int(TimeOut_ms_1))
            )
            if DataSize.value > 0:
                break
        log.info(f"DataBuf:     {DataBuf}")
        log.info(f"DataSize:    {DataSize.value}")
        log.info(f"Read_Byte:   {ret}")
        return ret
    

    def PY_PPCS_Read(self, Channel, MsgID, TimeOut_ms):        
        TimeOut_ms_1 = 500
        Retry = int(TimeOut_ms / 100)

        DataSize = ctypes.c_int(self.max_pk_size)
        DataBuf = (ctypes.c_char * self.max_pk_size)()   
        self.Lib.PPCS_Read.argtypes = [
            ctypes.c_int, 
            ctypes.c_char, 
            ctypes.POINTER(ctypes.c_char), 
            ctypes.POINTER(ctypes.c_int), 
            ctypes.c_uint
        ]
        self.Lib.PPCS_Read.restype = ctypes.c_int

        for k in range(Retry):
            DataSize = ctypes.c_int(self.max_pk_size)
            ret = self.Lib.PPCS_Read(
                ctypes.c_int(self.SessionID), 
                ctypes.c_char(int(Channel)), 
                ctypes.POINTER(ctypes.c_char)(DataBuf), 
                ctypes.POINTER(ctypes.c_int)(DataSize), 
                ctypes.c_uint(int(TimeOut_ms_1))
            )
            if DataSize.value > 0:
                break

        MsgLen = (ord(DataBuf[2]) << 8) + ord(DataBuf[3])       
        MsgIDRead = (ord(DataBuf[4]) << 8) + ord(DataBuf[5])
        MsgSessionID = (ord(DataBuf[6]) << 8) + ord(DataBuf[7])
        
        #debug
        log.info(f"TimeOut_ms:      {TimeOut_ms}")
        log.info(f"TimeOut_ms_1:    {TimeOut_ms_1}")
        log.info(f"Retry:           {Retry}")
        log.info(f"Channel:         {Channel}")
        log.info(f"SessionID:       {self.SessionID}")
        log.info(f"DataSize:        {DataSize.value}")
        log.info(f"DataBuf:         {DataBuf}")
        log.info(f"PPCS_Read:       {ret}")
        # log.debug(f"MsgLen:       {MsgLen}")
        # log.debug(f"MsgIDRead:    {MsgIDRead}")
        # log.debug(f"SessionID:    {MsgSessionID}")
        if DataSize.value < 8:
            log.error("Wrong size of read")
            return ERROR_PPCS_READ_SIZE
        if ord(DataBuf[0]) != 0xEF or ord(DataBuf[1]) != 0xEF:
            log.error("Wrong Mask Number")
            return ERROR_PPCS_READ_MASK
        if MsgIDRead != int(MsgID):
            log.error("Wrong Msg Id")
            return ERROR_PPCS_READ_MSGID
        
        res = (ctypes.c_char * (int(DataSize.value) - 8))()
        i = 8
        while (ord(DataBuf[i]) > 0x00  and ord(DataBuf[i]) < 0x7f):
            res[i - 8] = ord(DataBuf[i])
            i += 1
        log.info(f"res: {res.value}, Length: {len(res)}")

        return res.value
    

    def PY_PPCS_Write(self, Channel, MsgID, subMsgID="", MsgBody=""):
        pathMsgIDFile = str(self.pathAPIList) + "/" + str(MsgID)
        if subMsgID != "":
            pathMsgIDFile = pathMsgIDFile + '_' + str(subMsgID)
        if MsgBody == "":
            fd = open(pathMsgIDFile, 'r')
            MsgBody = fd.read()
            fd.close()
        log.info(f"MsgID Body:\n{MsgBody}")
        try:
            json.loads(MsgBody)
        except ValueError:
            log.error("MsgID body not a json")
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
        DataBuf[6] = (int(self.SessionID) >> 8) & 0xFF
        DataBuf[7] = int(self.SessionID) & 0xFF
        for i in range(MsgLen):
            DataBuf[8 + i] = ord(MsgBody[i])
        self.Lib.PPCS_Write.argtypes = [
            ctypes.c_int, 
            ctypes.c_char, 
            ctypes.POINTER(ctypes.c_char), 
            ctypes.c_int
        ]        
        self.Lib.PPCS_Write.restype = ctypes.c_int

        ret = self.Lib.PPCS_Write(
            ctypes.c_int(self.SessionID), 
            ctypes.c_char(int(Channel)), 
            ctypes.POINTER(ctypes.c_char)(DataBuf), 
            ctypes.c_int(DataSize)
        )

        log.info(f"PPCS_Write: {ret}")
        return ret


    def PY_PPCS_PktRecv(self, Channel, MsgID, TimeOut_ms):
        PktSize = ctypes.c_int(PACKET_SIZE)
        PktBuf = (ctypes.c_char * PACKET_SIZE)()
        TimeOut_ms_1 = int(TimeOut_ms) / 10
        TimeOut_s_1 = int(TimeOut_ms) / 10000
        self.Lib.PPCS_PktRecv.argtypes = [
            ctypes.c_int, 
            ctypes.c_char, 
            ctypes.POINTER(ctypes.c_char), 
            ctypes.POINTER(ctypes.c_int), 
            ctypes.c_uint
        ]
        self.Lib.PPCS_PktRecv.restype = ctypes.c_int

        # for k in range(50):
        ret = self.Lib.PPCS_PktRecv(
            self.SessionID, 
            ctypes.c_char(int(Channel)), 
            ctypes.POINTER(ctypes.c_char)(PktBuf), 
            ctypes.POINTER(ctypes.c_int)(PktSize), 
            int(TimeOut_ms)
        )
        #     if PktSize.value > 0:
        #         break
        MsgLen = (ord(PktBuf[2]) << 8) + ord(PktBuf[3])        
        MsgIDRead = (ord(PktBuf[4]) << 8) + ord(PktBuf[5])
        MsgSessionID = (ord(PktBuf[6]) << 8) + ord(PktBuf[7])

        log.info(f"TimeOut_ms_1: {TimeOut_ms_1}")
        log.info(f"TimeOut_s_1:  {TimeOut_s_1}")
        log.info(f"PktSize:      {PktSize.value}")
        log.info(f"PktBuf:       {PktBuf}")
        log.info(f"PPCS_PktRecv: {ret}")
        log.info(f"MsgLen:       {MsgLen}")
        log.info(f"MsgIDRead:    {MsgIDRead}")
        log.info(f"SessionID:    {MsgSessionID}")
        if PktSize.value < 8:
            log.error("Wrong size of read")
            return ERROR_PPCS_READ_SIZE
        
        if ord(PktBuf[0]) != 0xEF or ord(PktBuf[1]) != 0xEF:
            log.error("Wrong Mask Number")
            return ERROR_PPCS_READ_MASK
        
        if MsgIDRead != int(MsgID):
            log.error("Wrong Msg Id")
            return ERROR_PPCS_READ_MSGID
        
        res = (ctypes.c_char * (int(PktSize.value) - 8))()
        i = 8
        while ord(PktBuf[i]) > 0x00 and ord(PktBuf[i]) < 0x7f:
            res[i - 8] = ord(PktBuf[i])
            i += 1
        log.info("res: {0}, Length: {1}".format(res.value, len(res)))
        # res = json.loads(res.value)
        # ret = res['status']
        # log.info(f"PPCS_PktRecv: {ret}")
        # return ret
        return res.value
    
    def PY_PPCS_PktSend(self, Channel, MsgID, subMsgID=-1):
        pathMsgIDFile = self.pathAPIList + "/" + str(MsgID)
        if subMsgID != -1:
            pathMsgIDFile = pathMsgIDFile + '_' + str(subMsgID)
        fd = open(pathMsgIDFile, 'r')
        MsgBody = fd.read()
        fd.close()
        log.info(f"MsgID Body:\n{MsgBody}")
        try:
            json.loads(MsgBody)
        except ValueError:
            log.error("MsgID body not a json")
            return -1
        
        MsgLen = len(MsgBody)
        PktSize = MsgLen + HEADER_SIZE
        PktBuf = (ctypes.c_char * PktSize)()
        PktBuf[0] = 0xEF
        PktBuf[1] = 0xEF
        PktBuf[2] = (MsgLen >> 8) & 0xFF
        PktBuf[3] = MsgLen & 0xFF
        PktBuf[4] = (int(MsgID)) >> 8 & 0xFF
        PktBuf[5] = int(MsgID) & 0xFF
        PktBuf[6] = (int(self.SessionID) >> 8) & 0xFF
        PktBuf[7] = int(self.SessionID) & 0xFF
        for i in range(MsgLen):
            PktBuf[8 + i] = ord(MsgBody[i])
        # for i in range(8 + MsgLen, PACKET_SIZE):
        #     PktBuf[i] = 0x00
        self.Lib.PPCS_PktSend.argtypes = [
            ctypes.c_int, 
            ctypes.c_char, 
            ctypes.POINTER(ctypes.c_char), 
            ctypes.c_int
        ]
        self.Lib.PPCS_PktSend.restype = ctypes.c_int
        ret = self.Lib.PPCS_PktSend(
            self.SessionID, 
            ctypes.c_char(int(Channel)), 
            ctypes.POINTER(ctypes.c_char)(PktBuf), 
            ctypes.c_int(PktSize)
        )
        print(f"PPCS_PktSend: {ret}")
        return ret