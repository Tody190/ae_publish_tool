# -*- coding: utf-8 -*-
# author:yangtao
# time: 2021/06/10
import os
import sys
import re

import qdarkstyle
from Qt import QtWidgets

import ui
import ae_pyjsx_bridge

import hz.naming_api.naming as naming


class FileName():
    def __init__(self, file_path, comp_name):
        self.file_path = file_path
        self.comp_name = comp_name

        self.data = self.__deconstruct()    # 组成输出路径的基本元素

    def __deconstruct(self):
        # 切割文件路径
        root, show, seq, shot, category, task, publish = naming.deconstruct_filepath(self.file_path)
        project, project_short_name, project_id = naming.project_details_from_full_project(show)

        return {
            "name": '',
            "category": "2d",
            "ext": ".pm4",
        }

        """
        path: "{root}/{project_name}_{project_short_name}-{project_id}/{seq}/{shot}/elements/{category}/{task}"
        file: "{render_layer}v{version}/{resolution}/{aov}{project_short_name}_{seq}_{shot}_{task}_{name}v{version}_{user}{eye}.{render_layer2}{frame_range}{ext}"
         assets:
        :return:

        data = {
            "name": '',
            "category": "2d",
            "ext": ".pm4",
            "project_name": self.project_name,
            "project_short_name": self.project_short_name,
            "resolution": 'fullres',
            "root": self.root,
            "seq": seq_name,
            "shot": shot_name,
            "render_layer": None,
            "render_layer2": None,
            "project_id": self.project_id,
            "task": task_name,
            "user": user_short_name,
            "aov": None,
            "frame_range": None,
            "eye": None,
            "version": version
        }

        return data
        """

    def daily_path(self):
        pass

    def publish_path(self):
        pass


class Response(ui.MainUI):
    instance = None
    def __init__(self):
        super(Response, self).__init__()
        self.ae_js_interface = None
        self.render_comp_list = []    # 渲染的 comp 列表

        self.__setup_data()
        self.__coneect()

    def __setup_data(self):
        # 获取 AE 路径
        self.afterfx_version = self.settings.value(u"ae_version", None)
        self.afterfx_path = self.settings.value(u"afterfx_path", None)
        if self.afterfx_path:
            self.set_afterfx_button.setText(self.afterfx_version)
            self.ae_js = ae_pyjsx_bridge.AEJSInterface(self.afterfx_path)
            # 添加渲染列表
            self.set_render_queue()

    def __coneect(self):
        self.set_afterfx_button.clicked.connect(self.get_afterfx)
        self.refresh_button.clicked.connect(self.set_render_queue)
        self.publish_button.clicked.connect(self.render_publish)

    def set_render_queue(self):
        # 清空渲染队列列表
        self.render_queue_listwidget.clear()
        if self.ae_js:
            # 获取队列
            self.render_comp_list = self.ae_js.get_render_queue()
            i = 0
            for r in self.render_comp_list:
                i += 1
                self.render_queue_listwidget.addItem("(%s) %s" % (str(i), r))

    def render_daily(self):
        pass

    def render_publish(self):
        # 获取工程路径
        file_path = self.ae_js.get_file_path()

        # 获取当前选中的渲染列表的索引值
        queue_index = self.render_queue_listwidget.currentRow()
        if queue_index < 0:
            self.show_warning_dialog(content=u"请先选中一个需要输出的项")
            return

        # 当前选中的额 comp 名
        comp_name = self.render_comp_list[queue_index]

        # 获取输出路径
        print(file_path, comp_name)
        FN = FileName(file_path, comp_name)
        FN.deconstruct()

        # ddd = self.ae_js.set_render_output(queue_index, r"D:\work\py\yangtao\resource\ae_project\output\test[####]")
        # print(ddd)
        # select_render_queue_items = self.render_queue_listwidget.selectedItems()
        # if select_render_queue_items:
        #     for item in select_render_queue_items:
        #         print(item.text())

    def render_select(self):
        # 获取选中的 index 值
        aa = self.render_comp_list.count()
        print(aa)
        # 通过命名

    def get_local_afterfx(self):
        afterfx_path = ""

        # 获取 AE 执行文件
        root_path = "C:/Program Files/Adobe"
        if not os.path.isdir(root_path):
            return afterfx_path

        # 查找有没有 Adobe After Effects CC xxxx 的目录
        for f in os.listdir(root_path):
            if re.match("Adobe After Effects CC \d+", f, re.I):
                # 检查 AfterFX.exe 是否存在
                afterfx = os.path.join(root_path, f, "Support Files/AfterFX.exe")
                if os.path.isfile(afterfx):
                    afterfx_path = afterfx.replace("\\", "/")

        return afterfx_path

    def get_afterfx(self):
        ae_version = None
        afterfx_path = self.ae_form_dialog(text=self.get_local_afterfx())
        if os.path.isfile(afterfx_path):
            # 检测输入的是否是 AE 路径
            ae_path_search = re.search("(Adobe After Effects CC \d+)\/Support Files\/AfterFX.exe", afterfx_path)
            if ae_path_search:
                ae_version = ae_path_search.group(1)
                # 将 AE 名和路径保存到设置中
                self.settings.setValue(u"ae_version", ae_version)
                self.settings.setValue(u"afterfx_path", afterfx_path)
        if ae_version:
            self.set_afterfx_button.setText(ae_version)
        else:
            self.show_warning_dialog(content=u"请输入正确的 AE 软件路径")


def load_ui():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api="PySide"))
    if not Response.instance:
        Response.instance = Response()
    Response.instance.show()
    Response.instance.raise_()
    sys.exit(app.exec_())


if __name__ == "__main__":
    #load_ui()
    file_path = 'x:/wangzherongyao_non-0067/ep02/0170/assets/mgfx/non_ep02_0170_mgfx_v003_lyy.aep'
    comp_name = 'non_ep02_0170_plate_v002_gen'
    file_name = FileName(file_path, comp_name)
    file_name.deconstruct()