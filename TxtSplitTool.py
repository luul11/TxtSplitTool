# coded by 伊玛目的门徒  V2.2.0
import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, scrolledtext
import chardet
import time
import threading
import re

# 默认终止词
termination_words = ["章", "回", "节"]

def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']

def is_chapters_title(text, terms):
    chinese_numbers = r'零一二三四五六七八九十百千万亿'
    pattern = r'^第(?:(?:' + '|'.join(re.escape(num) for num in chinese_numbers) + r')+|\d+)(?:' + '|'.join(re.escape(term) for term in terms) + r')?\s+.*$'
    return re.match(pattern, text, re.IGNORECASE) is not None

def get_chapter_title(text, terms):
    chinese_numbers = r'零一二三四五六七八九十百千万亿'
    pattern = r'^第(?:(?:' + '|'.join(re.escape(num) for num in chinese_numbers) + r')+|\d+)(?:' + '|'.join(re.escape(term) for term in terms) + r')?\s+(.*)$'
    match = re.match(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None

def split_by_chapter(file_content, terms):
    chapters = []
    buffer = ''
    first_chapter_found = False  # 标记是否找到了第一个章节标题

    for line in file_content.splitlines():
        stripped_line = line.strip()
        if is_chapters_title(stripped_line, terms):
            if not first_chapter_found and buffer:  # 如果还没有找到第一个章节标题并且缓冲区有内容
                chapters.append(buffer)  # 保存前言
                buffer = ''  # 清空缓冲区
            if buffer:  # 如果已经找到了第一个章节标题并且缓冲区有内容
                chapters.append(buffer)
            buffer = stripped_line + '\n'  # 开始新章节
            first_chapter_found = True  # 设置标记，表示找到了第一个章节标题
        else:
            buffer += stripped_line + '\n'
    if buffer:  # 添加最后一章或后续内容
        chapters.append(buffer)
    return chapters

# 在 save_as_utf8 函数中更新 GUI 并包含章节编号
def save_as_utf8(content, file_path, chapter_title, log_text, chapter_number):
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    # 更新 GUI 日志
    log_text.insert(tk.END, f"章节已保存为：{chapter_number:03d}_{chapter_title}.txt\n")
    log_text.update_idletasks()  # 刷新 GUI

def split_file_by_chapter(file_path, save_dir, log_text, terms):
    encoding = detect_encoding(file_path)
    with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
        content = f.read()

    chapters = split_by_chapter(content, terms)
    log_text.insert(tk.END, "开始按章节切分文件...\n")

    for i, chapter in enumerate(chapters, start=1):
        if not chapter:
            continue
        if i == 1 and not is_chapters_title(chapter.split('\n', 1)[0], terms):
            # 保存前言
            chapter_title = "前言"
            chapter_file_name = f"000_{chapter_title}.txt"
        else:
            chapter_title = get_chapter_title(chapter.split('\n', 1)[0], terms) or f"Chapter_{i}"
            chapter_file_name = f"{i:03d}_{chapter_title[:25]}.txt"
        
        chapter_file_path = os.path.join(save_dir, chapter_file_name)
        save_as_utf8(chapter, chapter_file_path, chapter_title, log_text, i)

    total_time = time.time() - start_time
    log_text.insert(tk.END, f"所有任务执行完毕，总用时：{total_time:.2f}秒\n")
    messagebox.showinfo("完成", "所有文件切分完成！")

def split_file_by_quantity(file_path, save_dir, log_text, quantity):
    encoding = detect_encoding(file_path)
    with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
        lines = f.readlines()

    total_lines = len(lines)
    lines_per_file = (total_lines + quantity - 1) // quantity  # 向上取整

    log_text.insert(tk.END, "开始按数量切分文件...\n")
    log_text.insert(tk.END, "采用智能分段（避免断句）\n")
    log_text.insert(tk.END, f"每份大约 {lines_per_file} 行...\n")

    current_file_lines = []
    current_file_number = 1
    line_count = 0

    for line in lines:
        if line_count < lines_per_file:
            current_file_lines.append(line)
            line_count += 1
        else:
            # 确保段落不被拆开
            if line.strip() and not (line.strip().endswith('。') or line.strip().endswith('\n')):
                current_file_lines.append(line)
                line_count += 1
            else:
                file_name = f"{current_file_number:03d}_part.txt"
                file_path = os.path.join(save_dir, file_name)
                save_as_utf8(''.join(current_file_lines), file_path, f"Part_{current_file_number}", log_text, current_file_number)
                current_file_lines = [line]
                current_file_number += 1
                line_count = 1  # 重置计数器

    if current_file_lines:
        file_name = f"{current_file_number:03d}_part.txt"
        file_path = os.path.join(save_dir, file_name)
        save_as_utf8(''.join(current_file_lines), file_path, f"Part_{current_file_number}", log_text, current_file_number)

    actual_quantity = current_file_number
    log_text.insert(tk.END, f"实际切分数量为：{actual_quantity}\n")

    total_time = time.time() - start_time
    log_text.insert(tk.END, f"所有任务执行完毕，总用时：{total_time:.2f}秒\n")
    messagebox.showinfo("完成", "所有文件切分完成！")

def estimate_chapters(file_path, terms):
    encoding = detect_encoding(file_path)
    with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
        content = f.read()

    chapters = split_by_chapter(content, terms)
    return len(chapters)

def start_splitting():
    source_path = file_path_entry.get()
    save_dir = folder_path_entry.get()

    if not source_path or not save_dir:
        messagebox.showerror("错误", "请确保已选择源文件和目标文件夹")
        return

    global log_text, start_time
    chapters_count = estimate_chapters(source_path, termination_words)
    log_text.insert(tk.END, f"预估共{chapters_count}个章节\n")

    # 显示当前终止词
    current_terms = ', '.join(termination_words)
    new_term = simpledialog.askstring("终止词", f"当前终止词：{current_terms}\n请添加新的终止词（以逗号分隔），或留空继续：", parent=root)
    if new_term:
        new_terms = [term.strip() for term in new_term.split(',')]
        termination_words.extend(new_terms)

    start_time = time.time()
    log_text.insert(tk.END, f"执行UTF-8转化...\n")
    threading.Thread(target=split_file_by_chapter, args=(source_path, save_dir, log_text, termination_words)).start()

def start_splitting_by_quantity():
    source_path = file_path_entry.get()
    save_dir = folder_path_entry.get()

    if not source_path or not save_dir:
        messagebox.showerror("错误", "请确保已选择源文件和目标文件夹")
        return

    quantity = simpledialog.askinteger("输入切分数量", "请输入切分数量：", parent=root, minvalue=1)
    if not quantity:
        return

    global log_text, start_time
    start_time = time.time()
    log_text.insert(tk.END, f"执行按数量切分...\n")
    threading.Thread(target=split_file_by_quantity, args=(source_path, save_dir, log_text, quantity)).start()

def show_main_buttons():
    main_buttons_frame.pack_forget()
    back_button.pack_forget()
    main_buttons_frame.pack()
    back_button.pack(side=tk.BOTTOM, pady=10)

def show_split_buttons():
    main_buttons_frame.pack_forget()
    split_buttons_frame.pack(pady=10)
    back_button.pack(side=tk.BOTTOM, pady=10)

root = tk.Tk()
root.title("TXT文件切分工具")
root.geometry("650x700")

# 软件简介
intro_label = tk.Label(root, text="""
欢迎使用TXT文件切分工具（TxtSplitTool）！


功能概述：
有下述两个文件的切分方式：
- 按章节切分：识别文本中的章节标题，按标题自动切分文件。
- 按数量切分：将文件按输入的切分数量进行智能切分，均匀地分成指定数量的部分。
Welcome to the TXT File Splitter! 
Features include automatic splitting by chapter titles and even distribution into a specified number of parts.
Simply select your source file and target folder to easily split your files.
""")
intro_label.pack(pady=10)

tk.Label(root, text="源文件路径：").pack()
file_path_entry = tk.Entry(root, width=50)
file_path_entry.pack()
tk.Button(root, text="选择文件", command=lambda: file_path_entry.delete(0, tk.END) or file_path_entry.insert(0, filedialog.askopenfilename(title="选择文件", filetypes=[("Text files", "*.txt")]))).pack()

tk.Label(root, text="切分后文件夹路径：").pack()
folder_path_entry = tk.Entry(root, width=50)
folder_path_entry.pack()
tk.Button(root, text="选择文件夹", command=lambda: folder_path_entry.delete(0, tk.END) or folder_path_entry.insert(0, filedialog.askdirectory(title="选择文件夹"))).pack()

log_text = scrolledtext.ScrolledText(root, width=70, height=15)
log_text.pack()

main_buttons_frame = tk.Frame(root)
main_buttons_frame.pack(pady=10)

tk.Button(main_buttons_frame, text="预估章节数", command=lambda: messagebox.showinfo("章节数", f"预估共{estimate_chapters(file_path_entry.get(), termination_words)}个章节")).pack(side=tk.LEFT, padx=10)
tk.Button(main_buttons_frame, text="按章节切分", command=start_splitting).pack(side=tk.LEFT, padx=10)
tk.Button(main_buttons_frame, text="按数量切分", command=show_split_buttons).pack(side=tk.LEFT, padx=10)

split_buttons_frame = tk.Frame(root)

tk.Button(split_buttons_frame, text="启动：数量切分", command=start_splitting_by_quantity).pack(side=tk.LEFT, padx=10)

back_button = tk.Button(root, text="返回", command=show_main_buttons)

# 作者信息
author_info_label = tk.Label(root, text="""
作者：Luke（伊玛目的门徒）
邮箱：luul11@163.com
博客主页：https://blog.csdn.net/qq_37195257
github address：  https://github.com/luul11/TxtSplitTool
版本号：V2.2.0  
""")
author_info_label.pack(side=tk.BOTTOM, pady=10)

root.mainloop()