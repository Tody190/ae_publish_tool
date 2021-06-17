# -*- coding: utf-8 -*-
# author:yangtao
# time: 2021/06/10
"""
参考的 AE_PyJsx 写的 ae 的 python 包装器
https://github.com/kingofthebongo/AE_PyJsx

AEJSWrapper 需要 AfterFX.exe 作为参数
execute_js 为运行 js 脚本的方法，将 ae 的 js
"""

import os
import time
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

    def make_commands(self, execute_commands, ret_val="null"):
        # 拼接要执行的 js 脚本
        # 脚本包含 写入返回值 和 写入报错信息功能
        self.commands = (
                """
function writ_ret(ret_val) {
var dat_file = new File("%s");
dat_file.open("w");
dat_file.writeln(String(ret_val));
dat_file.close();
}

try {

// 要执行的脚本
%s

// 写入保存返回值的临时文件
// 如果需要获取返回值，写入到临时文件
if (%s) {
var ret_val = %s; //  告诉脚本哪个需要参数的值需要返回
writ_ret(ret_val);
}
// 如果不需要获取返回值，写入“”到临时文件
// 保证读取临时文件循环能正常中断
else{
writ_ret("");
}

} catch (e) {
// 将报错写入返回值
writ_ret(e);
}
            """ % (self.ret_file_clean,
                   execute_commands,
                   ret_val,
                   ret_val)
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

    def execute_js(self, commands, ret_val="null"):
        """
        运行 js 脚本
        :param ret_val:
        :param commands:
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
        ret_str = self.read_ret()
        # 如果设置了返回值，并且有返回结果返回
        if ret_val and ret_str:
            return ret_str
        # 如果不设置返回值并产生了返回结果，应为报错信息，打印之
        if ret_str:
            print(ret_str)

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

        render_queue_comp = self.execute_js(command)
        if render_queue_comp:
            return render_queue_comp.split(",")
        else:
            return []

    def get_file_path(self):
        # 获取当前工程的完整路径
        command = (
            """
file_path = app.project.file
            """
        )
        file_path = self.execute_js(command)
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
        file_path = self.execute_js(command)
        try:
            file_path = file_path.replace("\\", "/").split("/", 1)[1].replace("/", ":/", 1)
            return file_path
        except:
            return

    def output_module_setting(self, queue_index):
        pass

    def set_render_output(self, queue_index, output_path):
        # AE js 渲染列表索引值从 1 开始
        queue_index += 1
        # 将路径格式化成 AE 可以接受的路径类型
        #
        output_path = "/" + output_path.replace("\\", "/").replace(":", "").lower()
        command = (
            """
aa = app.project.renderQueue.item({item_index}).outputModule(1).file = new File('{output_path}')
            """
        ).format(item_index=queue_index,
                 output_path=output_path)
        print(command)

        return self.execute_js(command)


if __name__ == "__main__":
    # aejs = AEJSInterface(r"C:\Program Files\Adobe\Adobe After Effects CC 2018\Support Files\AfterFX.exe")
    # file = aejs.get_file_path()

    aejsw = AEJSWrapper(r"C:\Program Files\Adobe\Adobe After Effects CC 2018\Support Files\AfterFX.exe")
    command = """
var num=a;
    """
    ret = aejsw.execute_js(command, ret_val="num")
    print(ret)
