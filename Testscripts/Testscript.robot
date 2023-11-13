#version: 1.0.1
*** Settings ***
Library      ../Libs/Test_API.py
Variables    ../Libs/Msg_API.py
Resource     ../Validation/val_list.txt
*** Variables ***
${NULL}  

*** Keywords ***    
TEST_GET
    [Arguments]
    ...    ${name}=${NULL}
    ...    ${msgID}=1050
    ...    ${valFile}=${NULL}
    ...    ${keyCheck}=all
    ...    ${infoType}=DEVICE_INFO
    ...    ${timeout}=3000

    ${ret} =    TEST_CASE_GET
    ...    ${name}
    ...    ${msgID}
    ...    ${valFile}
    ...    ${keyCheck}
    ...    ${infoType}
    ...    ${timeout}
    Should Be True    ${ret} >= 0

TEST_SET
    [Arguments]
    ...    ${name}=${NULL}
    ...    ${msgID}=1050
    ...    ${subMsgID}=${NULL}
    ...    ${timeout}=3000
  
    ${ret} =    TEST_CASE_SET
    ...    ${name}
    ...    ${msgID}
    ...    ${subMsgID}
    ...    ${timeout}
    Should Be True    ${ret} >= 0

TEST_RECORD
    [Arguments]
    ...    ${name}=${NULL}
    ...    ${testType}="GET"
    ...    ${recordMode}="ALWAYS"
    ...    ${duration}=1
    ...    ${startTime}="00:00"
    ...    ${endTime}="23:59"
    ...    ${checkFlag}=0
    ...    ${msgID}=-1
    ...    ${subMsgID}=${NULL}
    ...    ${timeout}=3000

    ${ret} =    TEST_CASE_RECORD
    ...    ${name}
    ...    ${testType}
    ...    ${recordMode}
    ...    ${duration}    
    ...    ${startTime}
    ...    ${endTime}
    ...    ${checkFlag}
    ...    ${msgID}
    ...    ${subMsgID}
    ...    ${timeout}
    Should Be True    ${ret} >= 0



#####################################
TEST_SET_DEMO
    [Arguments]
    ...    ${name}=${NULL}
    ...    ${msgID}=1050
    ...    ${subMsgID}=${NULL}
    ...    ${timeout}=3000
  
    ${ret} =    TEST_CASE_SET
    ...    ${name}
    ...    ${msgID}
    ...    ${subMsgID}
    ...    ${timeout}
    Should Be True    ${ret} >= 0