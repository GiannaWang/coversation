import tkinter as tk
from tkinter import ttk, messagebox
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
        self.root.minsize(900, 500)
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

        # 加载功能映射
        self.func_map = load_functions()  # {模块名: 中文名称}
        self.rev_func_map = {v: k for k, v in self.func_map.items()}  # 反向映射 {中文名称: 模块名}

        # 默认功能（dialogDL）
        self.default_func = "dialogDL"
        self.default_cname = self.func_map.get(self.default_func, "dialogDL")

        # 创建UI
        try:
            self.create_widgets()
        except Exception as e:
            messagebox.showerror("错误", f"界面初始化失败：\n{e}")
            raise

    def create_widgets(self):
        """创建UI布局"""
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TNotebook.Tab", padding=[12, 6])

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True)

        gen_tab = tk.Frame(notebook)
        dict_tab = tk.Frame(notebook)
        notebook.add(gen_tab, text="生成对话")
        notebook.add(dict_tab, text="修改字典")

        self._build_generate_tab(gen_tab)
        self._build_dict_tab(dict_tab)

    def _build_generate_tab(self, parent):
        main_frame = tk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = tk.Frame(main_frame)
        right_frame = tk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        right_frame.grid(row=0, column=1, sticky="ns", padx=10, pady=5)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=0)

        self.input_text = tk.Text(
            left_frame, font=("Consolas", 12), bg="#f8f8f8", relief="solid", bd=1
        )
        self.output_text = tk.Text(
            left_frame, font=("Consolas", 12), bg="#f8f8f8", relief="solid", bd=1
        )
        self.input_text.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self.output_text.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        left_frame.grid_rowconfigure(0, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)
        left_frame.grid_columnconfigure(1, weight=1)

        tk.Label(right_frame, text="选择功能：", font=("微软雅黑", 12)).pack(pady=5)
        self.func_var = tk.StringVar()
        func_order = ["dialogDL", "dialogDL_auto", "convertChat", "dialogXJ", "dialogXT"]
        func_cnames = [self.func_map.get(key) for key in func_order if self.func_map.get(key)]
        if not func_cnames:
            func_cnames = list(self.func_map.values()) if self.func_map else []
        self.func_dropdown = ttk.Combobox(
            right_frame, textvariable=self.func_var, values=func_cnames, state="readonly", width=18
        )
        if self.default_cname in func_cnames:
            self.func_var.set(self.default_cname)
        elif func_cnames:
            self.func_var.set(func_cnames[0])
        self.func_dropdown.pack(pady=5)

        actions = [
            ("运行", self.run),
            ("清空输入", self.clear_input),
            ("清空输出", self.clear_output),
            ("复制输出", self.copy_output),
        ]
        for text, func in actions:
            btn = tk.Button(right_frame, text=text, width=15, command=func)
            btn.pack(pady=5)

    def _build_dict_tab(self, parent):
        main_frame = tk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = tk.Frame(main_frame)
        right_frame = tk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        right_frame.grid(row=0, column=1, sticky="ns", padx=10, pady=5)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=0)

        self.dict_text = tk.Text(
            left_frame, font=("Consolas", 11), bg="#f8f8f8", relief="solid", bd=1
        )
        self.dict_text.pack(fill=tk.BOTH, expand=True)

        tk.Label(right_frame, text="选择字典：", font=("微软雅黑", 12)).pack(pady=5)
        self.dict_var = tk.StringVar()
        self.dict_options = {
            "顶流降临立绘": {"module": "portrait_dict", "attr": "IMGS", "kind": "list"},
            "情绪字典": {"module": "emotion_dict", "attr": "EMOTION_KEYWORDS", "kind": "dict"},
            "仙劫一落立绘": {"module": "XJ_dict", "attr": "IMGS", "kind": "list"},
            "系统那些年立绘": {"module": "XT_dict", "attr": "IMGS", "kind": "list"},
        }
        dict_labels = list(self.dict_options.keys())
        self.dict_dropdown = ttk.Combobox(
            right_frame, textvariable=self.dict_var, values=dict_labels, state="readonly", width=18
        )
        if dict_labels:
            self.dict_var.set(dict_labels[0])
        self.dict_dropdown.pack(pady=5)
        self.dict_dropdown.bind("<<ComboboxSelected>>", lambda _e: self.load_dict())

        tk.Button(right_frame, text="保存修改", width=15, command=self.save_dict).pack(pady=5)
        tk.Button(right_frame, text="取消修改", width=15, command=self.load_dict).pack(pady=5)

        self.load_dict()

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
    def load_dict(self):
        label = self.dict_var.get()
        if not label:
            return
        info = self.dict_options.get(label)
        if not info:
            return
        module = importlib.import_module(info["module"])
        data = getattr(module, info["attr"])
        self.dict_text.delete("1.0", tk.END)
        self.dict_text.insert(tk.END, json.dumps(data, ensure_ascii=False, indent=2))

    def save_dict(self):
        label = self.dict_var.get()
        if not label:
            return
        info = self.dict_options.get(label)
        if not info:
            return
        raw = self.dict_text.get("1.0", tk.END).strip()
        try:
            data = json.loads(raw)
            if info["kind"] == "dict":
                if not isinstance(data, dict):
                    raise ValueError("根节点必须是字典")
                for key, value in data.items():
                    if not isinstance(value, list):
                        raise ValueError("每个表情必须对应数组")
            else:
                if not isinstance(data, list):
                    raise ValueError("根节点必须是数组")
                for item in data:
                    if not isinstance(item, dict):
                        raise ValueError("数组元素必须是对象")
                    if "名称" not in item or "图片" not in item:
                        raise ValueError("每个对象必须包含“名称”和“图片”字段")

            file_path = os.path.join(FUNCTION_DIR, f"{info['module']}.py")
            if info["kind"] == "dict":
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
            else:
                file_content = "IMGS = " + json.dumps(data, ensure_ascii=False, indent=2) + "\n"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(file_content)
            messagebox.showinfo("成功", "已保存字典")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败：{e}")

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
