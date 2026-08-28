from typing import Literal

from pydantic import BaseModel, Field


class PreprocessingConfig(BaseModel):
    normalize_unicode: bool = True
    strip_html: bool = True
    normalize_whitespace: bool = True
    normalize_urls: bool = True
    remove_urls: bool = False
    lowercase: bool = False
    normalize_punctuation_spacing: bool = True


class TextCompositionConfig(BaseModel):
    mode: Literal["title_only", "content_only", "title_and_content"] = "title_and_content"
    separator: str = Field(default="\n\n", min_length=1, max_length=20)

