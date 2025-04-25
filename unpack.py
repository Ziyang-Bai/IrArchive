import zipfile
import hashlib
import os
import io
import glob

def calculate_md5(data):
    """计算数据的 MD5 哈希值"""
    hash_md5 = hashlib.md5()
    hash_md5.update(data)
    return hash_md5.hexdigest()

def extract_zip_from_memory(zip_data, extract_to):
    """从内存中的 ZIP 数据解压到指定目录"""
    with zipfile.ZipFile(io.BytesIO(zip_data), 'r') as zipf:
        zipf.extractall(extract_to)

def main():
    base_file = input("请输入分卷文件的基础名称（例如 'archive'）: ")
    extract_to = input("请输入解压目标目录: ")

    part_files = glob.glob(f"{base_file}.ira") + glob.glob(f"{base_file}_part*.ira")
    if not part_files:
        print("未找到任何分卷文件或单文件！")
        return

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
                print(f"文件 {part_file} 格式错误：未找到换行符分隔头信息。")
                return
            header = content[:header_end].decode('utf-8')
            chunk = content[header_end+1:]
            try:
                ver, md5, part_no_str, total_str = header.split(',', 3)
                part_no = int(part_no_str)
                total = int(total_str)
            except ValueError as e:
                print(f"文件 {part_file} 头信息解析失败: {e}")
                return

            if part_no in seen_part_nos:
                print(f"错误：分卷号 {part_no} 重复于文件 {part_file}")
                return
            seen_part_nos.add(part_no)

            if part_no < 1 or part_no > total:
                print(f"错误：分卷号 {part_no} 超出范围 (1-{total})")
                return

            if version is None:
                version, md5_hash, total_chunks = ver, md5, total
            else:
                if version != ver or md5_hash != md5 or total_chunks != total:
                    print(f"文件 {part_file} 头信息不匹配！")
                    return

            parts.append( (part_no, chunk) )

    if len(parts) != total_chunks:
        print(f"分卷数量错误，期望 {total_chunks} 个，实际 {len(parts)} 个")
        return

    expected_parts = set(range(1, total_chunks+1))
    missing = expected_parts - seen_part_nos
    if missing:
        print(f"缺少分卷号: {missing}")
        return

    parts.sort(key=lambda x: x[0])
    zip_data = b''.join(chunk for _, chunk in parts)

    calculated_md5 = calculate_md5(zip_data)
    print(f"计算MD5: {calculated_md5}")
    print(f"期望MD5: {md5_hash}")

    if calculated_md5 != md5_hash:
        print("MD5校验失败！文件可能损坏。")
        return

    os.makedirs(extract_to, exist_ok=True)
    extract_zip_from_memory(zip_data, extract_to)
    print(f"解包完成，文件已解压至: {extract_to}")

if __name__ == "__main__":
    main()