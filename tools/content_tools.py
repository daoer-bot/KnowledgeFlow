"""
内容处理工具
包含 RSS 解析、网页抓取、全文提取等功能
"""

import feedparser
import trafilatura
import yaml
import logging
import requests
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class RSSFeedReader:
    """RSS 订阅源读取器"""
    
    def __init__(self, config_path: str = "config/rss_feeds.yaml"):
        """
        初始化 RSS 读取器
        
        Args:
            config_path: RSS 配置文件路径
        """
        self.config_path = config_path
        self.feeds = []
        self.config = {}
        self._load_config()
    
    def _load_config(self):
        """加载 RSS 配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                self.feeds = [feed for feed in data.get('feeds', []) if feed.get('enabled', True)]
                self.config = data.get('collection', {})
                logger.info(f"Loaded {len(self.feeds)} RSS feeds")
        except Exception as e:
            logger.error(f"Failed to load RSS config: {str(e)}")
            self.feeds = []
    
    def fetch_feed(self, feed_url: str, max_items: int = 10) -> List[Dict[str, Any]]:
        """
        抓取单个 RSS 源
        
        Args:
            feed_url: RSS 源 URL
            max_items: 最大条目数
            
        Returns:
            文章列表
        """
        try:
            feed = feedparser.parse(feed_url)
            
            if feed.bozo:  # 解析出错
                logger.warning(f"Feed parsing error for {feed_url}: {feed.bozo_exception}")
            
            items = []
            for entry in feed.entries[:max_items]:
                item = {
                    'title': entry.get('title', 'Untitled'),
                    'url': entry.get('link', ''),
                    'summary': entry.get('summary', ''),
                    'published': entry.get('published', ''),
                    'author': entry.get('author', ''),
                }
                
                # 尝试提取全文
                if item['url']:
                    full_content = self.extract_content(item['url'])
                    if full_content:
                        item['content'] = full_content
                
                items.append(item)
            
            logger.info(f"Fetched {len(items)} items from {feed_url}")
            return items
            
        except Exception as e:
            logger.error(f"Error fetching feed {feed_url}: {str(e)}")
            return []
    
    def fetch_hackernews_api(self, api_type: str = "top", count: int = 5) -> List[Dict[str, Any]]:
        """
        通过 Hacker News API 抓取内容
        
        Args:
            api_type: API 类型 (top/new/best)
            count: 抓取数量
            
        Returns:
            文章列表
        """
        try:
            # 获取故事 ID 列表
            api_urls = {
                'top': 'https://hacker-news.firebaseio.com/v0/topstories.json',
                'new': 'https://hacker-news.firebaseio.com/v0/newstories.json',
                'best': 'https://hacker-news.firebaseio.com/v0/beststories.json'
            }
            
            api_url = api_urls.get(api_type, api_urls['top'])
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            story_ids = response.json()[:count]
            
            items = []
            for story_id in story_ids:
                # 获取故事详情
                story_response = requests.get(
                    f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json',
                    timeout=10
                )
                
                if story_response.ok:
                    story = story_response.json()
                    if story and story.get('title'):
                        url = story.get('url', f'https://news.ycombinator.com/item?id={story_id}')
                        
                        # 构建内容项
                        item = {
                            'title': story.get('title', 'Untitled'),
                            'url': url,
                            'summary': f"⬆️ {story.get('score', 0)} points | 💬 {story.get('descendants', 0)} comments",
                            'author': story.get('by', 'unknown'),
                            'published': datetime.fromtimestamp(story.get('time', 0)).isoformat() if story.get('time') else '',
                        }
                        
                        # 如果有外部 URL，尝试提取全文
                        if url and not url.startswith('https://news.ycombinator.com'):
                            full_content = self.extract_content(url)
                            if full_content:
                                item['content'] = full_content
                        
                        items.append(item)
            
            logger.info(f"Fetched {len(items)} items from Hacker News API ({api_type})")
            return items
            
        except Exception as e:
            logger.error(f"Error fetching Hacker News API: {str(e)}")
            return []
    
    def fetch_all_feeds(self) -> List[Dict[str, Any]]:
        """
        抓取所有配置的 RSS 源
        
        Returns:
            包含来源信息的文章列表
        """
        all_items = []
        max_items = self.config.get('max_items_per_feed', 10)
        
        for feed_config in self.feeds:
            feed_name = feed_config['name']
            category = feed_config.get('category', 'general')
            feed_type = feed_config.get('type', 'rss')
            
            logger.info(f"Fetching feed: {feed_name} (type: {feed_type})")
            
            # 根据类型选择抓取方法
            if feed_type == 'hackernews_api':
                # Hacker News API 源
                api_type = feed_config.get('api_type', 'top')
                fetch_count = feed_config.get('fetch_count', 5)
                items = self.fetch_hackernews_api(api_type, fetch_count)
            else:
                # 标准 RSS 源
                feed_url = feed_config['url']
                items = self.fetch_feed(feed_url, max_items)
            
            # 添加来源信息
            for item in items:
                item['source'] = feed_name
                item['source_type'] = feed_type
                item['category_hint'] = category
            
            all_items.extend(items)
        
        logger.info(f"Total fetched: {len(all_items)} items from {len(self.feeds)} feeds")
        return all_items
    
    @staticmethod
    def extract_content(url: str, timeout: int = 30) -> Optional[str]:
        """
        从 URL 提取全文内容
        
        Args:
            url: 文章 URL
            timeout: 超时时间（秒）
            
        Returns:
            提取的文本内容
        """
        try:
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                content = trafilatura.extract(
                    downloaded,
                    include_comments=False,
                    include_tables=True,
                    no_fallback=False
                )
                return content
        except Exception as e:
            logger.warning(f"Failed to extract content from {url}: {str(e)}")
        
        return None


class WebScraper:
    """网页内容抓取器"""
    
    @staticmethod
    def scrape_url(url: str) -> Optional[Dict[str, Any]]:
        """
        抓取指定 URL 的内容
        
        Args:
            url: 目标 URL
            
        Returns:
            包含标题和内容的字典
        """
        try:
            # 下载网页
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                logger.error(f"Failed to download {url}")
                return None
            
            # 提取内容
            content = trafilatura.extract(
                downloaded,
                include_comments=False,
                include_tables=True,
                no_fallback=False,
                output_format='json'
            )
            
            if not content:
                logger.error(f"Failed to extract content from {url}")
                return None
            
            # trafilatura 返回 JSON 字符串
            import json
            data = json.loads(content)
            
            result = {
                'title': data.get('title', 'Untitled'),
                'url': url,
                'content': data.get('text', ''),
                'author': data.get('author', ''),
                'date': data.get('date', ''),
                'source': data.get('sitename', 'Unknown'),
                'source_type': 'web'
            }
            
            logger.info(f"Scraped {len(result['content'])} characters from {url}")
            return result
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return None
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """
        验证 URL 格式
        
        Args:
            url: URL 字符串
            
        Returns:
            是否有效
        """
        import re
        pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE
        )
        return pattern.match(url) is not None


class ContentProcessor:
    """内容处理辅助类"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        清理文本
        
        - 移除多余空白
        - 统一换行符
        """
        if not text:
            return ""
        
        import re
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        # 统一换行
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()
    
    @staticmethod
    def extract_keywords(text: str, top_n: int = 5) -> List[str]:
        """
        提取关键词（简单版本，基于词频）
        
        Args:
            text: 文本内容
            top_n: 返回前N个关键词
            
        Returns:
            关键词列表
        """
        import re
        from collections import Counter
        
        # 简单分词（仅作演示，实际应使用 jieba 等工具）
        words = re.findall(r'\w+', text.lower())
        
        # 过滤停用词（简化版）
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = [w for w in words if w not in stopwords and len(w) > 2]
        
        # 统计词频
        counter = Counter(words)
        
        return [word for word, count in counter.most_common(top_n)]
    
    @staticmethod
    def count_words(text: str) -> int:
        """
        统计字数
        
        中文按字符数，英文按单词数
        """
        if not text:
            return 0
        
        # 统计中文字符
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        
        # 统计英文单词
        import re
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
        
        return chinese_chars + english_words
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
        """
        截断文本
        
        Args:
            text: 原文本
            max_length: 最大长度
            suffix: 后缀
            
        Returns:
            截断后的文本
        """
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def format_content_card(content_data: Dict[str, Any]) -> str:
        """
        格式化内容卡片（用于频道消息）
        
        Args:
            content_data: 内容数据
            
        Returns:
            格式化的 Markdown 文本
        """
        title = content_data.get('title', 'Untitled')
        url = content_data.get('url', '')
        source = content_data.get('source', 'Unknown')
        summary = content_data.get('summary_paragraph', content_data.get('summary', ''))
        category = content_data.get('category', '')
        tags = content_data.get('tags', {})
        
        # 构建卡片
        card = f"📌 **{title}**\n\n"
        
        if summary:
            card += f"📝 {summary}\n\n"
        
        # 标签
        if tags:
            tag_list = []
            for tag_type, tag_values in tags.items():
                if isinstance(tag_values, list):
                    tag_list.extend(tag_values)
            
            if tag_list:
                card += f"🏷️ {' '.join(['#' + t for t in tag_list[:5]])}\n\n"
        
        # 来源和分类
        card += f"📚 {source}"
        if category:
            card += f" | {category}"
        card += "\n"
        
        if url:
            card += f"🔗 {url}\n"
        
        return card


# 便捷函数
def get_rss_reader() -> RSSFeedReader:
    """获取 RSS 读取器实例"""
    return RSSFeedReader()


def get_web_scraper() -> WebScraper:
    """获取网页抓取器实例"""
    return WebScraper()