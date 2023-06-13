import socket
import re
import sys
import time
import threading
import pandas as pd
import PyQt5.QtCore as QtC
import PyQt5.QtWidgets as QtW
import PyQt5.QtGui as QtG


#Getting all setups from Excel
platformList = pd.read_excel(r"EXCEL SETUPS PATH PATH")
platformList = platformList.set_index("Name")[["Dut", "Ctrlr", "Rack"]].to_dict("index")
platformList = {k: [v["Dut"], v["Ctrlr"], v["Rack"]] for k, v in platformList.items()}
platformList.popitem()
pduList={}
df = pd.read_excel(r"EXCEL PDU PATH")
for index, row in df.iterrows():
    pduList[row[0]] = row[1]


class ListCreation(QtW.QListWidget):
    def __init__(self):
        super().__init__()
        self.last_call_time=0
    
    def checkplatform(self ,name, dut_ip, ctrlr_ip, rack, all_arr, dut_arr, ctrl_arr):
        sock_ssh = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_rdp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket.setdefaulttimeout(1.0)

        result_ssh = sock_ssh.connect_ex((dut_ip, 22))
        result_rdp = sock_rdp.connect_ex((ctrlr_ip, 3389))

        sock_ssh.close()
        sock_rdp.close()

        if result_ssh != 0:
            dut_arr[name]=dut_ip + ";" + ctrlr_ip
            string_ssh = "\tDUT " + dut_ip + " 🔴"
        else: string_ssh = "\tDUT " + dut_ip + " 🟢"
        if result_rdp != 0:
            ctrl_arr[name]=ctrlr_ip
            string_rdp = "\tCTRLr " + ctrlr_ip + " 🔴"
        else: string_rdp = "\tCTRLr " + ctrlr_ip + " 🟢"

        all_arr[name + "\n" + string_ssh + "\n" + string_rdp]=rack
    
    def checkpdu(rack, ip, pdu_arr):
        sock_https = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket.setdefaulttimeout(1.0)
        result_https = sock_https.connect_ex((ip, 443))
        sock_https.close()
        if result_https != 0:
            pdu_arr.append(rack + " (" + ip + ") 🔴")
        else: pdu_arr.append(rack + " (" + ip + ") 🟢")

    def CreateRackSet(self, all_strings):
        racks_set = set(all_strings.values())
        racks_list = list(racks_set)
        return racks_list

    def CreateLastRackVar(self, racks_list):
        last_rack = racks_list[-1]
        return last_rack
        
    def MainLoop(self, all_strings, dead_dut, dead_ctrl, all_pdu, pduList, platformList):
        all_strings.clear()
        dead_dut.clear()
        dead_ctrl.clear()
        all_pdu.clear()
        for name, (dut_ip, ctrlr_ip, rack) in platformList.items():
            self.checkplatform(self, name, dut_ip, ctrlr_ip, rack, all_strings, dead_dut, dead_ctrl)
        for rack, ip in pduList.items():
            self.checkpdu(rack, ip, all_pdu)

    def RackListCreate(self, rack_nr, all_strings, all_pdu):
        self.clear()
        self.setFixedSize(275, 700)
        input_string=all_pdu[rack_nr-1]
        ip_pattern = r'\((\d+\.\d+\.\d+\.\d+)\)'
        match = re.search(ip_pattern, input_string)
        if match:
            ip_address = match.group(1)
        pdu_item = QtW.QListWidgetItem(all_pdu[rack_nr-1])
        pdu_item.setData(QtC.Qt.UserRole, QtC.QUrl(f"http://{ip_address}:80"))
        self.addItem(pdu_item)
        self.addItem("\n")
        for string, rack in all_strings.items():
            if rack == rack_nr:
                item = QtW.QListWidgetItem(string)
                lines = string.split('\n')
                ip_line = lines[2].split()
                ip_final = ip_line[1]
                item.setData(QtC.Qt.UserRole, QtC.QUrl(f"http://{ip_final}:8732"))
                self.addItem(item)
        self.itemActivated.connect(self.on_item_clicked)

    def OtherListCreate(self, rack_nr, all_strings):
        self.clear()
        for string, rack, in all_strings.items():
            if rack==rack_nr:
                self.addItem(string)

    def on_item_clicked(self, item):
        current_time = time.time()
        if current_time > self.last_call_time + 0.7:
            url = item.data(QtC.Qt.UserRole)
            QtG.QDesktopServices.openUrl(url)
            self.last_call_time = current_time


class MainWindow(QtW.QMainWindow):
    def __init__(self):
        super().__init__()

        #SET LAYOUT
        window_layout = QtW.QVBoxLayout()
        rack_list_layout = QtW.QHBoxLayout()
        central_widget = QtW.QWidget()
        central_widget.setLayout(window_layout)
        window_layout.addLayout(rack_list_layout)
        self.setCentralWidget(central_widget)

        #DATA ARRAYS ASIGNMENT
        all_strings = {}
        dead_dut = {}
        dead_ctrl = {}
        all_pdu = []

        #Filling arrays with data
        ListCreation.MainLoop(ListCreation, all_strings, dead_dut, dead_ctrl, all_pdu, pduList, platformList)
        racks_list = ListCreation.CreateRackSet(ListCreation, all_strings)
        last_rack = ListCreation.CreateLastRackVar(ListCreation, racks_list)
        racks_list.pop()

        def raportLoop():
            ListCreation.MainLoop(ListCreation, all_strings, dead_dut, dead_ctrl, all_pdu, pduList, platformList)
            for value in racks_list:
                lists_arr[value-1].RackListCreate(value, all_strings, all_pdu)
            self.other_list.OtherListCreate(last_rack, all_strings)
        def raportLoopThread():
            t = threading.Thread(target=raportLoop)
            t.start()

        #Creating list Widgets
        lists_arr = []
        for value in racks_list:
            while len(lists_arr) < value:
                lists_arr.append(None)
            lists_arr[value-1] = ListCreation()
            rack_list_layout.addWidget(lists_arr[value-1])
            lists_arr[value-1].RackListCreate(value, all_strings, all_pdu)

        self.other_list=ListCreation()
        self.other_list.setFlow(QtW.QListView.LeftToRight)
        self.other_list.setViewMode(QtW.QListView.IconMode)
        window_layout.addWidget(self.other_list)
        self.other_list.OtherListCreate(last_rack, all_strings)


        #WINDOW PARAMS
        self.showMaximized()

        #LOOP TIMER
        self.timer = QtC.QTimer()
        self.timer.timeout.connect(raportLoopThread)
        self.timer.start(70000)


#Main window call
app = QtW.QApplication(sys.argv)
main = MainWindow()
main.show()
QtW.QApplication.exec_()