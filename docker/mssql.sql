CREATE DATABASE elixirdb;
GO
CREATE LOGIN test_user WITH PASSWORD = 'StrongPassword!123';
GO
EXEC sp_addsrvrolemember 'test_user', 'sysadmin';
GO
USE elixirdb;
GO
CREATE USER test_user FOR LOGIN test_user;
GO


CREATE TABLE test_data (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(255),
    dob DATE NOT NULL DEFAULT FORMAT(GETDATE() - ABS(CHECKSUM(NEWID()) % 20000), 'yyyy-MM-dd'),
    uuid CHAR(36)
);

GO
BULK INSERT test_data
FROM '/docker-entrypoint-initdb.d/test_data.csv'
WITH (
    FORMAT = 'CSV',
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',
    FIRSTROW = 1,
    FORMATFILE = '/docker-entrypoint-initdb.d/mssql.fmt'
);
GO


IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'users')
BEGIN
    CREATE TABLE users (
        id INT IDENTITY(1,1) PRIMARY KEY,
        name NVARCHAR(255) NOT NULL,
        dob DATE NOT NULL DEFAULT FORMAT(GETDATE() - ABS(CHECKSUM(NEWID()) % 20000), 'yyyy-MM-dd')
    );
END;
GO

DECLARE @max_id INT = ISNULL((SELECT MAX(id) FROM users), 0);
DECLARE @target_rows INT = 100

DECLARE @counter INT = 1;
WHILE @counter <= @target_rows
BEGIN
    INSERT INTO users (name, dob) VALUES (CONCAT('User ', FORMAT(@max_id + @counter, '000')), FORMAT(GETDATE() - ABS(CHECKSUM(NEWID()) % 20000), 'yyyy-MM-dd'));
    SET @counter = @counter + 1;
END;
GO

IF OBJECT_ID('GetUserName', 'P') IS NOT NULL
BEGIN
    DROP PROCEDURE GetUserName;
END;
GO

CREATE PROCEDURE GetUserName @id INT
AS
BEGIN
    SELECT name FROM test_data WHERE id = @id;
END;
GO
