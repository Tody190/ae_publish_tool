# -*- coding: utf-8 -*-
# author:yangtao
# time: 2021/06/10


import sys
import os

import qdarkstyle
from Qt import QtWidgets
from Qt import QtCore
from Qt import QtGui


RES_DIRECTORY = os.path.join(os.path.dirname(__file__), "res")


class DropLineEdit(QtWidgets.QLineEdit):
    def __init__(self):
        super(DropLineEdit, self).__init__()
        self.setAcceptDrops(True)
        self.setDragEnabled(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super(DropLineEdit, self).dragEnterEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            url_object = event.mimeData().urls()[0]
            self.setText(url_object.toLocalFile())
        else:
            super(DropLineEdit, self).dropEvent(event)


class FormDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, title=None, message=None, text=None):
        super(FormDialog, self).__init__(parent)
        self.title = title
        self.message = message
        self.text = text

        self.input_value = ""

        self.__setup_ui()
        self.__retranslate_ui()
        self.__setup_connect()

    def __setup_ui(self):
        self.message_label = QtWidgets.QLabel()
        self.edit = DropLineEdit()
        self.button = QtWidgets.QPushButton()

        layout = QtWidgets.QVBoxLayout()
        if self.message:
            layout.addWidget(self.message_label)
        if self.text:
            self.edit.setText(self.text)

        layout.addWidget(self.edit)
        layout.addWidget(self.button)

        self.setLayout(layout)

    def __retranslate_ui(self):
        if self.message:
            self.message_label.setText(self.message)
        if self.title:
            self.setWindowTitle(self.title)
        self.setMinimumWidth(220)
        self.button.setText(u"确定")

    def __setup_connect(self):
        self.button.clicked.connect(self.save_value)
        #self.edit.editingFinished.connect(self.button.clicked.emit)

    def save_value(self):
        self.input_value = self.edit.text()
        self.close()

    def get_value(self):
        return self.input_value


class InfoDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(InfoDialog, self).__init__(parent)

        self.status_value = False

        self.__setup_ui()
        self.__retranslate_ui()
        self.__set_connect()

    def __setup_ui(self):
        self.main_window = QtWidgets.QVBoxLayout(self)

        # 信息框
        self.info_textedit = QtWidgets.QTextEdit()

        self.buttton_layout = QtWidgets.QHBoxLayout()
        # 确认按钮
        self.confirm_button = QtWidgets.QPushButton()
        # 取消按钮
        self.cancel_button = QtWidgets.QPushButton()
        self.buttton_layout.addWidget(self.confirm_button)
        self.buttton_layout.addWidget(self.cancel_button)

        self.main_window.addWidget(self.info_textedit)
        self.main_window.addLayout(self.buttton_layout)

    def __retranslate_ui(self):
        self.confirm_button.setText(u"确定")
        self.cancel_button.setText(u"取消")

    def __set_connect(self):
        self.confirm_button.clicked.connect(self.confirm_info)
        self.cancel_button.clicked.connect(self.cancel_info)

    def show_info(self, title="", content=""):
        # 设置标题
        self.setWindowTitle(title)
        # 设置显示的内容
        self.info_textedit.setText(content)
        #self.show()

    def get_value(self):
        return self.status_value

    def confirm_info(self):
        self.status_value = True
        self.close()

    def cancel_info(self):
        self.status_value = False
        self.close()


class MainUI(QtWidgets.QWidget):
    def __init__(self):
        super(MainUI, self).__init__()
        self.settings = QtCore.QSettings(u"hz_soft", u"ae_publish_tool")  # 保存设置类
        #self.settings.clear()

        self.__setup_ui()
        self.__retranslate_ui()

    def __setup_ui(self):
        self.name_space_layout = QtWidgets.QVBoxLayout(self)
        self.set_afterfx_button = QtWidgets.QPushButton()
        self.render_queue_listwidget = QtWidgets.QListWidget()
        self.refresh_button = QtWidgets.QPushButton()

        self.button_layout = QtWidgets.QHBoxLayout()
        self.daily_button = QtWidgets.QPushButton()
        self.publish_button = QtWidgets.QPushButton()
        self.button_layout.addWidget(self.daily_button)
        self.button_layout.addWidget(self.publish_button)

        self.name_space_layout.addWidget(self.set_afterfx_button)
        self.name_space_layout.addWidget(self.render_queue_listwidget)
        self.name_space_layout.addWidget(self.refresh_button)
        self.name_space_layout.addLayout(self.button_layout)

    def __retranslate_ui(self):
        app_icon = QtGui.QIcon(os.path.join(RES_DIRECTORY, "app_logo.png"))
        self.setWindowIcon(app_icon)
        # 设置窗口大小
        try:
            self.restoreGeometry(self.settings.value(u"mainwindow_geo"))
        except:
            pass

        self.setWindowTitle(u"AE提交工具")
        self.set_afterfx_button.setText(u"未设置AE版本")
        self.refresh_button.setText(u"刷新")
        self.daily_button.setText(u"输出小样")
        self.daily_button.setMinimumHeight(30)
        self.daily_button.setStyleSheet(":hover{background-color: DarkSlateBlue; color:White }")
        self.publish_button.setText(u"输出大样")
        self.publish_button.setMinimumHeight(30)
        self.publish_button.setStyleSheet(":hover{background-color: DarkMagenta; color:White }")

    def show_critical_dialog(self, content):
        QtWidgets.QMessageBox(QtWidgets.QMessageBox.Critical, u"错误", content).exec_()
        raise

    def show_warning_dialog(self, content):
        QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, u"警告", content).exec_()

    def show_form_dialog(self, title, message=None, text=None):
        form_dialog = FormDialog(self, title=title, message=message, text=text)
        form_dialog.exec_()
        return form_dialog.get_value()

    def show_info_dialog(self, title="", message=""):
        info_dialog = InfoDialog(self)
        info_dialog.show_info(title, message)
        info_dialog.exec_()
        return info_dialog.get_value()

    def ae_form_dialog(self, text=""):
        return self.show_form_dialog(title=u"设置AE路径", text=text)

    def add_render_item(self, item_str):
        self.render_queue_listwidget.addItem(item_str)
        self.render_queue_listwidget.scrollToBottom()

    def set_button_enabled(self, status):
        self.refresh_button.setEnabled(status)
        self.daily_button.setEnabled(status)
        self.publish_button.setEnabled(status)

    def closeEvent(self, event):
        self.settings.setValue("mainwindow_geo", self.saveGeometry())

