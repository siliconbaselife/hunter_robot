CREATE TABLE IF NOT EXISTS `chat`(
   `account_id` VARCHAR(100) NOT NULL COMMENT '联系账号的account_id',
   `job_id` VARCHAR(100) NOT NULL COMMENT '候选的岗位job_id',
   `candidate_id` VARCHAR(100) NOT NULL COMMENT '候选人ID',
   `candidate_name` VARCHAR(100) NOT NULL COMMENT '候选人姓名',
   `source` VARCHAR(256) NOT NULL COMMENT '联系人是搜索匹配的主动联系的：search或者user_ask',
   `status` VARCHAR(256) NOT NULL COMMENT '当前状态',
   `contact` LONGTEXT COMMENT '联系方式',
   `details` LONGTEXT COMMENT '对话详情',
   `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
   `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
   CONSTRAINT `candidate_info` UNIQUE(`account_id`, `job_id`, `candidate_id`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_as_cs;

ALTER TABLE chat ADD filter_result LONGTEXT COMMENT 'filter详情' AFTER details;


CREATE TABLE IF NOT EXISTS `candidate`(
   `candidate_id` VARCHAR(100) NOT NULL COMMENT '候选人ID',
   `candidate_name` VARCHAR(100) NOT NULL COMMENT '候选人姓名',
   `age` int COMMENT '年龄',
   `degree` VARCHAR(100) COMMENT '学历',
   `location` VARCHAR(100) COMMENT '目标工作地点',
   `contact` LONGTEXT COMMENT '联系方式',
   `details` LONGTEXT COMMENT '候选人详细信息',
   `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
   `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
   PRIMARY KEY ( `candidate_id` )
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_as_cs;

ALTER TABLE candidate ADD position VARCHAR(100) COMMENT '目标工作职位' AFTER location;
ALTER TABLE candidate ADD filter_result LONGTEXT COMMENT 'filter详情' AFTER details;

CREATE TABLE IF NOT EXISTS `job`(
   `job_id` VARCHAR(100) NOT NULL COMMENT '岗位唯一标识',
   `platform_type` VARCHAR(256) NOT NULL COMMENT '招聘平台枚举，如：boss',
   `platform_id` VARCHAR(256) NOT NULL COMMENT '招聘平台内的job id',
   `job_name` VARCHAR(100) NOT NULL COMMENT '岗位名称',
   `job_jd` LONGTEXT COMMENT '岗位jd',
   -- `requirement_config` LONGTEXT COMMENT '岗位需求配置',
   `robot_api` LONGTEXT COMMENT '算法调用api',
   `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
   `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
   PRIMARY KEY ( `job_id` ),
   CONSTRAINT `account_info` UNIQUE(`platform_type`, `platform_id`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_as_cs;

alter table job add job_config varchar(512) NOT NULL DEFAULT "" COMMENT '岗位配置' after robot_api;
{"group_msg":"beijing","filter_config":"common_custom_service_filter"}


-- =====requirement_config===========
-- [
--    ["age", "range", 18, 35],
--    ["education", "min", "大专"],
--    ["experience", "contain", "客服"]
-- ]

CREATE TABLE IF NOT EXISTS `account`(
   `account_id` VARCHAR(100) NOT NULL COMMENT '账号唯一标识',
   `platform_type` VARCHAR(256) NOT NULL COMMENT '招聘平台枚举，如：boss',
   `platform_id` VARCHAR(256) NOT NULL COMMENT '招聘平台内的账号id',
   `jobs` LONGTEXT COMMENT '招聘的岗位job_id列表',
   `task_config` LONGTEXT COMMENT '任务配置，根据招聘的职位生成',
   `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
   `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
   PRIMARY KEY ( `account_id` ),
   CONSTRAINT `account_info` UNIQUE(`platform_type`, `platform_id`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_as_cs;
alter table account add description varchar(100) NOT NULL DEFAULT "" COMMENT '账户描述' after task_config;


=====task_config===========
[
	{
      "task_type":"batchTouch",
		"job_id":"common_kefu",
		"hello_sum":50,
		"time_percent": [
		{
			"time":"09:00",
			"percent":"50"
		}, 
		{
			"time":"16:00",
			"percent":"50"
		}
		]
	}
]

CREATE TABLE `account_exec_log` (
  `id` bigint(10) unsigned NOT NULL AUTO_INCREMENT COMMENT 'id',
  `account_id` varchar(60) NOT NULL COMMENT 'boss直聘唯一id',
  `job_id` varchar(60) NOT NULL COMMENT '岗位id',
  `exec_date` varchar(60) NOT NULL COMMENT '任务执行日期',
  `hello_sum_need` int unsigned NOT NULL COMMENT '应打招呼数量',
  `hello_sum_exec` int unsigned NOT NULL DEFAULT 0  COMMENT '实际打招呼数量',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='账号任务执行记录'


CREATE TABLE IF NOT EXISTS `wechat_account`(
   `wechat_account_id` VARCHAR(100) NOT NULL COMMENT '账号唯一标识',
   `task_config` LONGTEXT COMMENT '日常任务',
   `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
   `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
   PRIMARY KEY ( `wechat_account_id` )
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_as_cs;
<<<<<<< HEAD
=======
alter table wechat_account add description varchar(100) NOT NULL DEFAULT "" COMMENT '账户描述' after wechat_account_id;

>>>>>>> v2.0


CREATE TABLE IF NOT EXISTS `wechat_chat`(
   `candidate_id` VARCHAR(100) NOT NULL COMMENT '候选人的id',
   `candidate_name` VARCHAR(100) NOT NULL COMMENT '候选人名字',
   `wechat_id` VARCHAR(256) NOT NULL COMMENT '候选人的微信id',
   `wechat_alias_id` VARCHAR(256) NOT NULL COMMENT '给候选人的备注',
   `wechat_accoount_id` VARCHAR(256) NOT NULL COMMENT '我们的微信账号',
   `details` LONGTEXT COMMENT '对话详情',
   `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
   `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
   PRIMARY KEY ( `candidate_id`, `wechat_accoount_id` )
)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_as_cs;
<<<<<<< HEAD
=======
alter table wechat_chat add `status` int unsigned NOT NULL DEFAULT 0 COMMENT '状态0待添加，1已发送请求，2已添加成功' after `details`;

>>>>>>> v2.0











