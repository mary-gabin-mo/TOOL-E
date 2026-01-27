USE `tool_e_db`;

INSERT INTO `transactions`
(`user_id`, `tool_id`, `checkout_timestamp`, `desired_return_date`, `return_timestamp`, `quantity`, `purpose`, `image_path`, `classification_correct`, `weight`)
VALUES
(101, 1, CURRENT_TIMESTAMP, DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 7 DAY), NULL, 1, 'Prototype build', 'uploads/mock_tool_1.jpg', 1, 0),
(102, 2, DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 2 DAY), DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 5 DAY), NULL, 2, 'Lab assignment', 'uploads/mock_tool_2.jpg', 0, 0),
(103, 3, DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 5 DAY), DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 2 DAY), DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 1 DAY), 1, 'Maintenance', 'uploads/mock_tool_3.jpg', 1, 0),
(104, 4, DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 1 DAY), DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 6 DAY), NULL, 1, 'Electronics project', 'uploads/mock_tool_4.jpg', 1, 0),
(105, 5, DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 3 DAY), DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 4 DAY), NULL, 3, 'Workshop demo', 'uploads/mock_tool_5.jpg', 0, 0);
