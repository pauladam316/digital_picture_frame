from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import *
import sys
import wifi_ui
import subprocess
import os
import urllib.request
import time
from wifi import Cell, Scheme
from wifi import exceptions as wifiexceptions
from threading import Thread

class WifiFinder:
    def __init__(self, *args, **kwargs):
        self.server_name = kwargs['server_name']
        self.password = kwargs['password']
        self.interface_name = kwargs['interface']
        self.main_dict = {}

    def run(self):
        command = """sudo iwlist wlan0 scan | grep -ioE 'ssid:"(.*{}.*)'"""
        result = os.popen(command.format(self.server_name))
        result = list(result)

        if "Device or resource busy" in result:
                return None
        else:
            ssid_list = [item.lstrip('SSID:').strip('"\n') for item in result]
            print("Successfully get ssids {}".format(str(ssid_list)))

        for name in ssid_list:
            try:
                result = self.connection(name)
            except Exception as exp:
                print("Couldn't connect to name : {}. {}".format(name, exp))
            else:
                if result:
                    print("Successfully connected to {}".format(name))

    def connection(self, name):
        try:
            os.system("nmcli d wifi connect {} password {}".format(name,
       self.password))
        except:
            raise
        else:
            return True


class WifiConnection(QtWidgets.QMainWindow, wifi_ui.Ui_MainWindow):
  

    def check_connection(self, host='http://google.com'):
        try:
            urllib.request.urlopen(host) #Python 3.x
            return True
        except:
            return False

    def get_wifi_list(self):
        wifi_list = list(Cell.all('wlan0'))
        ssids = []
        for element in wifi_list:
                ssids.append(element.ssid)
        return ssids
        # using the check_output() for having the network term retrieval
        devices = subprocess.check_output(['netsh','wlan','show','network'])
        #os.system('cmd /c "netsh wlan show networks"')

        # decode it to strings
        devices = devices.decode('ascii')
        devices= devices.replace("\r","")
        devices = devices.split("\n")
        for line in devices:
            #print(line)
            if "SSID" in line:
                line.replace("\n","")
                split_line = line.split(" : ")
                
                wifi_list.append(split_line[1])

        return wifi_list

    def refresh_wifi_list(self):
        self.cb_wifi_names.clear()
        self.cb_wifi_names.addItems(self.get_wifi_list())

    def closeEvent(self, event):
        os.system("dbus-send --type=method_call --dest=org.onboard.Onboard /org/onboard/Onboard/Keyboard org.onboard.Onboard.Keyboard.Hide")
        event.accept()

    def __init__(self, parent=None):
        super(WifiConnection, self).__init__(parent)
        self.setWindowIcon(QtGui.QIcon('logo.ico'))
        self.setupUi(self)

        print(list(Cell.all('wlan0')))
        self.cb_wifi_names.addItems(self.get_wifi_list())
        self.pb_connect.clicked.connect(self.pb_connect_clicked)
        self.pushButton_2.clicked.connect(self.refresh_wifi_list)
        self.setWindowFlags(Qt.WindowStaysOnBottomHint)
        self.show()
        self.enable_keyboard()
        #print(devices)
        #print(devices)

    def enable_keyboard(self):
        print('enabling')
        os.system("dbus-send --type=method_call --dest=org.onboard.Onboard /org/onboard/Onboard/Keyboard org.onboard.Onboard.Keyboard.Show")

    def pb_connect_clicked(self):
        name = self.cb_wifi_names.currentText()

        #self.createNewConnection(name, name, self.le_password.text())
        #result = self.connect_to_wifi(name, self.le_password.text())
        #if result == False:
        #    self.lb_conn_status.setText("Connection Failed")
        #    return
        WF = WifiFinder(server_name=name,
               password=self.le_password.text(),
               interface='wlan0')
        thread = Thread(target = WF.run)
        thread.start()


        timeout = time.time()+30
        connected = False
        i = 0
        while (time.time() < timeout):
            time.sleep(0.5)
            connection_string = "Connecting"
            for element in range(i%4):
                connection_string += "."
            self.lb_conn_status.setText(connection_string)
            QApplication.processEvents()
            i += 1
            if (self.check_connection()):
                connected = True
                break
        
        if (connected == False):
            self.lb_conn_status.setText("Connection Failed")
        else:
            self.lb_conn_status.setText("Connection Succesful")



        
def main():
    app = QApplication(sys.argv)
    form = WifiConnection()
    form.show()
    app.exec()

if __name__ == '__main__':
    main()
