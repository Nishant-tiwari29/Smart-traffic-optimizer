CREATE DATABASE IF NOT EXISTS smart_traffic;
USE smart_traffic;

CREATE TABLE users (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(120) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE locations (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  code VARCHAR(32) NOT NULL UNIQUE,
  name VARCHAR(160) NOT NULL,
  latitude DECIMAL(10,7) NOT NULL,
  longitude DECIMAL(10,7) NOT NULL
);

CREATE TABLE intersections (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  location_id BIGINT NOT NULL UNIQUE,
  FOREIGN KEY (location_id) REFERENCES locations(id)
);

CREATE TABLE roads (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  code VARCHAR(64) NOT NULL UNIQUE,
  start_intersection_id BIGINT NOT NULL,
  end_intersection_id BIGINT NOT NULL,
  distance_km DECIMAL(8,3) NOT NULL,
  speed_limit_kph DECIMAL(6,2) NOT NULL,
  road_condition ENUM('good','fair','poor') NOT NULL,
  FOREIGN KEY (start_intersection_id) REFERENCES intersections(id),
  FOREIGN KEY (end_intersection_id) REFERENCES intersections(id)
);

CREATE TABLE traffic_data (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  road_id BIGINT NOT NULL,
  congestion DECIMAL(4,3) NOT NULL,
  observed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (road_id) REFERENCES roads(id),
  INDEX idx_traffic_road_time (road_id, observed_at)
);

CREATE TABLE routes (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NULL,
  source_intersection_id BIGINT NOT NULL,
  destination_intersection_id BIGINT NOT NULL,
  algorithm VARCHAR(32) NOT NULL,
  distance_km DECIMAL(9,3) NOT NULL,
  travel_time_min DECIMAL(9,3) NOT NULL,
  optimization_cost DECIMAL(12,5) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (source_intersection_id) REFERENCES intersections(id),
  FOREIGN KEY (destination_intersection_id) REFERENCES intersections(id)
);

CREATE TABLE route_history (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  route_id BIGINT NOT NULL,
  sequence_number INT NOT NULL,
  road_id BIGINT NOT NULL,
  FOREIGN KEY (route_id) REFERENCES routes(id) ON DELETE CASCADE,
  FOREIGN KEY (road_id) REFERENCES roads(id),
  UNIQUE KEY uq_route_sequence (route_id, sequence_number)
);

INSERT INTO locations (code, name, latitude, longitude) VALUES
('A','Central Station',37.7760000,-122.4170000),('B','Market Street',37.7800000,-122.4130000),
('C','Civic Center',37.7730000,-122.4100000),('D','Union Square',37.7870000,-122.4090000),
('E','Mission District',37.7660000,-122.4140000),('F','Waterfront',37.7930000,-122.4020000),
('G','Embarcadero',37.7800000,-122.3970000),('H','North Point',37.7990000,-122.4050000);

INSERT INTO intersections (id, location_id)
SELECT 1,id FROM locations WHERE code='A' UNION ALL SELECT 2,id FROM locations WHERE code='B'
UNION ALL SELECT 3,id FROM locations WHERE code='C' UNION ALL SELECT 4,id FROM locations WHERE code='D'
UNION ALL SELECT 5,id FROM locations WHERE code='E' UNION ALL SELECT 6,id FROM locations WHERE code='F'
UNION ALL SELECT 7,id FROM locations WHERE code='G' UNION ALL SELECT 8,id FROM locations WHERE code='H';

INSERT INTO roads (id, code, start_intersection_id, end_intersection_id, distance_km, speed_limit_kph, road_condition) VALUES
(1,'AB',1,2,1.8,35,'fair'),(2,'AC',1,3,1.5,30,'good'),
(3,'AE',1,5,1.7,40,'good'),(4,'BC',2,3,1.4,30,'fair'),
(5,'BD',2,4,1.2,25,'poor'),(6,'BF',2,6,2.0,45,'good'),
(7,'CD',3,4,2.2,40,'good'),(8,'CE',3,5,1.1,25,'fair'),
(9,'DE',4,5,2.6,40,'fair'),(10,'DF',4,6,1.3,35,'good'),
(11,'DG',4,7,2.0,45,'good'),(12,'FG',6,7,1.5,30,'poor'),
(13,'FH',6,8,1.4,40,'good'),(14,'GH',7,8,2.1,45,'good'),
(15,'EH',5,8,4.8,50,'good'),(16,'CH',3,8,5.1,50,'fair');

INSERT INTO traffic_data (road_id, congestion) VALUES
(1,.78),(2,.18),(3,.25),(4,.30),(5,.86),(6,.16),(7,.20),(8,.35),
(9,.72),(10,.12),(11,.22),(12,.90),(13,.15),(14,.24),(15,.10),(16,.48);
