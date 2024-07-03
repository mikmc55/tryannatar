from enum import Enum
from typing import Any, Generator

import Levenshtein
import PTN
import structlog
from pydantic import BaseModel, Field, field_validator

from annatar import config

log = structlog.get_logger(__name__)

# Space required for values
# 1 bit:  2 values  (0 to 1) # good for boolean flags like HDR or Year
# 2 bits: 4 values  (0 to 3)
# 3 bits: 8 values  (0 to 7)
# 4 bits: 16 values  (0 to 15)
# I'm not using any more than this. 8 is far too wide a decision tree

eru/fuzzy-match-title
NAME_MATCH_BIT_POS = 24
=======
TRASH = ["Cam", "Telesync", "Telecine", "Screener", "Workprint"]
master
SEASON_MATCH_BIT_POS = 20
RESOLUTION_BIT_POS = 14
AUDIO_BIT_POS = 8
YEAR_MATCH_BIT_POS = 6

RESOLUTION_SCORES = {
    "720p": 1,
    "1080p": 2,
    # QHD
    "QHD": 3,
    # 4K
    "4K": 4,
    # 5K
    "5K": 5,
    # 8K
    "8K": 6,
}
RESOLUTION_BITS_LENGTH = 3


def max_resolution_score(resolution: str) -> int:
    return (score_resolution(resolution) + 1 << RESOLUTION_BIT_POS) - 1


def min_resolution_score(resolution: str) -> int:
    return score_resolution(resolution) << RESOLUTION_BIT_POS


def score_resolution(resolution: str) -> int:
    """
    Gives the resolution a score between 0 and (RESOLUTION_BITS_LENGTH^2)-1
    Higher number is better
    """
    if resolution in RESOLUTION_SCORES:
        return RESOLUTION_SCORES[resolution]
    return 0


def get_resolution(score: int) -> str:
    mask = ((1 << RESOLUTION_BITS_LENGTH) - 1) << RESOLUTION_BIT_POS
    resolution_value = (score & mask) >> RESOLUTION_BIT_POS
    for resolution, value in RESOLUTION_SCORES.items():
        if value == resolution_value:
            return resolution
    return "Unknown"


class Category(str, Enum):
    Movie = "movie"
    Series = "series"

    def __str__(self) -> str:
        return self.value

    def id(self) -> int:
        if self == Category.Movie:
            return 2000
        if self == Category.Series:
            return 5000
        raise ValueError(f"Unknown category {self}")


class TorrentMeta(BaseModel):
    title: str
    imdb: str | None = None
    audio: list[str] = Field(default_factory=list)
    bitDepth: list[int] = Field(default_factory=list)
    codec: list[str] = Field(default_factory=list)
    encoder: list[str] = Field(default_factory=list)
    episode: list[int] = Field(default_factory=list)
    episodeName: str = ""
    extended: bool = False
    filetype: list[str] = Field(default_factory=list)
    hdr: bool = False
    language: list[str] = Field(default_factory=list)
    quality: list[str] = Field(default_factory=list)
    remastered: bool = False
    remux: bool = False
    resolution: list[str] = Field(default_factory=list)
    season: list[int] = Field(default_factory=list)
    subtitles: list[str] = Field(default_factory=list)
    year: list[int] = Field(default_factory=list)
    raw_title: str = ""

    @field_validator("resolution", mode="before")
    @classmethod
    def standardize_resolution(cls: Any, v: Any):
        if v is None:
            return ""
        if isinstance(v, bytes):
            v = v.decode("utf-8")

        if isinstance(v, str):
            if v.lower() == "1440p":
                return "QHD"
            if v.lower() == "2160p":
                return "4K"
            if v.lower() == "2880p":
                return "5K"
            if v.lower() == "4320p":
                return "8K"
            return v
        if isinstance(v, list):
            return [x for x in [cls.standardize_resolution(r) for r in v if r] if x]
        return v

    @field_validator("imdb", mode="before")
    @classmethod
    def fix_imdb_id(cls: Any, v: Any):
        if v is None:
            return None
        if isinstance(v, int):
            return f"tt{v:07d}"
        if isinstance(v, str):
            if v.startswith("tt"):
                return v
            return f"tt{int(v):07d}"
        return v

    def with_info_hash(self, info_hash: str) -> "Torrent":
        return Torrent(**self.model_dump(), info_hash=info_hash)

    @staticmethod
    def parse_title(title: str) -> "TorrentMeta":
        meta: dict[Any, Any] = PTN.parse(title, standardise=True, coherent_types=True)
        meta["raw_title"] = title
        return TorrentMeta.model_validate(meta)

    @property
    def audio_channels(self) -> Generator[str, None, None]:
        if any("7.1" in a for a in self.audio):
            yield "7.1"
        if any("5.1" in a for a in self.audio):
            yield "5.1"

    def is_season_episode(self, season: int, episode: int) -> bool:
        return self.score_series(season=season, episode=episode) > 0

    def is_trash(self) -> bool:
        return any(x in self.quality for x in TRASH)

    def score_series(self, season: int, episode: int) -> int:
        """
        Score a torrent based on season and episode where the rank is as follows:
           3 -> Whole series matches
           2 -> Whole season matches
           1 -> Single episode matches
           0 -> No match at all
        -100 -> Mismatch Season
         -10 -> Mismatch Episode
          -1 -> Unknown mismatch
        """
        if not season and not episode:
            # no season or episode. Probably a movie
            return 0
        if self.season and season not in self.season:
            # season mismatch
            return -100
        if self.episode and episode not in self.episode:
            # episode mismatch
            return -10
        if not self.season and not self.episode:
            # no season or episode
            return 0
        if len(self.season) > 1 and season in self.season:
            # series matches
            return 3
        if season in self.season and not self.episode:
            # whole season matches
            return 2
        if season in self.season and episode in self.episode:
            # single episode matches
            return 1
        return -1

    def matches_name(self, title: str) -> bool:
        eru/fuzzy-match-title
        return (
            Levenshtein.ratio(self.title.lower(), title.lower())
            >= config.TORRENT_TITLE_MATCH_THRESHOLD
        )

        return Levenshtein.ratio(self.title.lower(), title.lower()) > 0.9
        master

    @property
    def score(self):
        return self.match_score(
            title=self.title,
            year=self.year.pop() if self.year else 0,
            season=self.season[0] if self.season else 0,
            episode=self.episode[0] if self.episode else 0,
        )

    def match_score(
        self,
        year: int,
        title: str | None = None,
        season: int = 0,
        episode: int = 0,
    ) -> int:
        if title and not self.matches_name(title):
            return -1000
        if self.is_trash():
            return -5000
        if self.year and year and year not in self.year:
            return -2000

        season_match_score = (
            self.score_series(season=season, episode=episode) << SEASON_MATCH_BIT_POS
        )
        if season_match_score < 0:
            return season_match_score
        resolution_score = (
            score_resolution(self.resolution.pop()) << RESOLUTION_BIT_POS
            if len(self.resolution) > 0
            else 0
        )
        audio_score = (
            2 if "7.1" in self.audio_channels else 1 if "5.1" in self.audio_channels else 0
        ) << AUDIO_BIT_POS

        year_match_score = (1 if self.year and year in self.year else 0) << YEAR_MATCH_BIT_POS
        result: int = season_match_score | resolution_score | audio_score | year_match_score
        return result


class Torrent(TorrentMeta, BaseModel):
    info_hash: str

    @field_validator("info_hash", mode="before")
    @classmethod
    def consistent_info_hash(cls: Any, v: Any):
        if v is None:
            return None
        if isinstance(v, str):
            # info_hash needs to be upper case for comparison
            return v.upper()
        return v


class TorrentList(BaseModel):
    torrents: list[str]


def max_score_for(resolution: str) -> int:
    return Torrent.parse_title(
        title=f"Friends S01-S10 1994 7.1 COMPLETE {resolution}",
    ).match_score(title="Friends", year=1994, season=5, episode=10)


def lowest_score_for(resolution: str) -> int:
    return Torrent.parse_title(
        title=f"Oppenheimer {resolution}",
    ).match_score(title="Oppenheimer", year=2022, season=1, episode=1)


def score_range_for(resolution: str) -> range:
    return range(lowest_score_for(resolution), max_score_for(resolution) + 1)
