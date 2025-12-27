#!/usr/bin/env python3
"""
KnowledgeFlow 看板工具
查看文章统计、RSS 源管理、创作进度

用法:
    python3 dashboard.py          # 显示所有看板
    python3 dashboard.py stats    # 仅显示文章统计
    python3 dashboard.py rss      # 仅显示 RSS 源管理
    python3 dashboard.py creation # 仅显示创作进度
    python3 dashboard.py --json   # 输出 JSON 格式
"""

import sys
import json
import argparse
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from mods.content_stats import ContentStatsMod
from mods.rss_manager import RSSManagerMod
from mods.creation_tracker import CreationTrackerMod

# 默认配置
DB_PATH = 'data/knowledge-flow/content.db'
FEEDS_CONFIG = 'config/rss_feeds.yaml'


def get_content_stats_mod():
    mod = ContentStatsMod()
    mod.update_config({'db_path': DB_PATH})
    mod.initialize()
    return mod


def get_rss_manager_mod():
    mod = RSSManagerMod()
    mod.update_config({'db_path': DB_PATH, 'feeds_config': FEEDS_CONFIG})
    mod.initialize()
    return mod


def get_creation_tracker_mod():
    mod = CreationTrackerMod()
    mod.update_config({'db_path': DB_PATH})
    mod.initialize()
    return mod


def show_stats(as_json=False):
    """显示文章统计"""
    mod = get_content_stats_mod()
    if as_json:
        print(json.dumps(mod.get_dashboard_data(), ensure_ascii=False, indent=2))
    else:
        print(mod.format_dashboard_text())


def show_rss(as_json=False):
    """显示 RSS 源管理"""
    mod = get_rss_manager_mod()
    if as_json:
        print(json.dumps(mod.get_feed_stats(), ensure_ascii=False, indent=2))
    else:
        print(mod.format_dashboard_text())


def show_creation(as_json=False):
    """显示创作进度"""
    mod = get_creation_tracker_mod()
    if as_json:
        print(json.dumps(mod.get_dashboard_data(), ensure_ascii=False, indent=2))
    else:
        print(mod.format_dashboard_text())


def show_all(as_json=False):
    """显示所有看板"""
    if as_json:
        data = {
            'content_stats': get_content_stats_mod().get_dashboard_data(),
            'rss_manager': get_rss_manager_mod().get_feed_stats(),
            'creation_tracker': get_creation_tracker_mod().get_dashboard_data()
        }
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        show_stats()
        print()
        show_rss()
        print()
        show_creation()


def main():
    parser = argparse.ArgumentParser(
        description='KnowledgeFlow 看板工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 dashboard.py              显示所有看板
  python3 dashboard.py stats        仅显示文章统计
  python3 dashboard.py rss          仅显示 RSS 源管理
  python3 dashboard.py creation     仅显示创作进度
  python3 dashboard.py --json       输出 JSON 格式
  python3 dashboard.py stats --json 文章统计 JSON 格式
        """
    )

    parser.add_argument(
        'dashboard',
        nargs='?',
        choices=['stats', 'rss', 'creation', 'all'],
        default='all',
        help='要显示的看板 (默认: all)'
    )

    parser.add_argument(
        '--json', '-j',
        action='store_true',
        help='输出 JSON 格式'
    )

    args = parser.parse_args()

    if args.dashboard == 'stats':
        show_stats(args.json)
    elif args.dashboard == 'rss':
        show_rss(args.json)
    elif args.dashboard == 'creation':
        show_creation(args.json)
    else:
        show_all(args.json)


if __name__ == "__main__":
    main()
