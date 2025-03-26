# ElixirDB - Simplified SQLAlchemy Interaction

[![PyPI - Version](https://img.shields.io/pypi/v/elixirdb.svg)](https://pypi.org/project/elixirdb)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/elixirdb.svg)](https://pypi.org/project/elixirdb)

<!--start-->

ElixirDB simplifies interaction with SQLAlchemy, providing streamlined database operations, enhanced configuration management, and improved developer experience.

## Key Features

- **Automatic loading:** Define an \*\*elixir\*\*.yaml file in your project, and it will be automatically loaded into the ElixirDB instance.
- **Pydantic Integration:** Define and validate database configurations (including engine_options, session_options, and execution_options) using Pydantic models, ensuring type safety and robust settings management.
- **Multi-Engine Support:**  Seamlessly manage multiple database engines through a central class object.
- **Multi-dialect Support:**  Support for MySQL/MariaDB, postgresql, Oracle, and MSSQL.
- **Engine Types:** Allows for simple creation of `direct`, `session` and `scoped_session` engines with a single parameter.
- **Handler Framework:**  A flexible handler framework empowers customized processing of parameters, result_objects, and central error control - mirroring middleware functionality.
- **Stored Procedure Support:**  Execute stored procedures with ease, with automatically generated statements based on dialect.
- **Testing Suite:** A testing suite with a Docker Compose setup that provisions five testing databases, preloaded with the necessary tables and data for testing.

## Table of Contents

- [ElixirDB - Simplified SQLAlchemy Interaction](#elixirdb---simplified-sqlalchemy-interaction)
  - [Key Features](#key-features)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
  - [Using ElixirDB](#using-elixirdb)
    - [Loading configuration and basic usage](#loading-configuration-and-basic-usage)
      - [Manual Loading](#manual-loading)
      - [Load file with different partial](#load-file-with-different-partial)
  - [Pydantic Models for Configuration](#pydantic-models-for-configuration)
    - [Multi-Engine Configuration](#multi-engine-configuration)
    - [Loading with Models](#loading-with-models)
    - [Loading an Invalid Configuration](#loading-an-invalid-configuration)
  - [Engine Types](#engine-types)
  - [Handler Framework](#handler-framework)
    - [Parameter Handlers](#parameter-handlers)
    - [Result Handlers](#result-handlers)
    - [Error Handlers](#error-handlers)
    - [Putting it all together](#putting-it-all-together)
  - [Extras](#extras)
    - [Attribute calls, Attribute Wrap, and Result Types](#attribute-calls-attribute-wrap-and-result-types)
    - [Stored Procedures Mixin](#stored-procedures-mixin)
  - [License](#license)

## Installation

ElixirDB is available on PyPI and can be installed using pip:

```bash
pip install elixirdb
```

Install with your dialect and default drivers.

```bash
pip install elixirdb[mysql]
```

You can also install the testing suite, which includes a complete pytest suite with html reports and  coverage reports by cloning
the repo and installing the testing suite. The project was built using `uv` as the package manager.

```bash
# Clone repo
git clone https://github.com/hotnsoursoup/elixirdb.git
```

```bash
# Install uv
pip install uv
```

Change your directory to the cloned repo (and create a virtual environment if you wish)

```bash
# Run uv and create a virtual environment
uv venv

# Pick your extras/groups
uv sync --group dev --group test --extra mysql

# or
uv sync --all-extras --all-groups
```

If you have issues, try running --no-cache.

```bash
uv sync --extra mysql --no-cache
```

## Using ElixirDB

### Loading configuration and basic usage

You have various options in how you can load your configuration.
By default, ElixirDB will automatically load a yaml file with `elixir` in the name. (e.g. `myelixirdb.yaml`) by searching within your project structure, using pyrootutils.find_root(), and identifying a yaml or json file with the name `elixir` in the name.

```python
from elixirdb import ElixirDB

try:
    connection = ElixirDB()
except FileNotFoundError:
    print("No elixir.yaml file found.")

# Note - TextClause is automatically applied to the statement.
result = connection.execute("SELECT * FROM mytable")


for record in result:
    print(record)
```

#### Manual Loading

Though the library does support automatic loading, you have the option to do it manually. One way is to pass in as a dictionary. The dictionary below uses the default drivername for the given dialect.

```python
myconfig = {
    "dialect": "postgres",
    "url_params": {
        "host": "localhost",
        "port": 5432,
        "database": "mydatabase",
        "username": "user",
    },
    "engine_options": {
        "pool_size": 10,
        "pool_recycle": 3600,
        "pool_pre_ping": True,
        }
    }

connection = ElixirDB(myconfig)
```

#### Load file with different partial

load_config can also be used to find a different file name, wherever it may be, using a `partial` string and a `file_type` (yaml/json).

```python
""" Will find any wildcard matching **dbfile**.json in the project structure."""

from elixirdb import load_config, ElixirDB

myconfig = load_config(partial="dbfile", file_type="json")
connection = ElixirDB(myconfig)

connection.execute("SELECT * FROM mytable")
results = connection.fetchall()
```

## Pydantic Models for Configuration

ElixirDB leverages Pydantic models for database configuration, providing type safety, validation, and a structured approach to managing connection parameters.  This eliminates common configuration errors and improves code maintainability. The class definitions will have descriptions for each field. This is just an example.

```python
class EngineModel(BaseModel):
    """
    Single sqlalchemy database engine configuration model.
    """
    engine_key: str
    dialect: Dialect
    url: str | None = None
    url_params: UrlParams | None = None
    default: bool = False # Defines the default engine to use in a multi-enginee configuration
    engine_options: EngineOptions | None = None
    session_options: SessionOptions | None = None
    execution_options: ExecutionOptions | None = None
    # ... other fields
```

### Multi-Engine Configuration

Manage connections to multiple databases effortlessly with ElixirDB's multi-engine support. Define separate configurations for each database and switch between them seamlessly.

```python
class EngineManager(StrictModel):
    """
    Configuration for the application and databases.
    """
    default_engine_key: ClassVar[DatabaseKey | None] = None

    defaults: Mapping[str, Any] | None = Field(
        None,
        description=(
            "A mapping of EngineModel values. All fields become optional "
            "and these values are inherited by all engines. Values within "
            "each engine will take precedence over the defaults."
        ),
    )
    engines: Mapping[EngineKey, EngineModel]
    # ... other fields

    @model_validator(mode="after")
    def get_and_set_default_engine_key(self) -> Self:
        """ Get the and set default engine key if not provided. """
    #... other validators
```

Sample yaml configuration for EngineManager

```yaml
app:
    defaults: # All engines adopt these as a base.
        engine_options:
            echo: False
            pool_size: 20
            max_overflow: 10
            pool_recycle: 3600
engines:
    dbkey1:
        dialect: mysql
        url: mysql+pymysql://myuser:password@localhost:3306/db1
        default: true # This engine will be used by default if an engine_key is not provided.
        execution_options:
            autocommit: True
            isolation_level: READ_COMMITTED
            preserve_rowcount: True
    loggingdb:
        dialect: postgres
        url_params:
            drivername: psycopg2
            host: localhost
            port: 5432
            username: postgres
            password: password
            query:
                schema: public
        engine_options:
            echo: True
            pool_timeout: 30
            hide_parameters: True
    customerdb:
        dialect: oracle
        url: oracle+cx_oracle://user:password@localhost:1521/orcl
```

Loading `db1`.

**Note** - The instance will start in a disconnected state unless `auto_connect` is set to `True` in the config.

```python
from elixirdb import ElixirDB

# The configuration is automatically loaded from the elixir.yaml file
connection = ElixirDB(engine_key="db1")

with connection.connect() as conn:
    # ... perform operations on db1

# Print the valdated pydantic model with only the values set by the user.
print(connection.db.model_dump(unset=True))

# Switch engines
connection.set_engine("customerdb")

```

### Loading with Models

The models provide a structured way to define and manage database configurations. The recommended approach is to view the model class, but if you want to dump it to a json file, you always have that option as well using `.model_json_schema()` on the class, but is much easier to read the pydantic model definition.

In this example, we load each model separately and reconstruct it to the EngineModel.

**Note** - Not all models are shown.

```python
from elixirdb import ElixirDB
from elixirdb import EngineModel
from elixirdb import EngineOptions
from elixirdb import ExecutionOptions


execution_options = ExecutionOptions(
    preserve_rowcount=True,
    isolation_level="READ_COMMITTED",
    insertmanyvalues_page_size=1000,
    no_parameters=True,
)

# Execution options are assigned to engine options
engine_options = EngineOptions(
    echo=True,
    pool_size=20,
    nax_overflow=10,
    execution_options=execution_options,
)

config = EngineModel(
    dialect="mysql",
    url="mysql+pymysql://user:password@localhost:3306/db1",
    engine_options=engine_options,
)

connection = ElixirDB(config)

```

### Loading an Invalid Configuration

If your configuration is missing a required field or an invalid input is provided, you may see an error like this. In some cases, after resolving them, you may find more errors arise due to the way pydantic validates before and after validators.

```python
from pydantic import ValidationError
from elixirdb import EngineManager
from elixirdb import print_and_raise_validation_errors


invalid_config = {
    "something": "something",
    "engines": {
        "engine1": {
            "url": "postgresql+psycopg2://test_user:StrongPassword!123@localhost:5432/elixirdb",
            "default": True,
        },
        "engine2": {
            "name": "DB2",
            "default": True,
            "dialect": "mysql0",
            "url": "wrong_url",
            "engine_options": {"pool_size": 10},
        },
    },
}

try:
    EngineManager(**invalid_config)
except ValidationError as e:
    print_and_raise_validation_errors(e, raise_error=False)
```

Console Output:

```console
Configuration Errors:
   - Type: extra_forbidden
     Location: something
     Message: Extra inputs are not permitted
     Input: something
Engine Errors: engine1
   - Type: missing
     Location: dialect
     Message: Field required
Engine Errors: engine2
   - Type: literal_error
     Location: dialect
     Message: Input should be 'mysql', 'postgres', 'mariadb', 'sqlite', 'mssql' or 'oracle'
     Input: mysql0
     Expected: 'mysql', 'postgres', 'mariadb', 'sqlite', 'mssql' or 'oracle'
   - Type: value_error
     Location: url
     Message: Invalid url format. Value provided: wrong_url
     Input: wrong_url
     Url: https://docs.sqlalchemy.org/en/20/core/engines.html#sqlalchemy.engine.make_url
```

## Engine Types

| Engine Type | Description                                                                                         | Documentation Link                                                                                                                                           |
|-------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `direct`    | Utilizes the `create_engine` function to establish a direct connection to the database.             | [SQLAlchemy Engine Configuration](https://docs.sqlalchemy.org/en/latest/core/engines.html)                                                                   |
| `session`   | Employs the `sessionmaker` function to create sessions for managing transactions and ORM operations.| [SQLAlchemy Session API](https://docs.sqlalchemy.org/en/latest/orm/session_api.html)                                                                         |
| `scoped`    | Uses `scoped_session` in conjunction with `sessionmaker` to provide thread-local sessions, ensuring each thread has its own session instance. | [SQLAlchemy Contextual/Thread-local Sessions](https://docs.sqlalchemy.org/en/latest/orm/contextual.html) |

Engine type is set during instantiation as a keyword argument. The default engine_type is `direct`. The `session` engine_type comes with a method to create a new session from the session_factory. This allows it to transfer the ElixirDB configuration to a new instance, including the session_factory.

```python
connection = ElixirDB(engine_type="session")

with connection.new_session() as session:
    print(type(session))

<class 'elixirdb.db.ElixirDB'>
```

When the instance is created and a connection is made, ElixirDB will automatically assign
the `connection` for `direct` engines to the `connection` attribute. For sessions, it will assign it to the `session` attribute.

When executing any statements or queries, you can access the attribute to connection or attributes for session directly on the ElixirDB class itself. The `__getaattr__` definition will pass the command to the appropriate attribute. (e.g. connection.execute(), instead of connection.connection.execute() or connection.session.execute())

## Handler Framework

Implement custom logic for handling parameters before execution and processing results after fetching data.

### Parameter Handlers

```python
""" Parameter handlers """

from elixirdb import ElixirDB

# Create various parameter handlers.
def my_param_cleanser(params):
    # ... modify params

def my_param_logger(params):
    if self.engine_key == "loggingdb":
        # ... log params
    return params

param_handlers = [my_param_cleanser, my_param_logger]

```

### Result Handlers

**NOTE** - Result handlers may require more advanced configurations, see **configuring result_types**.

```python

""" Result handlers """

def convert_cursor_to_list(result):
    if isinstance(result, CursorResult):
        # Convert CursorResult to a list
    else:
        return result

def serialize_results(result):
    # ... serialize result

def redact_results(result, **kwargs):
    for row in result:
        # ... redact results

result_handlers = [convert_cursor_to_list, serialize_results, redact_results]
```

### Error Handlers

```python
""" Error handlers """

def handle_operational_errors(error):
    if isinstance(error, OperationalError):
        # ... handle error
        # raise error
    return error

def log_specific_errors(error):
    # ... do something else.
    return error # so the error is  passed to a different handler

error_handlers = [log_specific_errors, handle_operational_errors]
```

### Putting it all together

```python
handlers = {
    "param_handlers": param_handlers,
    "result_handlers": result_handlers,
    "error_handlers": error_handlers,
}

connection = ElixirDB(handlers=handlers)
```

You can also append to existing handlers.

```python:
connection.result_handlers.append(serialize_results)
```

## Extras

### Attribute calls, Attribute Wrap, and Result Types

ElixirDB natively intercepts attribute and method lookups (by defining a `__getattr__`). Currently, this is still a work in progress, but the current implementation logic works as follows in cascading order:

1. **Checks Built-ins or Class Attributes**
   - If the attribute is in the instance’s own `__slots__` or class-level attributes, as `falsy`  attributes trigger **getattr** to recursively loop, so it must look at dict and class attributes first then return the falsy value.

2. **Handles Result 'type' Attributes**
   - Checks to see if there is a result (self.result) and hasattr (e.g., `fetchone`, `fetchall`) and returns the corresponding method from the internal result object.

3. **Check connection/session attributes**
    - Will check 'connection' for 'direct' engine_type and 'session' for 'session' and 'scopped' engine_type for the attributes.
4. **Checks attribute and wrap it**
   - Ensures attribute is not None and callable(attribute). If it is, wrap it to process any args/kwargs (such as for param processing). I may separate the execute logic completely from this and assign a value to a lookup table to check states and trigger another getattr lookup with the lookup to determine the next action.
5. **Process attribute and return result**
   - The `attribute(*args, **kwargs)` is called and is assigned to the result. If it is a result object in `self.result_types` - which is assigned by the user, then the result is processed with `self.result_handlers`. If it is a result type, it also assigned to `self.result`.

### Stored Procedures Mixin

The stored procedure mixin providess a convenient way to execute stored procedures in your database. It comes as a Mixin class, but also available through ElixirDBStatements.

```python
class ElixirDBStatements(StatementsMixin, ElixirDB):
    """Statement enabled connection class."""
```

Since it is a mixin class, you can use it the same as you would with ElixirDB. The mixin class automatically generates the stored procedure for the supported dialects (mysql, mariadb, postgres, oracle, mssql).

```python
from elixirdb import ElixirDBStatements

connection = ElixirDBStatements(engine_type="session", engine_key="my_db")

# Define the parameters

params = {
    "param1": 123,
    "param2": "example",
}

# Execute a stored procedure. The default behavior is for the class to create a connection.
result = connection.procedure("my_procedure", params)

print(connection.rowcount)
```


## License

ElixirDB is licensed under the MIT License - see the [LICENSE](https://github.com/hotnsoursoup/quik-db/blob/master/LICENSE) file for details

<!--end-->
