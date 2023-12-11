#version: 1.0.2
#truongbv

import logging
import json

from utils.ppcs.ppcs import LibPPCS
from utils.msg_api import MsgID

from datetime import datetime, timedelta
from datetime import time as dtime
import time

#log: .debug, .info, .critical, .error
#DEBUG < INFO < WARNING < ERROR < CRITICAL
logger = logging.getLogger(__name__)
log_formatter = logging.Formatter('%(levelname)-8s [%(filename)-13s:%(funcName)-12s] %(message)s')
log_handler = logging.StreamHandler()
log_handler.setFormatter(log_formatter)
logger.addHandler(log_handler)
logger.setLevel(logging.DEBUG)
####

class BaseTest:
    def __init__(self, ppcs_cfg, msg_login):
        self.msgID = MsgID()
        self.msgLogin = msg_login
        self.msgResponse = None
        #{"device_id": "", "init_string": ""}
        self.P2P = LibPPCS()
        self.P2P.device_id = ppcs_cfg["device_id"]
        self.P2P.init_string = ppcs_cfg["init_string"]

    def login(self):
        ret = self.P2P.ppcs_init_api()
        if(ret < 0):
            logger.error(f"P2P init failed. ({ret})")
            return -1
        ret = self.P2P.ppcs_set_get_api(self.msgID.LOGIN, self.msgLogin)
        if ret < 0:
            logger.error(f"P2P login failed. ({ret})")
            return -1
        return 0

    def testcase(self, msg_id, msg_body, get_type=False):
        ret = self.login()
        if(ret < 0):
            logger.error(f"TC init failed. ({ret})")
            return -1
        ret = self.P2P.ppcs_set_get_api(msg_id, msg_body, get_type)
        if get_type == False and ret < 0:
            logger.error(f"TC set failed. ({ret})")
        elif get_type == True and type(ret) != dict:
            logger.error(f"TC get info failed")
        if type(ret) == dict:
            self.msgResponse = ret
            ret = 0
        self.P2P.ppcs_deinit_api()
        return ret
    
    def testcase_run(self, data):
        # logger.info(f"Read datatest:\n{data}")

        tc_name = data["testcase_name"]
        tc_type = data["type_info"]
        tc_cfg  = data["type_cfg"]
        tc_msg  = data["msg_set"]        
        tc_msg_id   = int(data["msg_id"])
        tc_msg_val  = data["msg_val"]
        tc_result   = data["result_expect"]
        tc_msg_set  = json.dumps(tc_msg)

        logger.info(f"call testcase: {tc_name}")

        ret = 0
        type_cfg = True if tc_cfg == "get" else False              
        ret = self.testcase(tc_msg_id, tc_msg_set, type_cfg)
        if(ret < 0):
            logger.error(f"{tc_cfg} {tc_msg_id} failed. ({ret})")
        
        if type_cfg:
            if len(tc_msg_val) == 0 or self.msgResponse == None:
                logger.error(f"msg or res is empty!")
                ret = -1
            else:
                ret = 0
                for key, value in tc_msg_val.items():
                    if key not in self.msgResponse:
                        logger.error(f"key '{key}' not in msg response of camera")
                        ret = -1
                        continue
                    if value != self.msgResponse[key]:
                        logger.error(f"{key}: {value} != {self.msgResponse[key]}")
                        ret = -1

        if tc_result == "FALSE":
            ret = 0 if ret < 0 else -1
        logger.info(f"testcase: {tc_name} done")
        return ret


class DEVICE_INFO(BaseTest):
    def __init__(self, ppcs_cfg, msg_login):
        super().__init__(ppcs_cfg, msg_login)
        logger.info("Init DEVICE_INFO")
    # def testcase():
    #     print("not override")

class WIFI(BaseTest):
    def __init__(self, ppcs_cfg, msg_login):
        super().__init__(ppcs_cfg, msg_login)
        logger.info("Init WIFI")

    def testcase_run(self, data):
        tc_name = data["testcase_name"]
        tc_type = data["type_info"]
        tc_cfg  = data["type_cfg"]
        tc_msg  = data["msg_set"]        
        tc_msg_id   = int(data["msg_id"])
        tc_msg_val  = data["msg_val"]
        tc_result   = data["result_expect"]
        tc_msg_set  = json.dumps(tc_msg)

        logger.info(f"call testcase: {tc_name}")

        ret = 0
        type_cfg = True if tc_cfg == "get" else False
        ret = self.testcase(tc_msg_id, tc_msg_set, type_cfg)
        if(ret < 0):
            logger.error(f"{tc_cfg} {tc_msg_id} failed. ({ret})")
        
        if type_cfg == True and self.msgID.WIFI_SCAN == tc_msg_id:
            if len(tc_msg_val) == 0 or self.msgResponse == None:
                logger.error(f"msg or res is empty!")
                ret = -1
            else:
                ret = 0
                list_ssid_val = list(tc_msg_val["ssid"])
                list_ssid_cam = []
                for element in self.msgResponse["wifi"]:
                    list_ssid_cam.append(element["ssid"])
                list_intersection =  set(list_ssid_cam).intersection(list_ssid_val)
                count = len(list_intersection)
                if count > 0:
                    logger.info(f"wifi found: {list_intersection}")
                    if count != len(list_ssid_val):
                        logger.warn(f"wifi not found: {set(list_ssid_val) - list_intersection}")
                        # ret = -1
                else:
                    logger.error(f"wifi not found: {list_ssid_val}")
                    ret = -1

        if tc_result == "FALSE":
            ret = 0 if ret < 0 else -1
        logger.info(f"testcase: {tc_name} done")
        return ret

class MOTION(BaseTest):
    def __init__(self, ppcs_cfg, msg_login):
        super().__init__(ppcs_cfg, msg_login)
        logger.info("Init MOTION")

    # override testcase-func of BaseTest-class for type motion
    def testcase(self, msg_id, msg_body, get_type=False):
        ret = self.login()
        if(ret < 0):
            logger.error(f"TC init failed. ({ret})")
            return -1
        ret = self.P2P.ppcs_set_get_api(msg_id, msg_body, get_type)
        if get_type == False and ret < 0:
            logger.error(f"TC set failed. ({ret})")
        elif get_type == True and type(ret) != dict:
            logger.error(f"TC get info failed")
        if type(ret) == dict:
            self.msgResponse = ret["motion_detect"] #special field
            ret = 0
        self.P2P.ppcs_deinit_api()
        return ret


class RECORD(BaseTest):
    def __init__(self, ppcs_cfg, msg_login):
        super().__init__(ppcs_cfg, msg_login)
        logger.info("Init RECORD")

        self.record_cache = ".record_cache.josn"
        self.content_cache = {
            "record_enable": 0,
            "record_mode": 0,
            "start_time": 0,
            "end_time": 0
        }
        self.record_modes = {
            "OFF": -1, 
            "ALWAYS": 0, "SCHEDULE": 1, "EVENT": 2, 
            "FAIL": 3
        }

    # override testcase-func of BaseTest-class for type motion
    def testcase(self, msg_id, msg_body, get_type=False, reset_record=False, params=None):
        ret = self.login()
        if(ret < 0):
            logger.error(f"TC init failed. ({ret})")
            return -1
        if reset_record:
            msg_off = json.dumps({"record": -1})
            ret = self.P2P.ppcs_set_get_api(msg_id, msg_off)
            time.sleep(2) # wait 2s
            if(ret < 0):
                logger.error(f"Turn off record failed. ({ret})")

            if params != None and self.record_modes["SCHEDULE"] == msg_body["record"]:
                ret = self.P2P.ppcs_set_get_api(self.msgID.SET_RECORD_SCHEDULE, params)
            if params != None and self.record_modes["ALWAYS"] == msg_body["record"]:
                ret = self.P2P.ppcs_set_get_api(self.msgID.SET_RECORD_SCHEDULE, params)
            
            self.content_cache["record_mode"] = msg_body["record"]
        if ret >= 0:
            ret = self.P2P.ppcs_set_get_api(msg_id, msg_body, get_type)
        if get_type == False and ret < 0:
            logger.error(f"TC set failed. ({ret})")
        elif get_type == True and type(ret) != dict:
            logger.error(f"TC get info failed")
        if type(ret) == dict:
            self.msgResponse = ret["record"] #special field
            ret = 0
        self.P2P.ppcs_deinit_api()
        return ret
    
    
    def testcase_run(self, data):
        tc_name = data["testcase_name"]
        tc_type = data["type_info"]
        tc_cfg  = data["type_cfg"]
        tc_msg  = data["msg_set"]        
        tc_msg_id   = int(data["msg_id"])
        tc_msg_val  = data["msg_val"]
        tc_result   = data["result_expect"]
        tc_msg_set  = json.dumps(tc_msg)

        logger.info(f"call testcase: {tc_name}")

        ret = 0


        type_cfg = False if tc_cfg == "set" else True
        reset_record = False
        if self.msgID.RECORD == tc_msg_id and tc_msg["record"] != -1:
            reset_record = True

        ret = self.testcase(tc_msg_id, tc_msg_set, type_cfg, reset_record)
        if(ret < 0):
            logger.error(f"{tc_cfg} {tc_msg_id} failed. ({ret})")
        
        # if type_cfg:
        #     if len(tc_msg_val) == 0 or self.msgResponse == None:
        #         logger.error(f"msg or res is empty!")
        #         ret = -1
        #     else:
        #         ret = 0
        #         for key, value in tc_msg_val.items():
        #             if key not in self.msgResponse:
        #                 logger.error(f"key '{key}' not in msg response of camera")
        #                 ret = -1
        #                 continue
        #             if value != self.msgResponse[key]:
        #                 logger.error(f"{key}: {value} != {self.msgResponse[key]}")
        #                 ret = -1

        if tc_result == "FALSE":
            ret = 0 if ret < 0 else -1
        logger.info(f"testcase: {tc_name} done")
        return ret