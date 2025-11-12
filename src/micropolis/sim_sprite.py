# ============================================================================
# Data Structure Classes
# ============================================================================


from pydantic import BaseModel


class SimSprite(BaseModel):
    """Moving sprite object (cars, disasters, etc.)"""

    name: str = ""
    type: int = 0
    frame: int = 0
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    x_offset: int = 0
    y_offset: int = 0
    x_hot: int = 0
    y_hot: int = 0
    orig_x: int = 0
    orig_y: int = 0
    dest_x: int = 0
    dest_y: int = 0
    count: int = 0
    sound_count: int = 0
    dir: int = 0
    new_dir: int = 0
    step: int = 0
    flag: int = 0
    control: int = 0
    turn: int = 0
    accel: int = 0
    speed: int = 0
    next: "SimSprite | None" = None
