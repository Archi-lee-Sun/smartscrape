from pydantic import BaseModel, HttpUrl
from typing import Literal
from datetime import datetime

class RawItem(BaseModel):
    source_type : Literal["reddit" , "rss" , "telegram"]
    source_name : str
    title : str
    content : str
    url : HttpUrl
    published_at : datetime
    fetched_at : datetime

