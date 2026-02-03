"""下载NLTK数据脚本"""

import os
import sys
import zipfile

import nltk


def check_nltk_data_exists(package_name):
    """检查NLTK数据包是否已存在"""
    try:
        nltk.data.find(package_name)
        return True
    except LookupError:
        return False


def cleanup_corrupted_zip_files():
    """清理损坏的zip文件"""
    nltk_data_dir = nltk.data.path[0]
    if not os.path.exists(nltk_data_dir):
        return

    corrupted_files = []
    for root, dirs, files in os.walk(nltk_data_dir):
        for file in files:
            if file.endswith(".zip"):
                zip_path = os.path.join(root, file)
                try:
                    with zipfile.ZipFile(zip_path, "r") as zip_ref:
                        zip_ref.testzip()
                except (zipfile.BadZipFile, zipfile.LargeZipFile):
                    corrupted_files.append(zip_path)
                    print(f"发现损坏的zip文件: {zip_path}")

    for corrupted_file in corrupted_files:
        try:
            os.remove(corrupted_file)
            print(f"已删除损坏的文件: {corrupted_file}")
        except Exception as e:
            print(f"删除文件失败 {corrupted_file}: {e}")


def download_nltk_data_with_mirrors(package_name, mirrors=None):
    """尝试从多个镜像源下载NLTK数据"""
    if mirrors is None:
        mirrors = [
            None,
            "https://gitee.com/gislite/nltk_data/raw/",
            "https://mirror.ghproxy.com/https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/",
        ]

    for mirror in mirrors:
        try:
            if mirror:
                print(f"尝试从镜像源下载 {package_name}: {mirror}")
                nltk.data.path.insert(0, mirror)

            nltk.download(package_name, quiet=True)
            print(f"[OK] 成功下载 {package_name}")
            return True
        except Exception as e:
            print(f"[WARN] 从镜像源下载失败: {e}")
            if mirror and mirror in nltk.data.path:
                nltk.data.path.remove(mirror)
            continue

    return False


def main():
    """主函数"""
    required_packages = [
        "wordnet",
        "punkt",
        "averaged_perceptron_tagger",
    ]

    print("开始下载NLTK数据...")

    print("清理清理损坏的zip文件...")
    cleanup_corrupted_zip_files()

    success_count = 0
    for package in required_packages:
        if check_nltk_data_exists(package):
            print(f"[OK] {package} 已存在，跳过下载")
            success_count += 1
        else:
            if download_nltk_data_with_mirrors(package):
                success_count += 1
            else:
                print(f"[FAIL] {package} 下载失败")

    print(f"\n下载完成: {success_count}/{len(required_packages)} 个包成功")

    if success_count == len(required_packages):
        print("[OK] 所有NLTK数据包下载成功")
        return 0
    else:
        print("[WARN] 部分NLTK数据包下载失败，但继续执行测试")
        return 0


if __name__ == "__main__":
    sys.exit(main())
