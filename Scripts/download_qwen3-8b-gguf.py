# 模型下载
import os
import shutil
from modelscope.hub.file_download import model_file_download

# 获取项目根目录（Scripts目录的父目录）
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

# 确保下载目录存在
download_dir = os.path.join(project_root, ".models", "qwen")
os.makedirs(download_dir, exist_ok=True)

# 指定要下载的文件
model_id = "Qwen/Qwen3-8B-GGUF"
target_file = "Qwen3-8B-Q5_K_M.gguf"  # 从ModelScope模型页面获取的准确文件名

# 使用model_file_download精确下载单个文件
print(f"开始下载模型文件 {target_file}...")
downloaded_path = model_file_download(
    model_id=model_id, file_path=target_file, revision="master"
)

print(f"文件已下载至临时位置: {downloaded_path}")

# 将文件移动到指定目录
target_path = os.path.join(download_dir, target_file)
print(f"\n将文件移动到目标目录 {target_path}...")
shutil.copy2(downloaded_path, target_path)
print(f"文件已成功移动到目标目录")

# 验证下载结果
print(f"\n验证下载结果:")

# 检查下载目录中的文件
print(f"\n下载目录 {download_dir} 中的文件:")
dir_files = os.listdir(download_dir)
for file in dir_files:
    file_path = os.path.join(download_dir, file)
    file_size = os.path.getsize(file_path) / (1024 * 1024 * 1024)  # GB
    print(f"  - {file} ({file_size:.2f} GB)")

    # 检查是否有多余的gguf文件
    if file.endswith(".gguf") and file != target_file:
        print(f"    ⚠️  警告: 发现多余的gguf文件 {file}")

# 确认目标文件是否存在且大小合理
if os.path.exists(target_path):
    target_size = os.path.getsize(target_path) / (1024 * 1024 * 1024)  # GB
    print(f"\n✅ 成功: 目标文件 {target_file} 已下载完成")
    print(f"   大小: {target_size:.2f} GB")
    print(f"   路径: {target_path}")
else:
    print(f"\n❌ 错误: 目标文件 {target_file} 下载失败")

print("\n下载完成！")
