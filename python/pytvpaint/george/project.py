from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from pytvpaint.george.base import (
    FieldOrder,
    GrgErrorValue,
    ResizeOption,
    RGBColor,
    TVPSound,
    undo,
)
from pytvpaint.george.client import send_cmd, try_cmd
from pytvpaint.george.client.parse import (
    consecutive_optional_args_to_list,
    tv_cast_to_type,
    tv_parse_list,
)
from pytvpaint.george.exceptions import NoObjectWithIdError


@dataclass(frozen=True)
class TVPProject:
    id: str = field(metadata={"parsed": False})

    path: Path
    width: int
    height: int
    pixel_aspect_ratio: float
    frame_rate: float
    field_order: FieldOrder
    start_frame: int


class BackgroundMode(Enum):
    CHECK = "check"
    COLOR = "color"
    NONE = "none"


def tv_background_get() -> tuple[RGBColor, RGBColor] | RGBColor | None:
    """Get the background mode of the project"""
    res = send_cmd("tv_Background")

    mode, *values = res.split(" ")

    if mode == BackgroundMode.NONE.value:
        return None

    if mode == BackgroundMode.CHECK.value:
        c1 = map(int, values[:3])
        c2 = map(int, values[3:])
        return (RGBColor(*c1), RGBColor(*c2))

    return RGBColor(*map(int, values))


@undo
def tv_background_set(
    mode: BackgroundMode, c1: RGBColor | None = None, c2: RGBColor | None = None
) -> None:
    """Set the background mode of the project"""
    if mode == BackgroundMode.NONE:
        args = []
    elif mode == BackgroundMode.CHECK:
        assert c1 and c2
        args = [c1.r, c1.g, c1.b, c2.r, c2.g, c2.b]
    else:
        assert c1
        args = [c1.r, c1.g, c1.b]
    send_cmd("tv_Background", mode.value, *args)


@try_cmd(exception_msg="Project created but may be corrupted")
def tv_project_new(
    project_path: Path | str,
    width: int = 1920,
    height: int = 1080,
    pixel_aspect_ratio: float = 1.0,
    frame_rate: float = 24.0,
    field_order: FieldOrder = FieldOrder.NONE,
    start_frame: int = 1,
) -> str:
    """Create a new project"""
    return send_cmd(
        "tv_ProjectNew",
        Path(project_path).as_posix(),
        width,
        height,
        pixel_aspect_ratio,
        frame_rate,
        field_order.value,
        start_frame,
        error_values=[GrgErrorValue.EMPTY],
    )


@try_cmd(exception_msg="Invalid format")
def tv_load_project(project_path: Path | str, silent: bool | None = None) -> str:
    """Load a file as a project if possible or open Import panel"""
    project_path = Path(project_path)

    if not project_path.exists():
        raise ValueError(f"Project not found at: {project_path.as_posix()}")

    args: list[Any] = [project_path.as_posix()]

    if silent is not None:
        args.extend(["silent", int(silent)])

    return send_cmd("tv_LoadProject", *args, error_values=[-1])


def tv_save_project(project_path: Path | str) -> None:
    """Save the current project as tvpp"""
    project_path = Path(project_path)
    parent = project_path.parent

    if not parent.exists():
        msg = f"Can't save because parent folder does not exist: {parent.as_posix()}"
        raise ValueError(msg)

    send_cmd("tv_SaveProject", project_path.as_posix())


@try_cmd(exception_msg="Can't duplicate the current project")
def tv_project_duplicate() -> None:
    """Duplicate the current project"""
    send_cmd("tv_ProjectDuplicate", error_values=[0])


@try_cmd(exception_msg="No project at provided position")
def tv_project_enum_id(position: int) -> str:
    """Get the id of the project at the given position"""
    return send_cmd("tv_ProjectEnumId", position, error_values=[GrgErrorValue.NONE])


def tv_project_current_id() -> str:
    """Get the id of the current project"""
    return send_cmd("tv_ProjectCurrentId")


@try_cmd(raise_exc=NoObjectWithIdError)
def tv_project_info(project_id: str) -> TVPProject:
    """Get info of the given project"""
    result = send_cmd("tv_ProjectInfo", project_id, error_values=[GrgErrorValue.EMPTY])
    project = tv_parse_list(result, with_fields=TVPProject)
    project["id"] = project_id
    return TVPProject(**project)


def tv_get_project_name() -> str:
    """Returns the save path of the current project"""
    return send_cmd("tv_GetProjectName")


def tv_project_select(project_id: str) -> str:
    """Make the given project current"""
    return send_cmd("tv_ProjectSelect", project_id)


def tv_project_close(project_id: str) -> None:
    """Close the given project"""
    send_cmd("tv_ProjectClose", project_id)


def tv_resize_project(width: int, height: int) -> None:
    """
    Resize the current project
    Note: changes the id of the current project
    """
    send_cmd("tv_ResizeProject", width, height)


def tv_resize_page(width: int, height: int, resize_opt: ResizeOption) -> None:
    """Create a new resized project and close the current one"""
    send_cmd("tv_ResizePage", width, height, resize_opt.value)


def tv_get_width() -> int:
    """Get the current project width"""
    return int(send_cmd("tv_GetWidth"))


def tv_get_height() -> int:
    """Get the current project height"""
    return int(send_cmd("tv_GetHeight"))


def tv_ratio() -> float:
    """
    Get the current project pixel aspect ratio
    TODO: figure out why it doesn't work and returns an empty string
    """
    return float(send_cmd("tv_GetRatio", error_values=[GrgErrorValue.EMPTY]))


def tv_get_field() -> FieldOrder:
    """Get the current project field mode"""
    return tv_cast_to_type(send_cmd("tv_GetField"), cast_type=FieldOrder)


def tv_save_sequence(
    export_path: Path | str,
    mark_in_out: tuple[int, int] | None = None,
) -> None:
    """Save the current project"""
    export_path = Path(export_path)

    if not export_path.parent.exists():
        raise ValueError(
            "Can't save the sequence because parent"
            f"folder does not exist: {export_path.parent.as_posix()}"
        )

    args: list[Any] = [export_path.as_posix()]

    if mark_in_out:
        mark_in, mark_out = mark_in_out
        args.extend([mark_in, mark_out])

    send_cmd("tv_SaveSequence", *args)


def tv_project_save_sequence(
    export_path: Path | str,
    use_camera: bool | None = None,
    start_end_frame: tuple[int, int] | None = None,
) -> None:
    """Save the current project"""
    export_path = Path(export_path)
    args: list[Any] = [export_path.as_posix()]

    if use_camera:
        args.append("camera")
    if start_end_frame:
        args.extend(start_end_frame)

    send_cmd(
        "tv_ProjectSaveSequence",
        *args,
        error_values=[-1],
    )


def tv_project_render_camera(project_id: str) -> str:
    """
    Render the given project in camera view to another new project

    Returns the new project id
    """
    return send_cmd(
        "tv_ProjectRenderCamera",
        project_id,
        error_values=[GrgErrorValue.ERROR],
    )


def tv_frame_rate_get() -> tuple[float, float]:
    """
    Get the framerate of the current project
    """
    parse = tv_parse_list(
        send_cmd("tv_FrameRate", 1, "info"),
        with_fields=[
            ("project_fps", float),
            ("playback_fps", float),
        ],
    )
    project_fps, playback_fps = parse.values()
    return project_fps, playback_fps


@undo
def tv_frame_rate_set(
    frame_rate: float, time_stretch: bool = False, preview: bool = False
) -> None:
    """
    Get the framerate of the current project
    """
    args: list[Any] = []
    if time_stretch:
        args = ["timestretch"]
    if preview:
        args = ["preview"]
    args.insert(0, frame_rate)
    send_cmd("tv_FrameRate", *args)


@undo
def tv_frame_rate_project_set(
    frame_rate: float, time_stretch: bool | None = None
) -> None:
    """Set the framerate of the current project"""
    args: list[Any] = [frame_rate]
    if time_stretch:
        args.append("timestretch")
    send_cmd("tv_FrameRate", *args)


@undo
def tv_frame_rate_preview_set(frame_rate: float) -> None:
    """Set the framerate of the preview (playback)"""
    send_cmd("tv_FrameRate", frame_rate, "preview")


def tv_project_current_frame_get() -> int:
    """Get the current frame of the current project"""
    return int(send_cmd("tv_ProjectCurrentFrame"))


@undo
def tv_project_current_frame_set(frame: int) -> int:
    """
    Set the current frame of the current project
    Note: this is relative to the current clip markin
    """
    return int(send_cmd("tv_ProjectCurrentFrame", frame))


def tv_load_palette(palette_path: Path | str) -> None:
    """Load a palette(s) from a file/directory"""
    palette_path = Path(palette_path)
    if not palette_path.exists():
        raise ValueError(f"Palette not found at: {palette_path.as_posix()}")
    send_cmd("tv_LoadPalette", palette_path.as_posix())


def tv_save_palette(palette_path: Path | str) -> None:
    """Save the current palette"""
    palette_path = Path(palette_path)

    if not palette_path.parent.exists():
        parent_path = palette_path.parent.as_posix()
        msg = f"Can't save palette because parent folder doesn't exist: {parent_path}"
        raise ValueError(msg)

    send_cmd("tv_SavePalette", palette_path.as_posix())


@undo
def tv_project_save_video_dependencies() -> None:
    """Saves current project video dependencies"""
    send_cmd("tv_ProjectSaveVideoDependencies")


@undo
def tv_project_save_audio_dependencies() -> None:
    """Saves current project audio dependencies"""
    send_cmd("tv_ProjectSaveAudioDependencies")


def tv_sound_project_info(project_id: str, track_index: int) -> TVPSound:
    """Get information about a project sound track"""
    res = send_cmd(
        "tv_SoundProjectInfo", project_id, track_index, error_values=[-1, -2, -3]
    )
    res_parse = tv_parse_list(res, with_fields=TVPSound)
    return TVPSound(**res_parse)


@undo
def tv_sound_project_new(sound_path: Path | str) -> None:
    """Add a new project sound track"""
    path = Path(sound_path)
    if not path.exists():
        raise ValueError(f"Sound file not found at : {path.as_posix()}")

    send_cmd("tv_SoundProjectNew", path.as_posix(), error_values=[-1, -3, -4])


@undo
def tv_sound_project_remove(track_index: int) -> None:
    """Remove a project sound track"""
    send_cmd("tv_SoundProjectRemove", track_index, error_values=[-2])


@undo
def tv_sound_project_reload(project_id: str, track_index: int) -> None:
    """Reload a project sound track from its file"""
    send_cmd(
        "tv_SoundProjectReload",
        project_id,
        track_index,
        error_values=[-1, -2, -3],
    )


@undo
def tv_sound_project_adjust(
    track_index: int,
    mute: bool | None = None,
    volume: float | None = None,
    offset: float | None = None,
    fade_in_start: float | None = None,
    fade_in_stop: float | None = None,
    fade_out_start: float | None = None,
    fade_out_stop: float | None = None,
    color_index: int | None = None,
) -> None:
    """Modify a project sound track"""
    optional_args = [
        int(mute) if mute is not None else None,
        volume,
        offset,
        (fade_in_start, fade_in_stop, fade_out_start, fade_out_stop),
        color_index,
    ]

    args = consecutive_optional_args_to_list(optional_args)

    send_cmd(
        "tv_SoundProjectAdjust",
        track_index,
        *args,
        error_values=[-2, -3],
    )


@try_cmd(raise_exc=NoObjectWithIdError, exception_msg="Invalid project id")
def tv_project_header_info_get(project_id: str) -> str:
    """Get the project header info"""
    return send_cmd(
        "tv_ProjectHeaderInfo",
        project_id,
        error_values=[GrgErrorValue.ERROR],
    ).strip('"')


@undo
@try_cmd(raise_exc=NoObjectWithIdError, exception_msg="Invalid project id")
def tv_project_header_info_set(project_id: str, text: str) -> None:
    send_cmd(
        "tv_ProjectHeaderInfo",
        project_id,
        text,
        error_values=[GrgErrorValue.ERROR],
    )


@try_cmd(raise_exc=NoObjectWithIdError, exception_msg="Invalid project id")
def tv_project_header_author_get(project_id: str) -> str:
    return send_cmd(
        "tv_ProjectHeaderAuthor",
        project_id,
        error_values=[GrgErrorValue.ERROR],
    ).strip('"')


@undo
@try_cmd(raise_exc=NoObjectWithIdError, exception_msg="Invalid project id")
def tv_project_header_author_set(project_id: str, text: str) -> None:
    send_cmd(
        "tv_ProjectHeaderAuthor",
        project_id,
        text,
        error_values=[GrgErrorValue.ERROR],
    )


@try_cmd(raise_exc=NoObjectWithIdError, exception_msg="Invalid project id")
def tv_project_header_notes_get(project_id: str) -> str:
    return send_cmd(
        "tv_ProjectHeaderNotes",
        project_id,
        error_values=[GrgErrorValue.ERROR],
    ).strip('"')


@undo
@try_cmd(raise_exc=NoObjectWithIdError, exception_msg="Invalid project id")
def tv_project_header_notes_set(project_id: str, text: str) -> None:
    send_cmd(
        "tv_ProjectHeaderNotes",
        project_id,
        text,
        error_values=[GrgErrorValue.ERROR],
    )


def tv_start_frame_get() -> int:
    """Get the start frame of the current project (starts at 1)"""
    return int(send_cmd("tv_StartFrame"))


@undo
def tv_start_frame_set(start_frame: int) -> int:
    """Set the start frame of the current project (starts at 1)"""
    return int(send_cmd("tv_StartFrame", start_frame))
