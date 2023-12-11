#version: 1.0.2
#truongbv
*** Settings ***
Library    utils.test_api.TestAPI    WITH NAME     LibPY

*** Keywords ***
RUN_TESTCASE_BY_ID
    [Arguments]    @{testcase_id}
    ${ret} =    LibPY.run_testcase    @{testcase_id}
    Should Be True    ${ret} >= 0

# dont define right here 
# *** Test Cases ***
# TC_EXAMPLE_CHECK_VERSION_FW
#     RUN_TESTCASE_BY_ID    check_version_fw