# -*- coding: utf-8 -*-
"""
泛弦搜索·SDSS公开数据查询脚本 v1.1（安全修正版）
修正：URL 白名单+协议限制+IP 边界校验（红队 SSRF 修正）
搜索：SDSS DR17 光谱中 8035-8045Å（f₀=373THz）范围内的异常谱线特征
数据：SDSS SkyServer 公开 API
"""
import numpy as np, json, os, sys

# 安全白名单：仅允许 SDSS SkyServer 域名（HTTPS）
ALLOWED_HOSTS = {"skyserver.sdss.org"}
ALLOWED_PROTOCOL = "https"
SKYSERVER_PATH = "/dr18/en/tools/search/sql.aspx"

def safe_fetch(query, timeout=60):
    """安全查询 SDSS SkyServer（白名单域名/HTTPS/私网 IP 阻断）"""
    import urllib.request, urllib.parse
    params = urllib.parse.urlencode({"cmd": query, "format": "csv"})
    url = f"{ALLOWED_PROTOCOL}://{list(ALLOWED_HOSTS)[0]}{SKYSERVER_PATH}?{params}"

    # 协议白名单
    proto = urllib.parse.urlparse(url).scheme
    host = urllib.parse.urlparse(url).hostname
    if proto != "https" or host not in ALLOWED_HOSTS:
        raise ValueError(f"URL 不在白名单内: {url}")

    # DNS 解析后检查 IP（防 DNS rebinding）
    import socket
    try:
        ip = socket.getaddrinfo(host, None)[0][4][0]
        # 私网/环回/链路本地阻断
        if ip.startswith(("10.", "172.16.", "192.168.", "127.", "169.254.")):
            raise ValueError(f"DNS 解析到私网 IP: {ip}")
    except socket.gaierror:
        pass  # DNS 失败由后续请求处理

    req = urllib.request.Request(url, headers={"User-Agent": "PanXianSearch/1.0"})
    resp = urllib.request.urlopen(req, timeout=timeout)
    return resp.read().decode("utf-8")

# SDSS SQL 查询
QUERY_SPECTRAL_LINES = """
SELECT
    sp.specobjid, sp.plate, sp.mjd, sp.fiberID,
    sp.z AS redshift,
    s.el_wavelength AS line_wavelength,
    s.el_type AS line_type
FROM SpecLine AS s
JOIN SpecObj AS sp ON s.specobjid = sp.specobjid
WHERE s.el_wavelength BETWEEN 8035 AND 8045
  AND sp.z < 0.1
ORDER BY s.el_wavelength
"""

if __name__ == "__main__":
    print("=== 泛弦搜索·SDSS 查询脚本 v1.1 ===")
    print(f"域名白名单: {ALLOWED_HOSTS}")
    print(f"协议: {ALLOWED_PROTOCOL}")
    print(f"搜索范围: 8035-8045 Å")
    print(f"\n⚠ 需要网络连接 + 知世批准（对外数据查询=对外闸门）")
    print(f"脚本就绪。执行需: 知世批准 + 网络连接。")
