USE `tool_e_db`;

DROP TABLE IF EXISTS `transactions`;

CREATE TABLE `transactions` (
  `transaction_id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT,
  `tool_id` BIGINT UNSIGNED,
  `checkout_timestamp` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `desired_return_date` TIMESTAMP NULL,
  `return_timestamp` TIMESTAMP NULL,
  `quantity` INT NOT NULL DEFAULT 1,
  `purpose` VARCHAR(255) NULL,
  `image_path` VARCHAR(512) NULL,
  `classification_correct` BOOLEAN NULL,
  `weight` INT DEFAULT 0,
  PRIMARY KEY (`transaction_id`),
  CONSTRAINT `fk_tool`
    FOREIGN KEY (`tool_id`)
    REFERENCES `tools` (`tool_id`)
    ON DELETE SET NULL
);

INSERT INTO `transactions`
(`user_id`, `tool_id`, `checkout_timestamp`, `desired_return_date`, `return_timestamp`, `quantity`, `purpose`, `image_path`, `classification_correct`, `weight`)
VALUES
(101, 1, CURRENT_TIMESTAMP, DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 7 DAY), NULL, 1, 'Prototype build', 'uploads/mock_tool_1.jpg', 1, 0);
