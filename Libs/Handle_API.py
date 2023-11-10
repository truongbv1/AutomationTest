import logging
import json

from datetime import datetime, timedelta
from datetime import time as dtime

#log: .debug, .info, .critical, .error
logging.basicConfig(
    format='%(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', 
    level=logging.DEBUG
)
log = logging.getLogger(__name__)

###########################################################################################
class DEVICE_INFO:
    def __init__(self):
        log.info("init DEVICE_INFO")

    def validation_info(self, cam_info, val_info, keyword):
        list_keyword = list(str(keyword).split(":"))
        log.info(f"KEYWORD: {len(list_keyword)}, {list_keyword}")
        
        if len(list_keyword) == 1:
            if keyword == "all":
                if cam_info != val_info:
                    log.error(f"check '{keyword}' failed")
                    for key, value in cam_info.items():
                        if value != val_info[key]:
                            log.error(f"{key}: {value} != {val_info[key]}")
                    return -1
            # for common api
            elif cam_info[str(keyword)] != val_info[str(keyword)]:
                log.error(f"check '{keyword}' failed.\n[ {cam_info[str(keyword)]} != {val_info[str(keyword)]} ]")
                return -1
            log.info(f"check '{keyword}' success")

        #for list/array keyword
        else:
            cam_json_tmp = cam_info
            val_json_tmp = val_info
            for key in list_keyword:
                if key in cam_json_tmp and key in val_json_tmp:
                    cam_json_tmp = cam_json_tmp[key]
                    val_json_tmp = val_json_tmp[key]
                else:
                    log.error(f"'{key}' not in {cam_json_tmp} or {val_json_tmp}")
                    return -1
                
            if cam_json_tmp != val_json_tmp:
                log.error(f"check '{keyword}' failed.\n[ {cam_json_tmp} != {val_json_tmp} ]")
                return -1
            else:
                log.info(f"check '{keyword}' success")
        return 0

###########################################################################################
class WIFI:
    def __init__(self):
        self.scan_wifi_checks = {"intersection": 0, "equal": 1}

    def scan_wifi_validation(self, cam_info, val_info, type_check="intersection"):
        if type_check not in  self.scan_wifi_checks:
            log.error(f"wifi not support type_check: {type_check}")
            return -1

        list_ssid_val = list(val_info["ssid"])
        list_ssid_cam = []
        for element in cam_info["wifi"]:
            list_ssid_cam.append(element["ssid"])
        list_intersection =  set(list_ssid_cam).intersection(list_ssid_val)
        count = len(list_intersection)
        if count > 0:
            log.info(f"wifi found: {list_intersection}")
            if self.scan_wifi_checks[type_check] and (count != len(list_ssid_val)):
                log.error(f"wifi not found: {set(list_ssid_val) - list_intersection}")
                return -1
        else:
            log.error(f"wifi not found: {list_ssid_val}")
            return -1

        log.info(f"check 'scan_wifi_{type_check}' success")
        return 0


###########################################################################################
class RECORD:
    def __init__(self):
        # print("init")
        # RECORD_MODE     = ["OFF", "ALWAYS", "SCHEDULE", "EVENT", "FAIL"]
        # TEST_TYPE       = ["GET", "SET"]
        # MSGID_SET_MODE  = 1010
        # MSGID_GET_INFO  = 1059
        # time_wait = 2 #2s
        self.record_modes = {"OFF": -1, "ALWAYS": 0, "SCHEDULE": 1, "EVENT": 2, "FAIL": 3}
        self.msg_set_mode = {"record": -1} #-1 off, 0 always, 1 schedule, 2 event

        self.record_enable = False
        self.record_mode = -1
        self.schedules = []
        self.dayofweek = []
        self.sdoverride = False
        self.cloud = False

        self.list_msg_api = [] #object datetime
        self.msg_get_videos = { "begin": 0, "end":  0, "type": 0, "page": 0 }

    def parse_record_info(self, record_info):
        """
        { 
            "record": {
                "record_enable": true,
                "record_mode": 2,
                "schedules": [ [ "06:48", "06:57" ], [ "07:18", "08:57" ], [ "16:48", "18:57" ] ],
                "dayofweek": [ 0, 1, 2, 5, 6 ],
                "sdoverride": true,
                "cloud": false
            },
            "status": 0
        }
        """
        log.info("parse")
        record = record_info["record"]
        self.record_enable = record["record_enable"]
        self.record_mode = record["record_mode"]        
        self.dayofweek = record["dayofweek"]
        self.sdoverride = record["sdoverride"]
        self.cloud = record["cloud"]
        # self.schedules = []

        now_date = datetime.today()
        now_weekday = (now_date.weekday() + 1) % 7 #Sunday=0, Monday, ..., Saturday=6        

        if self.record_mode == 1: # for schedules
            schs = record["schedules"]
            for s in schs:
                start_time = datetime.strptime(s[0], '%H:%M')
                end_time = datetime.strptime(s[1], '%H:%M')
                start_s = datetime.combine(datetime.today(), datetime.time(start_time))
                end_s = datetime.combine(datetime.today(), datetime.time(end_time))
                self.schedules.append([start_s, end_s])
                # datetime.today() - timedelta(days=1)
            
            weekday_ready = [ wd for wd in self.dayofweek if wd <= now_weekday] #or weekday_ready = self.dayofweek
            log.info(f"now: {now_weekday} => ready with {weekday_ready}")
            for wd in weekday_ready:
                day = now_date - timedelta(days=(now_weekday - wd))
                log.info(f"{day.strftime('%Y-%m-%d')}: {day.strftime('%A')}")\
                # self.dayofweek_ready.append(day)

                # tz = timedelta(hours=7)
                # start_day = datetime.combine(day, dtime(0, 0, 0)) - tz
                # end_day = datetime.combine(day, dtime(23, 59, 59)) - tz
                start_day = datetime.combine(day, dtime(0, 0, 0))
                end_day = datetime.combine(day, dtime(23, 59, 59))
                self.msg_get_videos["begin"] = int(start_day.timestamp())
                self.msg_get_videos["end"] = int(end_day.timestamp())
                self.msg_get_videos["type"] = self.record_mode #schedule
                msg_json = json.dumps(self.msg_get_videos)
                self.list_msg_api.append([msg_json, start_day])

            # log.info(f"list api search: {self.list_msg_api}")
        
        elif self.record_mode == 0:
            # tz = timedelta(hours=7)
            # start_day = datetime.combine(now_date, dtime(0, 0, 0)) - tz
            # end_day = datetime.combine(now_date, dtime(23, 59, 59)) - tz
            start_day = datetime.combine(now_date, dtime(0, 0, 0))
            end_day = datetime.combine(now_date, dtime(23, 59, 59))
            self.msg_get_videos["begin"] = int(start_day.timestamp())
            self.msg_get_videos["end"] = int(end_day.timestamp())
            self.msg_get_videos["type"] = self.record_mode #always
            msg_json = json.dumps(self.msg_get_videos)
            self.list_msg_api.append([msg_json, start_day])

    def check_list_video_record(self, list_info, ts_start, ts_end, duration, delta_duration=3):
        """
        {
            "amount": 253,
            "list": "[ 
                {
                    "name":"media/sdcard/videos/20210620_110505.mp4",
                    "event_type":0,
                    "timestamp":1624187105
                    "duration": 60
                },
                {
                    "name":"/media/sdcard/videos/20210620_112005.mp4",
                    "event_type":1,
                    "timestamp":1624188005
                    "duration": 300
                },
                …
            ]
            "page" : 0,
            "page_total" : 3,
            "status": 0
        }
        """
        count_list = list_info["amount"]
        log.info(f"Total videos: {count_list}")
        if count_list <= 0:
            log.error("List video empty")
            return -1

        count_list = 0
        total_duration = 0
        for video_info in list_info["list"]:
            if ts_start <= int(video_info["timestamp"]) <= ts_end:
                log.info(f"Video: {video_info['name']} (Duration: {video_info['duration']}s)")
                count_list += 1
                total_duration += int(video_info['duration'])

        if count_list <= 0:
            log.error(f"No video in [{ts_start} : {ts_end}]")
            return -1
        
        log.info(f"Total duration: {total_duration}")
        if abs(duration - total_duration) >= delta_duration:
            log.error(f"duration: {duration} != {total_duration} (+/- {delta_duration}s)")
            return -1

        return 0

    def check_record_schedule(self, list_video_info, day=datetime.today()):
        error = 0
        now = datetime.today()
        for s in self.schedules:
            start_s = datetime.combine(day, datetime.time(s[0]))
            end_s = datetime.combine(day, datetime.time(s[1]))
            timestamp_start = int(start_s.timestamp())
            timestamp_end = int(end_s.timestamp())
            if int(now.timestamp()) <= timestamp_end:
                log.warn(f"current time <= end time: {now.strftime('%H:%M')} <= {end_s.strftime('%H:%M')}]")
                continue
            ret = self.check_list_video_record(list_video_info, timestamp_start, timestamp_end, timestamp_end-timestamp_start)
            if ret < 0:
                log.error(f"record schedule failed: [{day.strftime('%Y-%m-%d')}: {start_s.strftime('%H:%M')}->{end_s.strftime('%H:%M')}]")
                error = -1            
        return error

    def check_record_always(self, list_video_info, timestamp_start, timestamp_end, duration):
        """
        duration (second)
        """
        now_st = datetime.today().timestamp()
        if int(now_st) <= timestamp_end:
            log.warn(f"current time <= end time: {int(now_st)} <= {timestamp_end}]")
            return -1
        ret = self.check_list_video_record(list_video_info, timestamp_start, timestamp_end, duration)
        if ret < 0:
            log.error(f"record always failed: [{duration}s: {timestamp_start}->{timestamp_end}]")
            return -1        
        return 0
##################################################################################################################

