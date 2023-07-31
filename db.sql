CREATE TABLE `account_config` (
  `id` bigint(10) unsigned NOT NULL AUTO_INCREMENT COMMENT 'id',
  `boss_id` varchar(60) NOT NULL COMMENT 'boss直聘唯一id',
  `config` text NOT NULL DEFAULT '' COMMENT '执行配置',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='账号配置表'

=====config===========
[
	{
		"job":"common_kefu",
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
  `boss_id` varchar(60) NOT NULL COMMENT 'boss直聘唯一id',
  `exec_log` text NOT NULL DEFAULT '' COMMENT '执行情况',
  `status` tinyint(4) NOT NULL DEFAULT 0 COMMENT '状态 1执行中, 2已完成 -1执行失败', 
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='账号任务执行记录'


=========exec_log========
[
	{
		"job":"common_kefu",
		"hello_sum_exec":25
	}
]

