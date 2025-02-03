CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO test_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO test_user;
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    uuid UUID DEFAULT uuid_generate_v4(),
    dob DATE NOT NULL
);
CREATE TABLE IF NOT EXISTS test_data (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    dob DATE,
    uuid UUID
);

WITH RECURSIVE seq AS (
    SELECT 1 AS id
    UNION ALL
    SELECT id + 1 FROM seq WHERE id < 100
)
INSERT INTO users (name, dob)
SELECT CONCAT('User ', LPAD(seq.id::TEXT, 3, '0')),
       (CURRENT_DATE - (random() * 365 * 30)::INT * INTERVAL '1 day')::DATE
FROM seq
WHERE NOT EXISTS (SELECT 1 FROM users WHERE id = seq.id);

CREATE OR REPLACE PROCEDURE UpdateUserUUID(user_id INT, new_uuid UUID)
LANGUAGE plpgsql AS $$
BEGIN
    UPDATE test_data SET uuid = new_uuid WHERE id = user_id;
END;
$$;


COPY test_data(id, name, dob, uuid)
FROM '/docker-entrypoint-initdb.d/test_data.csv'
DELIMITER ','
CSV;
