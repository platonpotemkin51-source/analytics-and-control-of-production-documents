from enum import Enum


class RoleEnum(str, Enum):
    global_admin = "global_admin"
    company_admin = "company_admin"
    manager = "manager"
    warehouse = "warehouse"


class BatchStatus(str, Enum):
    warehouse = "warehouse"
    formed = "formed"
    shipped = "shipped"
