from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QApplication
import sys
import wifi
import subprocess
import os
import urllib.request
import time

class WifiConnection(QtWidgets.QMainWindow, wifi.Ui_MainWindow):
  
    # function to establish a new connection
    def createNewConnection(self, name, SSID, password):
        config = """<?xml version=\"1.0\"?>
        <WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
            <name>"""+name+"""</name>
            <SSIDConfig>
                <SSID>
                    <name>"""+SSID+"""</name>
                </SSID>
            </SSIDConfig>
            <connectionType>ESS</connectionType>
            <connectionMode>auto</connectionMode>
            <MSM>
                <security>
                    <authEncryption>
                        <authentication>WPA2PSK</authentication>
                        <encryption>AES</encryption>
                        <useOneX>false</useOneX>
                    </authEncryption>
                    <sharedKey>
                        <keyType>passPhrase</keyType>
                        <protected>false</protected>
                        <keyMaterial>"""+password+"""</keyMaterial>
                    </sharedKey>
                </security>
            </MSM>
        </WLANProfile>"""
        command = "netsh wlan add profile filename=\""+name+".xml\""+" interface=Wi-Fi"
        with open(name+".xml", 'w') as file:
            file.write(config)
        os.system(command)

    def check_connection(self, host='http://google.com'):
        try:
            urllib.request.urlopen(host) #Python 3.x
            return True
        except:
            return False

    
    # function to connect to a network   
    def connect_to_wifi(self, name, SSID):
        command = "netsh wlan connect name=\""+name+"\" ssid=\""+SSID+"\" interface=Wi-Fi"
        output = subprocess.check_output(command)
        print(output)
        return True # Connected

    def get_wifi_list(self):
        wifi_list = []
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

    def __init__(self, parent=None):
        super(WifiConnection, self).__init__(parent)
        self.setWindowIcon(QtGui.QIcon('logo.ico'))
        self.setupUi(self)

        
        self.cb_wifi_names.addItems(self.get_wifi_list())
        self.pb_connect.clicked.connect(self.pb_connect_clicked)
        self.showMaximized()
        #print(devices)
        #print(devices)

    def pb_connect_clicked(self):
        self.lb_conn_status.setText("Connecting...")
        self.lb_conn_status.repaint()
        name = self.cb_wifi_names.currentText()

        self.createNewConnection(name, name, self.le_password.text())
        self.connect_to_wifi(name, name)

        timeout = time.time()+30
        connected = False
        while (time.time() < timeout):
            if (self.check_connection()):
                print("connection")
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