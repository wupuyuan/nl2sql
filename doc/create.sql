CREATE TABLE IF NOT EXISTS `demo_orders` (
  `order_id` INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '订单号',
  `order_name` VARCHAR(100) NOT NULL COMMENT '订单名称',
  `order_detail` TEXT COMMENT '订单明细',
  `order_type` TINYINT NOT NULL COMMENT '1=采购，2=销售',
  `amount` DECIMAL(12,2) NOT NULL COMMENT '金额',
  `order_status` TINYINT NOT NULL DEFAULT 1 COMMENT '-1=作废，1=正常',
  `area` VARCHAR(50) NOT NULL DEFAULT 'beijing' COMMENT '地区：beijing, shanghai',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`order_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单测试表';