# -*- coding: utf-8 -*-
"""mini GGUF 解析器（读 V4.1 分片1 的元数据与张量目录）——不依赖 gguf 包"""
import struct, sys, json

PATH = r"I:\DeepSeek-V4.1-Flash-IQ2XXS\DeepSeek-V4-Flash-UD-IQ2_XXS-00001-of-00003.gguf"

def read_str(f):
    (n,) = struct.unpack("<Q", f.read(8))
    return f.read(n).decode("utf-8", "replace")

def skip_value(f, t):
    sizes = {0:1,1:1,2:2,3:2,4:4,5:4,6:4,7:1,8:0,9:0,10:8,11:8,12:8}
    if t == 8:  # string
        read_str(f)
    elif t == 9:  # array
        (et,) = struct.unpack("<I", f.read(4))
        (n,) = struct.unpack("<Q", f.read(8))
        for _ in range(n):
            skip_value(f, et)
    elif t == 10:  # bf16 不定长？GGUF 无此——保险 2
        f.read(2)
    elif t in sizes:
        f.read(sizes[t])
    else:
        raise ValueError(f"unknown type {t}")

def main():
    with open(PATH, "rb") as f:
        magic = f.read(4)
        (version,) = struct.unpack("<I", f.read(4))
        (tcount,) = struct.unpack("<Q", f.read(8))
        (kvcount,) = struct.unpack("<Q", f.read(8))
        print("magic:", magic, "version:", version, "tensors:", tcount, "kv:", kvcount)
        meta = {}
        for _ki in range(kvcount):
            k = read_str(f)
            print('  kv', _ki, 'off', f.tell(), k[:30], file=sys.stderr)
            (t,) = struct.unpack("<I", f.read(4))
            if t == 8:
                meta[k] = read_str(f)
            elif t == 4:
                (v,) = struct.unpack("<I", f.read(4)); meta[k] = v
            elif t == 5:
                (v,) = struct.unpack("<f", f.read(4)); meta[k] = v
            elif t == 6:
                (v,) = struct.unpack("<B", f.read(1)); meta[k] = bool(v)
            elif t == 7:
                (v,) = struct.unpack("<Q", f.read(8)); meta[k] = v
            elif t == 10:
                (v,) = struct.unpack("<Q", f.read(8)); meta[k] = v
            else:
                skip_value(f, t)
        arch = meta.get("general.architecture", "")
        print("arch:", arch, "| vocab:", meta.get(arch+".vocab_size"),
              "| embedding:", meta.get(arch+".embedding_length"),
              "| layers:", meta.get(arch+".block_count"),
              "| experts:", meta.get(arch+".expert_count"),
              "| used:", meta.get(arch+".expert_used_count"))
        # 张量目录
        want = []
        for _ in range(tcount):
            name = read_str(f)
            (nd,) = struct.unpack("<I", f.read(4))
            dims = struct.unpack("<" + "Q"*nd, f.read(8*nd))
            (tt,) = struct.unpack("<I", f.read(4))
            (off,) = struct.unpack("<Q", f.read(8))
            if "embd" in name or name.startswith("output") or ("ffn" in name and "exp" in name):
                want.append((name, tt, list(dims), off))
        print("目标张量:")
        for name, tt, dims, off in want[:8]:
            print(f"  {name} type={tt} dims={dims} off={off}")
        print("目标张量总数:", len(want))

if __name__ == "__main__":
    main()
