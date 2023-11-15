import logging
import argparse
from envparse import env
import os
import shutil
import paramiko
import subprocess

ARG_FILE_PREFIX = "argumentfile"
PORT_IN = 7000
PORT_OUT = 7100
DEFAULT_PABOTLIB_PORT = 8270

class TestExecutor:
    def __init__(self, args):
        self.sys_test_params = args.sys_test_params
        self.test_params = env.json(str(args.sys_test_params))
        self.argumentFilePath = args.arguments_file
        self.remote_pc_host = args.remote_pc_host
        self.remote_pc_username = args.remote_pc_username
        self.remote_pc_password = args.remote_pc_password
        self.output_dir = args.output_dir
        self.xunit = args.xunit
        self.build_id = args.build_id
        self.test_script_dir = args.test_script_dir
        self.listener = args.listener

        # Logger
        self.logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(funcName)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

        # Init SSH Client
        # self.initSshClient()        

    def initSshClient(self):
        """ 
        Initialize SSH Client 
        If id_rsa file which located at path ~/.ssh/id_rsa is not found, return None
        """
        self.logger.info("Initializing SSH Client")
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh_client = ssh_client

        # id_rsa_file_path = os.path.expanduser('~') + '/.ssh/id_rsa'
        # if not os.path.exists(id_rsa_file_path):
        #     self.logger.info("Not found id_rsa file at path: {}".format(id_rsa_file_path))
        #     return None

        # private_key = paramiko.RSAKey.from_private_key_file(id_rsa_file_path)
        # self.ssh_private_key = private_key

    def closeSshClient(self):
        """ Close SSH Client """
        ssh_client = self.getSshClient()
        if ssh_client:
            ssh_client.close()

    def getSshClient(self):
        """ Get SSH Client instance """
        return self.ssh_client

    def getSshPrivateKey(self):
        """ Get SSH Private Key file """
        return self.ssh_private_key

    def getRemotePcHost(self):
        """ Get Remote Test Control PC hostname or IP address """
        return self.remote_pc_host

    def getRemotePcUsername(self):
        """ Get Remote Test Control PC username """
        return self.remote_pc_username

    def getRemotePcPassword(self):
        """ Get Remote Test Control PC password """
        return self.remote_pc_password

    def getNumberOfArgs(self, testcase):
        processes = testcase.get("processes")
        try:
            number_of_args = len(processes[0].get("args"))
            for item in processes:
                args = item.get("args")
                p = len(args)
                if p < number_of_args:
                    number_of_args = p
            return number_of_args
            
        except Exception as e:
            self.logger.error(e)
            return 0

    def getArgFileCount(self):
        return len(self.list_argument_files)

    def getListener(self):
        """ Get listener main python file """
        return self.listener

    def getOuputDir(self):
        """ Get output directory """
        return self.output_dir

    def getXunitFilePath(self):
        """ Get Xunit file path """
        return self.xunit

    def getBuildId(self):
        """ Get BuildID """
        return self.build_id

    def getTestScriptDir(self):
        """ Get Test Script directory path """
        return self.test_script_dir

    def getTestSuiteName(self):
        """ Get TestSuite name """
        return self.test_params.get("testSuiteName")

    def getTestSuiteRunId(self):
        """ Get TestSuiteRun Id """
        return self.test_params.get("testSuiteRunId")

    def getTestMode(self):
        """ Get Test Mode """
        return self.test_params.get("testMode")

    def getArgumentFilePath(self):
        """ Get input argument file path """
        return self.argumentFilePath
    
    def getListArgumentFilesName(self):
        """ Get list which contains argument files name """
        return self.list_argument_files

    def getTestCases(self):
        """ Get list of TestCases from SYS_TEST_PARAMS """
        return self.test_params.get("testCases")

    def getNumberOfTestCases(self):
        """ Get number of TestCases from SYS_TEST_PARAMS """
        test_cases = self.getTestCases()
        return len(test_cases)

    def getListTestScripts(self, path):
        """ Get list of TestScript at directory """
        list_testscripts = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        return list_testscripts

    def getNumberOfProcesses(self):
        """ Get maximum number of processes. Default is 1 """
        test_cases = self.getTestCases()
        result = 1
        for item in test_cases:
            processes = item.get("processes")
            p_len = len(processes)
            if p_len > result:
                result = p_len
        return result

    def getTestSuiteDir(self):
        return self.test_suite_dir

    def getNumberOfTestSuiteFiles(self):
        """ Get number of TestSuite files in TestSuite directory """
        test_suite_dir = self.getTestSuiteDir()
        list_test_suite_files = [f for f in os.listdir(test_suite_dir)]
        return len(list_test_suite_files)

    def getNumberOfConnectedMobiles(self):
        """ Get number of connected mobile devices """
        list_device_id = self.getListOfConnectedMobilesId()
        return len(list_device_id)

    def getListOfConnectedMobilesId(self):
        """ Get list of connected mobile devices id """
        stdin, stdout, stderr = self.executeRemoteCommand("adb devices | grep -w 'device' | awk '{print $1}'")
        list_device_id = [item.strip() for item in stdout.readlines()]
        return list_device_id

    def generateTestSuite(self):
        self.logger.info("Prepare to generate TestSuite")
        # Get TestSuiteName
        test_suite_name = self.getTestSuiteName()
        if test_suite_name == None:
            self.logger.warn("Missing Test Suite name, using default TestSuite name: {}".format("TestSuite"))
            test_suite_name = "TestSuite"
        self.test_suite_dir = test_suite_name
        self.logger.info("Using TestSuite name: {}".format(test_suite_name))

        # Get TestMode
        test_mode = self.getTestMode()
        if test_mode == None:
            self.logger.warn("Missing Test Mode, using default Test Mode: {} (concurrent)".format(0))
            test_mode = 0
        self.logger.info("Using Test Mode: {}".format(test_mode))

        # Get TestCases
        test_cases = self.getTestCases()

        # Get Number of TestCases
        number_of_testcases = self.getNumberOfTestCases()
        self.logger.info("Number of TestCases to be executed: {}".format(number_of_testcases))

        # Delete old TestSuite directory
        try:
            if os.path.exists(test_suite_name):       
                self.logger.info("Delete old directory {}".format(test_suite_name))     
                shutil.rmtree(test_suite_name)
        except:
            self.logger.error("Cannot delete directory {}".format(test_suite_name))

        # Create new TestSuite directory
        try:
            self.logger.info("Create new directory {}".format(test_suite_name))
            if not os.path.exists(test_suite_name):
                os.makedirs(test_suite_name)  
        except:
            self.logger.error("Cannot create new directory {}".format(test_suite_name))

        # List file in lib directory
        test_script_dir = self.getTestScriptDir()
        if test_script_dir == None:
            test_script_dir = os.getcwd() + "/lib/"
        if not test_script_dir.endswith("/"):
            test_script_dir += "/"
        list_testscripts = self.getListTestScripts(test_script_dir)
        self.logger.info("Test Script directory: {}".format(test_script_dir))
        self.logger.info("Import list of Test Scripts: {}".format(list_testscripts))

        if test_mode == 1 and number_of_testcases > 1:
            self.logger.info("Generate multiple TestSuite files")
            for test_case in test_cases:
                file_content = ["*** Settings ***"]
                file_content.extend(["Resource    {}{}".format(test_script_dir, item) for item in list_testscripts])
                file_content.append("*** Test Cases ***")

                test_case_name = test_case.get("testCaseName")
                test_script_name = test_case.get("testScriptName")
                test_case_process = test_case.get("processes")
                file_content.append(test_case_name)

                # Determine which process id run test case
                tmp = "    ${isExecute}=    Get Variable Value    ${" + str(test_case_name) + "_TC_RUN_ID}\n"
                tmp += "    Pass Execution If    '${isExecute}' == 'None'    Not running test"
                file_content.append(tmp)
                
                test_script_args = "    " + test_script_name
                number_of_args = self.getNumberOfArgs(test_case)
                for index in range(1, number_of_args + 1):
                    test_script_args += "    " + "${" + test_case_name + "_ARGS_" + str(index) + "}" 
                file_content.append(test_script_args)

                file_content = [item + "\n" for item in file_content]

                # with open(os.path.join(test_suite_name, test_case_name + ".robot"), "wb") as test_case_file:
                with open(os.path.join(test_suite_name, test_case_name + ".robot"), "w") as test_case_file:
                    test_case_file.writelines(file_content)
                self.logger.info("TestSuite file {}.robot created".format(os.path.join(test_suite_name, test_case_name)))
                   
        else:
            self.logger.info("Generate single TestSuite file, TestMode = {}".format(test_mode))            
            file_content = ["*** Settings ***"]
            file_content.extend(["Resource    {}{}".format(test_script_dir, item) for item in list_testscripts])
            file_content.append("*** Test Cases ***")

            for test_case in test_cases:                
                test_case_name = test_case.get("testCaseName")
                test_script_name = test_case.get("testScriptName")
                test_case_process = test_case.get("processes")
                self.logger.info("Test Case Name: {}".format(test_case_name))
                file_content.append(test_case_name)

                # Append arguments to Test Scripts
                if test_mode == 0:
                    test_script_args = "    " + test_script_name
                    test_case_args = test_case_process[0].get("args")
                    for item in test_case_args:
                        test_script_args += "    " + item
                    file_content.append(test_script_args)

                elif test_mode == 1 and number_of_testcases == 1:
                    test_script_args = "    " + test_script_name
                    number_of_args = self.getNumberOfArgs(test_case)
                    for index in range(1, number_of_args + 1):
                        test_script_args += "    " + "${" + test_case_name + "_ARGS_" + str(index) + "}" 
                    file_content.append(test_script_args)
            
            file_content = [item + "\n" for item in file_content]

            #with open(os.path.join(test_suite_name, test_suite_name + ".robot"), "wb") as test_suite_file:
            with open(os.path.join(test_suite_name, test_suite_name + ".robot"), "w") as test_suite_file:
                test_suite_file.writelines(file_content)
            self.logger.info("TestSuite file {}.robot created".format(os.path.join(test_suite_name, test_suite_name)))
            
    # #
    # Generate argument files 
    # #      
    def generateArgumentFiles(self):
        test_mode = self.getTestMode()
        arg_file_count = 0

        test_cases = self.getTestCases()
        test_mode = self.getTestMode()

        if test_mode == 1:
            for test_case in test_cases:
                processes = test_case.get("processes")
                arg_file_count += len(processes)
        else:
            arg_file_count = 1

        self.logger.info("Number of argument file need to generate: {}".format(arg_file_count))
        input_arg_file_path = self.getArgumentFilePath()
        self.logger.info("Input argument file path: {}".format(input_arg_file_path))

        list_argument_files = list()

        for i in range(1, arg_file_count + 1):
            arg_file_name = ARG_FILE_PREFIX + str(i) + ".txt"

            # Delete old argument files
            try:
                if os.path.exists(arg_file_name):
                    self.logger.info("Delete argument file: {}".format(arg_file_name))
                    os.remove(arg_file_name)
            except:
                self.logger.warn("Cannot delete argument file: {}".format(arg_file_name))

            # Create new argument files
            try:
                self.logger.info("Create argument file: {}".format(arg_file_name))
                # Create file
                new_file = open(arg_file_name, 'w')

                # Append input argument file content to multiple argument files
                if not input_arg_file_path == None:
                    # with open(input_arg_file_path, 'rb') as in_file, open(arg_file_name, 'wb') as out_file:
                    with open(input_arg_file_path, 'r') as in_file, open(arg_file_name, 'w') as out_file:
                        lines = in_file.readlines()
                        out_file.writelines([line for line in lines])
                    self.logger.info("Append input argument file")

                # Save a list of argument file name
                list_argument_files.append(arg_file_name)

            except Exception as e:
                self.logger.warn("Cannot create argument file: {}, error: {}".format(arg_file_name, e))
        
        self.list_argument_files = list_argument_files
        self.logger.info("List argument files name: {}".format(self.list_argument_files))      

    def executeRemoteCommand(self, command):
        ssh_client = self.getSshClient()
        # private_key = self.getSshPrivateKey()
        host = self.getRemotePcHost()
        username = self.getRemotePcUsername()
        password = self.getRemotePcPassword()

        try:
            if host == None:
                self.logger.error("Missing Remote Test Control PC Hostname")
                return None
            if username == None:
                self.logger.warn("Missing Remote Test Control PC Username, try using default username: ubuntu")
                username = "ubuntu"
            # if not private_key == None:
            #     ssh_client.connect(hostname=host, username=username, pkey=private_key)
            #     self.logger.info("SSH connecting to {}@{}".format(username, host))
            #     result = ssh_client.exec_command(command)
            #     self.logger.info("Executing command: {}".format(command))
            #     # ssh_client.close()
            #     return result
            if not password == None:
                ssh_client.connect(hostname=host, username=username, password=password)
                self.logger.info("SSH connecting to {}@{}".format(username, host))
                result = ssh_client.exec_command(command)
                self.logger.info("Executing command: {}".format(command))
                # ssh_client.close()
                return result
        except Exception as e:
            self.logger.error("Error: {}".format(e))
        return None


    def killAllRemoteAppiumServers(self):
        """ Kill all remote Appium Servers """
        # stdin, stdout, stderr = self.executeRemoteCommand("killall node")
        stdin, stdout, stderr = self.executeRemoteCommand("ps aux | grep appium | awk '{print $2}'")
        appium_pids = stdout.readlines()
        for index, pid in enumerate(appium_pids):
            stdin, stdout, stderr = self.executeRemoteCommand("kill -9 {}".format(pid.strip('\n')))
            self.logger.info("Kill remote Appium Server PID: {}, output: {}, error: {}".format(pid.strip('\n'), stdout.read(), stderr.read()))

    def startRemoteAppiumServers(self):
        """ Start remote Appium Servers """
        list_device_id = self.getListOfConnectedMobilesId()

        for index, device_id in enumerate(list_device_id):
            port_in = str(PORT_IN + index)
            port_out = str(PORT_OUT + index)

            self.executeRemoteCommand("appium -p {} -bp {} -U {} > /dev/null 2>&1 &".format(port_in, port_out, device_id))
            self.logger.info("Start Appium Server on port {} for DeviceId: {}".format(port_in, device_id))

    def appendArguments(self):
        """ 
        *** DEPRECATED, use appendDeviceIds INSTEAD ***
        Append arguments to argument files 
        For each TestCase, there are a number of processes.
        For each process of TestCase, append arguments of that process to argument file
        """
        list_argument_files = self.getListArgumentFilesName()
        test_cases = self.getTestCases()
        test_mode = self.getTestMode()
        for test_case in test_cases:
            test_case_name = test_case.get("testCaseName")
            processes = test_case.get("processes")
            if test_mode == 0:
                args = processes[0].get("args")
                arg_file = list_argument_files[0]
                # with open(arg_file, 'ab') as out_file:
                with open(arg_file, 'a') as out_file:
                    for arg_index, arg in enumerate(args):
                        out_file.write("--variable {}_ARGS_{}:{}\n".format(test_case_name, str(arg_index + 1), arg))
            else:
                for index, p in enumerate(processes):
                    args = p.get("args")
                    arg_file = list_argument_files[index]
                    # with open(arg_file, 'ab') as out_file:
                    with open(arg_file, 'a') as out_file:
                        for arg_index, arg in enumerate(args):
                            out_file.write("--variable {}_ARGS_{}:{}\n".format(test_case_name, str(arg_index + 1), arg))

    def appendDeviceIds(self):
        """ Append content: --variable DEVICE_NAME:<DEVICE_ID> to argument files """
        list_device_id = self.getListOfConnectedMobilesId()
        list_argument_files = self.getListArgumentFilesName()

        for index, file_name in enumerate(list_argument_files):
            try:
                device_id = list_device_id[index]
                port_in = str(PORT_IN + index)
                # with open(file_name, 'ab') as out_file:
                with open(file_name, 'a') as out_file:
                    out_file.write("--variable DEVICE_NAME:{}\n".format(device_id)) 
                    out_file.write("--variable APPIUM_REMOTE_PORT:{}\n".format(port_in))
            except IndexError:
                self.logger.warn("Number of processes: {} is larger than number of connected devices: {}, skip argument file: {}".format(len(list_argument_files), len(list_device_id), file_name))
            
    def appendTestCaseRunId(self):
        """ Append content: --variable <TestCaseName>_TC_RUN_ID:<TestCaseRunId> to argument files """
        list_testcases = self.getTestCases()
        list_argument_files = self.getListArgumentFilesName()
        test_mode = self.getTestMode()

        argument_file_index = 0

        for test_case in list_testcases:
            testcase_name = test_case.get("testCaseName")
            processes = test_case.get("processes")
            if test_mode == 0:
                testcase_run_id = processes[0].get("testCaseRunId")
                args = processes[0].get("args")
                arg_file = list_argument_files[0]
                # with open(arg_file, 'ab') as out_file:
                with open(arg_file, 'a') as out_file:
                    out_file.write("--variable {}_TC_RUN_ID:{}\n".format(testcase_name, testcase_run_id))
                    for arg_index, arg in enumerate(args):
                        out_file.write("--variable {}_ARGS_{}:{}\n".format(testcase_name, str(arg_index + 1), arg))
                    
            else:
                for index, p in enumerate(processes):
                    testcase_run_id = p.get("testCaseRunId")
                    args = p.get("args")
                    if argument_file_index > self.getArgFileCount():
                        self.logger.error("Out of index in list argument file.")
                        return
                    arg_file = list_argument_files[argument_file_index]
                    argument_file_index += 1
                    # with open(arg_file, 'ab') as out_file:
                    with open(arg_file, 'a') as out_file:
                        out_file.write("--variable {}_TC_RUN_ID:{}\n".format(testcase_name, testcase_run_id))
                        for arg_index, arg in enumerate(args):
                            out_file.write("--variable {}_ARGS_{}:{}\n".format(testcase_name, str(arg_index + 1), arg))

    def isRemotePortIsUsed(self, port):
        """ Check if remote port is used, if used return True, otherwise return False """
        # If return code is 0, port is used, otherwise port is not used
        devnull = open(os.devnull, 'w')     # Redirect ouput to devnull
        return_code = subprocess.call("lsof -i:{}".format(port), shell=True, stdout=devnull, stderr=subprocess.STDOUT)
        if int(return_code) == 0:
            return True
        else: 
            return False

    def startPabot(self):
        # Detemine pabotlib port
        pabotlib_port = DEFAULT_PABOTLIB_PORT
        for i in range(1, 20):
            # From 8271 -> 8289
            tmp = DEFAULT_PABOTLIB_PORT + i
            if not self.isRemotePortIsUsed(tmp):
                self.logger.info("Using pabotlib port: {}".format(tmp))
                pabotlib_port = tmp
                break

        # Calculate number of processes
        # number_of_process = self.getNumberOfProcesses()
        number_of_process = self.getArgFileCount()
        number_of_test_suite_files = self.getNumberOfTestSuiteFiles()
        total_processes = number_of_process * number_of_test_suite_files

        # pabot_command = "pabot --processes {} --verbose --pabotlib --pabotlibport {}".format(total_processes, pabotlib_port)
        # list_argument_files = self.getListArgumentFilesName()
        # for index, argument_file in enumerate(list_argument_files):
        #     pabot_command += " --argumentfile" + str(index + 1) + " " + argument_file
        pabot_command = "pabot --processes {} --verbose".format(total_processes)

        # Get output directory
        output_dir = self.getOuputDir()
        build_id = self.getBuildId()
        if output_dir == None:
            if not os.path.exists("output"):
                self.logger.info("Output directory does not existed, create one")
                os.makedirs("output") 
            output_dir = os.getcwd() + "/output/" + str(build_id)
            self.logger.warn("Missing output directory, using default: {}".format(output_dir))            
        
        # Get Xunit
        xunit = self.getXunitFilePath()
        if xunit == None:
            xunit = "TestXunit.xml"
            self.logger.warn("Missing xunit file path, using default: {}".format(xunit))

        pabot_command += " -d {} -x {}".format(output_dir, xunit)

        # Get listener
        # listener = self.getListener()
        # if not listener == None:
        #     pabot_command += " --listener {}:{}:{}".format(listener, self.sys_test_params, output_dir)

         # Get TestSuite dir
        test_suite_dir = self.getTestSuiteDir()
        test_mode = self.getTestMode()
        if int(test_mode) == 1 and int(number_of_test_suite_files) > 1:
            # Run directory
            pabot_command += " {}".format(test_suite_dir)
        else:
            # Run file
            pabot_command += " {}/{}.robot".format(test_suite_dir,test_suite_dir)

        self.logger.info("Run Pabot command: {}".format(pabot_command))
        subprocess.call(pabot_command, shell=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test executor for Robotframework.")

    parser.add_argument("-s", "--sys-test-params", metavar="", dest="sys_test_params", required=False, help="Name of SYS_TEST_PARAMS environment variable")
    parser.add_argument("-a", "--arguments-file", metavar="", dest="arguments_file", help="Path to argument file")
    parser.add_argument("-o", "--output-dir", metavar="", dest="output_dir", help="Test output directory")
    parser.add_argument("-x", "--xunit", metavar="", dest="xunit", help="XUnit file name")
    parser.add_argument("-b", "--build-id", metavar="", dest="build_id", required=True, help="Build ID")
    parser.add_argument("-ts", "--test-script-dir", metavar="", dest="test_script_dir", help="Test Script directory path, MUST be absolute path")
    parser.add_argument("-rh", "--remote-pc-host", metavar="", dest="remote_pc_host", required=False, help="Remote Test Control PC hostname")
    parser.add_argument("-ru", "--remote-pc-username", metavar="", dest="remote_pc_username", help="Remote Test Cotrol PC username")
    parser.add_argument("-rp", "--remote-pc-password", metavar="", dest="remote_pc_password", required=False, help="Remote Test Control PC password")
    parser.add_argument("-l", "--listener", metavar="", dest="listener", help="Listener main python file")

    args = parser.parse_args()

    testExecutor = TestExecutor(args)

    testExecutor.generateTestSuite()
    # testExecutor.generateArgumentFiles()

    # testExecutor.appendDeviceIds()
    # testExecutor.appendTestCaseRunId()

    # testExecutor.killAllRemoteAppiumServers()
    # testExecutor.startRemoteAppiumServers()

    testExecutor.startPabot()

    # testExecutor.closeSshClient()

    