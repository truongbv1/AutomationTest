*** Settings ***
Resource    ../Libs/Testscript.robot
# Resource    Validation/val_list.txt
*** Test Cases ***

### test as vpman
VQMan_CHECK_VERSION_FW
    TEST_GET    CHECK_VERSION_FW     ${GET_DEVICE_INFO}    ${GET_DEVICE_INFO_FILE_VAL}    version

VQMan_SET_MD_INFO
    TEST_SET    GET_MD_INFO    ${GET_MD_INFO}