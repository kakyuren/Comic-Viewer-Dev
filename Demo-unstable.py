#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import re
import pickle
from PyQt5.QtWidgets import (QApplication,QPushButton,QMainWindow,QWidget,QSizePolicy,QLabel,QScrollArea,QToolBar,QMessageBox)
from PyQt5.QtCore import Qt,QUrl,QPoint,pyqtSignal,QByteArray,QObject
from PyQt5.QtWebKitWidgets import *
from PyQt5.QtGui import QImage,QPixmap,QPainter
from PyQt5.QtNetwork import *

sys.setrecursionlimit(2000)
homepage = "http://www.tuku.cc"

class Record:
    currenturl = ''
    centralHeight = 0
    centralWidth = 0
    targeturl = "http://www.tuku.cc"

class PostionCheck:
    def __init__(self,a=None,b=None):
        self.width=a
        self.mx=b
    def location(self):
        if self.mx < self.width//2:
            return "left"
        else:
            return "right"


class Page(QWebPage):
    def __init__(self,targeturl):
        super().__init__()
        self.userAgentForUrl(QUrl(Record.targeturl))
        self.setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.html = self.mainFrame().toHtml()

    def userAgentForUrl(self,url):
        return "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.80 Safari/537.36"

    def getHtml(self):
        return self.mainFrame().toHtml()

class Signal(QObject):
    sendUrl = pyqtSignal(str)
    rebuildScreen = pyqtSignal()
    analyseHtml = pyqtSignal()

class WebView(QWebView):
    def __init__(self,targeturl):
        super().__init__()
        self.setPage(Page(Record.targeturl))
        self.page().linkClicked.connect(self.clicked)
        self.load(QUrl(Record.targeturl))
        self.sin = Signal()

    def clicked(self,url):
        self.load(url)

    def goback(self):
        self.back()

    def goforward(self):
        self.forward()

    def reloadpage(self):
        self.reload()

    def catchImgUrl(self):
        htmlcode = self.page().getHtml()
        pa = re.compile(r"http://tkpic.tukucc.com/[\S]*")
        pa2 = re.compile(r"<a[\s]id=\"nextpage\"[\s]*href=\"/comic/[\w]*[\S]*\"")
        pa3 = re.compile(r"<a[\s]id=\"nextchapter\"[\s]*href=\"/comic/[\w]*[\S]*\"")
        if pa.findall(htmlcode):
            currentimgurl = pa.findall(htmlcode)[0][:-1]
            nexturl = pa2.findall(htmlcode)[0][23:][:-1]
            nextchapter = pa3.findall(htmlcode)[0][26:][:-1]
            nexturl = homepage+nexturl
            nextchapter = homepage+nextchapter
            qucurrenturl = self.url()
            qscurrenturl = qucurrenturl.toString()
            Record.currenturl = qscurrenturl
            self.sin.sendUrl.emit(currentimgurl)
            if self.url() != QUrl(nexturl):
                Record.targeturl = nexturl
            else:
                Record.targeturl = nextchapter

class Label(QLabel):
    def __init__(self,img):
        super().__init__()
        self.setPixmap(img)
        self.setAlignment(Qt.AlignHCenter)

    def scaledToHeight(self):
        img=img.scaledToHeight(Record.centralHeight,0)
        self.setPixmap(img)

class Scroll(QScrollArea):
    def __init__(self,img):
        super().__init__()
        self.setWidget(Label(img))
        self.setWidgetResizable(True)
        self.point = PostionCheck()
        self.signal = Signal()

    def mousePressEvent(self,event):
        if event.button() == Qt.LeftButton:
            self.point.mx = event.x()
            if self.point.location() == "left":pass
            else:
                self.signal.rebuildScreen.emit()

    def resizeEvent(self,event):
        self.point.width = self.width()

class MainScreen(QMainWindow):
    def __init__(self,targeturl):
        super().__init__()
        self.signal = Signal()
        self.setWindowTitle("有进无退漫画盗链阅读")
        self.webview = WebView(Record.targeturl)
        self.ptoolwidget = QWidget()
        self.ptoolbar = self.addToolBar('工具栏')
        statusbar = self.statusBar()
        self.initPageUI()
        self.setGeometry(50, 50, 1440, 960)

        if self.ptoolbar:
            self.ptoolwidget.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
            pblist = Button().pbuttonlist
            self.ptoolbar.addWidget(self.ptoolwidget)

        for i in range(len(pblist)):
            self.ptoolbar.addWidget(pblist[i])
        pblist[0].clicked.connect(self.centralWidget().goback)
        pblist[1].clicked.connect(self.centralWidget().forward)
        pblist[2].clicked.connect(self.centralWidget().reload)

    def initPageUI(self):

        self.setCentralWidget(self.webview)
        self.centralWidget().loadFinished.connect(self.webview.catchImgUrl)
        self.centralWidget().sin.sendUrl.connect(self.getUrl)

    def getUrl(self,testurl):
        manager = QNetworkAccessManager(self)
        manager.finished.connect(self.replyFinished)
        manager.get(QNetworkRequest(QUrl(testurl)))

    def replyFinished(self,reply):
        qbytearray = reply.readAll()
        img = QPixmap()
        img.loadFromData(qbytearray)
        h = self.centralWidget().height()
        # img=img.scaledToHeight(h)
        self.scroll = Scroll(img)
        self.ptoolbar.setVisible(False)
        self.setCentralWidget(self.scroll)
        self.scroll.signal.rebuildScreen.connect(self.test)

    def test(self):
        self.setCentralWidget(WebView(Record.targeturl))
        self.centralWidget().setVisible(False)
        self.centralWidget().loadFinished.connect(self.centralWidget().catchImgUrl)
        self.centralWidget().sin.sendUrl.connect(self.getUrl)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, '退出',
            "是否退出？", QMessageBox.Yes | 
            QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
           with open('history.pickle','wb') as historysavedata:
            pickle.dump(Record.currenturl,historysavedata)
            event.accept()
        else:
            event.ignore()

class StatusBar(QWidget):
    pass

class Button(QPushButton):
    def __init__(self):
        super().__init__()
        self.pbuttonlist = [QPushButton('<--'),QPushButton('-->'),QPushButton('刷新')]

class MessageBox(QMessageBox):
    def __init__(self):
        super().__init__()
        startquestion = self.question(self,'开始',
            "是否继续上次页面？", QMessageBox.Yes | 
            QMessageBox.No, QMessageBox.No)
        if startquestion == QMessageBox.Yes:
            if os.path.exists('history.pickle'):
                f = open('history.pickle', 'rb')
                historylist = pickle.load(f)
                Record.targeturl = historylist
        else:
            Record.targeturl = homepage


if __name__ == '__main__':
    app = QApplication(sys.argv)
    start = MessageBox()
    screen = MainScreen(Record.targeturl)
    screen.show()
    sys.exit(app.exec_())
