USE `tool_e_db`;

DROP TABLE IF EXISTS `tools`;

CREATE TABLE `tools` (
  `tool_id` bigint UNSIGNED NOT NULL AUTO_INCREMENT,
  `tool_name` varchar(255) NOT NULL,
  `tool_size` varchar(100) DEFAULT NULL,
  `tool_type` varchar(20) DEFAULT NULL,
  `current_status` varchar(50) DEFAULT 'Available',
  `total_quantity` int DEFAULT 0,
  `available_quantity` int DEFAULT 0,
  `consumed_quantity` int DEFAULT 0,
  `trained` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`tool_id`)
);

INSERT INTO `tools` (`tool_name`, `tool_size`, `tool_type`, `current_status`, `total_quantity`, `available_quantity`, `consumed_quantity`, `trained`) VALUES
('Adjustable Wrench', 'onesize', 'Hand Tool', 'Available', 5, 5, 0, 1),
('Allen Key', 'onesize', 'Hand Tool', 'Available', 5, 5, 0, 1),
('Box Cutter', 'onesize', 'Hand Tool', 'Available', 5, 5, 0, 1),
('Breadboard', 'onesize', 'Hand Tool', 'Available', 5, 5, 0, 1),
('Caliper', 'onesize', 'Hand Tool', 'Available', 5, 5, 0, 1),
('Channel Lock', 'onesize', 'Hand Tool', 'Available', 5, 5, 0, 1),
('File', 'onesize', 'Hand Tool', 'Available', 5, 5, 0, 1),
('Hot Glue Gun', 'onesize', 'Hand Tool', 'Available', 5, 5, 0, 1),
('Multimeter', 'onesize', 'Hand Tool', 'Available', 5, 5, 0, 1),
('Plier', 'onesize', 'Hand Tool', 'Available', 5, 5, 0, 1),
('Safety Glasses', 'onesize', 'Hand Tool', 'Available', 5, 5, 0, 1),
('Scissors', 'onesize', 'Hand Tool', 'Available', 5, 5, 0, 1),
('Screwdriver', 'onesize', 'Hand Tool', 'Available', 5, 5, 0, 1),
('Super Glue', 'onesize', 'Hand Tool', 'Available', 5, 5, 0, 1),
('Tape Measure', 'onesize', 'Hand Tool', 'Available', 5, 5, 0, 1);
