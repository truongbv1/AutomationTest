from PPCS_API import PPCSAPI
from Handle_API import DEVICE_INFO, WIFI, RECORD
from Msg_API import Msg_API
import logging
import json
import time
# import datetime
from datetime import datetime, timedelta
import sys


#log: .debug, .info, .critical, .error
logging.basicConfig(
    format='%(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', 
    level=logging.DEBUG
)
log = logging.getLogger(__name__)

# ERROR CODE LOCAL
ERROR_TESTAPI_INIT_P2P  = -1100
ERROR_TESTAPI_LOGIN_P2P = -1101
ERROR_TESTAPI_TEST_CASE = -1102



P2P_LIB_DLL_PATH     = "Libs/LIB_PPCS_API.dll"
P2P_LIB_SO_PATH      = "Libs/LIB_PPCS_API.so"
CONFIGS_PATH         = "Configs/configs.json"
MSG_API_FILE         = "APIList"
VAL_API_FILE         = "Validation"

class Test_API:
    def __init__(self):
        p2p_lib_path = P2P_LIB_DLL_PATH
        if sys.platform == "linux":
            p2p_lib_path = P2P_LIB_SO_PATH
        self.P2P = PPCSAPI(p2p_lib_path)
        self.P2P.pathAPIList = MSG_API_FILE
        self.P2P_channel = 0
        self.MSGID = Msg_API()

        self.msg_login_json = {"user": "admin", "password": "vnpt@123"} #default
        self.msg_login_str = json.dumps(self.msg_login_json)
        ret = self.parse_configs()
        if ret < 0:
            log.error("setup configs failed!")
            exit()
        log.info("Test API class init done")

    def parse_configs(self):
        fd = open(CONFIGS_PATH, 'r')
        conf_str = fd.read()
        fd.close()

        conf_json = None
        try:
            conf_json = json.loads(conf_str)
        except ValueError:
            log.error("Configs not a json object. Parse failed")
            return -1

        target_cfg = str(conf_json["select_config"])
        if target_cfg == "":
            log.error("'select_config' failed")
            return -1
        cam_cfg_json = conf_json[target_cfg]

        u = str(cam_cfg_json["login_usr"])
        p = str(cam_cfg_json["login_pwd"])
        d = str(cam_cfg_json["p2p_did"])
        i = str(cam_cfg_json["p2p_init_str"])
        if u == "" or p == "" or d == "" or i == "":
            log.error(f"get info '{target_cfg}' failed")
            return -1

        self.msg_login_json["user"]     = u
        self.msg_login_json["password"] = p
        self.P2P.DID                    = d
        self.P2P.InitString             = i

        self.msg_login_str = json.dumps(self.msg_login_json)
        return 0

    def P2P_INIT(self):
        ret = self.P2P.PY_PPCS_GetAPIInformation()        
        ret = self.P2P.PY_PPCS_Initialize()
        ret = self.P2P.PY_PPCS_NetworkDetect()
        if ret < 0:
            log.error("PY_PPCS_NetworkDetect failed")
            return ret
        
        ret = self.P2P.PY_PPCS_Connect('z', 0)
        if ret < 0:
            log.error("PY_PPCS_Connect failed")
            return ret
        
        ret = self.P2P.PY_PPCS_Check()
        if ret < 0:
            log.error("PY_PPCS_Check failed")
            return ret
        log.info("INIT P2P done")
        return 0
    
    def P2P_DEINIT(self):
        ret = self.P2P.PY_PPCS_Close()
        if ret < 0:
            log.error("PY_PPCS_Close failed")
            return ret
        
        ret = self.P2P.PY_PPCS_DeInitialize()
        if ret < 0:
            log.error("PY_PPCS_DeInitialize failed")
            return ret
        log.info("DEINIT P2P done")
        return 0

    def P2P_SET_GET_API(self, MsgID=1050, subMsgID="", inMsgBody="", outMsgBody=False, timeout=3000):
        # msg_out = None
        ret = self.P2P.PY_PPCS_Write(self.P2P_channel, MsgID, subMsgID, inMsgBody)
        if ret < 0:
            log.error("PY_PPCS_Write failed")
            return ret
        
        msg_byte_str = self.P2P.PY_PPCS_Read(self.P2P_channel, MsgID, timeout)
        msg_json = json.loads(msg_byte_str)

        ret = msg_json['status']
        if subMsgID != "":
            log.info(f"===> Result API {MsgID}_{subMsgID}: {ret}")
        else:
            log.info(f"===> Result API {MsgID}: {ret}")

        if outMsgBody == True and ret >= 0:
            ret = msg_json
        return ret
    
    def CHECK_DEVICE_INFO(self, MsgID=1050, fileVal="", keyword="all", info_type="DEVICE_INFO", timeout=3000):
        """
        type: device info, scan_wifi, ...
        """
        # INFO_TYPES = ["DEVICE_INFO", "SCAN_WIFI"]

        res_cam_json = self.P2P_SET_GET_API(MsgID, outMsgBody=True, timeout=timeout)
        if type(res_cam_json) != dict:
            log.error(f"Get info failed")
            return -1
        if fileVal == "":
            log.error(f"path file val is null")
            return -1
        pathDeviceInfo = VAL_API_FILE + "/" + fileVal
        fd = open(pathDeviceInfo, 'r')
        body = fd.read()
        fd.close()
        body_val_json = json.loads(body)

        ret = 0
        if info_type == "DEVICE_INFO":
            log.info(f"P: {info_type}")
            device_info = DEVICE_INFO()
            ret = device_info.validation_info(res_cam_json, body_val_json, keyword)
            
        elif info_type == "SCAN_WIFI":
            wifi_info = WIFI()            
            ret = wifi_info.scan_wifi_validation(res_cam_json, body_val_json, keyword)
        else:
            log.error(f"not support type '{info_type}'")
            ret = -1

        if ret < 0:
            log.error(f"Validation info failed!")
        return ret
    ############################################################################################



    ############################################################################################
    def TEST_CASE_SET(self, name="", MsgID=1050, subMsgID="", timeout=3000):
        log.info(f"TEST_CASE: {name}")
        ret = self.P2P_INIT()
        if(ret < 0):
            log.error(f"P2P_Init failed. ({ret})")
            return ERROR_TESTAPI_INIT_P2P
        
        # login p2p
        # ret = self.P2P_SET_GET_API(1111)
        # ret = self.P2P_SET_GET_API(1111, "app.txt")
        ret = self.P2P_SET_GET_API(self.MSGID.LOGIN, inMsgBody=self.msg_login_str)
        if ret < 0:
            log.error(f"Login p2p failed. ({ret})")
            self.P2P_DEINIT()
            return ERROR_TESTAPI_LOGIN_P2P
        
        # test api msgid
        ret = self.P2P_SET_GET_API(MsgID, subMsgID, timeout=timeout)
        if ret < 0:
            log.error(f"Test case failed. ({ret})")
            self.P2P_DEINIT()
            return ERROR_TESTAPI_TEST_CASE
        
        self.P2P_DEINIT()
        log.info(f"TEST_CASE: {name} done")
        return 0
    
    def TEST_CASE_GET(self, name="", MsgID=1050, fileVal="", keyword="all", info_type="DEVICE_INFO", timeout=3000):
        log.info(f"TEST_CASE: {name}")
        ret = self.P2P_INIT()
        if(ret < 0):
            log.error(f"P2P_Init failed. ({ret})")
            return ERROR_TESTAPI_INIT_P2P
        
        # login p2p
        ret = self.P2P_SET_GET_API(self.MSGID.LOGIN, inMsgBody=self.msg_login_str)
        if ret < 0:
            log.error(f"Login p2p failed. ({ret})")
            self.P2P_DEINIT()
            return ERROR_TESTAPI_LOGIN_P2P
        
        # test api msgid
        ret = self.CHECK_DEVICE_INFO(MsgID, fileVal, keyword, info_type, timeout)
        if ret < 0:
            log.error(f"Test case failed. ({ret})")
            self.P2P_DEINIT()
            return ERROR_TESTAPI_TEST_CASE
        
        self.P2P_DEINIT()
        log.info(f"TEST_CASE: {name} done")
        return 0
    
    ############################################################################################
    ############################################################################################


    ############################################################################
    def TEST_CASE_RECORD(self, name="", test_type="GET", record_mode="ALWAYS", 
        duration=1, start_time="00:00", end_time="23:59", check_flag=0,
        msgID=-1, subMsgID="", timeout=3000):
        """
        start_time: start time for always_record with check_flag=1
        end_time: end time for always_record with check_flag=1: only check result in [start:end] time
        duration: (min) duration for always_record with check_flag=0: auto setup always record mode and check result
        msgID: msg API for set schedule record
        subMsgID: extension of msgID 
        """
        RECORD_API = RECORD()

        flag_set_get_always = False
        start_tmp = datetime.strptime(start_time, '%H:%M')
        end_tmp = datetime.strptime(end_time, '%H:%M')

        time_wait = 2 #2s
        duration = duration*60 #min -> second
        log.info(f"TEST_CASE: {name}")
        if record_mode not in RECORD_API.record_modes:
            log.error(f"RECORD MODE '{record_mode}' not support")
            return -1        
        
        ret = self.P2P_INIT()
        if(ret < 0):
            log.error(f"P2P_Init failed. ({ret})")
            return ERROR_TESTAPI_INIT_P2P
 
        ret = self.P2P_SET_GET_API(self.MSGID.LOGIN, inMsgBody=self.msg_login_str)
        if(ret < 0):
            log.error(f"Login p2p failed. ({ret})")
            self.P2P_DEINIT()
            return ERROR_TESTAPI_LOGIN_P2P
        

        if test_type == "SET":
            if record_mode != "OFF":
                log.info(f"Turn off record before turn on mode {record_mode}_RECORD")
                RECORD_API.msg_set_mode["record"] = -1
                msg_set_mode = json.dumps(RECORD_API.msg_set_mode)
                ret = self.P2P_SET_GET_API(self.MSGID.RECORD, inMsgBody=msg_set_mode)
                if(ret < 0):
                    log.error(f"Turn off record failed. ({ret})")
                    self.P2P_DEINIT()
                    return ERROR_TESTAPI_TEST_CASE

                if record_mode == "SCHEDULE" and msgID != -1:
                    log.info(f"Set record schedule: {msgID}")
                    ret = self.P2P_SET_GET_API(msgID, subMsgID)
                    if(ret < 0):
                        log.error(f"Set record schedule failed. ({ret})")
                        self.P2P_DEINIT()
                        return ERROR_TESTAPI_TEST_CASE
                    
                if record_mode == "ALWAYS" and check_flag == 0:
                    start_tmp = datetime.today()
                    time.sleep(10) # wait 10s

                time.sleep(time_wait) # wait 2s

            log.info(f"Set record mode: {record_mode}")
            RECORD_API.msg_set_mode["record"] = RECORD_API.record_modes[record_mode]
            msg_set_mode = json.dumps(RECORD_API.msg_set_mode)
            ret = self.P2P_SET_GET_API(self.MSGID.RECORD, inMsgBody=msg_set_mode)
            if(ret < 0):
                log.error(f"Turn {record_mode} record failed. ({ret})")
                self.P2P_DEINIT()
                return ERROR_TESTAPI_TEST_CASE
            
            if record_mode == "ALWAYS" and check_flag == 0:
                log.info(f"record always in {duration}s: waiting ... ")
                time.sleep(duration) # waiting ...

                RECORD_API.msg_set_mode["record"] = -1
                msg_set_mode = json.dumps(RECORD_API.msg_set_mode)
                ret = self.P2P_SET_GET_API(self.MSGID.RECORD, inMsgBody=msg_set_mode)
                if(ret < 0):
                    log.error(f"Turn off record failed. ({ret})")
                    self.P2P_DEINIT()
                    return ERROR_TESTAPI_TEST_CASE
                
                end_tmp = datetime.today()
                flag_set_get_always = True
                time.sleep(time_wait) # wait
            
        if test_type == "GET" or flag_set_get_always:
            res_cam_json = self.P2P_SET_GET_API(self.MSGID.GET_RECORD_INFO, outMsgBody=True, timeout=timeout)
            if type(res_cam_json) != dict:
                log.error(f"Get info failed")
                return -1
            
            RECORD_API.parse_record_info(res_cam_json)

            if ((RECORD_API.record_modes[record_mode] < 0) == RECORD_API.record_enable):
                if flag_set_get_always:
                    log.warn(f"Check record is '{record_mode}' but 'record_enable'={RECORD_API.record_enable}")
                else:
                    log.error(f"Check record is '{record_mode}' but 'record_enable'={RECORD_API.record_enable}")
                    return -1
            
            # if RECORD_API.record_enable == False:
            #     log.info(f"Record turn off")
            #     return 0
            
            if RECORD_API.record_mode != RECORD_API.record_modes[record_mode]:
                log.error(f"Check record is '{record_mode}' but 'record_mode'={RECORD_API.record_mode}")
                return -1
            
            error = 0
            for msg, day in RECORD_API.list_msg_api:
                list_videos = self.P2P_SET_GET_API(self.MSGID.LIST_VIDEO, inMsgBody=msg, outMsgBody=True, timeout=timeout)
                if type(list_videos) != dict:
                    log.error(f"Get list videos failed")
                    error = -1
                    continue

                if record_mode == "SCHEDULE":             
                    if RECORD_API.check_record_schedule(list_videos, day) < 0:                        
                        error = -1                    
                
                elif record_mode == "ALWAYS":
                    if check_flag:
                        start_tmp = datetime.combine(datetime.today(), datetime.time(start_tmp))
                        end_tmp = datetime.combine(datetime.today(), datetime.time(end_tmp))
                    start_timestamp = int(start_tmp.timestamp())
                    end_timestamp = int(end_tmp.timestamp())
                    if RECORD_API.check_record_always(list_videos, start_timestamp, end_timestamp, duration) < 0:
                        error = -1
                else:
                    log.warn(f"not support mode: {record_mode}")

            if error < 0:
                log.error(f"Record {record_mode}: incorrect!")
                return -1
            
        if test_type not in ["SET", "GET"]:
            log.error(f"not support {test_type}")
            return -1
        
        return 0




    
    ############################################################################
