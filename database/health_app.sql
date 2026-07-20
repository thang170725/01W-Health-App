create database if not exists health_app
	character set utf8mb4
	collate utf8mb4_unicode_ci;

use health_app;

show tables;
select * from health_logs hl ;

-- Tables are normally created by SQLAlchemy (initialize_database).
-- Reference schema for documentation / manual setup:

/*
CREATE TABLE users (
  id INT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(50) NOT NULL UNIQUE,
  password VARCHAR(100) NOT NULL,
  age INT NULL,
  gender VARCHAR(10) NULL
);

CREATE TABLE health_logs (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  log_date DATE NOT NULL,
  weight FLOAT NOT NULL,
  height FLOAT NOT NULL,
  bmi FLOAT NOT NULL,
  activity_minutes INT NOT NULL DEFAULT 0,
  steps INT NOT NULL DEFAULT 0,
  heart_rate INT NULL,
  sleep_hours FLOAT NULL,
  water_ml INT NOT NULL DEFAULT 0,
  source VARCHAR(20) NOT NULL DEFAULT 'manual',
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE user_goals (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL UNIQUE,
  target_weight FLOAT NULL,
  target_activity INT NOT NULL DEFAULT 30,
  target_water INT NOT NULL DEFAULT 2000,
  max_bmi FLOAT NOT NULL DEFAULT 25.0,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
*/
