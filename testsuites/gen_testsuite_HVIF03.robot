*** Settings ***
Resource    ../testscripts/testscript_v102.robot
*** Test Cases ***
TC1050_deviceinfo_check_version_fw
	RUN_TESTCASE_BY_ID		check_version_fw
TC1072_wifi_check_scan_wifi
	RUN_TESTCASE_BY_ID		check_scan_wifi
