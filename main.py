import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import pyperclip
import importlib.util  # 显式导入util，确保Python版本≥3.4
import importlib
import json

# ------------------------------
# 路径设置与系统路径添加
# ------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FUNCTION_DIR = os.path.join(BASE_DIR, "functions")
# 将functions目录添加到系统路径（关键：解决模块导入问题）
if FUNCTION_DIR not in sys.path:
    sys.path.insert(0, FUNCTION_DIR)

FUNC_NAMES_JSON = os.path.join(BASE_DIR, "func_names.json")

# ------------------------------
# 资源路径处理（兼容py运行，移除exe相关冗余）
# ------------------------------
def resource_path(relative_path):
    """获取资源路径（仅保留py运行逻辑）"""
    return os.path.join(BASE_DIR, relative_path)

# ------------------------------
# 载入功能名称映射
# ------------------------------
def load_functions():
    """读取func_names.json，返回 {模块名: 中文名称}"""
    json_path = resource_path("func_names.json")
    if not os.path.exists(json_path):
        messagebox.showerror("错误", f"找不到func_names.json\n路径：{json_path}")
        # 自动生成空的func_names.json（容错）
        with open(json_path, "w", encoding="utf-8") as f:
            f.write("{}")
        return {}

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            import json
            func_map = json.load(f)
        return func_map
    except Exception as e:
        messagebox.showerror("错误", f"func_names.json解析失败：\n{e}")
        return {}

# ------------------------------
# 动态加载模块（改用importlib.util，兼容Python3.4+）
# ------------------------------
def load_module(module_name):
    """加载指定名称的模块（从functions目录）"""
    module_path = os.path.join(FUNCTION_DIR, f"{module_name}.py")
    if not os.path.exists(module_path):
        raise FileNotFoundError(f"模块文件不存在：{module_path}")

    try:
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        raise ImportError(f"模块加载失败：{e}")

# ------------------------------
# UI主程序
# ------------------------------
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("文本转换工具 v1.0")
        self.root.geometry("1100x600")

        # 加载功能映射
        self.func_map = load_functions()  # {模块名: 中文名称}
        self.rev_func_map = {v: k for k, v in self.func_map.items()}  # 反向映射 {中文名称: 模块名}

        # 默认功能（dialogDL）
        self.default_func = "dialogDL"
        self.default_cname = self.func_map.get(self.default_func, "dialogDL")

        # 创建UI
        self.create_widgets()

    def create_widgets(self):
        """创建UI布局"""
        # 左侧输入区
        self.input_text = tk.Text(self.root, width=40, height=35, font=("Consolas", 12))
        self.input_text.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        # 中间输出区
        self.output_text = tk.Text(self.root, width=40, height=35, font=("Consolas", 12))
        self.output_text.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        # 右侧工具栏
        right_frame = tk.Frame(self.root)
        right_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # 功能选择下拉框
        tk.Label(right_frame, text="选择功能：", font=("微软雅黑", 12)).pack(pady=5)
        self.func_var = tk.StringVar()
        func_cnames = list(self.func_map.values()) if self.func_map else []
        self.func_dropdown = ttk.Combobox(
            right_frame,
            textvariable=self.func_var,
            values=func_cnames,
            state="readonly",
            width=18
        )
        # 设置默认选中
        if self.default_cname in func_cnames:
            self.func_var.set(self.default_cname)
        elif func_cnames:
            self.func_var.set(func_cnames[0])
        self.func_dropdown.pack(pady=5)

        # 功能按钮（移除了修改配置按钮）
        actions = [
            ("运行", self.run),
            ("清空输入", self.clear_input),
            ("清空输出", self.clear_output),
            ("复制输出", self.copy_output),
            ("编辑表情词典", self.edit_emotion_dict),
            ("顶流立绘", self.edit_portrait_dict),
            ("退出", self.root.destroy),
        ]
        for text, func in actions:
            btn = tk.Button(right_frame, text=text, width=15, command=func)
            btn.pack(pady=5)

    def run(self):
        """运行选中的功能（修正版）"""
        # 获取选中的中文名称和模块名
        selected_cname = self.func_var.get()
        if not selected_cname:
            messagebox.showwarning("提示", "请选择功能")
            return

        module_name = self.rev_func_map.get(selected_cname)
        if not module_name:
            messagebox.showerror("错误", "无法找到对应模块名")
            return

        # 获取输入文本
        input_text = self.input_text.get("1.0", tk.END).strip()
        if not input_text:
            messagebox.showwarning("提示", "请先输入文本")
            return

        # 加载模块并执行
        try:
            module = load_module(module_name)
            if not hasattr(module, "process"):
                raise AttributeError(f"模块{module_name}.py缺少process(input_text)函数")

            # 执行处理函数（不再传递配置参数）
            result = module.process(input_text)
            result_str = str(result) if result is not None else ""  # 处理None值

            # 显示结果（清空原有内容）
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, result_str)

        except Exception as e:
            messagebox.showerror("错误", f"执行失败：\n{str(e)}")

    def clear_input(self):
        """清空输入区"""
        self.input_text.delete("1.0", tk.END)

    def clear_output(self):
        """清空输出区"""
        self.output_text.delete("1.0", tk.END)

    def copy_output(self):
        """复制输出区内容到剪贴板"""
        output_text = self.output_text.get("1.0", tk.END).strip()
        if not output_text:
            messagebox.showwarning("提示", "输出区为空")
            return

        pyperclip.copy(output_text)
        messagebox.showinfo("成功", "已复制到剪贴板")

    def edit_emotion_dict(self):
        """编辑表情词典（emotion_dict.py）"""
        editor = tk.Toplevel(self.root)
        editor.title("编辑表情词典")
        editor.geometry("600x500")
        editor.minsize(500, 400)

        text = tk.Text(editor, font=("Consolas", 11))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        emotion_module = importlib.import_module("emotion_dict")
        text.insert(tk.END, json.dumps(emotion_module.EMOTION_KEYWORDS, ensure_ascii=False, indent=2))

        btn_frame = tk.Frame(editor)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        def save_dict():
            raw = text.get("1.0", tk.END).strip()
            try:
                data = json.loads(raw)
                if not isinstance(data, dict):
                    raise ValueError("根节点必须是字典")
                for key, value in data.items():
                    if not isinstance(value, list):
                        raise ValueError("每个表情必须对应数组")
                file_path = os.path.join(FUNCTION_DIR, "emotion_dict.py")
                file_content = (
                    "EMOTION_KEYWORDS = "
                    + json.dumps(data, ensure_ascii=False, indent=2)
                    + "\n\n\n"
                    + "def detect_emotion(text):\n"
                    + "    if not text:\n"
                    + "        return None\n"
                    + "    for emotion, keywords in EMOTION_KEYWORDS.items():\n"
                    + "        for keyword in keywords:\n"
                    + "            if keyword in text:\n"
                    + "                return emotion\n"
                    + "    return None\n"
                )
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(file_content)
                messagebox.showinfo("成功", "已保存表情词典")
                editor.destroy()
            except Exception as e:
                messagebox.showerror("错误", f"保存失败：{e}")

        tk.Button(btn_frame, text="保存", width=10, command=save_dict).pack(side=tk.RIGHT, padx=5)
        tk.Button(btn_frame, text="取消", width=10, command=editor.destroy).pack(side=tk.RIGHT)

    def edit_portrait_dict(self):
        """编辑顶流立绘（portrait_dict.py）"""
        editor = tk.Toplevel(self.root)
        editor.title("编辑顶流立绘")
        editor.geometry("700x550")
        editor.minsize(600, 450)

        text = tk.Text(editor, font=("Consolas", 11))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        portrait_module = importlib.import_module("portrait_dict")
        text.insert(tk.END, json.dumps(portrait_module.IMGS, ensure_ascii=False, indent=2))

        btn_frame = tk.Frame(editor)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        def save_dict():
            raw = text.get("1.0", tk.END).strip()
            try:
                data = json.loads(raw)
                if not isinstance(data, list):
                    raise ValueError("根节点必须是数组")
                for item in data:
                    if not isinstance(item, dict):
                        raise ValueError("数组元素必须是对象")
                    if "名称" not in item or "图片" not in item:
                        raise ValueError("每个对象必须包含“名称”和“图片”字段")
                file_path = os.path.join(FUNCTION_DIR, "portrait_dict.py")
                file_content = "IMGS = " + json.dumps(data, ensure_ascii=False, indent=2) + "\n"
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(file_content)
                messagebox.showinfo("成功", "已保存顶流立绘")
                editor.destroy()
            except Exception as e:
                messagebox.showerror("错误", f"保存失败：{e}")

        tk.Button(btn_frame, text="保存", width=10, command=save_dict).pack(side=tk.RIGHT, padx=5)
        tk.Button(btn_frame, text="取消", width=10, command=editor.destroy).pack(side=tk.RIGHT)

# ------------------------------
# 程序入口
# ------------------------------
if __name__ == "__main__":
    # 检查Python版本（确保≥3.4）
    if sys.version_info < (3, 4):
        messagebox.showerror("错误", "Python版本需≥3.4，请升级Python")
        sys.exit(1)

    root = tk.Tk()
    app = App(root)
    root.mainloop()
