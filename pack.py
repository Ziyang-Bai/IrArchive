import zipfile
import hashlib
import os
import io

def create_zip_in_memory(source_path):
    """在内存中创建 ZIP 文件"""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        if os.path.isdir(source_path):
            for root, _, files in os.walk(source_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_path)
                    zipf.write(file_path, arcname)
        else:
            zipf.write(source_path, os.path.basename(source_path))
    zip_buffer.seek(0)
    return zip_buffer

def calculate_md5(data):
    """计算数据的 MD5 哈希值"""
    hash_md5 = hashlib.md5()
    hash_md5.update(data)
    return hash_md5.hexdigest()

def split_into_chunks(data, chunk_size):
    """将数据分割成指定大小的块"""
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]

def main():
    source_path = input("请输入要打包的目录或文件路径: ")
    output_file = input("请输入输出文件名（不含扩展名）: ")
    chunk_size_kb = int(input("请输入分卷大小（KB，输入 -1 表示不分卷）: "))
    version = "1.0.0"

    zip_buffer = create_zip_in_memory(source_path)
    zip_data = zip_buffer.getvalue()
    md5_hash = calculate_md5(zip_data)

    chunk_size = -1 if chunk_size_kb == -1 else chunk_size_kb * 1024
    chunks = list(split_into_chunks(zip_data, chunk_size)) if chunk_size != -1 else [zip_data]
    total_chunks = len(chunks)

    for i, chunk in enumerate(chunks, start=1):
        if total_chunks > 1:
            part_file = f"{output_file}_part{i}.ira"
        else:
            part_file = f"{output_file}.ira"
        with open(part_file, "wb") as f:
            header = f"{version},{md5_hash},{i},{total_chunks}\n".encode('utf-8')
            f.write(header)
            f.write(chunk)
        print(f"分卷 {i}/{total_chunks} 已写入: {part_file}")

if __name__ == "__main__":
    main()