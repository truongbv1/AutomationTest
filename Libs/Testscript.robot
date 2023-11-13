#version: 1.0.1
*** Settings ***
Library      Test_API.py
Variables    Msg_API.py
Resource     ../Validation/val_list.txt
*** Variables ***
${NULL}  

*** Keywords ***    
TEST_GET
    [Arguments]
    ...    ${name}=${NULL}
    ...    ${msg_api}=1050
    ...    ${val_file}=${NULL}
    ...    ${key_check}=all
    ...    ${info_type}=DEVICE_INFO
    ...    ${timeout}=3000

    ${ret} =    TEST_CASE_GET
    ...    ${name}
    ...    ${msg_api}
    ...    ${val_file}
    ...    ${key_check}
    ...    ${info_type}
    ...    ${timeout}
    Should Be True    ${ret} >= 0

TEST_SET
    [Arguments]
    ...    ${name}=${NULL}
    ...    ${msg_api}=1050
    ...    ${sub_msg_api}=${NULL}
    ...    ${timeout}=3000
  
    ${ret} =    TEST_CASE_SET
    ...    ${name}
    ...    ${msg_api}
    ...    ${sub_msg_api}
    ...    ${timeout}
    Should Be True    ${ret} >= 0

TEST_RECORD
    [Arguments]
    ...    ${name}=${NULL}
    ...    ${test_type}="GET"
    ...    ${record_mode}="ALWAYS"
    ...    ${duration}=1
    ...    ${start_time}="00:00"
    ...    ${end_time}="23:59"
    ...    ${check_flag}=0
    ...    ${msgID}=-1
    ...    ${subMsgID}=${NULL}
    ...    ${timeout}=3000

    ${ret} =    TEST_CASE_RECORD
    ...    ${name}
    ...    ${test_type}
    ...    ${record_mode}
    ...    ${duration}    
    ...    ${start_time}
    ...    ${end_time}
    ...    ${check_flag}
    ...    ${msgID}
    ...    ${subMsgID}
    ...    ${timeout}
    Should Be True    ${ret} >= 0