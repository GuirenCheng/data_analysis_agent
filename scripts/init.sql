-- Data Analysis Agent v2.0 数据库初始化脚本
-- 由 docker-compose 在 MySQL 首次启动时自动执行

CREATE DATABASE IF NOT EXISTS data_analysis_agent
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE data_analysis_agent;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id CHAR(36) PRIMARY KEY,
    username VARCHAR(128) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 分析会话表
CREATE TABLE IF NOT EXISTS analysis_sessions (
    id CHAR(36) PRIMARY KEY,
    user_id CHAR(36) NOT NULL,
    title VARCHAR(512),
    query TEXT NOT NULL,
    status ENUM('pending','running','completed','failed','cancelled') DEFAULT 'pending',
    max_rounds INT DEFAULT 20,
    current_round INT DEFAULT 0,
    output_dir VARCHAR(1024),
    report_path VARCHAR(1024),
    progress FLOAT DEFAULT 0.0,
    error_message TEXT,
    started_at DATETIME,
    completed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 分析步骤表
CREATE TABLE IF NOT EXISTS analysis_steps (
    id CHAR(36) PRIMARY KEY,
    session_id CHAR(36) NOT NULL,
    round_number INT NOT NULL,
    action VARCHAR(32) NOT NULL,
    code MEDIUMTEXT,
    response_text MEDIUMTEXT,
    execution_output TEXT,
    execution_error TEXT,
    execution_success BOOLEAN,
    figures_collected JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES analysis_sessions(id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_session_round (session_id, round_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 上传文件表
CREATE TABLE IF NOT EXISTS analysis_files (
    id CHAR(36) PRIMARY KEY,
    user_id CHAR(36) NOT NULL,
    session_id CHAR(36),
    original_name VARCHAR(512) NOT NULL,
    stored_path VARCHAR(1024) NOT NULL,
    file_size BIGINT,
    mime_type VARCHAR(128),
    columns_detected JSON,
    row_count INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_session_id (session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 用户配置表
CREATE TABLE IF NOT EXISTS user_configs (
    id CHAR(36) PRIMARY KEY,
    user_id CHAR(36) NOT NULL UNIQUE,
    llm_provider VARCHAR(64) DEFAULT 'openai',
    llm_model VARCHAR(128) DEFAULT 'gpt-4-turbo-preview',
    llm_base_url VARCHAR(512),
    llm_api_key_encrypted VARCHAR(512),
    temperature FLOAT DEFAULT 0.1,
    max_tokens INT DEFAULT 16384,
    default_max_rounds INT DEFAULT 20,
    default_output_dir VARCHAR(512) DEFAULT 'outputs',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- RAG 文档元数据表
CREATE TABLE IF NOT EXISTS rag_documents (
    id CHAR(36) PRIMARY KEY,
    user_id CHAR(36) NOT NULL,
    source_session_id CHAR(36),
    chunk_index INT,
    content_type VARCHAR(64) DEFAULT 'query',
    content_text TEXT NOT NULL,
    chroma_id VARCHAR(128),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (source_session_id) REFERENCES analysis_sessions(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_content_type (content_type),
    FULLTEXT INDEX ft_content (content_text)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
