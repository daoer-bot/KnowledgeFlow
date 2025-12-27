#!/usr/bin/env python3
"""
KnowledgeFlow 网络启动脚本
确保自定义 mods 可以被正确加载
"""

import sys
import os
from pathlib import Path

# 将项目目录添加到 Python 路径，使自定义 mods 可被导入
project_dir = Path(__file__).parent.absolute()
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

# 加载 .env 文件
env_file = project_dir / '.env'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# 确保数据目录存在
data_dir = project_dir / 'data' / 'knowledge-flow'
data_dir.mkdir(parents=True, exist_ok=True)

logs_dir = project_dir / 'logs'
logs_dir.mkdir(parents=True, exist_ok=True)

# 启动网络
if __name__ == '__main__':
    from openagents import AgentNetwork

    print("=" * 60)
    print("🚀 KnowledgeFlow 网络启动")
    print("=" * 60)
    print(f"📁 项目目录: {project_dir}")
    print(f"📁 数据目录: {data_dir}")
    print(f"🔧 Python 路径已添加: {project_dir}")
    print("=" * 60)

    # 加载并启动网络
    network = AgentNetwork.load(
        config=str(project_dir / 'network.yaml'),
        workspace_path=str(project_dir)
    )

    print("\n✅ 网络已加载")
    print(f"📡 已加载的 Mods: {list(network.mods.keys())}")
    print("\n🌐 启动网络服务...")

    network.start()
