CREATE TABLE IF NOT EXISTS `transactions` (
    `transaction_id` INT NOT NULL AUTO_INCREMENT,
    `user_id` INT DEFAULT NULL,
    `tool_id` INT DEFAULT NULL,
    `checkout_timestamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `desired_return_date` DATETIME DEFAULT NULL,
    `return_timestamp` DATETIME DEFAULT NULL,
    `quantity` INT DEFAULT 1,
    `purpose` TEXT,
    `image_path` VARCHAR(255) DEFAULT NULL,
    `classification_correct` BOOLEAN DEFAULT NULL,
    `weight` INT DEFAULT 0,
    PRIMARY KEY (`transaction_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
