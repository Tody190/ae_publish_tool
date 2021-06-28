# -*- coding: utf-8 -*-
# author:yangtao
# time: 2021/06/10
"""
参考的 AE_PyJsx 写的 ae 的 python 包装器
https://github.com/kingofthebongo/AE_PyJsx
"""

import os
import time
import re
import subprocess
import tempfile


# JS commands 的 python 包装器
class AEJSWrapper(object):
    def __init__(self, afterfx):
        self.afterfx = afterfx  # AE 的应用位置
        # 生成临时文件保存js指令
        self.js_script_file = self.__build_temp_file("js_script_file.jsx")
        # 生成临时文件保存返回结果
        self.ret_file = self.__build_temp_file("ret_file")
        self.ret_file_clean = "/" + self.ret_file.replace("\\", "/").replace(":", "").lower()
        # 获取记录获取返回值的文件最后修改时间
        self.last_mod_time = os.path.getmtime(self.ret_file)
        # 需要执行的 js 指令列表
        self.commands = ""

    def make_commands(self, execute_commands, ret_val=None):
        # 拼接要执行的 js 脚本
        # 脚本包含 写入返回值 和 写入报错信息功能
        self.commands = (
                """
// 要执行的脚本
%s
                """ % str(execute_commands)
        )

        if ret_val:
            self.commands += (
                """
                
function writ_ret(ret_val) {
var dat_file = new File("%s");
dat_file.open("w");
dat_file.writeln(String(ret_val));
dat_file.close();
}

// 保存返回值
try {
var ret_val = %s;
writ_ret(ret_val);
} catch (e) {
// 将报错写入返回值
writ_ret(e);
}
                """ % (self.ret_file_clean,
                       str(ret_val))
            )


    def __build_js_file(self):
        """
        将 js 指令写入 临时的 js 文件
        :param commands:
        :return:
        """
        with open(self.js_script_file, "wb") as f:
            for command in self.commands:
                f.write(command)

    def __build_temp_file(self, file_name):
        """
        :return:
        """
        tmp_path = tempfile.gettempdir()
        tmp_file = os.path.join(tmp_path, file_name)
        f = open(tmp_file, "wb")
        f.close()
        return tmp_file

    def open_ae(self):
        # 打开AE
        target = [self.aeApp]
        subprocess.Popen(target)

    def execute_js(self, commands, ret_val=None):
        """
        运行 js 脚本
        :param ret_val: 需要返回的参数
        :param commands: 执行的 js 脚本
        :return:
        """
        # 生成要执行的 js 脚本
        self.make_commands(execute_commands=commands,
                           ret_val=ret_val)

        # 指令写入临时 js 文件
        self.__build_js_file()
        # 运行
        target = [self.afterfx, "-ro", self.js_script_file]
        ret = subprocess.Popen(target)

        # 读取返回值
        if ret_val:
            return self.read_ret()

    def read_ret(self):
        """
        读取返回值
        :return:
        """
        # 等待文件更新
        updated = False
        while not updated:
            # 等待文件写入
            time.sleep(1)
            # 获取当前文件最后修改时间
            this_mod_time = os.path.getmtime(self.ret_file)
            # 如果当前时间不等于文件创建时间，停止循环
            if str(this_mod_time) != str(self.last_mod_time):
                updated = True
                self.last_mod_time = this_mod_time

        f = open(self.ret_file, "r+")
        content = f.read()
        f.close()

        if content:
            content = content.replace("\n", "")
        return content


class AEJSInterface(AEJSWrapper):
    def __init__(self, afterfx):
        super(AEJSInterface, self).__init__(afterfx=afterfx)

    def activate_render_item(self, queue_index):
        command = (
            """
var render_queue_items = app.project.renderQueue.items;
for(var i=1; i <=render_queue_items.length; i++ ){
    try{
    app.project.renderQueue.item(i).render = false;
    } catch(e){
    }
}

var activate_status = "true";
try{
app.project.renderQueue.item(%s).render = true;
} catch(e){
var activate_status = "false";
}
            """
        ) % queue_index
        activate_status = self.execute_js(command, ret_val="activate_status")
        return activate_status

    def get_render_queue(self):
        # 队列中的渲染列表名
        command = (
            """
var render_queue_items = app.project.renderQueue.items;
var render_queue_comp = [];
for(var i=1; i <=render_queue_items.length; i++ ){
    var comp_name = app.project.renderQueue.item(i).comp.name;
    render_queue_comp.push(comp_name);}
            """
        )

        render_queue_comp = self.execute_js(command, ret_val="render_queue_comp")
        if render_queue_comp:
            return render_queue_comp.split(",")
        else:
            return []

    def get_render_queue_and_status(self):
        # 队列中的渲染列表名
        command = (
            """
var render_queue_items = app.project.renderQueue.items;
var render_queue_comp = [];
for(var i=1; i <=render_queue_items.length; i++ ){
    var comp_name = app.project.renderQueue.item(i).comp.name;
    render_queue_comp.push(comp_name);
    var render_item_status = app.project.renderQueue.item(i).status;
    render_queue_comp.push(render_item_status);}
            """
        )

        render_queue_comp = self.execute_js(command, ret_val="render_queue_comp")

        if render_queue_comp:
            return render_queue_comp.split(",")
        else:
            return []


        # rende_comp_and_status = {}
        # if render_queue_comp:
        #     rende_comp_list = render_queue_comp.split(",")
        #     for i, item in enumerate(rende_comp_list):
        #         if (i % 2) == 0:
        #             rende_comp_and_status["(%s)%s"%(str(i), item)] = rende_comp_list[i+1]
        #
        # return rende_comp_and_status

    def get_render_item_status(self, queue_index):
        # 获取渲染状态
        command = (
            """
status_num = app.project.renderQueue.item(%s).status
            """
        ) % queue_index

        return self.execute_js(command, ret_val="status_num")

    def show_render_queue(self):
        command = (
            """
app.project.renderQueue.showWindow(true)
            """
        )
        self.execute_js(command)

    def render(self, queue_index):
        command = (
            """
// 尝试将所有渲染项目移除渲染队列
var render_queue_items = app.project.renderQueue.items;
for(var i=1; i <=render_queue_items.length; i++ ){
    try{
    app.project.renderQueue.item(i).render = false;
    } catch(e){
    }
}

// 将当前项添加到渲染队列
var activate_status = true;
try{
app.project.renderQueue.item(%s).render = true;
} catch(e){
var activate_status = false;
}

// 如果添加成功，就开始渲染
if (activate_status){
app.project.renderQueue.render()
}
            """
        ) % queue_index
        self.execute_js(command)

    def get_file_path(self):
        # 获取当前工程的完整路径
        command = (
            """
file_path = app.project.file
            """
        )
        file_path = self.execute_js(command, ret_val="file_path")
        try:
            file_path = file_path.replace("\\", "/").split("/", 1)[1].replace("/", ":/", 1)
            return file_path
        except:
            return

    def get_active_comp(self):
        # 获取当前工程的完整路径
        command = (
            """
active_item = app.project.activeItem
            """
        )
        file_path = self.execute_js(command, ret_val="active_item")
        try:
            file_path = file_path.replace("\\", "/").split("/", 1)[1].replace("/", ":/", 1)
            return file_path
        except:
            return

    def get_setting_format(self, queue_index):
        """
        :param queue_index: 渲染列表索引值
        :return:
        """
        command = (
                """
var omItem_str = app.project.renderQueue.item({queue_ui_index}).outputModule(1).getSettings(GetSettingsFormat.STRING).Format;
                """
            ).format(queue_ui_index=queue_index)
        return self.execute_js(command, ret_val="omItem_str")

    def get_output_file_name(self, queue_index):
        """
        :param queue_index: 渲染列表索引值
        :return:
        """
        command = (
            """
var omItem_str = app.project.renderQueue.item({queue_ui_index}).outputModule(1).getSettings(GetSettingsFormat.STRING)["Output File Info"]["File Name"];
            """
        ).format(queue_ui_index=queue_index)
        return self.execute_js(command, ret_val="omItem_str")

    def get_output_info(self, queue_index):
        command = (
            """
var output_info = []
var format = app.project.renderQueue.item({queue_ui_index}).outputModule(1).getSettings(GetSettingsFormat.STRING).Format
output_info.push(format)
var full_flat_path = app.project.renderQueue.item({queue_ui_index}).outputModule(1).getSettings(GetSettingsFormat.STRING)["Output File Info"]["Full Flat Path"]
output_info.push(full_flat_path)
            """
        ).format(queue_ui_index=queue_index)
        output_info = self.execute_js(command, ret_val="output_info")
        if output_info:
            return output_info.split(",")

    def set_render_output(self, queue_index, output_path):
        # 将路径格式化成 AE 可以接受的路径类型
        #
        output_path = "/" + output_path.replace("\\", "/").replace(":", "").lower()
        command = (
            """
var process = app.project.renderQueue.item({item_index}).outputModule(1).file = new File('{output_path}')
            """
        ).format(item_index=queue_index,
                 output_path=output_path)
        self.execute_js(command, ret_val="process")


if __name__ == "__main__":
    # aejs = AEJSInterface(r"C:\Program Files\Adobe\Adobe After Effects CC 2018\Support Files\AfterFX.exe")
    # file = aejs.get_file_path()

    aejsw = AEJSWrapper(r"C:\Program Files\Adobe\Adobe After Effects CC 2018\Support Files\AfterFX.exe")
    command = """
var num=a;
    """
    ret = aejsw.execute_js(command, ret_val="num")
    print(ret)
