# 🔧 Agents 无输出问题诊断指南

## 问题描述
使用 `screen` 启动了 7 个 agents，但是没有任何输出/反应。

## 根本原因分析

### 1. **日志文件为空**
所有 agent 的日志文件都是空的：
- `logs/agents/rss_reader.log` - 空
- `logs/agents/web_scraper.log` - 空  
- `logs/agents/summarizer.log` - 空
- `logs/network.log` - 空

这说明：
- ✅ Agents 可能启动了（screen 会话存在）
- ❌ 但日志完全没有输出

### 2. **可能的原因**

#### 原因 A: 日志配置问题
agents 代码中使用 Python logging，但在 screen 会话中：
- `logging.basicConfig()` 默认输出到 stderr
- screen 的 detached 模式可能没有正确捕获 stderr
- 日志文件路径可能配置错误

#### 原因 B: 网络连接失败
所有 agents 都需要先连接到 network-server (localhost:8700)：
- 如果 network-server 没有正确启动
- 或者 agents 连接超时
- Agents 会静默失败（取决于错误处理）

#### 原因 C: 环境变量问题
screen 会话可能没有继承环境变量：
- `OPENAI_API_KEY` 未设置
- `start_all.sh` 中通过 `export` 设置的变量可能在 screen 子进程中不可见

#### 原因 D: Import 错误
agents 代码中有复杂的路径操作：
```python
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))
```
这可能导致 import 失败，而错误没有被记录。

## 🎯 解决方案

### 方案 1: 使用简化测试（推荐）

我已经创建了诊断工具：

#### 步骤 1: 前台启动网络服务器
```bash
# 这样可以直接看到输出
./start_simple_test.sh
```

等待看到类似输出：
```
✓ Network server started on http://localhost:8700
✓ Studio UI available at http://localhost:8700/studio
```

然后按 Ctrl+C 停止。

#### 步骤 2: 在新终端启动网络服务器（后台）
```bash
# 终端 1
conda run -n openagents openagents network start network.yaml
```

#### 步骤 3: 在另一个终端测试 agent
```bash
# 终端 2
conda run -n openagents python test_agent_simple.py
```

这个测试 agent 会：
- ✅ 直接输出到终端（不依赖日志文件）
- ✅ 显示每个步骤的状态
- ✅ 测试网络连接
- ✅ 测试消息发送

### 方案 2: 修复日志配置

修改所有 agents，添加文件日志处理器：

```python
# 在每个 agent 的 main() 函数中
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/agents/{agent_name}.log'),  # 文件日志
        logging.StreamHandler(sys.stdout)  # 终端日志
    ]
)
```

### 方案 3: 改用 tmux 而不是 screen

tmux 对日志处理更友好：

```bash
# 检查是否安装 tmux
which tmux

# 如果未安装
brew install tmux  # macOS
```

`start_all.sh` 已经支持 tmux（优先于 screen）。

### 方案 4: 直接在终端运行（不用 screen/tmux）

**最简单的调试方法：**

```bash
# 终端 1: 网络服务器
conda run -n openagents openagents network start network.yaml

# 终端 2: RSS Reader
conda run -n openagents python agents/rss_reader.py

# 终端 3: Summarizer  
conda run -n openagents python agents/summarizer.py

# ... 其他 agents
```

这样可以直接看到所有输出。

## 🔍 诊断命令

### 检查 screen 会话实际状态
```bash
# 连接到某个 screen 会话查看
screen -r rss-reader

# 如果看不到输出，尝试发送回车键看是否有反应
# 分离: Ctrl+A 然后 D
```

### 检查网络服务器是否真正运行
```bash
# 检查端口是否被占用
lsof -i :8700

# 或者
netstat -an | grep 8700

# 测试 HTTP 端点
curl http://localhost:8700/health
```

### 检查环境变量
```bash
# 在 screen 会话中检查
screen -r rss-reader -X stuff 'echo $OPENAI_API_KEY\n'
```

## 🎨 最佳实践建议

### 1. 改进日志配置
在所有 agents 中添加更详细的启动日志：

```python
async def on_startup(self):
    print(f"{'='*60}")
    print(f"Agent {self.agent_id} 正在启动...")
    print(f"连接到: {self.network_host}:{self.network_port}")
    print(f"{'='*60}")
    sys.stdout.flush()  # 强制刷新输出
```

### 2. 添加健康检查
创建 `check_status.sh` 改进版：

```bash
#!/bin/bash
echo "检查网络服务器..."
curl -s http://localhost:8700/health || echo "❌ 网络服务器未响应"

echo ""
echo "检查 agents..."
# 检查 screen 会话是否存活
screen -ls | grep -E "(rss-reader|web-scraper|summarizer)" || echo "❌ 没有找到 agent 会话"
```

### 3. 统一使用环境变量文件
确保所有启动脚本都正确加载 `.env`：

```bash
# 在 start_all.sh 中
set -a  # 自动导出所有变量
source .env
set +a
```

## 📝 下一步行动

1. **立即测试**: 运行 `./start_simple_test.sh` 验证网络服务器
2. **测试 Agent**: 运行 `python test_agent_simple.py` 测试连接
3. **根据结果**: 
   - 如果成功 → 问题在于 screen 的日志配置
   - 如果失败 → 查看具体错误信息

## 🐱 小贴士

> Screen 是个好工具，但对于开发调试，直接在终端运行会更直观喵~  
> 等确认一切正常后，再用 screen/tmux 后台运行喵！

---

有任何问题随时告诉我喵~ 🐾