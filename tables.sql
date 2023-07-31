CREATE TABLE IF NOT EXISTS `candidate`(
   `account_id` VARCHAR(100) NOT NULL COMMENT '联系账号的account_id',
   `job_id` VARCHAR(100) NOT NULL COMMENT '候选的岗位job_id',
   `candidate_id` VARCHAR(100) NOT NULL COMMENT '候选人ID',
   `candidate_name` VARCHAR(100) NOT NULL COMMENT '候选人姓名',
   `status` VARCHAR(256) NOT NULL COMMENT '当前状态',
   `contact` LONGTEXT COMMENT '联系方式',
   `details` LONGTEXT COMMENT '对话详情',
   `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
   `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
   PRIMARY KEY ( `candidate_id` ),
   CONSTRAINT `candidate_info` UNIQUE(`account_id`, `job_id`, `candidate_id`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_as_cs;


CREATE TABLE IF NOT EXISTS `job`(
   `job_id` VARCHAR(100) NOT NULL COMMENT '岗位唯一标识',
   `job_name` VARCHAR(100) NOT NULL COMMENT '岗位名称',
   `job_jd` LONGTEXT COMMENT '岗位jd',
   `robot_api` LONGTEXT COMMENT '算法调用api',
   `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
   `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
   PRIMARY KEY ( `job_id` )
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_as_cs;


CREATE TABLE IF NOT EXISTS `account`(
   `account_id` VARCHAR(100) NOT NULL COMMENT '账号唯一标识',
   `platform_type` VARCHAR(256) NOT NULL COMMENT '招聘平台枚举，如：boss',
   `platform_id` VARCHAR(256) NOT NULL COMMENT '招聘平台内的id',
   `task_config` LONGTEXT COMMENT '任务配置，根据招聘的职位生成',
   `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
   `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
   PRIMARY KEY ( `account_id` )
   CONSTRAINT `account_info` UNIQUE(`platform_type`, `platform_id`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_as_cs;