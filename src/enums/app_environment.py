from enum import Enum

class AppEnvironment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"