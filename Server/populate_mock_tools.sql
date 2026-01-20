USE `tool_e_db`;

-- Recreate the table structure
DROP TABLE IF EXISTS `tools`;

CREATE TABLE `tools` (
  `tool_id` int NOT NULL AUTO_INCREMENT,
  `tool_name` varchar(255) NOT NULL,
  `tool_size` varchar(100) DEFAULT NULL,
  `tool_type` varchar(100) NOT NULL,
  `current_status` varchar(50) DEFAULT 'Available',
  `total_quantity` int DEFAULT 0,
  `available_quantity` int DEFAULT 0,
  `consumed_quantity` int DEFAULT 0,
  `trained` boolean DEFAULT false,
  PRIMARY KEY (`tool_id`)
);

INSERT INTO `tools` 
(`tool_name`, `tool_size`, `tool_type`, `current_status`, `total_quantity`, `available_quantity`, `consumed_quantity`, `trained`) 
VALUES 
-- Hand Tools
('Slip Joint Pliers', '6 inch', 'Hand Tool', 'Available', 10, 8, 0, 0),
('Needle Nose Pliers', 'Small', 'Hand Tool', 'Available', 12, 10, 0, 0),
('Wire Strippers', 'Standard', 'Hand Tool', 'Available', 8, 5, 0, 0),
('Phillips Screwdriver', '#2', 'Hand Tool', 'Available', 20, 15, 0, 0),
('Flathead Screwdriver', '3mm', 'Hand Tool', 'Low Stock', 15, 3, 0, 0),
('Rubber Mallet', '16 oz', 'Hand Tool', 'Available', 5, 5, 0, 0),
('Claw Hammer', '16 oz', 'Hand Tool', 'Available', 8, 7, 0, 0),
('Adjustable Wrench', '8 inch', 'Hand Tool', 'Available', 10, 9, 0, 0),

-- Power Tools (Requiring Training)
('Cordless Drill', '18V', 'Power Tool', 'Available', 6, 4, 0, 1),
('Impact Driver', '18V', 'Power Tool', 'In Use', 4, 0, 0, 1),
('Heat Gun', '1500W', 'Power Tool', 'Available', 3, 3, 0, 1),
('Soldering Iron', 'Standard', 'Power Tool', 'Available', 10, 8, 0, 1),

-- Consumables
('Sandpaper 100 Grit', 'Sheet', 'Consumable', 'Available', 100, 85, 15, 0),
('Wood Glue', '8 oz', 'Consumable', 'Available', 20, 18, 2, 0),
('Electrical Tape', 'Roll', 'Consumable', 'Available', 30, 25, 5, 0),
('Solder Wire', 'Spool', 'Consumable', 'Low Stock', 10, 2, 8, 0);
