import os

env = os.environ.get("DJANGO_ENV", "dev").lower()

if env == "prod":
    from .prod import *  # noqa: F403
elif env == "dev":
    from .dev import *  # noqa: F403
else:
    raise RuntimeError("DJANGO_ENV must be either 'dev' or 'prod'.")
