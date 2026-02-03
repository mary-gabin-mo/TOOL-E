CREATE TABLE IF NOT EXISTS `tools` (
    `tool_id` INT NOT NULL AUTO_INCREMENT,
    `tool_name` VARCHAR(255) NOT NULL,
    `tool_size` VARCHAR(50) DEFAULT NULL,
    `tool_type` VARCHAR(100) NOT NULL,
    `current_status` VARCHAR(50) DEFAULT 'Available',
    `total_quantity` INT NOT NULL,
    `available_quantity` INT NOT NULL,
    `consumed_quantity` INT DEFAULT 0,
    `trained` TINYINT(1) DEFAULT 0,
    PRIMARY KEY (`tool_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
