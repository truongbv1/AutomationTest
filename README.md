# AUTOMATION TEST
* version: v102
## Structure
* testdatas: Danh sách các file cấu hình testcase camera
* configs: Chứa các cấu hình mô trường ban đầu trước khi test
* utils: chứ các thư viện P2P, API xử lý bản tin, dữ liệu
* testsuites: chứa các testsuite
* testscripts: chứa các file script test, keywork
* outputs: lưu các kết quả test
## Run
```
# run local with python
python test_run.py --build_id DIR_OUTPUT --config "CAM_NAME" -run_local

# run local with python + robot
python test_run.py --build_id DIR_OUTPUT --config "CAM_NAME" -run_local -run_robot

# run with vqman 
python test_run.py --sys-test-params SYS_TEST_PARAMS --build_id ${BUILD_ID} --config ${CAM_NAME} -run_robot
```

<details><summary> <b>Contributors</b> </summary>

* *TruongBV*
* *EnMT*

</details>
