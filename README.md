# AUTOMATION TEST
## Structure
* APIList: Danh sách các file bản tin cấu hình camera
* Configs: Chứa các cấu hình mô trường ban đầu trước khi test
* Libs: chứ các thư viện P2P, API xử lý bản tin
* Testsuites: chứa các testsuite
* Validation: chứa các file xác thực, để kiểm tra với các thông tin lấy về từ camera
## Install
```
pip install robotframework
```
## RUN Testsuite
```
robot Testsuites\Testsuite_example.robot

# or run with a test case
robot -t CHECK_DEVICE_INFO Testsuites\Testsuite_example.robot
```
## RUN with Ride
```
python run_ride_app.py
```
<details><summary> <b>install ride</b> </summary>

```
pip install robotframework-ride
```
</details>




<details><summary> <b>Contributors</b> </summary>

* *TruongBV*
* *EnMT*
* *ManhPT*

</details>