*** Settings ***
Resource    ../testscripts/testscript_v102.robot
*** Test Cases ***
IPCAM_AUTOTEST-CHECK_VERSION_FW
	RUN_TESTCASE_BY_ID	check_version_fw	
IPCAM_AUTOTEST-DEMO_SET_ALARM_ON
	RUN_TESTCASE_BY_ID	check_scan_wifi	
