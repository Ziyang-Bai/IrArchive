import zipfile
import hashlib
import os
import io
import glob
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.ttk import Progressbar

def calculate_md5(data):
    """计算数据的 MD5 哈希值"""
    hash_md5 = hashlib.md5()
    hash_md5.update(data)
    return hash_md5.hexdigest()

def extract_zip_from_memory(zip_data, extract_to, progress_callback=None):
    """从内存中的 ZIP 数据解压到指定目录"""
    with zipfile.ZipFile(io.BytesIO(zip_data), 'r') as zipf:
        file_list = zipf.namelist()
        total_files = len(file_list)
        for i, file in enumerate(file_list, start=1):
            zipf.extract(file, extract_to)
            if progress_callback:
                progress_callback(i, total_files)

def unpack_files(base_file, extract_to, progress_callback=None):
    # 修改查找逻辑，直接使用 base_file 作为单文件路径
    if not os.path.exists(base_file):
        raise FileNotFoundError(f"未找到文件: {base_file}")

    # 如果文件名中包含 "_part"，按分卷逻辑处理，否则按单文件处理
    if "_part" in base_file or not base_file.endswith(".ira"):
        part_files = glob.glob(f"{base_file}_part*.ira")
        if not part_files:
            raise FileNotFoundError("未找到任何分卷文件！")
    else:
        part_files = [base_file]

    parts = []
    version = None
    md5_hash = None
    total_chunks = None
    seen_part_nos = set()

    for part_file in part_files:
        with open(part_file, "rb") as f:
            content = f.read()
            header_end = content.find(b'\n')
            if header_end == -1:
                raise ValueError(f"文件 {part_file} 格式错误：未找到换行符分隔头信息。")
            header = content[:header_end].decode('utf-8')
            chunk = content[header_end+1:]
            try:
                ver, md5, part_no_str, total_str = header.split(',', 3)
                part_no = int(part_no_str)
                total = int(total_str)
            except ValueError as e:
                raise ValueError(f"文件 {part_file} 头信息解析失败: {e}")

            if part_no in seen_part_nos:
                raise ValueError(f"错误：分卷号 {part_no} 重复于文件 {part_file}")
            seen_part_nos.add(part_no)

            if part_no < 1 or part_no > total:
                raise ValueError(f"错误：分卷号 {part_no} 超出范围 (1-{total})")

            if version is None:
                version, md5_hash, total_chunks = ver, md5, total
            else:
                if version != ver or md5_hash != md5 or total_chunks != total:
                    raise ValueError(f"文件 {part_file} 头信息不匹配！")

            parts.append((part_no, chunk))

    if len(parts) != total_chunks:
        raise ValueError(f"分卷数量错误，期望 {total_chunks} 个，实际 {len(parts)} 个")

    expected_parts = set(range(1, total_chunks+1))
    missing = expected_parts - seen_part_nos
    if missing:
        raise ValueError(f"缺少分卷号: {missing}")

    parts.sort(key=lambda x: x[0])
    zip_data = b''.join(chunk for _, chunk in parts)

    calculated_md5 = calculate_md5(zip_data)
    if calculated_md5 != md5_hash:
        raise ValueError("MD5校验失败！文件可能损坏。")

    os.makedirs(extract_to, exist_ok=True)
    extract_zip_from_memory(zip_data, extract_to, progress_callback)

def browse_file():
    """浏览分卷文件的基础名称"""
    file_path = filedialog.askopenfilename(
        title="选择分卷文件的基础名称",
        filetypes=[("分卷文件", "*.ira"), ("所有文件", "*.*")]
    )
    if file_path:
        file_entry.delete(0, tk.END)
        file_entry.insert(0, file_path)
        # 自动设置默认解压目录
        default_extract_to = os.path.join(
            os.path.dirname(file_path),
            os.path.splitext(os.path.basename(file_path))[0]
        )
        dir_entry.delete(0, tk.END)
        dir_entry.insert(0, default_extract_to)

def browse_directory():
    """浏览解压目标目录"""
    directory = filedialog.askdirectory(title="选择解压目标目录")
    if directory:
        dir_entry.delete(0, tk.END)
        dir_entry.insert(0, directory)

def start_unpack():
    base_file = file_entry.get()
    extract_to = dir_entry.get()

    if not base_file:
        messagebox.showerror("错误", "请选择分卷文件的基础名称！")
        return
    if not extract_to:
        messagebox.showerror("错误", "请选择解压目标目录！")
        return

    progress_bar["value"] = 0
    progress_label["text"] = "准备解压..."

    try:
        unpack_files(base_file, extract_to, progress_callback=update_progress)
        messagebox.showinfo("完成", f"解包完成，文件已解压至: {extract_to}")
    except Exception as e:
        messagebox.showerror("错误", str(e))

def update_progress(current, total):
    progress_bar["value"] = (current / total) * 100
    progress_label["text"] = f"解压进度: {current}/{total} 文件"

# 创建 GUI
root = tk.Tk()
root.title("IrArchive 解包工具")

frame = tk.Frame(root, padx=10, pady=10)
frame.pack(fill="both", expand=True)

title_label = tk.Label(frame, text="IrArchive 解包工具", font=("Arial", 16))
title_label.grid(row=0, column=0, columnspan=3, pady=10)

file_label = tk.Label(frame, text="分卷文件:")
file_label.grid(row=1, column=0, sticky="e", padx=5, pady=5)

file_entry = tk.Entry(frame, width=40)
file_entry.grid(row=1, column=1, padx=5, pady=5)

file_browse_button = tk.Button(frame, text="浏览", command=browse_file)
file_browse_button.grid(row=1, column=2, padx=5, pady=5)

dir_label = tk.Label(frame, text="解压目录:")
dir_label.grid(row=2, column=0, sticky="e", padx=5, pady=5)

dir_entry = tk.Entry(frame, width=40)
dir_entry.grid(row=2, column=1, padx=5, pady=5)

dir_browse_button = tk.Button(frame, text="浏览", command=browse_directory)
dir_browse_button.grid(row=2, column=2, padx=5, pady=5)

start_button = tk.Button(frame, text="开始解包", command=start_unpack)
start_button.grid(row=3, column=0, columnspan=3, pady=10)

progress_bar = Progressbar(frame, orient="horizontal", length=300, mode="determinate")
progress_bar.grid(row=4, column=0, columnspan=3, pady=10)

progress_label = tk.Label(frame, text="等待操作...")
progress_label.grid(row=5, column=0, columnspan=3, pady=5)

root.mainloop()