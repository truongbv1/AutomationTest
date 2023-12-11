#version: 1.0.2
#truongbv

from utils.handle_api import BaseTest, DEVICE_INFO, WIFI, RECORD, MOTION
from utils.handle_api import logger
import json
import sys
import csv
import os
# import subprocess
# import robot #robot framework

CONFIGS_PATH = "configs/config_init.json"
TESTSCRIPT_DIR = "testscripts"
TESTSUITE_DIR = "testsuites"


class TestAPI:
    def __init__(self):
        self.ppcs_cfg = {"device_id": "", "init_string": ""}
        self.login_default = {"user": "admin", "password": "vnpt@123"} #default
        self.login_str = json.dumps(self.login_default)
        self.path_testdatas = "testdatas/default.csv"
        self.target_name = ""
        ret = self.parse_configs("")
        if ret < 0:
            logger.error("setup configs failed!")
            exit()
        self.list_datatest = self.get_testdatas(self.path_testdatas)        
        
        self.testsuite_filename = ""
        self.build_id = 0
        self.output_log = []
        

    def parse_configs(self, target_cfg):
        fd = open(CONFIGS_PATH, 'r')
        conf_str = fd.read()
        fd.close()

        conf_json = None
        try:
            conf_json = json.loads(conf_str)
        except ValueError:
            logger.error("Configs not a json object. Parse failed")
            return -1

        # target_cfg = str(conf_json["select_config"])
        if target_cfg == "":
            target_cfg = str(conf_json["select_config"])
            self.target_name = target_cfg
            # logger.error("'select_config' failed")
            # return -1
        cam_cfg_json = conf_json[target_cfg]

        u = str(cam_cfg_json["login_usr"])
        p = str(cam_cfg_json["login_pwd"])
        d = str(cam_cfg_json["p2p_did"])
        i = str(cam_cfg_json["p2p_init_str"])
        t = str(cam_cfg_json["path_data_test"])

        if u == "" or p == "" or d == "" or i == "" or t == "":
            logger.error(f"get info '{target_cfg}' failed")
            return -1

        self.login_default["user"]      = u
        self.login_default["password"]  = p
        self.ppcs_cfg["device_id"]      = d
        self.ppcs_cfg["init_string"]    = i
        self.path_testdatas             = t

        self.login_str = json.dumps(self.login_default)
        return 0
    
    def convert_to_json(self, input_str):
        json_obj = {}
        if input_str == "":
            # logger.warn("input_str is null")
            return json_obj
        try:
            json_obj = json.loads(input_str)
        except ValueError:
            logger.error("input_str is not json obj")
        return json_obj

    def get_testdatas(self, path_csv_file):
        list_testdatas = []
        with open(path_csv_file) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            column_names = []
            for row in csv_reader:
                if line_count == 0:
                    column_names = row
                    line_count += 1
                else:
                    row_dict = {column_names[idx]:row[idx] for idx in range(len(column_names))}

                    row_dict["msg_set"] = self.convert_to_json(row_dict["msg_set"])
                    row_dict["msg_result"] = self.convert_to_json(row_dict["msg_result"])
                    row_dict["msg_val"] = self.convert_to_json(row_dict["msg_val"])
                    list_testdatas.append(row_dict)
                    line_count += 1
        return list_testdatas
    
    def run_testcase(self, testcase_id):

        tc_search = [tc for tc in self.list_datatest if tc["testcase_id"] == testcase_id]
        len_tc = len(tc_search)
        if len_tc == 0:
            logger.error(f"Testcase not found: {testcase_id}")
            return -1
        elif len_tc > 1:
            logger.error(f"Testcase_id is not unique: len={len_tc} > 1")
            return -1
        ####
        testcase = tc_search[0]
        tc_type = testcase["type_info"]

        tc = None
        if tc_type == "common":
            tc = BaseTest(self.ppcs_cfg, self.login_str)
        elif tc_type == "deviceinfo":
            tc = DEVICE_INFO(self.ppcs_cfg, self.login_str)
        elif tc_type == "wifi":
            tc = WIFI(self.ppcs_cfg, self.login_str)
        elif tc_type == "record":
            tc = RECORD(self.ppcs_cfg, self.login_str)
        elif tc_type == "motion":
            tc = MOTION(self.ppcs_cfg, self.login_str)

        else:
            logger.error(f"Not not support type: {tc_type}")

        ret = tc.testcase_run(testcase) if tc != None else -1
        if ret < 0:
            logger.info("===> FAIL")
        else:
            logger.info("===> PASS")

        return ret
    
    def auto_run_testdata(self):
        list_tc = [tc for tc in self.list_datatest if int(tc["auto_run"]) > 0]
        self.output_log.append("Report of '" + self.target_name + "': ")
        out = ""
        cnt = 0
        n = len(list_tc)
        if n == 0:
            logger.error("Total testcase for autorun is 0")
            return -1
        for tc in list_tc:
            tc_id = tc["testcase_id"]
            tc_name = tc["testcase_name"]
            ret = self.run_testcase(tc_id)
            if ret >= 0:
                out = "FASS"
                cnt += 1
            else:
                out = "FAIL"

            self.output_log.append(out + ": " + str(tc_name))
        
        # logger.info("\nReport:")
        # for log in self.output_log:
        #     logger.info(f"{log}")

        log = f"Run {n} testcase done: {cnt} PASSED, {n - cnt} FAILED, %PASSED {int(100*cnt/n)}%"
        # logger.info(log)
        self.output_log.append(log)
        return 0
            
    def generate_testsuite(self):

        testscript_dir = os.getcwd() + "/" + TESTSCRIPT_DIR + "/"
        list_testscripts = [f for f in os.listdir(testscript_dir) if os.path.isfile(os.path.join(testscript_dir, f))]

        list_tc = [tc for tc in self.list_datatest if int(tc["auto_run"]) > 0]
        n = len(list_tc)
        if n == 0:
            logger.error("Total testcase for autorun is 0")
            return -1
        
        file_content = ["*** Settings ***"]
        # file_content.extend(["Resource    {}{}".format(testscript_dir, item) for item in list_testscripts])
        file_content.extend(["Resource    ../{}/{}".format(TESTSCRIPT_DIR, item) for item in list_testscripts])
        file_content.append("*** Test Cases ***")
        # for tc in self.list_datatest:
        for tc in list_tc:
            tc_id = tc["testcase_id"]
            tc_name = tc["testcase_name"]

            file_content.append(tc_name)
            file_content.append("\tRUN_TESTCASE_BY_ID\t\t" + tc_id)

        file_content = [item + "\n" for item in file_content]

        self.testsuite_filename = "gen_testsuite_" + self.target_name + ".robot"
        with open(os.path.join(TESTSUITE_DIR, self.testsuite_filename), "w") as testsuite_file:
            testsuite_file.writelines(file_content)
            logger.info(f"TestSuite file {self.testsuite_filename} created")
        return 0
    
    # test_params: 
    #{
    #   'testSuiteName': 'IPCAM_AUTOTEST-DEMO_SET_01', 'testSuiteRunId': 2565, 'testMode': 0, 
    #   'testCases': [
    #       {
    #       'testCaseName': 'IPCAM_AUTOTEST-DEMO_SET_ALARM_OFF', 
    #       'testScriptName': 'TEST_SET_DEMO', 
    #       'processes': [
    #           {'args': ['DEMO_SET_ALARM_OFF', '1037', 'OFF', '3000'], 
    #           'testCaseRunId': 28554
    #           }
    #        ]
    #       }, 
    #       ...
    #   ]
    #}
    def generate_testsuite_vqman(self, test_params):
        testscript_dir = os.getcwd() + "/" + TESTSCRIPT_DIR + "/"
        list_testscripts = [f for f in os.listdir(testscript_dir) if os.path.isfile(os.path.join(testscript_dir, f))]

        if type(test_params) != dict:
            logger.error("test_params is not dict")
            return -1
        testSuiteName = test_params.get("testSuiteName")
        list_testcases = test_params.get("testCases")
        
        file_content = ["*** Settings ***"]
        file_content.extend(["Resource    ../{}/{}".format(TESTSCRIPT_DIR, item) for item in list_testscripts])
        file_content.append("*** Test Cases ***")

        for tc in list_testcases:
            test_case_name = tc.get("testCaseName")
            test_script_name = tc.get("testScriptName")
            test_case_process = tc.get("processes")
            list_args = test_case_process[0].get("args")
            tmp_args = ""
            for arg in list_args:
                tmp_args = tmp_args + str(arg) + "\t"
            
            file_content.append(test_case_name)
            file_content.append("\t" + test_script_name + "\t" + tmp_args)
        
        file_content = [item + "\n" for item in file_content]

        self.testsuite_filename = "vqman_" + testSuiteName + "_" + self.target_name + ".robot"
        with open(os.path.join(TESTSUITE_DIR, self.testsuite_filename), "w") as testsuite_file:
            testsuite_file.writelines(file_content)
            logger.info(f"TestSuite file {self.testsuite_filename} created")



    def auto_run_testdata_robot(self, build_id=0):
        import robot #robot framework
        
        if self.testsuite_filename == "":
            logger.error("Path file testsuite fail")
            return -1
        
        # cmd = "robot --outputdir outputs " + TESTSUITE_DIR + "/" + self.testsuite_filename
        # logger.info(f"CMD: {cmd}")
        # subprocess.Popen(cmd, shell=True)
        output_dir = "outputs/" + str(build_id)
        robot.run(TESTSUITE_DIR + "/" + self.testsuite_filename, outputdir=output_dir)
        return 0
    
    