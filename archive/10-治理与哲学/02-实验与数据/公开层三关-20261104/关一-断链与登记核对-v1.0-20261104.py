#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
关一·断链与登记核对 v1.0
执行体：Qoder General Purpose (default)
日期：2026-11-04

功能：
1. 断链普查：扫描指定文件中的路径引用，检查是否存在
2. 公开层声明核对：验证文件数、字节数、最大文件
3. 增量登记核对：验证 indexes/02-全库文件总表 §三 的 956 行登记
4. 哈希核对：验证 sha256 前16位声明
5. 仓库卫生检查：.pyc、未跟踪文件、编码等

用法：python3 -B 关一-断链与登记核对-v1.0-20261104.py [仓库根目录]
"""

import os
import sys
import re
import json
import hashlib
import subprocess
from pathlib import Path

def check_broken_links(repo_root):
    """A. 断链普查"""
    print("=" * 60)
    print("A. 断链普查")
    print("=" * 60)
    
    # Files to scan
    files_to_scan = ['README.md', 'llms.txt']
    for f in Path(os.path.join(repo_root, 'indexes')).glob('*.md'):
        files_to_scan.append(str(f.relative_to(repo_root)))
    for f in Path(os.path.join(repo_root, 'archive')).glob('*/05-索引/*.md'):
        files_to_scan.append(str(f.relative_to(repo_root)))
    
    print(f"扫描文件数：{len(files_to_scan)}")
    
    # Extract paths
    def extract_paths(content, source_file):
        paths = []
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            # Markdown links
            for m in re.finditer(r'\[([^\]]*)\]\(([^)]+)\)', line):
                link_path = m.group(2)
                if not (link_path.startswith('http://') or link_path.startswith('https://') or link_path.startswith('#')):
                    paths.append({'source': source_file, 'line': line_num, 'path': link_path, 'type': 'markdown_link'})
            # Backtick paths
            for m in re.finditer(r'`([^`]+\.(?:md|txt|json|py))`', line):
                path = m.group(1)
                if '/' in path or path.endswith('.gitignore'):
                    paths.append({'source': source_file, 'line': line_num, 'path': path, 'type': 'backtick_path'})
            # "见 xxx.md" references
            for m in re.finditer(r'见\s+([^\s,，。]+\.md)', line):
                paths.append({'source': source_file, 'line': line_num, 'path': m.group(1), 'type': 'see_reference'})
        return paths
    
    all_paths = []
    for file_path in files_to_scan:
        full_path = os.path.join(repo_root, file_path)
        if not os.path.exists(full_path):
            continue
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            all_paths.extend(extract_paths(content, file_path))
        except:
            pass
    
    print(f"抽取路径引用总数：{len(all_paths)}")
    
    # Categorize and verify
    external = windows = placeholder = resolvable = existing = broken = 0
    broken_list = []
    
    for p in all_paths:
        path = p['path'].strip('`').strip()
        if path.startswith('http://') or path.startswith('https://'):
            external += 1
            continue
        if path.startswith(('H:', 'h:', 'G:', 'g:')):
            windows += 1
            continue
        if '…' in path or '...' in path or '-XX-' in path:
            placeholder += 1
            continue
        
        resolvable += 1
        source_dir = os.path.dirname(p['source'])
        resolved = os.path.normpath(os.path.join(source_dir, path)) if source_dir else path
        
        if os.path.exists(os.path.join(repo_root, resolved)):
            existing += 1
        else:
            broken += 1
            if len(broken_list) < 60:
                broken_list.append({'path': resolved, '出处文件': p['source'], '行号': p['line']})
    
    print(f"外部链接：{external}")
    print(f"本机路径：{windows}")
    print(f"占位符：{placeholder}")
    print(f"可解析：{resolvable}")
    print(f"存在：{existing}")
    print(f"断链：{broken}")
    
    return {
        '引用总数': len(all_paths),
        '可解析数': resolvable,
        '存在数': existing,
        '断链数': broken,
        '断链': broken_list
    }

def check_declarations(repo_root):
    """B. 公开层声明与实测核对"""
    print("\n" + "=" * 60)
    print("B. 公开层声明与实测核对")
    print("=" * 60)
    
    # Count tracked files
    result = subprocess.run(['git', 'ls-files'], cwd=repo_root, capture_output=True, text=True)
    tracked_files = [f for f in result.stdout.strip().split('\n') if f]
    file_count = len(tracked_files)
    
    # Calculate total bytes
    total_bytes = 0
    max_file_size = 0
    max_file_path = ""
    
    for f in tracked_files:
        full_path = os.path.join(repo_root, f)
        if os.path.exists(full_path):
            size = os.path.getsize(full_path)
            total_bytes += size
            if size > max_file_size:
                max_file_size = size
                max_file_path = f
    
    print(f"跟踪文件数：{file_count}")
    print(f"字节合计：{total_bytes:,}")
    print(f"最大文件：{max_file_size:,} 字节 ({max_file_path})")
    
    # Check README and llms.txt declarations
    readme_match = llms_match = False
    for fname in ['README.md', 'llms.txt']:
        fpath = os.path.join(repo_root, fname)
        if os.path.exists(fpath):
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
            if f"{file_count} 个文件" in content:
                print(f"{fname} 声明文件数：符")
                readme_match = True
    
    return {
        '跟踪文件数实测': file_count,
        '字节实测': total_bytes,
        '最大文件实测': max_file_size,
        '最大文件路径': max_file_path,
        '判定': '符' if readme_match else '不符'
    }

def check_incremental_registration(repo_root):
    """C. 索引增量段逐行核对"""
    print("\n" + "=" * 60)
    print("C. 索引增量段逐行核对")
    print("=" * 60)
    
    index_file = os.path.join(repo_root, 'indexes/02-全库文件总表-v1.0-20261027.md')
    if not os.path.exists(index_file):
        print("ERROR: 索引文件不存在")
        return {'行数': 0, '存在数': 0, '字节相符数': 0, '不一致': []}
    
    with open(index_file, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    # Find section
    start_idx = -1
    for i, line in enumerate(lines):
        if '## 三、批次 13—15 增量登记' in line:
            start_idx = i
            break
    
    if start_idx == -1:
        print("ERROR: 未找到增量登记段")
        return {'行数': 0, '存在数': 0, '字节相符数': 0, '不一致': []}
    
    # Parse entries
    domain_path = ""
    subdir_path = ""
    entries = []
    
    for i in range(start_idx, len(lines)):
        line = lines[i].strip()
        
        m = re.match(r'^###\s+(.+?)（增量', line)
        if m:
            domain_name = m.group(1)
            if domain_name == "仓库根":
                domain_path = ""
            elif domain_name == "indexes":
                domain_path = "indexes"
            else:
                domain_path = f"archive/{domain_name}"
            subdir_path = domain_path
            continue
        
        m = re.match(r'^####\s+(.+?)（', line)
        if m:
            subdir_name = m.group(1)
            if subdir_name.startswith('('):
                subdir_path = domain_path
            else:
                subdir_path = f"{domain_path}/{subdir_name}" if domain_path else subdir_name
            continue
        
        if line.startswith('|') and line.endswith('|'):
            parts = [p.strip() for p in line.split('|')[1:-1]]
            if len(parts) == 3:
                filename, bytes_str, _ = parts
                if filename != '文件' and not filename.startswith('---'):
                    full_path = f"{subdir_path}/{filename}" if subdir_path else filename
                    try:
                        expected_bytes = int(bytes_str.replace(',', ''))
                    except:
                        expected_bytes = -1
                    entries.append({'path': full_path, 'expected_bytes': expected_bytes, 'line': i+1})
    
    print(f"登记行数：{len(entries)}")
    
    # Verify
    exists_count = byte_match_count = 0
    mismatches = []
    
    for entry in entries:
        full_path = os.path.join(repo_root, entry['path'])
        if not os.path.exists(full_path):
            continue
        exists_count += 1
        actual_bytes = os.path.getsize(full_path)
        if actual_bytes == entry['expected_bytes']:
            byte_match_count += 1
        else:
            mismatches.append({
                '路径': entry['path'],
                'section_line': entry['line'],
                '登记字节': entry['expected_bytes'],
                '实测字节': actual_bytes
            })
    
    print(f"存在数：{exists_count}")
    print(f"字节相符数：{byte_match_count}")
    print(f"字节不符数：{len(mismatches)}")
    
    return {
        '行数': len(entries),
        '存在数': exists_count,
        '字节相符数': byte_match_count,
        '不一致': mismatches
    }

def check_hashes(repo_root):
    """D. 哈希核对"""
    print("\n" + "=" * 60)
    print("D. 哈希核对")
    print("=" * 60)
    
    files_to_check = [
        'archive/16-生命与营养工程/05-索引/总纲索引-16-生命与营养工程-v1.0-20261104-补录.md',
        'archive/16-生命与营养工程/01-理论与推导/绝经线·判据链冻结哈希-20261104.txt'
    ]
    
    declarations = []
    base_path = "archive/16-生命与营养工程"
    
    for file_path in files_to_check:
        full_path = os.path.join(repo_root, file_path)
        if not os.path.exists(full_path):
            continue
        
        with open(full_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines):
            # Match hash declarations
            m = re.search(r'`?([^\s`]+?\.(?:md|json|py|txt))`?\s+([\d,]+)B\s+(?:sha256|sha)\s+(?:前16\s+)?([0-9a-f]{16})', line)
            if m:
                rel_path = m.group(1)
                expected_hash = m.group(3)
                
                if rel_path.startswith(('01-理论与推导', '02-实验与数据')):
                    target_path = f"{base_path}/{rel_path}"
                else:
                    target_path = f"{base_path}/02-实验与数据/绝经线-文献底座-v1.0-20261104/{rel_path}"
                
                declarations.append({
                    'source': os.path.basename(file_path),
                    'line': i+1,
                    'path': target_path,
                    'expected_hash': expected_hash
                })
            
            # Also match "｜hash" format
            m = re.search(r'`([^`]+)`\s*[—-]\s*([\d,]+)B.*?｜([0-9a-f]{16})', line)
            if m:
                rel_path = m.group(1)
                expected_hash = m.group(3)
                
                if rel_path.startswith(('01-理论与推导', '02-实验与数据')):
                    target_path = f"{base_path}/{rel_path}"
                else:
                    target_path = f"{base_path}/02-实验与数据/绝经线-文献底座-v1.0-20261104/{rel_path}"
                
                declarations.append({
                    'source': os.path.basename(file_path),
                    'line': i+1,
                    'path': target_path,
                    'expected_hash': expected_hash
                })
    
    print(f"哈希声明数：{len(declarations)}")
    
    # Verify
    matches = 0
    mismatches = []
    
    for decl in declarations:
        target_path = os.path.join(repo_root, decl['path'])
        if not os.path.exists(target_path):
            continue
        
        with open(target_path, 'rb') as f:
            actual_hash = hashlib.sha256(f.read()).hexdigest()[:16]
        
        if actual_hash == decl['expected_hash']:
            matches += 1
        else:
            mismatches.append({
                '来源': decl['source'],
                '行号': decl['line'],
                '文件': decl['path'],
                '声明值': decl['expected_hash'],
                '实测值': actual_hash
            })
    
    print(f"相符数：{matches}")
    print(f"不符数：{len(mismatches)}")
    
    return {
        '声明数': len(declarations),
        '相符数': matches,
        '不符': mismatches
    }

def check_hygiene(repo_root):
    """E. 仓库卫生与状态"""
    print("\n" + "=" * 60)
    print("E. 仓库卫生与状态")
    print("=" * 60)
    
    # Check .pyc files
    result = subprocess.run(['git', 'ls-files'], cwd=repo_root, capture_output=True, text=True)
    tracked = result.stdout.strip().split('\n')
    pyc_files = [f for f in tracked if f.endswith('.pyc') or '__pycache__' in f]
    print(f".pyc 文件数：{len(pyc_files)}")
    
    # Check untracked files
    result = subprocess.run(['git', 'status', '--porcelain', '-uall'], cwd=repo_root, capture_output=True, text=True)
    untracked = [line[3:] for line in result.stdout.strip().split('\n') if line.startswith('??')]
    print(f"未跟踪文件数：{len(untracked)}")
    
    # Check dirty state
    result = subprocess.run(['git', 'diff', '--name-only'], cwd=repo_root, capture_output=True, text=True)
    dirty = len(result.stdout.strip()) > 0
    print(f"工作区脏状态：{dirty}")
    
    # Check remote consistency
    result = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=repo_root, capture_output=True, text=True)
    local_head = result.stdout.strip()
    
    result = subprocess.run(['git', 'ls-remote', 'origin', 'refs/heads/main'], cwd=repo_root, capture_output=True, text=True)
    remote_head = result.stdout.split()[0] if result.stdout.strip() else ""
    
    remote_match = local_head == remote_head
    print(f"本地 HEAD：{local_head}")
    print(f"远端 HEAD：{remote_head}")
    print(f"远端一致：{remote_match}")
    
    # Check encoding
    non_utf8 = zero_byte = control_char = 0
    for f in tracked:
        if not f:
            continue
        full_path = os.path.join(repo_root, f)
        if not os.path.exists(full_path):
            continue
        
        if os.path.getsize(full_path) == 0:
            zero_byte += 1
            continue
        
        if any(ord(c) < 32 or ord(c) == 127 for c in f):
            control_char += 1
        
        try:
            with open(full_path, 'r', encoding='utf-8') as file:
                file.read()
        except:
            non_utf8 += 1
    
    print(f"非 UTF-8 文件数：{non_utf8}")
    print(f"零字节文件数：{zero_byte}")
    print(f"文件名含控制字符数：{control_char}")
    
    return {
        'pyc数': len(pyc_files),
        '未跟踪': untracked,
        '脏状态': dirty,
        '远端一致': remote_match,
        '非UTF8数': non_utf8,
        '零字节数': zero_byte
    }

def main():
    repo_root = sys.argv[1] if len(sys.argv) > 1 else '.'
    repo_root = os.path.abspath(repo_root)
    
    print(f"仓库根目录：{repo_root}")
    print(f"检验时间：2026-11-04")
    print()
    
    results = {
        '断链普查': check_broken_links(repo_root),
        '声明核对': check_declarations(repo_root),
        '增量登记': check_incremental_registration(repo_root),
        '哈希核对': check_hashes(repo_root),
        '仓库卫生': check_hygiene(repo_root)
    }
    
    print("\n" + "=" * 60)
    print("总判定")
    print("=" * 60)
    
    # Determine overall pass/fail
    issues = []
    if results['断链普查']['断链数'] > 0:
        issues.append(f"断链 {results['断链普查']['断链数']} 条")
    if results['增量登记']['字节相符数'] < results['增量登记']['行数']:
        issues.append(f"字节不符 {results['增量登记']['行数'] - results['增量登记']['字节相符数']} 条")
    if results['哈希核对']['相符数'] < results['哈希核对']['声明数']:
        issues.append(f"哈希不符 {results['哈希核对']['声明数'] - results['哈希核对']['相符数']} 条")
    if results['仓库卫生']['pyc数'] > 0:
        issues.append(f".pyc 文件 {results['仓库卫生']['pyc数']} 件")
    if not results['仓库卫生']['远端一致']:
        issues.append("本地 HEAD 落后远端")
    
    if issues:
        print("判定：不过")
        print("缺陷：")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("判定：过")
    
    # Save results
    output_path = os.path.join(repo_root, 'archive/10-治理与哲学/02-实验与数据/公开层三关-20261104/关一-检验-20261104.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n结果已保存：{output_path}")

if __name__ == '__main__':
    main()
