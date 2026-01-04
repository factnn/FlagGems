#!/usr/bin/env python3
"""
检查当前分支下所有test文件的pre-commit错误
用法: python3 check_group.py
"""

import sys
import subprocess
from pathlib import Path

def get_all_test_files():
    """获取所有测试文件（不包括relu_test.py）"""
    test_dir = Path('src/flag_gems/experimental_ops/exp_tests')
    test_files = sorted([f for f in test_dir.glob('*_test.py')
                        if f.name != 'relu_test.py'])
    return test_files

def get_group_files(group_num, start_from=None):
    """获取指定组的文件"""
    test_files = get_all_test_files()

    # 如果指定了起始文件，找到它的位置
    if start_from:
        try:
            start_idx = next(i for i, f in enumerate(test_files)
                           if start_from in f.name)
            print(f"从 {test_files[start_idx].name} 开始（索引 {start_idx}）")
        except StopIteration:
            print(f"警告: 未找到起始文件 {start_from}，从开头开始")
            start_idx = 0
    else:
        start_idx = 0

    # 计算组的起始和结束索引
    group_start = start_idx + (group_num - 1) * 10
    group_end = group_start + 10

    return test_files[group_start:group_end]

def get_changed_test_files():
    """获取当前分支相对于master分支修改的所有test文件"""
    # 获取当前分支相对于master的差异文件
    result = subprocess.run(
        'git diff --name-only master...HEAD',
        shell=True,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("错误: 无法获取git差异")
        return []

    changed_files = result.stdout.strip().split('\n')
    if not changed_files or changed_files == ['']:
        print("当前分支没有相对于master的修改")
        return []

    # 筛选出test文件，跳过relu_test.py
    test_files = []
    for file_path in changed_files:
        if file_path.endswith('_test.py') and 'exp_tests' in file_path:
            if 'relu_test.py' not in file_path:
                test_files.append(Path(file_path))

    return sorted(test_files)

def get_operator_file(test_file):
    """根据测试文件名获取对应的算子文件"""
    test_name = test_file.stem.replace('_test', '')

    # 跳过 relu.py
    if test_name == 'relu':
        return None

    # 尝试普通文件名
    kernel_file = Path(f'src/flag_gems/experimental_ops/{test_name}.py')
    if kernel_file.exists() and kernel_file.name != 'relu.py':
        return kernel_file

    # 尝试带下划线的文件名
    kernel_file = Path(f'src/flag_gems/experimental_ops/_{test_name}.py')
    if kernel_file.exists():
        return kernel_file

    # 尝试其他可能的命名（如 fill__test.py -> fill_.py）
    if test_name.endswith('_'):
        kernel_file = Path(f'src/flag_gems/experimental_ops/{test_name}.py')
        if kernel_file.exists() and kernel_file.name != 'relu.py':
            return kernel_file

    return None

def main():
    if len(sys.argv) > 1:
        # 按组检查模式
        try:
            group_num = int(sys.argv[1])
            start_from = sys.argv[2] if len(sys.argv) > 2 else None
        except ValueError:
            print("用法: python3 check_group.py [组号] [起始文件]")
            print("例如: python3 check_group.py 1")
            print("例如: python3 check_group.py 1 hinge_embedding_loss")
            return

        print(f"=== 检查第 {group_num} 组文件的pre-commit错误 ===\n")
        test_files = get_group_files(group_num, start_from)
    else:
        # 检查所有修改的文件
        print("=== 检查当前分支下所有test文件的pre-commit错误 ===\n")
        test_files = get_changed_test_files()

    if not test_files:
        print("没有找到test文件")
        return

    print(f"找到 {len(test_files)} 个test文件:\n")
    file_paths = []

    for test_file in test_files:
        op_file = get_operator_file(test_file)

        print(f"  测试: {test_file.name}")
        if op_file:
            print(f"  算子: {op_file.name}")
            file_paths.append(str(op_file))
        else:
            print(f"  算子: (未找到或跳过)")

        file_paths.append(str(test_file))
        print()

    print(f"\n共 {len(file_paths)} 个文件")
    print("\n运行 pre-commit 检查...")
    print("=" * 60)

    # 构建pre-commit命令（检查所有hooks）
    files_str = ' '.join(file_paths)
    result = subprocess.run(
        f'pre-commit run --files {files_str}',
        shell=True,
        capture_output=True,
        text=True
    )

    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    print("=" * 60)
    print(f"\n检查完成。请手动修复上述错误。")

if __name__ == '__main__':
    main()
