-- ============================================================
-- easy_workbuddy / light_agent 建表脚本（MySQL 8.0）
-- 字符集：utf8mb4；引擎：InnoDB；软删除：deleted_at
-- 说明：所有业务数据归属 workspace_id + user_id，后端按当前用户做行级过滤
-- ============================================================

USE `light_agent`;

-- ---------- 用户与账户 ----------
CREATE TABLE IF NOT EXISTS `users` (
  `id`            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `username`      VARCHAR(64)  NOT NULL                COMMENT '登录名',
  `email`         VARCHAR(128) NOT NULL                COMMENT '邮箱（登录/通知）',
  `password_hash` VARCHAR(255) NOT NULL                COMMENT 'bcrypt 哈希',
  `status`        TINYINT      NOT NULL DEFAULT 1      COMMENT '0 禁用 / 1 正常',
  `last_login_at` DATETIME     NULL     DEFAULT NULL   COMMENT '最近登录',
  `created_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at`    DATETIME     NULL     DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`),
  UNIQUE KEY `uk_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

CREATE TABLE IF NOT EXISTS `user_profiles` (
  `id`         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id`    BIGINT UNSIGNED NOT NULL,
  `nickname`   VARCHAR(64)  NULL DEFAULT NULL          COMMENT '昵称',
  `avatar_url` VARCHAR(512) NULL DEFAULT NULL          COMMENT '头像',
  `phone`      VARCHAR(32)  NULL DEFAULT NULL          COMMENT '手机号',
  `bio`        VARCHAR(500) NULL DEFAULT NULL          COMMENT '简介',
  `settings`   JSON         NULL DEFAULT NULL          COMMENT '偏好设置（主题/语言等）',
  `created_at` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_id` (`user_id`),
  CONSTRAINT `fk_profiles_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='个人信息扩展';

-- ---------- 工作空间 ----------
CREATE TABLE IF NOT EXISTS `workspaces` (
  `id`          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id`     BIGINT UNSIGNED NOT NULL,
  `name`        VARCHAR(128) NOT NULL                COMMENT '空间名',
  `description` VARCHAR(500) NULL     DEFAULT NULL   COMMENT '描述',
  `is_default`  TINYINT      NOT NULL DEFAULT 0      COMMENT '是否默认空间',
  `created_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at`  DATETIME     NULL     DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_user` (`user_id`),
  CONSTRAINT `fk_ws_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工作空间';

-- ---------- 任务 ----------
CREATE TABLE IF NOT EXISTS `tasks` (
  `id`           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `workspace_id` BIGINT UNSIGNED NOT NULL,
  `user_id`      BIGINT UNSIGNED NOT NULL,
  `title`        VARCHAR(255) NOT NULL               COMMENT '标题',
  `description`  TEXT         NULL                   COMMENT '描述',
  `status`       TINYINT      NOT NULL DEFAULT 0     COMMENT '0 待办 / 1 进行中 / 2 已完成 / 3 已取消',
  `priority`     TINYINT      NOT NULL DEFAULT 2     COMMENT '1 低 / 2 中 / 3 高',
  `due_date`     DATETIME     NULL     DEFAULT NULL  COMMENT '截止时间',
  `completed_at` DATETIME     NULL     DEFAULT NULL  COMMENT '完成时间',
  `created_at`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at`   DATETIME     NULL     DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_workspace_user` (`workspace_id`, `user_id`),
  KEY `idx_status` (`status`),
  CONSTRAINT `fk_task_ws`   FOREIGN KEY (`workspace_id`) REFERENCES `workspaces` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_task_user` FOREIGN KEY (`user_id`)      REFERENCES `users` (`id`)      ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务表';

-- ---------- Agent（智能体） ----------
CREATE TABLE IF NOT EXISTS `agents` (
  `id`            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id`       BIGINT UNSIGNED NOT NULL,
  `workspace_id`  BIGINT UNSIGNED NULL     DEFAULT NULL,
  `name`          VARCHAR(128) NOT NULL               COMMENT 'Agent 名称',
  `description`   VARCHAR(500) NULL     DEFAULT NULL  COMMENT '描述',
  `system_prompt` TEXT         NULL                   COMMENT '系统提示词',
  `model`         VARCHAR(64)  NULL     DEFAULT NULL  COMMENT '使用的模型',
  `tools`         JSON         NULL     DEFAULT NULL  COMMENT '启用的工具名列表',
  `created_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at`    DATETIME     NULL     DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_agent_user` (`user_id`),
  KEY `idx_agent_ws` (`workspace_id`),
  CONSTRAINT `fk_agent_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_agent_ws`   FOREIGN KEY (`workspace_id`) REFERENCES `workspaces` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Agent 智能体';

-- ---------- 会话与消息 ----------
CREATE TABLE IF NOT EXISTS `conversations` (
  `id`            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id`       BIGINT UNSIGNED NOT NULL,
  `workspace_id`  BIGINT UNSIGNED NULL     DEFAULT NULL,
  `agent_id`      BIGINT UNSIGNED NULL     DEFAULT NULL,
  `title`         VARCHAR(255) NOT NULL DEFAULT '新会话' COMMENT '会话标题（可自动生成）',
  `model`         VARCHAR(64)  NULL     DEFAULT NULL  COMMENT '使用的模型',
  `summary`       VARCHAR(500) NULL     DEFAULT NULL  COMMENT '摘要',
  `created_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at`    DATETIME     NULL     DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_user` (`user_id`),
  KEY `idx_ws` (`workspace_id`),
  KEY `idx_agent` (`agent_id`),
  CONSTRAINT `fk_conv_user`  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_conv_ws`    FOREIGN KEY (`workspace_id`) REFERENCES `workspaces` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_conv_agent` FOREIGN KEY (`agent_id`) REFERENCES `agents` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会话表';

CREATE TABLE IF NOT EXISTS `messages` (
  `id`              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `conversation_id` BIGINT UNSIGNED NOT NULL,
  `role`            VARCHAR(16)  NOT NULL               COMMENT 'user / assistant / system',
  `content`         MEDIUMTEXT   NOT NULL               COMMENT '消息内容',
  `tokens`          INT          NULL     DEFAULT NULL  COMMENT 'token 消耗',
  `attachments`     MEDIUMTEXT   NULL                   COMMENT 'JSON：图片/文件附件（刷新后恢复展示）',
  `created_at`      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_conversation` (`conversation_id`, `created_at`),
  CONSTRAINT `fk_msg_conv` FOREIGN KEY (`conversation_id`) REFERENCES `conversations` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='消息表';

-- ---------- 资料库与文档 ----------
CREATE TABLE IF NOT EXISTS `knowledge_docs` (
  `id`            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id`       BIGINT UNSIGNED NOT NULL,
  `workspace_id`  BIGINT UNSIGNED NULL     DEFAULT NULL,
  `title`         VARCHAR(255) NOT NULL               COMMENT '文档标题',
  `category`      VARCHAR(64)  NULL     DEFAULT NULL  COMMENT '分类标签',
  `created_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at`    DATETIME     NULL     DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_user` (`user_id`),
  KEY `idx_ws` (`workspace_id`),
  CONSTRAINT `fk_kd_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_kd_ws`   FOREIGN KEY (`workspace_id`) REFERENCES `workspaces` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='资料库条目';

CREATE TABLE IF NOT EXISTS `documents` (
  `id`               BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `knowledge_doc_id` BIGINT UNSIGNED NULL     DEFAULT NULL,
  `user_id`          BIGINT UNSIGNED NOT NULL,
  `workspace_id`     BIGINT UNSIGNED NULL     DEFAULT NULL,
  `original_name`    VARCHAR(255) NOT NULL               COMMENT '原始文件名',
  `stored_path`      VARCHAR(512) NOT NULL               COMMENT 'MinIO 对象 key（如 ws-12/u-3/2026/abc.docx）',
  `file_type`        VARCHAR(32)  NULL     DEFAULT NULL  COMMENT 'docx/xlsx/pdf/...',
  `file_size`        BIGINT       NOT NULL DEFAULT 0     COMMENT '字节',
  `text_content`     LONGTEXT     NULL                   COMMENT '解析出的纯文本（用于检索）',
  `parse_status`     TINYINT      NOT NULL DEFAULT 0     COMMENT '0 待解析 / 1 成功 / 2 失败',
  `created_at`       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at`       DATETIME     NULL     DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_kd` (`knowledge_doc_id`),
  KEY `idx_user` (`user_id`),
  KEY `idx_ws` (`workspace_id`),
  CONSTRAINT `fk_doc_kd`   FOREIGN KEY (`knowledge_doc_id`) REFERENCES `knowledge_docs` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_doc_user` FOREIGN KEY (`user_id`)          REFERENCES `users` (`id`)          ON DELETE CASCADE,
  CONSTRAINT `fk_doc_ws`   FOREIGN KEY (`workspace_id`)     REFERENCES `workspaces` (`id`)     ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文档/附件元数据';
