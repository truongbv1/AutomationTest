#version: 1.0.2
#truongbv
#####################################################
# # Example test with name testcase_id: check_version_fw
# from utils.test_api import TestAPI
# test = TestAPI()
# test.run_testcase("check_version_fw")
#####################################################

from utils.test_api import TestAPI
# test = TestAPI()
# test.run_testcase("check_md_on")
# test.run_testcase("check_version_fw")
# test.run_testcase("check_scan_wifi")
# test.run_testcase("set_record_quality_fhd")
# test.run_testcase("set_record_quality_sd")
# test.run_testcase("set_record_quality_fail")
# test.run_testcase("get_record_mode_always")
# test.run_testcase("get_record_mode_schedule")
# test.run_testcase("get_record_on")

# test.auto_run_testdata()
# test.generate_testsuite()
# test.auto_run_testdata_robot()

import logging
import argparse
import os # os.environ
import threading
import time
import json

class TestExecutor():
    def __init__(self, args):
        # stmp = str.replace(args.list_cameras," ", "")
        # self.list_cameras = str.split(stmp, ",")
        self.config = args.config
        self.threads = []
        self.output_log = []
        self.build_id = args.build_id
        self.run_local = args.run_local
        self.run_robot = args.run_robot
        self.file_testsuite = args.run_testsuite
        self.path_camera_cfg = "configs/config_init.json"
        if args.sys_test_params != "":
            self.test_params = json.load(os.environ[args.sys_test_params]) 
            # self.test_params =  {'testSuiteName': 'IPCAM_AUTOTEST-DEMO_SET_01', 'testSuiteRunId': 2565, 'testMode': 0, 'testCases': [{'testCaseName': 'IPCAM_AUTOTEST-CHECK_VERSION_FW', 'testScriptName': 'RUN_TESTCASE_BY_ID', 'processes': [{'args': ['check_version_fw'], 'testCaseRunId': 28554}]}, {'testCaseName': 'IPCAM_AUTOTEST-DEMO_SET_ALARM_ON', 'testScriptName': 'RUN_TESTCASE_BY_ID', 'processes': [{'args': ['check_scan_wifi'], 'testCaseRunId': 28555}]}]}

    def run_with_robot(self):
        print("run_with_robot")
        test = TestAPI()
        test.generate_testsuite()
        test.auto_run_testdata_robot()

    def run_with_vqman(self):
        print("run_with_vqman")
        test = TestAPI()
        test.generate_testsuite_vqman(self.test_params)
        test.auto_run_testdata_robot(self.build_id)

    # def run_with_pabot(self):
    #     print("run_with_pabot")
    def run_file_testsuite(self):
        import robot
        output_dir = "outputs/" + str(self.build_id)
        robot.run(self.file_testsuite, outputdir=output_dir)
        return 0


    def run_with_python(self):
        print("run_with_python")
        test = TestAPI()
        test.auto_run_testdata()
        print("done")
        self.output_log.append(test.output_log)
        self.show_output()

    def show_output(self):
        for thread in self.output_log:
            print("================================================")
            for tc_log in thread:
                print(tc_log)
        print("================================================")

    def set_config(self):
        try:
            f = open (self.path_camera_cfg, "r")
            data = f.read()
            f.close()

            data_cfg = json.loads(data)
        except:
            self.logger.error(f"config faied: {self.path_camera_cfg}!")
            return -1
        
        if self.config not in data_cfg:
            self.logger.error(f"{self.config} not in config!")
            return -1
        
        data_cfg["select_config"] = self.config

        with open(self.path_camera_cfg, "w") as outfile:
            json.dump(data_cfg, outfile)
        return 0


    def run(self):

        if self.config != "":
            self.set_config()
        
        if self.file_testsuite != "":
            self.run_file_testsuite()
            return 0
        
        func = self.run_with_python
        if self.run_local:
            if self.run_robot:
                func = self.run_with_robot
            else:
                func = self.run_with_python
        else:
            func = self.run_with_vqman
        func()

        # n_thread = len(self.list_cameras)
        # if n_thread <= 0:
        #     print("error")
        #     return -1
        # else:

            # func = self.run_with_python
            # if self.run_local:
            #     if self.run_robot:
            #         func = self.run_with_robot
            #     else:
            #         func = self.run_with_python
            # else:
            #     func = self.run_with_vqman

            # func()
            # for i in range(n_thread):
            #     camera_cfg = self.list_cameras[i]
            #     t = threading.Thread(target=func, args=(camera_cfg,))
            #     self.threads.append(t)
            #     print("Init thread done")
            
        # for t in self.threads:
        #     time.sleep(2)
        #     t.start()

        # for t in self.threads:
        #     t.join()
        #     print("exit")

        # self.show_output()
        return 0

        

# python .\test_run.py --sys-test-params AA --build_id 0 --config "HVIF03" -run_local -run_robot
# python .\test_run.py --sys-test-params AA --build_id 0 --config "HVIF03" -run_robot
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test executor for Robotframework.")
    parser.add_argument("--sys-test-params", metavar="", dest="sys_test_params", type=str, default="", help="Name of SYS_TEST_PARAMS environment variable")
    

    parser.add_argument("--config", dest="config", type=str, default="Default", help="List config of cameras. Ex HVIF01, HVIF03")
    parser.add_argument("--build_id", dest="build_id", type=str, default="0", help="Build ID")
    parser.add_argument("-run_local", dest="run_local", action='store_true', help="run in local pc")
    parser.add_argument("-run_robot", dest="run_robot", action='store_true', help="use robot framework")
    parser.add_argument("--run_testsuite", dest="run_testsuite", type=str, default="", help="Path to testsuite file")

    args = parser.parse_args()


    tester = TestExecutor(args)
    tester.run()
    