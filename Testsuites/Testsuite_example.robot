#version: 1.0.1
*** Settings ***
Library      ../Libs/Test_API.py
Variables    ../Libs/Msg_API.py
Resource     ../Validation/val_list.txt

*** Test Cases ***

# RECORD
#####################################################################################
# SET_RECORD_OFF
#     ${ret} =    TEST_CASE_SET    OFF_RECORD    ${GET_RECORD_INFO}
#     Should Be True    ${ret} >= 0

# SET_RECORD_ALWAYS
#     ${ret} =    TEST_CASE_SET    ON_RECORD_ALWAYS    ${RECORD}    ALWAYS
#     Should Be True    ${ret} >= 0

# SET_RECORD_SCHEDULE
#     ${ret} =    TEST_CASE_SET    TURN_OFF    ${RECORD}    OFF
#     Should Be True    ${ret} >= 0
#     ${ret} =    TEST_CASE_SET    TURN_ON    ${RECORD}    SCHEDULE
#     Should Be True    ${ret} >= 0
#     ${ret} =    TEST_CASE_SET    SET_SCHEDULE    ${SET_RECORD_SCHEDULE}
#     Should Be True    ${ret} >= 0
# SET_RECORD_SCHEDULE
#     ${ret} =    TEST_CASE_RECORD    SET_RECORD_MODE    SET    record_mode=SCHEDULE    msgID=${SET_RECORD_SCHEDULE}
#     Should Be True    ${ret} >= 0

################################################################################
SET_RECORD_OFF
    ${ret} =    TEST_CASE_RECORD    SET_RECORD_MODE    SET    OFF
    Should Be True    ${ret} >= 0
################################################################################
#params: Function    name    SET    record_mode    msgID=1066    subMsgID=sub_name
SET_RECORD_SCHEDULE
    ${ret} =    TEST_CASE_RECORD    SET_RECORD_MODE_SCHEDULE    SET    SCHEDULE    msgID=${SET_RECORD_SCHEDULE}
    Should Be True    ${ret} >= 0

GET_RECORD_SCHEDULE
    ${ret} =    TEST_CASE_RECORD    CHECK_RECORD_MODE_SCHEDULE    GET    SCHEDULE
    Should Be True    ${ret} >= 0

################################################################################
# Kiểm tra ngay lập tức: ghi hình và kiểm tra kết quả
#params: Function    name    GET    record_mode=ALWAYS    duration
SET_RECORD_ALWAYS_0
    ${ret} =    TEST_CASE_RECORD    CHECK_RECORD_MODE_ALWAYS    SET    ALWAYS    duration=1
    Should Be True    ${ret} >= 0

################################################################################
# Bật trước và kiểm tra vào thời điểm khác: ghi hình riêng, kiểm tra kq riêng theo khoảng giờ đặt
#params: Function    name    SET    record_mode    duration
SET_RECORD_ALWAYS_1
    ${ret} =    TEST_CASE_RECORD    SET_RECORD_MODE_ALWAYS    SET    ALWAYS
    Should Be True    ${ret} >= 0

### waiting ..
#params: Function    name    GET    record_mode    duration    start_time    end_time    check_flag
GET_RECORD_ALWAYS_1
    ${ret} =    TEST_CASE_RECORD    CHECK_RECORD_MODE_ALWAYS    GET    ALWAYS    1    23:25    23:29  1
    Should Be True    ${ret} >= 0
################################################################################

SET_RECORD_EVENT
    ${ret} =    TEST_CASE_RECORD    SET_RECORD_MODE_EVENT    SET    EVENT
    Should Be True    ${ret} >= 0
################################################################################

SET_RECORD_FAIL
    ${ret} =    TEST_CASE_RECORD    SET_RECORD_MODE_FAIL    SET    FAIL
    Should Be True    ${ret} >= 0
################################################################################
#####################################################################################


# WIFI
#################################################################################
SETTING_WIFI
    ${ret} =    TEST_CASE_SET    SETTING_NEW_WIFI    ${WIFI}
    Should Be True    ${ret} >= 0

GET_WIFI_SIGNAL
    ${ret} =    TEST_CASE_SET    GET_WIFI_SIGNAL    ${GET_WIFI_SIGNAL}
    Should Be True    ${ret} >= 0

WIFI_SCAN
    ${ret} =    TEST_CASE_GET    CHECK_SCAN_WIFI    ${WIFI_SCAN}    ${SCAN_LIST_WIFI_FILE_VAL}    intersection    SCAN_WIFI
    Should Be True    ${ret} >= 0

WIFI_SCAN_equal
    ${ret} =    TEST_CASE_GET    CHECK_SCAN_WIFI    ${WIFI_SCAN}    ${SCAN_LIST_WIFI_FILE_VAL}    equal    SCAN_WIFI
    Should Be True    ${ret} >= 0

# DEVICE INFO
#################################################################################
# example get method 2
CHECK_VERSION_FW
    ${ret} =    TEST_CASE_GET    CHECK_VERSION_FW    ${GET_DEVICE_INFO}    ${GET_DEVICE_INFO_FILE_VAL}    version
    Should Be True    ${ret} >= 0

# example get method 2
CHECK_DEVICE_INFO_ALL
    ${ret} =    TEST_CASE_GET    CHECK_DEVICE_INFO    ${GET_DEVICE_INFO}    ${GET_DEVICE_INFO_FILE_VAL}    all
    Should Be True    ${ret} >= 0


# MOTION
#################################################################################
GET_MD_INFO
    ${ret} =    TEST_CASE_SET    GET_MD_INFO    ${GET_MD_INFO}
    Should Be True    ${ret} >= 0

GET_MD_ON_OFF
    ${ret} =    TEST_CASE_GET    CHECK_MD_ON_OFF    ${GET_MD_INFO}    ${GET_MD_INFO_FILE_VAL}    motion_detect:md
    Should Be True    ${ret} >= 0
#################################################################################