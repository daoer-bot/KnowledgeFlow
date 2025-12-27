"""
数据库操作模块
使用 SQLite 存储内容、大纲和草稿
"""

import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class Database:
    """数据库管理类"""
    
    def __init__(self, db_path: str = "data/knowledge-flow/content.db"):
        """
        初始化数据库连接
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        
        # 确保目录存在
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 创建表
        self._init_tables()
        
        logger.info(f"Database initialized at {db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 返回字典格式
        return conn
    
    def _init_tables(self):
        """创建数据库表"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 内容表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS content_items (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT UNIQUE,
                raw_content TEXT,
                source TEXT,
                source_type TEXT,
                collected_at DATETIME,
                
                summary_one_line TEXT,
                summary_paragraph TEXT,
                summary_detailed TEXT,
                key_points TEXT,
                key_quotes TEXT,
                
                tags TEXT,
                category TEXT,
                sentiment TEXT,
                relevance_score REAL,
                
                status TEXT DEFAULT 'discovered',
                processed_at DATETIME
            )
        """)
        
        # 大纲表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS outlines (
                id TEXT PRIMARY KEY,
                topic TEXT NOT NULL,
                content TEXT,
                style TEXT,
                related_content_ids TEXT,
                created_at DATETIME,
                selected BOOLEAN DEFAULT 0
            )
        """)
        
        # 草稿表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drafts (
                id TEXT PRIMARY KEY,
                outline_id TEXT,
                title TEXT,
                content TEXT,
                word_count INTEGER,
                status TEXT DEFAULT 'draft',
                created_at DATETIME,
                updated_at DATETIME,
                FOREIGN KEY (outline_id) REFERENCES outlines(id)
            )
        """)
        
        # 配置表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at DATETIME
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_content_status ON content_items(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_content_category ON content_items(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_content_collected ON content_items(collected_at)")
        
        conn.commit()
        conn.close()
    
    # ========== 内容操作 ==========
    
    def add_content(self, content_data: Dict[str, Any]) -> str:
        """
        添加新内容
        
        Args:
            content_data: 内容数据字典
            
        Returns:
            content_id: 内容ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        content_id = content_data.get('id') or str(uuid.uuid4())
        
        try:
            cursor.execute("""
                INSERT INTO content_items (
                    id, title, url, raw_content, source, source_type, collected_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'discovered')
            """, (
                content_id,
                content_data['title'],
                content_data.get('url'),
                content_data.get('raw_content'),
                content_data.get('source'),
                content_data.get('source_type', 'rss'),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            logger.info(f"Added content: {content_id}")
            return content_id
            
        except sqlite3.IntegrityError:
            logger.warning(f"Content already exists: {content_data.get('url')}")
            return None
        finally:
            conn.close()
    
    def update_content_summary(self, content_id: str, summary_data: Dict[str, Any]):
        """更新内容摘要"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE content_items SET
                summary_one_line = ?,
                summary_paragraph = ?,
                summary_detailed = ?,
                key_points = ?,
                key_quotes = ?,
                status = 'summarized'
            WHERE id = ?
        """, (
            summary_data.get('one_line'),
            summary_data.get('paragraph'),
            summary_data.get('detailed'),
            json.dumps(summary_data.get('key_points', []), ensure_ascii=False),
            json.dumps(summary_data.get('key_quotes', []), ensure_ascii=False),
            content_id
        ))
        
        conn.commit()
        conn.close()
        logger.info(f"Updated summary for content: {content_id}")
    
    def update_content_tags(self, content_id: str, tag_data: Dict[str, Any]):
        """更新内容标签"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE content_items SET
                tags = ?,
                category = ?,
                sentiment = ?,
                relevance_score = ?,
                status = 'processed',
                processed_at = ?
            WHERE id = ?
        """, (
            json.dumps(tag_data.get('tags', {}), ensure_ascii=False),
            tag_data.get('category'),
            tag_data.get('sentiment'),
            tag_data.get('relevance_score'),
            datetime.now().isoformat(),
            content_id
        ))
        
        conn.commit()
        conn.close()
        logger.info(f"Updated tags for content: {content_id}")
    
    def get_content(self, content_id: str) -> Optional[Dict[str, Any]]:
        """获取单个内容"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM content_items WHERE id = ?", (content_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_dict(row)
        return None
    
    def check_url_exists(self, url: str) -> bool:
        """检查URL是否已存在"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM content_items WHERE url = ?", (url,))
        exists = cursor.fetchone() is not None
        conn.close()
        
        return exists
    
    def search_content(
        self,
        keywords: Optional[List[str]] = None,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        搜索内容（简单关键词匹配）
        
        Args:
            keywords: 关键词列表
            category: 分类过滤
            limit: 返回数量限制
            
        Returns:
            内容列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM content_items WHERE status = 'processed'"
        params = []
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        if keywords:
            # 简单的关键词匹配
            keyword_conditions = []
            for keyword in keywords:
                keyword_conditions.append("(title LIKE ? OR summary_paragraph LIKE ?)")
                params.extend([f"%{keyword}%", f"%{keyword}%"])
            
            query += " AND (" + " OR ".join(keyword_conditions) + ")"
        
        query += " ORDER BY collected_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_dict(row) for row in rows]
    
    def get_recent_content(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取最近的内容"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM content_items 
            WHERE status = 'processed'
            ORDER BY collected_at DESC 
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_dict(row) for row in rows]
    
    # ========== 大纲操作 ==========
    
    def save_outline(self, outline_data: Dict[str, Any]) -> str:
        """保存大纲"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        outline_id = outline_data.get('id') or str(uuid.uuid4())
        
        cursor.execute("""
            INSERT INTO outlines (
                id, topic, content, style, related_content_ids, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            outline_id,
            outline_data['topic'],
            json.dumps(outline_data.get('content', {}), ensure_ascii=False),
            outline_data.get('style'),
            json.dumps(outline_data.get('related_content_ids', []), ensure_ascii=False),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        logger.info(f"Saved outline: {outline_id}")
        return outline_id
    
    def get_outline(self, outline_id: str) -> Optional[Dict[str, Any]]:
        """获取大纲"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM outlines WHERE id = ?", (outline_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_dict(row)
        return None
    
    def mark_outline_selected(self, outline_id: str):
        """标记大纲为已选择"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE outlines SET selected = 1 WHERE id = ?
        """, (outline_id,))
        
        conn.commit()
        conn.close()
    
    # ========== 草稿操作 ==========
    
    def save_draft(self, draft_data: Dict[str, Any]) -> str:
        """保存草稿"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        draft_id = draft_data.get('id') or str(uuid.uuid4())
        
        cursor.execute("""
            INSERT INTO drafts (
                id, outline_id, title, content, word_count, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            draft_id,
            draft_data.get('outline_id'),
            draft_data['title'],
            draft_data['content'],
            draft_data.get('word_count', 0),
            draft_data.get('status', 'draft'),
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        logger.info(f"Saved draft: {draft_id}")
        return draft_id
    
    def get_draft(self, draft_id: str) -> Optional[Dict[str, Any]]:
        """获取草稿"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return self._row_to_dict(row)
        return None

    def update_draft(self, draft_id: str, draft_data: Dict[str, Any]):
        """更新草稿"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 构建动态更新语句
        update_fields = []
        params = []

        if 'content' in draft_data:
            update_fields.append("content = ?")
            params.append(draft_data['content'])

        if 'word_count' in draft_data:
            update_fields.append("word_count = ?")
            params.append(draft_data['word_count'])

        if 'status' in draft_data:
            update_fields.append("status = ?")
            params.append(draft_data['status'])

        if 'title' in draft_data:
            update_fields.append("title = ?")
            params.append(draft_data['title'])

        # 总是更新 updated_at
        update_fields.append("updated_at = ?")
        params.append(datetime.now().isoformat())

        params.append(draft_id)

        query = f"UPDATE drafts SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, params)

        conn.commit()
        conn.close()
        logger.info(f"Updated draft: {draft_id}")

    def update_outline(self, outline_id: str, outline_data: Dict[str, Any]):
        """更新大纲"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 构建动态更新语句
        update_fields = []
        params = []

        if 'content' in outline_data:
            content = outline_data['content']
            if isinstance(content, dict):
                content = json.dumps(content, ensure_ascii=False)
            update_fields.append("content = ?")
            params.append(content)

        if 'style' in outline_data:
            update_fields.append("style = ?")
            params.append(outline_data['style'])

        if 'selected' in outline_data:
            update_fields.append("selected = ?")
            params.append(1 if outline_data['selected'] else 0)

        params.append(outline_id)

        query = f"UPDATE outlines SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, params)

        conn.commit()
        conn.close()
        logger.info(f"Updated outline: {outline_id}")

    # ========== 辅助方法 ==========
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """将数据库行转换为字典"""
        result = dict(row)
        
        # 解析 JSON 字段
        for key in ['key_points', 'key_quotes', 'tags', 'related_content_ids', 'content']:
            if key in result and result[key]:
                try:
                    result[key] = json.loads(result[key])
                except:
                    pass
        
        return result
    
    def close(self):
        """关闭数据库连接（SQLite 自动管理，无需显式关闭）"""
        pass


# 全局数据库实例
_db_instance = None


def get_database() -> Database:
    """获取全局数据库实例"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance