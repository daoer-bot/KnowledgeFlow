"""
会话管理器 - 创作工坊会话持久化
负责管理用户创作会话的生命周期和状态

状态流转：
  idle (空闲)
    → confirming_materials (确认素材)
    → generating_outlines (生成大纲)
    → waiting_selection (选择大纲)
    → editing_outline (修改大纲) [可选]
    → confirming_start (确认开始写作)
    → writing (写作中)
    → reviewing (评审中)
    → waiting_optimization (等待优化决定)
    → optimizing (优化中) [可选]
    → completed (完成)
"""

import json
import uuid
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


# 状态常量
class SessionState:
    """会话状态常量"""
    IDLE = 'idle'                           # 空闲
    CONFIRMING_MATERIALS = 'confirming_materials'  # 确认素材
    GENERATING_OUTLINES = 'generating_outlines'    # 生成大纲
    WAITING_SELECTION = 'waiting_selection'        # 等待选择大纲
    EDITING_OUTLINE = 'editing_outline'            # 修改大纲
    CONFIRMING_START = 'confirming_start'          # 确认开始写作
    WRITING = 'writing'                            # 写作中
    PAUSED_WRITING = 'paused_writing'              # 写作暂停（等待用户确认继续）
    REVIEWING = 'reviewing'                        # 评审中
    WAITING_OPTIMIZATION = 'waiting_optimization'  # 等待优化决定
    OPTIMIZING = 'optimizing'                      # 优化中
    COMPLETED = 'completed'                        # 完成
    ERROR = 'error'                                # 错误

    # 状态中文名称映射
    NAMES = {
        'idle': '空闲',
        'confirming_materials': '确认素材',
        'generating_outlines': '生成大纲中',
        'waiting_selection': '等待选择大纲',
        'editing_outline': '修改大纲中',
        'confirming_start': '确认开始写作',
        'writing': '写作中',
        'paused_writing': '写作暂停',
        'reviewing': '评审中',
        'waiting_optimization': '等待优化决定',
        'optimizing': '优化中',
        'completed': '已完成',
        'error': '出错'
    }

    @classmethod
    def get_name(cls, state: str) -> str:
        return cls.NAMES.get(state, state)


class CreationSession:
    """创作会话对象"""

    def __init__(self, data: dict):
        self.id = data.get('id')
        self.user_id = data.get('user_id')
        self.topic = data.get('topic')
        self.state = data.get('state', 'idle')

        # 素材相关
        self.material_ids = data.get('material_ids', [])  # 搜索到的素材ID列表
        self.confirmed_material_ids = data.get('confirmed_material_ids', [])  # 用户确认使用的素材

        # 大纲相关
        self.outline_ids = data.get('outline_ids', [])
        self.selected_outline_id = data.get('selected_outline_id')
        self.selected_outline = data.get('selected_outline')  # 选中的大纲内容（可能被用户修改）
        self.original_outline = data.get('original_outline')  # 原始大纲（用于对比）

        # 写作相关
        self.draft_id = data.get('draft_id')
        self.current_section_index = data.get('current_section_index', 0)  # 当前写作章节
        self.total_sections = data.get('total_sections', 0)  # 总章节数
        self.section_contents = data.get('section_contents', {})  # 各章节内容 {index: content}
        self.writing_mode = data.get('writing_mode', 'auto')  # 写作模式: auto/step_by_step

        # 评审相关
        self.review_scores = data.get('review_scores', {})  # {technical: 8, business: 7, ux: 9}
        self.review_suggestions = data.get('review_suggestions', [])  # 改进建议列表
        self.optimization_count = data.get('optimization_count', 0)  # 优化次数
        # 完整评审数据（临时存储，用于按需展示详细报告，不持久化）
        self.full_reviews = data.get('full_reviews', {})

        # 时间戳
        self.created_at = data.get('created_at')
        self.updated_at = data.get('updated_at')
        self.expires_at = data.get('expires_at')

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'topic': self.topic,
            'state': self.state,
            'material_ids': self.material_ids,
            'confirmed_material_ids': self.confirmed_material_ids,
            'outline_ids': self.outline_ids,
            'selected_outline_id': self.selected_outline_id,
            'selected_outline': self.selected_outline,
            'original_outline': self.original_outline,
            'draft_id': self.draft_id,
            'current_section_index': self.current_section_index,
            'total_sections': self.total_sections,
            'section_contents': self.section_contents,
            'writing_mode': self.writing_mode,
            'review_scores': self.review_scores,
            'review_suggestions': self.review_suggestions,
            'optimization_count': self.optimization_count,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'expires_at': self.expires_at
        }

    def get_state_name(self) -> str:
        """获取状态中文名称"""
        return SessionState.get_name(self.state)

    def get_progress_info(self) -> str:
        """获取进度信息"""
        if self.state == SessionState.WRITING:
            if self.total_sections > 0:
                return f"写作进度: {self.current_section_index}/{self.total_sections}"
            return "写作中..."
        elif self.state == SessionState.REVIEWING:
            completed = len(self.review_scores)
            return f"评审进度: {completed}/3"
        return self.get_state_name()


class SessionManager:
    """会话管理器"""

    def __init__(self, db):
        """
        初始化会话管理器

        Args:
            db: Database 实例
        """
        self.db = db
        self._init_table()
        logger.info("✅ SessionManager 初始化完成")

    def _init_table(self):
        """初始化会话表"""
        conn = self.db._get_connection()
        cursor = conn.cursor()

        # 创建新表（如果不存在）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS creation_sessions_v2 (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                topic TEXT,
                state TEXT DEFAULT 'idle',

                -- 素材相关
                material_ids TEXT,
                confirmed_material_ids TEXT,

                -- 大纲相关
                outline_ids TEXT,
                selected_outline_id TEXT,
                selected_outline TEXT,
                original_outline TEXT,

                -- 写作相关
                draft_id TEXT,
                current_section_index INTEGER DEFAULT 0,
                total_sections INTEGER DEFAULT 0,
                section_contents TEXT,
                writing_mode TEXT DEFAULT 'auto',

                -- 评审相关
                review_scores TEXT,
                review_suggestions TEXT,
                optimization_count INTEGER DEFAULT 0,

                -- 时间戳
                created_at DATETIME,
                updated_at DATETIME,
                expires_at DATETIME
            )
        """)

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_v2_user
            ON creation_sessions_v2(user_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_v2_state
            ON creation_sessions_v2(state)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_v2_expires
            ON creation_sessions_v2(expires_at)
        """)

        conn.commit()
        conn.close()
        logger.info("✅ 会话表 v2 初始化完成")

    def _parse_json_field(self, value: str, default=None):
        """安全解析 JSON 字段"""
        if not value:
            return default if default is not None else []
        try:
            return json.loads(value)
        except:
            return default if default is not None else []

    def _row_to_session(self, row) -> CreationSession:
        """将数据库行转换为 CreationSession 对象"""
        data = dict(row)
        # 解析 JSON 字段
        data['material_ids'] = self._parse_json_field(data.get('material_ids'), [])
        data['confirmed_material_ids'] = self._parse_json_field(data.get('confirmed_material_ids'), [])
        data['outline_ids'] = self._parse_json_field(data.get('outline_ids'), [])
        data['selected_outline'] = self._parse_json_field(data.get('selected_outline'), None)
        data['original_outline'] = self._parse_json_field(data.get('original_outline'), None)
        data['section_contents'] = self._parse_json_field(data.get('section_contents'), {})
        data['review_scores'] = self._parse_json_field(data.get('review_scores'), {})
        data['review_suggestions'] = self._parse_json_field(data.get('review_suggestions'), [])
        return CreationSession(data)

    async def get_or_create_session(self, user_id: str) -> CreationSession:
        """
        获取或创建会话
        优先返回用户的活跃会话，否则创建新会话

        Args:
            user_id: 用户ID

        Returns:
            CreationSession 对象
        """
        # 查找活跃会话
        conn = self.db._get_connection()
        cursor = conn.cursor()

        # 活跃状态列表（排除已完成和错误状态）
        inactive_states = (SessionState.COMPLETED, SessionState.ERROR)

        cursor.execute(f"""
            SELECT * FROM creation_sessions_v2
            WHERE user_id = ?
            AND state NOT IN (?, ?)
            AND datetime(expires_at) > datetime('now')
            ORDER BY updated_at DESC
            LIMIT 1
        """, (user_id, *inactive_states))

        row = cursor.fetchone()

        if row:
            conn.close()
            session = self._row_to_session(row)
            logger.info(f"📦 找到活跃会话: {session.id}, 状态: {session.state}")
            return session

        # 创建新会话
        session_id = str(uuid.uuid4())
        now = datetime.now()
        expires = now + timedelta(hours=2)

        cursor.execute("""
            INSERT INTO creation_sessions_v2 (
                id, user_id, state, writing_mode, optimization_count,
                current_section_index, total_sections,
                created_at, updated_at, expires_at
            ) VALUES (?, ?, 'idle', 'auto', 0, 0, 0, ?, ?, ?)
        """, (session_id, user_id, now.isoformat(),
              now.isoformat(), expires.isoformat()))

        conn.commit()
        conn.close()

        logger.info(f"🆕 创建新会话: {session_id}")

        return CreationSession({
            'id': session_id,
            'user_id': user_id,
            'state': SessionState.IDLE,
            'writing_mode': 'auto',
            'created_at': now.isoformat(),
            'updated_at': now.isoformat(),
            'expires_at': expires.isoformat()
        })
    
    async def update_session(self, session: CreationSession):
        """
        更新会话状态

        Args:
            session: CreationSession 对象
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE creation_sessions_v2 SET
                topic = ?,
                state = ?,
                material_ids = ?,
                confirmed_material_ids = ?,
                outline_ids = ?,
                selected_outline_id = ?,
                selected_outline = ?,
                original_outline = ?,
                draft_id = ?,
                current_section_index = ?,
                total_sections = ?,
                section_contents = ?,
                writing_mode = ?,
                review_scores = ?,
                review_suggestions = ?,
                optimization_count = ?,
                updated_at = ?
            WHERE id = ?
        """, (
            session.topic,
            session.state,
            json.dumps(session.material_ids) if session.material_ids else None,
            json.dumps(session.confirmed_material_ids) if session.confirmed_material_ids else None,
            json.dumps(session.outline_ids) if session.outline_ids else None,
            session.selected_outline_id,
            json.dumps(session.selected_outline) if session.selected_outline else None,
            json.dumps(session.original_outline) if session.original_outline else None,
            session.draft_id,
            session.current_section_index,
            session.total_sections,
            json.dumps(session.section_contents) if session.section_contents else None,
            session.writing_mode,
            json.dumps(session.review_scores) if session.review_scores else None,
            json.dumps(session.review_suggestions) if session.review_suggestions else None,
            session.optimization_count,
            datetime.now().isoformat(),
            session.id
        ))

        conn.commit()
        conn.close()

        logger.info(f"💾 更新会话: {session.id}, 状态: {session.state}")
    
    async def get_session(self, session_id: str) -> Optional[CreationSession]:
        """
        根据ID获取会话

        Args:
            session_id: 会话ID

        Returns:
            CreationSession 对象或 None
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM creation_sessions_v2 WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return self._row_to_session(row)

        return None

    async def reset_session(self, session: CreationSession):
        """
        重置会话到初始状态（保留用户ID和会话ID）

        Args:
            session: CreationSession 对象
        """
        session.topic = None
        session.state = SessionState.IDLE
        session.material_ids = []
        session.confirmed_material_ids = []
        session.outline_ids = []
        session.selected_outline_id = None
        session.selected_outline = None
        session.original_outline = None
        session.draft_id = None
        session.current_section_index = 0
        session.total_sections = 0
        session.section_contents = {}
        session.writing_mode = 'auto'
        session.review_scores = {}
        session.review_suggestions = []
        session.optimization_count = 0

        await self.update_session(session)
        logger.info(f"🔄 会话已重置: {session.id}")

    async def cleanup_expired_sessions(self):
        """清理过期会话"""
        conn = self.db._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM creation_sessions_v2
            WHERE datetime(expires_at) < datetime('now')
        """)

        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()

        if deleted_count > 0:
            logger.info(f"🗑️  清理了 {deleted_count} 个过期会话")

        return deleted_count

    async def get_pending_sessions(self) -> List[CreationSession]:
        """
        获取所有未完成的会话（用于恢复）

        Returns:
            会话列表
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()

        # 需要恢复的状态
        pending_states = (
            SessionState.GENERATING_OUTLINES,
            SessionState.WRITING,
            SessionState.REVIEWING,
            SessionState.OPTIMIZING
        )

        cursor.execute(f"""
            SELECT * FROM creation_sessions_v2
            WHERE state IN ({','.join(['?' for _ in pending_states])})
            AND datetime(expires_at) > datetime('now')
            ORDER BY updated_at DESC
        """, pending_states)

        rows = cursor.fetchall()
        conn.close()

        sessions = [self._row_to_session(row) for row in rows]
        return sessions

    async def get_user_history(self, user_id: str, limit: int = 10) -> List[CreationSession]:
        """
        获取用户的历史会话

        Args:
            user_id: 用户ID
            limit: 返回数量限制

        Returns:
            会话列表
        """
        conn = self.db._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM creation_sessions_v2
            WHERE user_id = ?
            ORDER BY updated_at DESC
            LIMIT ?
        """, (user_id, limit))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_session(row) for row in rows]