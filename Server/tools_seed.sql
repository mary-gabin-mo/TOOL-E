-- Schema for Tools Table
CREATE TABLE IF NOT EXISTS tools (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type ENUM('Borrowable', 'Consumable') NOT NULL,
    total_quantity INT NOT NULL DEFAULT 0,
    available_quantity INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Example Data (Seeds) matching Frontend Mock Data
INSERT INTO tools (name, type, total_quantity, available_quantity) VALUES
('Slip Joint Pliers', 'Borrowable', 10, 8),
('Long Nose Pliers Small', 'Borrowable', 10, 8),
('Tape Measure', 'Borrowable', 10, 8),
('Super Glue', 'Consumable', 10, 8),
('Hammer', 'Borrowable', 5, 2),
('Screwdriver Set', 'Borrowable', 15, 15);
