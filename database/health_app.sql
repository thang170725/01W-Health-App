use health_app;

create table user(
	id int auto_increment primary key,
	email varchar(50) not null,
	password varchar(500) not null
) engine=InnoDB;
select * from user;