create database if not exists health_app
	character set utf8mb4
	collate utf8mb4_unicode_ci;

use health_app;

create table if not exists user(
	id int auto_increment primary key,
	email varchar(50) not null,
	password varchar(500) not null
) engine=InnoDB;
