from enum import Enum


class MemberRole(str, Enum):
    OWNER = "owner"
    MANAGER = "manager"
    MEMBER = "member"
    VIEWER = "viewer"
