from __future__ import annotations

from pytvpaint.george.base import GrgErrorValue, undo
from pytvpaint.george.client import send_cmd, try_cmd


@try_cmd(exception_msg="No scene at provided position")
def tv_scene_enum_id(position: int) -> int:
    """Get the id of the scene at the given position in the current project"""
    return int(send_cmd("tv_SceneEnumId", position, error_values=[GrgErrorValue.NONE]))


def tv_scene_current_id() -> int:
    """Get the id of the current scene"""
    return int(send_cmd("tv_SceneCurrentId"))


@undo
def tv_scene_move(scene_id: int, position: int) -> None:
    """Move a scene to a another position"""
    send_cmd("tv_SceneMove", scene_id, position)


@undo
def tv_scene_new() -> None:
    """Create a new scene (with a new clip) after the scene of the current clip"""
    send_cmd("tv_SceneNew")


@undo
def tv_scene_duplicate(scene_id: int) -> None:
    """Duplicate the given scene"""
    send_cmd("tv_SceneDuplicate", scene_id)


@undo
def tv_scene_close(scene_id: int) -> None:
    """Remove the given scene"""
    send_cmd("tv_SceneClose", scene_id)
