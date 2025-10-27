import subprocess
import sys

if __name__ == "__main__":
    cmd = [
        "mysqlsh",
        "--log-level=@INFO",
        "--pym",
        "mysqloperator",
        "operator"
    ]

    try:
        # 执行命令并实时输出（可选）
        result = subprocess.run(
            cmd,
            capture_output=False,  # 若希望实时看到输出，设为 False；若需捕获，设为 True
            text=True,
            check=True
        )
    except FileNotFoundError:
        print("错误：未找到 mysqlsh 命令。请确保 MySQL Shell 已安装并已加入系统 PATH。", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"mysqlsh 命令执行失败，退出码：{e.returncode}", file=sys.stderr)
        sys.exit(e.returncode)