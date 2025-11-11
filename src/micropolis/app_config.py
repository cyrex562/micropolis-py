from pathlib import Path
from typing import Literal, Type

from pydantic import DirectoryPath, Field, FilePath
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)


class AppConfig(BaseSettings):
    """
    Application configuration model.

    This class can be expanded to include application-wide settings
    that can be validated and managed using Pydantic.
    """

    generate: bool = Field(
        default=False, description="Generate new terrain and start playing"
    )
    level: Literal["1", "easy", "2", "medium", "3", "hard"] = Field(
        default="1", description="Game difficulty level"
    )
    scenario: Literal[
        "1",
        "Dullsville",
        "2",
        "San_Francisco",
        "3",
        "Hamburg",
        "4",
        "Bern",
        "5",
        "Tokyo",
        "6",
        "Detroit",
        "7",
        "Boston",
        "8",
        "Rio_de_Janeiro",
    ] = Field(default="1", description="Start with specific scenario")
    wire_mode: bool = Field(
        default=False, description="Use networking mode (no shared memory)"
    )
    multiplayer: bool = Field(default=False, description="Enable multiplayer mode")
    filename: FilePath | None = Field(
        default=None, description="City file to load (.cty) or new city name"
    )
    home: DirectoryPath = Field(
        default=Path("."),
        description="Home directory for save files and configurations",
    )
    resource_dir: DirectoryPath = Field(
        default=Path("./assets"),
        description="Directory containing game resources",
    )
    

    model_config = SettingsConfigDict(toml_file="./config.toml")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (TomlConfigSettingsSource(settings_cls, "./config.toml"),)
