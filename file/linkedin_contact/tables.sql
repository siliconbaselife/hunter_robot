CREATE TABLE IF NOT EXISTS `extension_user`(
   `user_id` VARCHAR(100) NOT NULL COMMENT '用户id',
   `user_credit` int NOT NULL COMMENT '用户剩余credit',
   `user_email` VARCHAR(100) NOT NULL COMMENT '用户email',
   `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
   `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
   PRIMARY KEY ( `user_id`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_as_cs;

alter table extension_user add `already_contacts` LONGTEXT NOT NULL COMMENT '已购买联系人'  after `user_email`;
=====already_contacts===========
[
	("https://www.linkedin.com/in/kaiming-he-90664838", "personal_email"),
]

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
