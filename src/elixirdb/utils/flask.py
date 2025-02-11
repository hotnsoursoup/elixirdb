from elixirdb.exc import FlaskNotInstalledError


def flask_ctx(self) -> int:
    """
    Return the flask app context.

    Many thanks to flask_sqlalchemy for providing this. Credit goes to them.
    """
    try:
        from flask.gloabls import (  # noqa: PLC0415 # pyright: ignore[reportMissingImports]
            app_ctx,
        )
    except:  # noqa: E722
        raise FlaskNotInstalledError(  # noqa: B904
            "Flask is not installed. Please install Flask to use the "
            "enable_flask configuration. "
        )

    return id(app_ctx._get_current_object())
