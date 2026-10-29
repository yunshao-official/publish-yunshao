# -*- coding: utf-8 -*-
"""
T7 LLM 代谢化 · 实验框架（自检版）
用法：python t7_harness.py [--check]
--check：自检环境（模型服务/判据文件/种子哈希），不启动实验。
判据未签（实验协议 v0.1 草案待知世签）之前，本框架拒绝启动实验本体。
"""
import sys, os, json, hashlib, time
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
CRIT = os.path.join(BASE, "判据签名.json")
LLM_URL = "http://localhost:8080/health"

def check_env():
    report = {}
    # 模型服务
    try:
        r = urllib.request.urlopen(LLM_URL, timeout=3)
        report["模型服务"] = "在线 ✓"
    except Exception as e:
        report["模型服务"] = f"离线（WAIT_MODEL：{e.__class__.__name__}）"
    # 判据签名
    report["判据签名"] = "已签 ✓" if os.path.exists(CRIT) else "未签（协议 v0.1 草案待知世签）——实验锁死"
    # 种子哈希
    seed_hash = hashlib.sha256(b"T7-seeds-10-pairs-precommit").hexdigest()[:16]
    report["种子预提交哈希"] = seed_hash
    return report

if __name__ == "__main__":
    r = check_env()
    print(json.dumps(r, ensure_ascii=False, indent=1))
    ready = ("✓" in r["模型服务"]) and ("已签" in r["判据签名"])
    print("\n状态：", "READY（可开实验）" if ready else "NOT READY（缺模型服务或判据未签——按预注册纪律锁死）")
