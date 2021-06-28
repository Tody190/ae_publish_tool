# -*- coding: utf-8 -*-
# author:yangtao
# time: 2021/06/10
import os
import sys
import re
import _thread

import qdarkstyle
from Qt import QtWidgets
from Qt import QtCore

import ui
import ae_pyjsx_bridge


# import hz.naming_api.naming as naming


class FileName():
    def __init__(self, file_path, comp_name, ext):
        self.file_path = file_path.replace("\\", "/")
        self.comp_name = comp_name
        self.ext = ext
        self.version_num = ""
        self.show = ""
        self.project_short_name = ""
        self.seq = ""
        self.shot = ""
        self.user = ""

        # 版本之前的路径
        self.ver_path = "Y:/{show}/{seq}/{shot}/elements/2d/mgfx/v{version_num}/"
        self.file_name = "{project_short_name}_{seq}_{shot}_mgfx_v{version_num}_{user}{seq_num}{ext}"

        self.__setup_data()

    def __setup_data(self):
        # 插接路径名
        self.__deconstruct_file_path()
        # 拆解comp名
        self.__deconstruct_comp_name()

    def __deconstruct_file_path(self):
        self.show = (self.file_path.split(":")[-1]).split("/")[1]

    def __deconstruct_comp_name(self):
        name_split = self.comp_name.split("_")
        self.project_short_name = name_split[0]
        self.seq = name_split[1]
        self.shot = name_split[2]
        # self.task = name_split[3]
        # self.version = name_split[4]
        self.user = name_split[5]

    def make_ver_path(self):
        # 获取最大版本号
        max_ver_num = 0
        if os.path.isdir(self.ver_path):
            file_list = os.listdir(self.ver_path)
            # 获取所有版本号文件夹名
            for f in file_list:
                match_num = re.match("[v|v](\d{3})", f)
                if match_num:
                    match_num = int(match_num.group(1))
                    if match_num > max_ver_num:
                        max_ver_num = match_num

        ver_fromat = "%03d"
        if max_ver_num > 0:
            self.version_num = ver_fromat % (max_ver_num + 1)
        else:
            self.version_num = ver_fromat % 1

        self.ver_path = self.ver_path.format(show=self.show, seq=self.seq, shot=self.shot, version_num=self.version_num)

    def output_path(self, resolution, is_seq=False):
        """

        :param type: # seq ,media
        :param resolution:
        :return:
        """
        if is_seq:
            seq_num = ".[####]"
        else:
            seq_num = ""
        self.make_ver_path()
        self.file_name = self.file_name.format(project_short_name=self.project_short_name,
                                               seq=self.seq,
                                               shot=self.shot,
                                               version_num=self.version_num,
                                               user=self.user,
                                               seq_num=seq_num,
                                               ext=self.ext
                                               )
        return os.path.join(self.ver_path, resolution, self.file_name).replace("\\", "/")


class Response(ui.MainUI):
    instance = None
    add_item = QtCore.Signal(str)
    def __init__(self):
        super(Response, self).__init__()
        self.ae_js = None
        self.render_queue_list = []  # 渲染的 comp 列表

        self.__setup_data()
        self.__coneect()

    def __setup_data(self):
        self.afterfx_version = self.settings.value(u"ae_version", None)
        self.afterfx_path = self.settings.value(u"afterfx_path", None)
        if self.afterfx_version and self.afterfx_path:
            self.set_afterfx()

    def __coneect(self):
        self.set_afterfx_button.clicked.connect(self.get_afterfx)
        self.add_item.connect(self.add_render_item)
        self.refresh_button.clicked.connect(self.add_render_queue_thread)
        self.daily_button.clicked.connect(lambda: self.render_start("daily"))
        self.publish_button.clicked.connect(lambda: self.render_start("publish"))

    def get_local_afterfx(self):
        afterfx_path = ""

        # 获取 AE 执行文件
        root_path = "C:/Program Files/Adobe"
        if not os.path.isdir(root_path):
            return afterfx_path

        # 查找有没有 Adobe After Effects CC xxxx 的目录
        for f in os.listdir(root_path):
            if re.match("Adobe After Effects .+", f, re.I):
                # 检查 AfterFX.exe 是否存在
                afterfx = os.path.join(root_path, f, "Support Files/AfterFX.exe")
                if os.path.isfile(afterfx):
                    afterfx_path = afterfx.replace("\\", "/")

        return afterfx_path

    def set_afterfx(self):
        # 将按钮设置为 ae 版本名
        self.set_afterfx_button.setText(self.afterfx_version)
        # 获取 ae js python包的实例
        self.ae_js = ae_pyjsx_bridge.AEJSInterface(self.afterfx_path)

    def get_afterfx(self):
        afterfx_path = self.ae_form_dialog(text=self.get_local_afterfx())
        if os.path.isfile(afterfx_path):
            # 检测输入的是否是 AE 路径
            ae_path_search = re.search("(Adobe After Effects .+)\/Support Files\/AfterFX.exe", afterfx_path)
            if ae_path_search:
                # 设置路径
                self.afterfx_version = ae_path_search.group(1)
                self.afterfx_path = afterfx_path
                # 将 AE 名和路径保存到设置中
                self.settings.setValue(u"ae_version", self.afterfx_version)
                self.settings.setValue(u"afterfx_path", self.afterfx_path)
        if self.afterfx_version and self.afterfx_path:
            self.set_afterfx()
        else:
            self.show_critical_dialog(content=u"请输入正确的 AE 软件路径")

    def add_render_queue_thread(self):
        # 显示渲染面板
        if not self.ae_js:
            self.show_critical_dialog(content=u"请先设置之AE版本")
        _thread.start_new_thread(self.add_render_queue, ())

    def add_render_queue(self):
        self.set_button_enabled(False)
        # 清空渲染队列列表
        self.render_queue_listwidget.clear()
        self.ae_js.show_render_queue()
        try:
            # 获取队列
            self.render_queue_list = self.ae_js.get_render_queue()
            i = 0
            for r in self.render_queue_list:
                i += 1
                self.add_item.emit("(%s) %s" % (str(i), r))
            self.set_button_enabled(True)
        except Exception as e:
            print(e)
            self.set_button_enabled(True)

    def get_queue_index(self):
        # 获取当前选中的渲染列表的索引值
        queue_index = self.render_queue_listwidget.currentRow()

        if queue_index < 0:
            self.show_critical_dialog(content=u"请先选中一个需要输出的项")
        else:
            # AE js 渲染列表索引值从 1 开始
            return queue_index + 1

    def get_filename(self, queue_index):
        # 获取工程路径
        file_path = self.ae_js.get_file_path()
        if not file_path:
            self.show_critical_dialog(content=u"请先将工程文件保存至服务器指定位置")

        # 当前选中的额 comp 名
        queue_items_index = queue_index - 1
        comp_name = self.render_queue_list[queue_items_index]
        if len(comp_name.split("_")) < 6:
            self.show_critical_dialog(content=u"合成名命名不正确\n\
正确命名方式应为: [项目名缩写]_[seq]_[shot]_[task]_[v###]_[user]")
            return

        # 获取文件扩展名
        output_file_name = self.ae_js.get_output_file_name(queue_index)
        if not output_file_name:
            self.show_critical_dialog(u"请先随意指定一个输出目标，以便工具拾取正确的文件格式")
        ext = os.path.splitext(output_file_name)[-1]

        FN = FileName(file_path=file_path, comp_name=comp_name, ext=ext)
        return FN

    def creat_output_path(self, output_file):
        """
        创建输出目录
        :param output_file:
        :return:
        """
        output_path = os.path.dirname(output_file)
        if not os.path.isdir(output_path):
            try:
                os.makedirs(output_path)
            except IOError as e:
                self.show_critical_dialog(content=u"无法创建输出目录\n%s" % output_path)

    def render_info(self, queue_index):
        info = ""
        info_list = self.ae_js.get_output_info(queue_index)
        if info_list and len(info_list) == 2:
            info = u"输出格式: %s\n输出路径: %s"%(info_list[0], info_list[1])
        return info

    def render_start(self, type):
        # 获取当前选中的项索引值
        queue_index = self.get_queue_index()
        # 获取选中项目的名字
        render_item_name = self.render_queue_listwidget.item(queue_index-1).text()
        # 获取命名类实例
        FN = self.get_filename(queue_index)
        # 判断是否为序列文件
        is_seq = False
        output_format = self.ae_js.get_setting_format(queue_index)
        if "Sequence" in output_format:
            is_seq = True

        if type == "daily":
            output_file = FN.output_path(resolution="mp4", is_seq=is_seq)

        if type == "publish":
            output_file = FN.output_path(resolution="fullres", is_seq=is_seq)

        # 查看路径是否存，不存在就创建
        self.creat_output_path(output_file)

        # 设置输出路径
        self.ae_js.set_render_output(queue_index, output_file)

        # 激活当前渲染项，并反激活其它渲染项
        activate_status = self.ae_js.activate_render_item(queue_index)
        if activate_status == "false":
            self.show_critical_dialog(u"渲染项(%s)并不是可渲染状态"%str(queue_index))

        # 显示渲染信息
        message = self.render_info(queue_index)
        confirm_status = self.show_info_dialog(title=render_item_name, message=message)
        if confirm_status:
            # 开始渲染
            self.ae_js.render(queue_index)


def load_ui():
    app = QtWidgets.QApplication(sys.argv)
    #app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api="PySide"))
    if not Response.instance:
        Response.instance = Response()
    Response.instance.show()
    Response.instance.raise_()
    sys.exit(app.exec_())


if __name__ == "__main__":
    load_ui()