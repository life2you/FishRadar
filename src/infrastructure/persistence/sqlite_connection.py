"""
Database connection and schema initialization helpers.

The historical module name is kept for compatibility, but the implementation
now supports both SQLite and MySQL.
"""
from __future__ import annotations

import os
import re
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import threading
from typing import Any, Iterator
from urllib.parse import parse_qs, unquote, urlparse

from src.infrastructure.persistence.storage_names import DEFAULT_DATABASE_PATH

try:
    import pymysql
    from pymysql.cursors import DictCursor
except ImportError:  # pragma: no cover - only exercised when MySQL is requested
    pymysql = None
    DictCursor = None


BUSY_TIMEOUT_MS = 5000
SQLITE_BACKEND = "sqlite"
MYSQL_BACKEND = "mysql"
MYSQL_BOOTSTRAP_LOCK = threading.Lock()
MYSQL_READY_DATABASES: set[tuple[str, int, str, str]] = set()

SQLITE_SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS app_metadata (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY,
        task_name TEXT NOT NULL,
        enabled INTEGER NOT NULL,
        keyword TEXT NOT NULL,
        description TEXT,
        analyze_images INTEGER NOT NULL,
        max_pages INTEGER NOT NULL,
        personal_only INTEGER NOT NULL,
        min_price TEXT,
        max_price TEXT,
        cron TEXT,
        ai_prompt_base_file TEXT NOT NULL,
        ai_prompt_criteria_file TEXT NOT NULL,
        account_state_file TEXT,
        account_strategy TEXT NOT NULL,
        free_shipping INTEGER NOT NULL,
        new_publish_option TEXT,
        region TEXT,
        decision_mode TEXT NOT NULL,
        keyword_rules_json TEXT NOT NULL,
        is_running INTEGER NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS result_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        result_filename TEXT NOT NULL,
        keyword TEXT NOT NULL,
        task_name TEXT NOT NULL,
        crawl_time TEXT NOT NULL,
        publish_time TEXT,
        price REAL,
        price_display TEXT,
        item_id TEXT,
        title TEXT,
        link TEXT,
        link_unique_key TEXT NOT NULL,
        seller_nickname TEXT,
        is_recommended INTEGER NOT NULL,
        analysis_source TEXT,
        keyword_hit_count INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'active',
        raw_json TEXT NOT NULL,
        UNIQUE(result_filename, link_unique_key)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS price_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword_slug TEXT NOT NULL,
        keyword TEXT NOT NULL,
        task_name TEXT NOT NULL,
        snapshot_time TEXT NOT NULL,
        snapshot_day TEXT NOT NULL,
        run_id TEXT NOT NULL,
        item_id TEXT NOT NULL,
        title TEXT,
        price REAL NOT NULL,
        price_display TEXT,
        tags_json TEXT NOT NULL,
        region TEXT,
        seller TEXT,
        publish_time TEXT,
        link TEXT,
        UNIQUE(keyword_slug, run_id, item_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS result_blacklist_rules (
        result_filename TEXT PRIMARY KEY,
        blacklist_keywords_json TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_tasks_name ON tasks(task_name)",
    """
    CREATE INDEX IF NOT EXISTS idx_results_filename_crawl
    ON result_items(result_filename, crawl_time DESC)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_results_filename_publish
    ON result_items(result_filename, publish_time DESC)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_results_filename_price
    ON result_items(result_filename, price DESC)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_results_filename_recommended
    ON result_items(result_filename, is_recommended, analysis_source, crawl_time DESC)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_snapshots_keyword_time
    ON price_snapshots(keyword_slug, snapshot_time DESC)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_snapshots_keyword_item_time
    ON price_snapshots(keyword_slug, item_id, snapshot_time DESC)
    """,
)

MYSQL_SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS app_metadata (
        `key` VARCHAR(255) PRIMARY KEY COMMENT '元数据键',
        `value` TEXT NOT NULL COMMENT '元数据值'
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='应用元数据表'
    """,
    """
    CREATE TABLE IF NOT EXISTS tasks (
        id BIGINT PRIMARY KEY COMMENT '任务ID',
        task_name VARCHAR(255) NOT NULL COMMENT '任务名称',
        enabled TINYINT(1) NOT NULL COMMENT '是否启用',
        keyword VARCHAR(255) NOT NULL COMMENT '搜索关键词',
        description TEXT COMMENT '任务描述或AI筛选需求',
        analyze_images TINYINT(1) NOT NULL COMMENT '是否分析商品图片',
        max_pages INT NOT NULL COMMENT '最大翻页数',
        personal_only TINYINT(1) NOT NULL COMMENT '是否仅看个人卖家',
        min_price VARCHAR(64) COMMENT '最低价格',
        max_price VARCHAR(64) COMMENT '最高价格',
        cron VARCHAR(255) COMMENT 'Cron调度表达式',
        ai_prompt_base_file VARCHAR(255) NOT NULL COMMENT 'AI基础提示词文件路径',
        ai_prompt_criteria_file VARCHAR(255) NOT NULL COMMENT 'AI分析标准文件路径',
        account_state_file VARCHAR(255) COMMENT '绑定账号登录态文件路径',
        account_strategy VARCHAR(32) NOT NULL COMMENT '账号使用策略',
        free_shipping TINYINT(1) NOT NULL COMMENT '是否筛选包邮商品',
        new_publish_option VARCHAR(64) COMMENT '发布时间筛选条件',
        region VARCHAR(255) COMMENT '地区筛选条件',
        decision_mode VARCHAR(32) NOT NULL COMMENT '决策模式(ai或keyword)',
        keyword_rules_json LONGTEXT NOT NULL COMMENT '关键词规则JSON',
        is_running TINYINT(1) NOT NULL COMMENT '任务是否运行中'
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='监控任务配置表'
    """,
    """
    CREATE TABLE IF NOT EXISTS result_items (
        id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
        result_filename VARCHAR(255) NOT NULL COMMENT '结果集逻辑文件名',
        keyword VARCHAR(255) NOT NULL COMMENT '搜索关键词',
        task_name VARCHAR(255) NOT NULL COMMENT '来源任务名称',
        crawl_time VARCHAR(64) NOT NULL COMMENT '抓取时间',
        publish_time VARCHAR(64) COMMENT '商品发布时间',
        price DOUBLE COMMENT '商品数值价格',
        price_display VARCHAR(64) COMMENT '商品展示价格',
        item_id VARCHAR(255) COMMENT '商品ID',
        title TEXT COMMENT '商品标题',
        link TEXT COMMENT '商品链接',
        link_unique_key VARCHAR(512) NOT NULL COMMENT '商品去重键',
        seller_nickname VARCHAR(255) COMMENT '卖家昵称',
        is_recommended TINYINT(1) NOT NULL COMMENT '是否推荐',
        analysis_source VARCHAR(32) COMMENT '分析来源',
        keyword_hit_count INT NOT NULL COMMENT '关键词命中次数',
        status VARCHAR(32) NOT NULL DEFAULT 'active' COMMENT '结果状态(active/hidden/expired)',
        raw_json LONGTEXT NOT NULL COMMENT '原始结果JSON',
        UNIQUE KEY uniq_result_link (result_filename, link_unique_key)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='监控结果明细表'
    """,
    """
    CREATE TABLE IF NOT EXISTS price_snapshots (
        id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
        keyword_slug VARCHAR(255) NOT NULL COMMENT '关键词标准化标识',
        keyword VARCHAR(255) NOT NULL COMMENT '搜索关键词',
        task_name VARCHAR(255) NOT NULL COMMENT '来源任务名称',
        snapshot_time VARCHAR(64) NOT NULL COMMENT '快照时间',
        snapshot_day VARCHAR(32) NOT NULL COMMENT '快照日期',
        run_id VARCHAR(64) NOT NULL COMMENT '单次运行批次ID',
        item_id VARCHAR(255) NOT NULL COMMENT '商品ID',
        title TEXT COMMENT '商品标题',
        price DOUBLE NOT NULL COMMENT '商品价格',
        price_display VARCHAR(64) COMMENT '商品展示价格',
        tags_json LONGTEXT NOT NULL COMMENT '商品标签JSON',
        region VARCHAR(255) COMMENT '发货地区',
        seller VARCHAR(255) COMMENT '卖家昵称',
        publish_time VARCHAR(64) COMMENT '商品发布时间',
        link TEXT COMMENT '商品链接',
        UNIQUE KEY uniq_snapshot_item (keyword_slug, run_id, item_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='价格历史快照表'
    """,
    """
    CREATE TABLE IF NOT EXISTS result_blacklist_rules (
        result_filename VARCHAR(255) PRIMARY KEY COMMENT '结果集逻辑文件名',
        blacklist_keywords_json LONGTEXT NOT NULL COMMENT '黑名单关键词JSON',
        updated_at VARCHAR(64) NOT NULL COMMENT '更新时间'
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='结果黑名单规则表'
    """,
)

MYSQL_INDEX_DEFINITIONS = (
    ("idx_tasks_name", "tasks", "CREATE INDEX idx_tasks_name ON tasks(task_name)"),
    (
        "idx_results_filename_crawl",
        "result_items",
        "CREATE INDEX idx_results_filename_crawl ON result_items(result_filename, crawl_time)",
    ),
    (
        "idx_results_filename_publish",
        "result_items",
        "CREATE INDEX idx_results_filename_publish ON result_items(result_filename, publish_time)",
    ),
    (
        "idx_results_filename_price",
        "result_items",
        "CREATE INDEX idx_results_filename_price ON result_items(result_filename, price)",
    ),
    (
        "idx_results_filename_recommended",
        "result_items",
        "CREATE INDEX idx_results_filename_recommended ON result_items(result_filename, is_recommended, analysis_source, crawl_time)",
    ),
    (
        "idx_results_filename_status_crawl",
        "result_items",
        "CREATE INDEX idx_results_filename_status_crawl ON result_items(result_filename, status, crawl_time)",
    ),
    (
        "idx_snapshots_keyword_time",
        "price_snapshots",
        "CREATE INDEX idx_snapshots_keyword_time ON price_snapshots(keyword_slug, snapshot_time)",
    ),
    (
        "idx_snapshots_keyword_item_time",
        "price_snapshots",
        "CREATE INDEX idx_snapshots_keyword_item_time ON price_snapshots(keyword_slug, item_id, snapshot_time)",
    ),
)

MYSQL_COMMENT_MIGRATION_KEY = "migration:mysql_schema_comments_v1"
MYSQL_COMMENT_STATEMENTS = (
    """
    ALTER TABLE app_metadata
    MODIFY COLUMN `key` VARCHAR(255) NOT NULL COMMENT '元数据键',
    MODIFY COLUMN `value` TEXT NOT NULL COMMENT '元数据值',
    COMMENT = '应用元数据表'
    """,
    """
    ALTER TABLE tasks
    MODIFY COLUMN id BIGINT NOT NULL COMMENT '任务ID',
    MODIFY COLUMN task_name VARCHAR(255) NOT NULL COMMENT '任务名称',
    MODIFY COLUMN enabled TINYINT(1) NOT NULL COMMENT '是否启用',
    MODIFY COLUMN keyword VARCHAR(255) NOT NULL COMMENT '搜索关键词',
    MODIFY COLUMN description TEXT NULL COMMENT '任务描述或AI筛选需求',
    MODIFY COLUMN analyze_images TINYINT(1) NOT NULL COMMENT '是否分析商品图片',
    MODIFY COLUMN max_pages INT NOT NULL COMMENT '最大翻页数',
    MODIFY COLUMN personal_only TINYINT(1) NOT NULL COMMENT '是否仅看个人卖家',
    MODIFY COLUMN min_price VARCHAR(64) NULL COMMENT '最低价格',
    MODIFY COLUMN max_price VARCHAR(64) NULL COMMENT '最高价格',
    MODIFY COLUMN cron VARCHAR(255) NULL COMMENT 'Cron调度表达式',
    MODIFY COLUMN ai_prompt_base_file VARCHAR(255) NOT NULL COMMENT 'AI基础提示词文件路径',
    MODIFY COLUMN ai_prompt_criteria_file VARCHAR(255) NOT NULL COMMENT 'AI分析标准文件路径',
    MODIFY COLUMN account_state_file VARCHAR(255) NULL COMMENT '绑定账号登录态文件路径',
    MODIFY COLUMN account_strategy VARCHAR(32) NOT NULL COMMENT '账号使用策略',
    MODIFY COLUMN free_shipping TINYINT(1) NOT NULL COMMENT '是否筛选包邮商品',
    MODIFY COLUMN new_publish_option VARCHAR(64) NULL COMMENT '发布时间筛选条件',
    MODIFY COLUMN region VARCHAR(255) NULL COMMENT '地区筛选条件',
    MODIFY COLUMN decision_mode VARCHAR(32) NOT NULL COMMENT '决策模式(ai或keyword)',
    MODIFY COLUMN keyword_rules_json LONGTEXT NOT NULL COMMENT '关键词规则JSON',
    MODIFY COLUMN is_running TINYINT(1) NOT NULL COMMENT '任务是否运行中',
    COMMENT = '监控任务配置表'
    """,
    """
    ALTER TABLE result_items
    MODIFY COLUMN id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    MODIFY COLUMN result_filename VARCHAR(255) NOT NULL COMMENT '结果集逻辑文件名',
    MODIFY COLUMN keyword VARCHAR(255) NOT NULL COMMENT '搜索关键词',
    MODIFY COLUMN task_name VARCHAR(255) NOT NULL COMMENT '来源任务名称',
    MODIFY COLUMN crawl_time VARCHAR(64) NOT NULL COMMENT '抓取时间',
    MODIFY COLUMN publish_time VARCHAR(64) NULL COMMENT '商品发布时间',
    MODIFY COLUMN price DOUBLE NULL COMMENT '商品数值价格',
    MODIFY COLUMN price_display VARCHAR(64) NULL COMMENT '商品展示价格',
    MODIFY COLUMN item_id VARCHAR(255) NULL COMMENT '商品ID',
    MODIFY COLUMN title TEXT NULL COMMENT '商品标题',
    MODIFY COLUMN link TEXT NULL COMMENT '商品链接',
    MODIFY COLUMN link_unique_key VARCHAR(512) NOT NULL COMMENT '商品去重键',
    MODIFY COLUMN seller_nickname VARCHAR(255) NULL COMMENT '卖家昵称',
    MODIFY COLUMN is_recommended TINYINT(1) NOT NULL COMMENT '是否推荐',
    MODIFY COLUMN analysis_source VARCHAR(32) NULL COMMENT '分析来源',
    MODIFY COLUMN keyword_hit_count INT NOT NULL COMMENT '关键词命中次数',
    MODIFY COLUMN status VARCHAR(32) NOT NULL DEFAULT 'active' COMMENT '结果状态(active/hidden/expired)',
    MODIFY COLUMN raw_json LONGTEXT NOT NULL COMMENT '原始结果JSON',
    COMMENT = '监控结果明细表'
    """,
    """
    ALTER TABLE price_snapshots
    MODIFY COLUMN id BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    MODIFY COLUMN keyword_slug VARCHAR(255) NOT NULL COMMENT '关键词标准化标识',
    MODIFY COLUMN keyword VARCHAR(255) NOT NULL COMMENT '搜索关键词',
    MODIFY COLUMN task_name VARCHAR(255) NOT NULL COMMENT '来源任务名称',
    MODIFY COLUMN snapshot_time VARCHAR(64) NOT NULL COMMENT '快照时间',
    MODIFY COLUMN snapshot_day VARCHAR(32) NOT NULL COMMENT '快照日期',
    MODIFY COLUMN run_id VARCHAR(64) NOT NULL COMMENT '单次运行批次ID',
    MODIFY COLUMN item_id VARCHAR(255) NOT NULL COMMENT '商品ID',
    MODIFY COLUMN title TEXT NULL COMMENT '商品标题',
    MODIFY COLUMN price DOUBLE NOT NULL COMMENT '商品价格',
    MODIFY COLUMN price_display VARCHAR(64) NULL COMMENT '商品展示价格',
    MODIFY COLUMN tags_json LONGTEXT NOT NULL COMMENT '商品标签JSON',
    MODIFY COLUMN region VARCHAR(255) NULL COMMENT '发货地区',
    MODIFY COLUMN seller VARCHAR(255) NULL COMMENT '卖家昵称',
    MODIFY COLUMN publish_time VARCHAR(64) NULL COMMENT '商品发布时间',
    MODIFY COLUMN link TEXT NULL COMMENT '商品链接',
    COMMENT = '价格历史快照表'
    """,
    """
    ALTER TABLE result_blacklist_rules
    MODIFY COLUMN result_filename VARCHAR(255) NOT NULL COMMENT '结果集逻辑文件名',
    MODIFY COLUMN blacklist_keywords_json LONGTEXT NOT NULL COMMENT '黑名单关键词JSON',
    MODIFY COLUMN updated_at VARCHAR(64) NOT NULL COMMENT '更新时间',
    COMMENT = '结果黑名单规则表'
    """,
)


@dataclass(frozen=True)
class MysqlConfig:
    host: str
    port: int
    user: str
    password: str
    database: str
    charset: str = "utf8mb4"


class DatabaseCursor:
    def __init__(self, cursor):
        self._cursor = cursor

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    @property
    def rowcount(self) -> int:
        return int(getattr(self._cursor, "rowcount", 0) or 0)

    @property
    def lastrowid(self) -> Any:
        return getattr(self._cursor, "lastrowid", None)


class DatabaseConnection:
    def __init__(self, backend: str, raw_connection):
        self.backend = backend
        self._raw = raw_connection

    def execute(self, query: str, params: tuple | list | None = None) -> DatabaseCursor:
        cursor = self._raw.cursor()
        normalized_params = params or ()
        cursor.execute(
            _adapt_query(query, self.backend, normalized_params),
            _normalize_params(normalized_params),
        )
        return DatabaseCursor(cursor)

    def commit(self) -> None:
        self._raw.commit()

    def rollback(self) -> None:
        self._raw.rollback()

    def close(self) -> None:
        self._raw.close()


def get_database_url() -> str:
    return str(os.getenv("APP_DATABASE_URL", "") or "").strip()


def get_database_backend(db_path: str | None = None) -> str:
    if db_path is not None:
        return SQLITE_BACKEND
    url = get_database_url()
    if not url:
        return SQLITE_BACKEND
    if url.startswith(("mysql://", "mysql+pymysql://")):
        return MYSQL_BACKEND
    if url.startswith("sqlite://"):
        return SQLITE_BACKEND
    raise ValueError("Unsupported APP_DATABASE_URL. Use mysql:// or sqlite:///")


def get_database_path() -> str:
    url = get_database_url()
    if url.startswith("sqlite:///"):
        return url[len("sqlite:///") :]
    return os.getenv("APP_DATABASE_FILE", DEFAULT_DATABASE_PATH)


def _prepare_database_file(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def _parse_mysql_config(url: str) -> MysqlConfig:
    parsed = urlparse(url)
    if parsed.scheme not in {"mysql", "mysql+pymysql"}:
        raise ValueError("Unsupported MySQL URL scheme")
    database = parsed.path.lstrip("/")
    if not database:
        raise ValueError("MySQL URL must include a database name")
    query = parse_qs(parsed.query)
    charset = (query.get("charset") or ["utf8mb4"])[0]
    return MysqlConfig(
        host=parsed.hostname or "127.0.0.1",
        port=int(parsed.port or 3306),
        user=unquote(parsed.username or ""),
        password=unquote(parsed.password or ""),
        database=database,
        charset=charset,
    )


def _mysql_connect(config: MysqlConfig, *, with_database: bool):
    if pymysql is None:  # pragma: no cover - depends on optional dependency
        raise RuntimeError("PyMySQL is required when APP_DATABASE_URL points to MySQL")
    kwargs = {
        "host": config.host,
        "port": config.port,
        "user": config.user,
        "password": config.password,
        "charset": config.charset,
        "autocommit": False,
        "cursorclass": DictCursor,
    }
    if with_database:
        kwargs["database"] = config.database
    return pymysql.connect(**kwargs)


def _escape_mysql_identifier(identifier: str) -> str:
    return identifier.replace("`", "``")


def _ensure_mysql_database(config: MysqlConfig) -> None:
    ready_key = (config.host, config.port, config.user, config.database)
    if ready_key in MYSQL_READY_DATABASES:
        return
    with MYSQL_BOOTSTRAP_LOCK:
        if ready_key in MYSQL_READY_DATABASES:
            return
        bootstrap_conn = _mysql_connect(config, with_database=False)
        try:
            db_name = _escape_mysql_identifier(config.database)
            bootstrap_conn.cursor().execute(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            bootstrap_conn.commit()
        finally:
            bootstrap_conn.close()
        MYSQL_READY_DATABASES.add(ready_key)


def _apply_sqlite_pragmas(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute(f"PRAGMA busy_timeout={BUSY_TIMEOUT_MS}")


def _normalize_params(params):
    if isinstance(params, dict):
        return params
    return tuple(params)


def _adapt_query(query: str, backend: str, params=None) -> str:
    sql = query
    if backend == MYSQL_BACKEND:
        sql = sql.replace("INSERT OR IGNORE INTO", "INSERT IGNORE INTO")
        sql = sql.replace("INSERT OR REPLACE INTO", "REPLACE INTO")
        if isinstance(params, dict):
            sql = re.sub(r":([A-Za-z_][A-Za-z0-9_]*)", r"%(\1)s", sql)
        else:
            sql = sql.replace("?", "%s")
    return sql


def _mysql_column_exists(conn: DatabaseConnection, table_name: str, column_name: str) -> bool:
    row = conn.execute(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name = ?
          AND column_name = ?
        LIMIT 1
        """,
        (table_name, column_name),
    ).fetchone()
    return row is not None


def _mysql_index_exists(conn: DatabaseConnection, table_name: str, index_name: str) -> bool:
    row = conn.execute(
        """
        SELECT 1
        FROM information_schema.statistics
        WHERE table_schema = DATABASE()
          AND table_name = ?
          AND index_name = ?
        LIMIT 1
        """,
        (table_name, index_name),
    ).fetchone()
    return row is not None


def _init_mysql_schema(conn: DatabaseConnection) -> None:
    for statement in MYSQL_SCHEMA_STATEMENTS:
        conn.execute(statement)
    _migrate_result_items_status(conn)
    _apply_mysql_comments(conn)
    for index_name, table_name, statement in MYSQL_INDEX_DEFINITIONS:
        if not _mysql_index_exists(conn, table_name, index_name):
            conn.execute(statement)
    conn.commit()


def _init_sqlite_schema(conn: DatabaseConnection) -> None:
    for statement in SQLITE_SCHEMA_STATEMENTS:
        conn.execute(statement)
    _migrate_result_items_status(conn)
    conn.commit()


def init_schema(conn: DatabaseConnection) -> None:
    if conn.backend == MYSQL_BACKEND:
        _init_mysql_schema(conn)
        return
    _init_sqlite_schema(conn)


def _migrate_result_items_status(conn: DatabaseConnection) -> None:
    """Add the status column for older installs if it is missing."""
    row = conn.execute(
        "SELECT value FROM app_metadata WHERE `key` = ?",
        ("migration:result_items_status",),
    ).fetchone()
    if row is not None:
        return

    if conn.backend == MYSQL_BACKEND:
        if not _mysql_column_exists(conn, "result_items", "status"):
            conn.execute(
                "ALTER TABLE result_items ADD COLUMN status VARCHAR(32) NOT NULL DEFAULT 'active'"
            )
    else:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(result_items)").fetchall()]
        if "status" not in cols:
            conn.execute(
                "ALTER TABLE result_items ADD COLUMN status TEXT NOT NULL DEFAULT 'active'"
            )

    conn.execute(
        "INSERT OR REPLACE INTO app_metadata(`key`, value) VALUES (?, 'done')",
        ("migration:result_items_status",),
    )

    if conn.backend == MYSQL_BACKEND:
        if not _mysql_index_exists(conn, "result_items", "idx_results_filename_status_crawl"):
            conn.execute(
                "CREATE INDEX idx_results_filename_status_crawl ON result_items(result_filename, status, crawl_time)"
            )
    else:
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_results_filename_status_crawl"
            " ON result_items(result_filename, status, crawl_time DESC)"
        )


def _apply_mysql_comments(conn: DatabaseConnection) -> None:
    row = conn.execute(
        "SELECT value FROM app_metadata WHERE `key` = ?",
        (MYSQL_COMMENT_MIGRATION_KEY,),
    ).fetchone()
    if row is not None:
        return
    for statement in MYSQL_COMMENT_STATEMENTS:
        conn.execute(statement)
    conn.execute(
        "INSERT OR REPLACE INTO app_metadata(`key`, value) VALUES (?, 'done')",
        (MYSQL_COMMENT_MIGRATION_KEY,),
    )


@contextmanager
def sqlite_connection(
    db_path: str | None = None,
) -> Iterator[DatabaseConnection]:
    """
    Historical helper name kept for compatibility.

    When APP_DATABASE_URL points to MySQL, this yields a MySQL-backed
    connection wrapper; otherwise it falls back to SQLite.
    """
    backend = get_database_backend(db_path)
    if backend == MYSQL_BACKEND:
        config = _parse_mysql_config(get_database_url())
        _ensure_mysql_database(config)
        raw = _mysql_connect(config, with_database=True)
    else:
        path = db_path or get_database_path()
        _prepare_database_file(path)
        raw = sqlite3.connect(path)
        raw.row_factory = sqlite3.Row
        _apply_sqlite_pragmas(raw)

    conn = DatabaseConnection(backend, raw)
    try:
        yield conn
    except Exception:
        try:
            conn.rollback()
        finally:
            conn.close()
        raise
    else:
        conn.close()
