"""迁移脚本：新增 agents 表 + conversations 增加 agent_id 列（幂等）。"""
import asyncio
import sys
from pathlib import Path

# 确保能 import app 包（脚本位于 Backend/sql/ 下）
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from app.core.database import engine

DDL_AGENTS = """
CREATE TABLE IF NOT EXISTS `agents` (
  `id`            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id`       BIGINT UNSIGNED NOT NULL,
  `workspace_id`  BIGINT UNSIGNED NULL     DEFAULT NULL,
  `name`          VARCHAR(128) NOT NULL,
  `description`   VARCHAR(500) NULL     DEFAULT NULL,
  `system_prompt` TEXT         NULL,
  `model`         VARCHAR(64)  NULL     DEFAULT NULL,
  `tools`         JSON         NULL     DEFAULT NULL,
  `created_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at`    DATETIME     NULL     DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_agent_user` (`user_id`),
  KEY `idx_agent_ws` (`workspace_id`),
  CONSTRAINT `fk_agent_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_agent_ws`   FOREIGN KEY (`workspace_id`) REFERENCES `workspaces` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Agent 智能体';
"""


async def main():
    async with engine.begin() as conn:
        await conn.execute(text(DDL_AGENTS))

        # 检查 conversations 是否已有 agent_id 列
        r = await conn.execute(text(
            "SELECT COUNT(*) FROM information_schema.columns "
            "WHERE table_schema='light_agent' AND table_name='conversations' AND column_name='agent_id'"
        ))
        exists = r.scalar()
        if not exists:
            await conn.execute(text(
                "ALTER TABLE `conversations` "
                "ADD COLUMN `agent_id` BIGINT UNSIGNED NULL DEFAULT NULL AFTER `workspace_id`, "
                "ADD KEY `idx_agent` (`agent_id`), "
                "ADD CONSTRAINT `fk_conv_agent` FOREIGN KEY (`agent_id`) "
                "REFERENCES `agents` (`id`) ON DELETE SET NULL"
            ))
            print("已为 conversations 添加 agent_id 列")
        else:
            print("conversations 已存在 agent_id 列，跳过")

        # 校验 agents 表
        r = await conn.execute(text("SHOW TABLES LIKE 'agents'"))
        print("agents 表存在:", bool(r.scalar()))


if __name__ == "__main__":
    asyncio.run(main())
