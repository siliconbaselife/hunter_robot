CREATE TABLE IF NOT EXISTS `candidate`(
   `boss_id` VARCHAR(100) NOT NULL COMMENT 'boss用户ID',
   `candidate_id` VARCHAR(100) NOT NULL COMMENT '候选人ID',
   `status` VARCHAR(256) NOT NULL COMMENT '当前状态',
   `contact` VARCHAR(256) COMMENT '联系方式',
   `details` LONGTEXT COMMENT '对话详情',
   `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
   `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
   PRIMARY KEY ( `candidate_id` ),
   CONSTRAINT `candidate_info` UNIQUE(`boss_id`, `candidate_id`)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;
