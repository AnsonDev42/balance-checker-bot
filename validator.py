import pydantic
from pydantic import model_validator


class TimeModel(pydantic.BaseModel):
    """
    Check input string is valid 'DDHHMM' using pydantic model
    and output a list of [day, hour, minute]
    """

    time: str
    day: int = None
    hour: int = None
    minute: int = None

    @model_validator(mode="before")
    def check_and_set_time(cls, v):
        time_str = v["time"]

        if not time_str or not time_str.isdigit() or not len(time_str) == 6:
            raise ValueError("Time must be in format DDHHMM.")
        day, hour, minute = (
            int(time_str[:2]),
            int(time_str[2:4]),
            int(time_str[4:6]),
        )

        if not 0 < day <= 28:
            raise ValueError("Day must be between 01 and 28.")
        if not 0 <= hour < 24:
            raise ValueError("Hour must be between 00 and 23.")
        if not 0 <= minute < 60:
            raise ValueError("Minute must be between 00 and 59.")
        v["day"], v["hour"], v["minute"] = day, hour, minute
        return v


if __name__ == "__main__":
    try:
        model = TimeModel(time="250800")
        print("Day:", model.day)  # 25
        print("Hour:", model.hour)  # 8
        print("Minute:", model.minute)  # 0
    except pydantic.ValidationError as e:
        print("Error:", e)
