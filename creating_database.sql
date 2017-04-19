CREATE TABLE users (
	user_id 		INTEGER 	PRIMARY KEY,
	first_name 		TEXT,
	last_name 		TEXT,
	city 			TEXT,
	age 			INTEGER 	CHECK (age > 0 AND age < 200),
	login 			TEXT 		NOT NULL UNIQUE,
	password_hash 	TEXT 		NOT NULL UNIQUE,
	phone_number 	VARCHAR(15),
	email 			TEXT,
	social_network 	TEXT
);

CREATE TABLE transport (
	transport_id 	INTEGER 	PRIMARY KEY,
	departure_point TEXT,
	destination 	TEXT,
	departure_time 	TIMESTAMP WITH TIME ZONE,
	arrival_time 	TIMESTAMP WITH TIME ZONE,
	price 			MONEY,
	type 			TEXT 		NOT NULL,
	is_scheduled 	BOOLEAN 	NOT NULL
);

CREATE TABLE hotels (
	hotel_id 	INTEGER 	PRIMARY KEY,
	name 		TEXT 		NOT NULL,
	location 	TEXT 		NOT NULL,
	raiting 	VARCHAR(1)
);

CREATE TABLE rooms (
	room_id 		INTEGER 	PRIMARY KEY,
	hotel_id 		INTEGER 	NOT NULL REFERENCES hotels (hotel_id) ON DELETE CASCADE,
	comforts 		VARCHAR(50),
	people_amount 	INTEGER,
	price 			MONEY 		NOT NULL
);

CREATE TABLE activities (
	activity_id 	INTEGER 	PRIMARY KEY,
	name 			TEXT 		NOT NULL,
	location 		TEXT,
	price 			MONEY,
	description 	TEXT,
	people_amount 	INTEGER 	CHECK (people_amount > 0)
);

CREATE TABLE stops (
	stop_id 					INTEGER 	PRIMARY KEY,
	journey_id 					INTEGER 	NOT NULL,
	transport_id_for_arrival 	INTEGER 	REFERENCES transport (transport_id) ON DELETE SET NULL,
	transport_id_for_department INTEGER 	REFERENCES transport (transport_id) ON DELETE SET NULL,
	hotel_id 					INTEGER 	REFERENCES hotels (hotel_id) ON DELETE SET NULL,
	room_id 					INTEGER 	REFERENCES rooms (room_id) ON DELETE SET NULL,
	list_of_activities_id 		INTEGER		UNIQUE,
	next_stop_id 				INTEGER
);

CREATE TABLE journey (
	journey_id 		INTEGER 	PRIMARY KEY,
	start 			TEXT 		NOT NULL,
	destination 	TEXT 		NOT NULL,
	departure_date 	TIMESTAMP WITH TIME ZONE 	CHECK (departure_date - CURRENT_TIMESTAMP >= '0'),
	arrival_date 	TIMESTAMP WITH TIME ZONE 	CHECK (arrival_date - CURRENT_TIMESTAMP >= '0'),
	first_stop 		INTEGER 	REFERENCES stops (stop_id) ON DELETE RESTRICT,
	last_stop 		INTEGER 	REFERENCES stops (stop_id) ON DELETE RESTRICT,
	is_public 		BOOLEAN 	NOT NULL,
	budget 			MONEY,
	CHECK (arrival_date - departure_date >= '0')
);

CREATE TABLE travelers (
	journey_id 	INTEGER 	REFERENCES journey (journey_id) ON DELETE CASCADE,
	user_id 	INTEGER 	REFERENCES users (user_id) ON DELETE CASCADE,
	PRIMARY KEY(journey_id, user_id)
);

CREATE TABLE lists_of_activities (
	list_of_activities_id 	INTEGER 	REFERENCES stops (list_of_activities_id) ON DELETE CASCADE,
	activity_id				INTEGER		REFERENCES activities (activity_id) ON DELETE CASCADE,
	PRIMARY KEY(list_of_activities_id, activity_id)
);

ALTER TABLE stops ADD FOREIGN KEY (journey_id) REFERENCES journey (journey_id) ON DELETE CASCADE;