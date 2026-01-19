import argparse
import os
import sys
import importlib.util

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FUNCTION_DIR = os.path.join(BASE_DIR, "functions")

if FUNCTION_DIR not in sys.path:
    sys.path.insert(0, FUNCTION_DIR)


def load_module(module_name):
    module_path = os.path.join(FUNCTION_DIR, f"{module_name}.py")
    if not os.path.exists(module_path):
        raise FileNotFoundError(f"模块文件不存在：{module_path}")
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_input_text(path):
    if path:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return sys.stdin.read()


def main():
    parser = argparse.ArgumentParser(description="文本转换工具 CLI")
    parser.add_argument("-f", "--func", required=True, help="功能模块名，如 dialogDL_auto")
    parser.add_argument("-i", "--input", help="输入文件路径，不填则从 stdin 读取")
    args = parser.parse_args()

    text = read_input_text(args.input).strip()
    if not text:
        print("输入为空，请提供 stdin 或 -i 输入文件。", file=sys.stderr)
        sys.exit(1)

    module = load_module(args.func)
    if not hasattr(module, "process"):
        print(f"模块{args.func}.py缺少process(input_text)函数", file=sys.stderr)
        sys.exit(1)

    result = module.process(text)
    if result is None:
        result = ""
    print(result)


if __name__ == "__main__":
    main()
