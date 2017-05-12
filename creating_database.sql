CREATE TABLE users (
	user_id		INTEGER		PRIMARY KEY,
	login		TEXT 		NOT NULL UNIQUE,
);

CREATE TABLE transport (
	transport_id 	SERIAL		PRIMARY KEY,
	departure_point TEXT	NOT NULL,
	destination 	TEXT	NOT NULL,
	departure_time 	TIMESTAMP WITH TIME ZONE	NOT NULL,
	arrival_time	TIMESTAMP WITH TIME ZONE	NOT NULL,
	price		MONEY,
	type		TEXT		NOT NULL,
	is_scheduled	BOOLEAN		NOT NULL
);

CREATE TABLE stops (
	stop_id			SERIAL 	PRIMARY KEY,
	journey_id			INTEGER 	NOT NULL	REFERENCES journey (journey_id) ON DELETE CASCADE,
	transport_id_for_arrival	INTEGER 	REFERENCES transport (transport_id) ON DELETE SET NULL,
	transport_id_for_department 	INTEGER 	REFERENCES transport (transport_id) ON DELETE SET NULL,
);

CREATE TABLE journey (
	journey_id	SERIAL 	PRIMARY KEY,
	departure_point		TEXT 		NOT NULL,
	destination 	TEXT 		NOT NULL,
	departure_date 	TIMESTAMP WITH TIME ZONE 	CHECK (departure_date - CURRENT_TIMESTAMP >= '0'),
	arrival_date 	TIMESTAMP WITH TIME ZONE 	CHECK (arrival_date - CURRENT_TIMESTAMP >= '0'),
	first_stop	INTEGER 	REFERENCES stops (stop_id) ON DELETE RESTRICT,
	is_public	BOOLEAN 	NOT NULL,
	budget		MONEY,
	CHECK (arrival_date - departure_date >= '0')
);

CREATE TABLE travelers (
	journey_id 	INTEGER 	REFERENCES journey (journey_id) ON DELETE CASCADE,
	user_id 	INTEGER 	REFERENCES users (user_id) ON DELETE CASCADE,
	is_host		BOOLEAN		NOT NULL,
	PRIMARY KEY(journey_id, user_id)
);

ALTER TABLE stops ADD FOREIGN KEY (journey_id) REFERENCES journey (journey_id) ON DELETE CASCADE;