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

class WifiConnection(QtWidgets.QMainWindow, wifi_ui.Ui_MainWindow):
  
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

    def FindFromSavedList(self, ssid):
        cell = Scheme.find('wlan0', ssid)

        if cell:
            return cell

        return False

    def AddConnection(self, cell, password=None):
        if not cell:
            return False

        scheme = Scheme.for_cell('wlan0', cell.ssid, cell, password)
        scheme.save()
        return scheme


    def DeleteConnection(self, ssid):
        if not ssid:
            return False

        cell = self.FindFromSavedList(ssid)

        if cell:
            cell.delete()
            return True

        return False


    # function to connect to a network   
    def connect_to_wifi(self, name, password):
        cells = list(Cell.all('wlan0'))
        active_cell = None
        for cell in cells:
                if cell.ssid == name:
                        active_cell = cell
                        break

        if active_cell is None:
            return False

        self.DeleteConnection(name)

        savedcell = self.FindFromSavedList(active_cell.ssid)
        if savedcell:
            savedcell.activate()
            return False
        else:
            if cell.encrypted:
                if password:
                    print(password)
                    scheme = self.AddConnection(cell, password)

                    try:
                        scheme.activate()

                    # Wrong Password
                    except wifiexceptions.ConnectionError:
                        Delete(ssid)
                        return False

                    return True
                else:
                    return False
            else:
                scheme = self.AddConnection(cell)

                try:
                    scheme.activate()
                except wifiexceptions.ConnectionError:
                    self.DeleteConnection(ssid)
                    return False

                return True


        scheme = Scheme.for_cell('wlan0', 'home', active_cell, password)
        scheme.save()
        scheme.activate()

        scheme = Scheme.find('wlan0', 'home')
        scheme.activate()

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

    def closeEvent(self, event):
        os.system("sudo kill -9 `pidof matchbox-keyboard`")
        event.accept()

    def __init__(self, parent=None):
        super(WifiConnection, self).__init__(parent)
        self.setWindowIcon(QtGui.QIcon('logo.ico'))
        self.setupUi(self)

        print(list(Cell.all('wlan0')))
        self.cb_wifi_names.addItems(self.get_wifi_list())
        self.pb_connect.clicked.connect(self.pb_connect_clicked)
        self.setWindowFlags(Qt.WindowStaysOnBottomHint)
        self.showMaximized()
        self.enable_keyboard()
        #print(devices)
        #print(devices)

    def enable_keyboard(self):
        print('enabling')
        subprocess.Popen("matchbox-keyboard")

    def pb_connect_clicked(self):
        self.lb_conn_status.setText("Connecting...")
        self.lb_conn_status.repaint()
        name = self.cb_wifi_names.currentText()

        #self.createNewConnection(name, name, self.le_password.text())
        result = self.connect_to_wifi(name, self.le_password.text())
        if result == False:
            self.lb_conn_status.setText("Connection Failed")
            return
        
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
