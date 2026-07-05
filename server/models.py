from pydantic import BaseModel, HttpUrl
from typing import Literal
from datetime import datetime

class RawItem(BaseModel):
    source_type : Literal["reddit" , "rss" , "telegram"]  # "reddit" | "rss" | "telegram"
    source_name : str   # მაგ. "r/football" ან "BBC News"
    title : str         # სათაური
    content : str       # ტექსტი / კონტენტი
    url : HttpUrl       # სტატიის ლინკი
    published_at : datetime     # გამოქვეყნების დრო
    fetched_at : datetime       # ჩვენი ბექენდის მიერ წამოღების დრო

