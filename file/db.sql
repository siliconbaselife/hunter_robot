CREATE TABLE `account_config` (
  `id` bigint(10) unsigned NOT NULL AUTO_INCREMENT COMMENT 'id',
  `account_id` varchar(60) NOT NULL COMMENT 'boss直聘唯一id',
  `config` text NOT NULL DEFAULT '' COMMENT '执行配置',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='账号配置表'

=====config===========
[
	{
		"job_id":"common_kefu",
		"hello_sum":50,
		"time_percent": [
		{
			"time":"09:00",
			"percent":50
		}, 
		{
			"time":"16:00",
			"percent":50
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




