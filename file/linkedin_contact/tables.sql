-- CREATE TABLE IF NOT EXISTS `extension_user`(
--    `user_id` VARCHAR(100) NOT NULL COMMENT '用户id',
--    `user_credit` int NOT NULL COMMENT '用户剩余credit',
--    `user_email` VARCHAR(100) NOT NULL COMMENT '用户email',
--    `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
--    `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
--    PRIMARY KEY ( `user_id`)
-- )ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_as_cs;

-- alter table extension_user add `already_contacts` LONGTEXT NOT NULL COMMENT '已购买联系人'  after `user_email`;

-- # "use email as user_id, same as table manage_account"
-- ALTER TABLE extension_user DROP COLUMN user_email; 
-- # "refresh table use data from manage_account"
-- insert into extension_user (user_id, user_credit, already_contacts) 
-- select manage_account_id, 0, '[]' from manage_account 
-- where manage_account_id like '%@%';

-- =====already_contacts===========
-- [
-- 	("https://www.linkedin.com/in/kaiming-he-90664838", "personal_email"),
-- ]

CREATE TABLE IF NOT EXISTS `extension_user_credit`(
   `user_id` VARCHAR(100) NOT NULL COMMENT '用户id',
   `user_credit` int NOT NULL COMMENT '用户剩余credit',
   `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
   `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
   PRIMARY KEY ( `user_id`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_as_cs;

CREATE TABLE IF NOT EXISTS `extension_user_link`(
   `user_id` VARCHAR(100) NOT NULL COMMENT '用户id',
   `link_linkedin_id` VARCHAR(200) NOT NULL COMMENT '已购买联系人linkedin_id',
   `link_contact_type` VARCHAR(100) NOT NULL COMMENT '已购买联系人联系方式(enum: personal_email, work_email, phone)',
   `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
   `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
   PRIMARY KEY ( `user_id`, `link_linkedin_id`, `link_contact_type`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_as_cs;


CREATE TABLE IF NOT EXISTS `contact_bank`(
   `linkedin_profile` VARCHAR(200) NOT NULL COMMENT 'linedin_profile url',
   `linkedin_id` VARCHAR(200) NOT NULL COMMENT 'linedin_profile id',
   `name` VARCHAR(50) NOT NULL COMMENT 'name',
   `personal_email` VARCHAR(500) NOT NULL COMMENT '个人email',
   `work_email` VARCHAR(500) NOT NULL COMMENT '工作email',
   `phone` VARCHAR(200) NOT NULL COMMENT '手机号码',
   `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
   `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
   PRIMARY KEY ( `linkedin_profile`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_as_cs;
alter table contact_bank add `work_email_status` LONGTEXT NOT NULL COMMENT '工作邮件状态'  after `work_email`;
alter table contact_bank ADD INDEX index_name (`linkedin_id`);