from pydantic import BaseModel
from datetime import datetime

class SynthesizedCluster(BaseModel) :
    title : str
    content : str
    url : str
    source_type : str
    source_name : str 
    published_at : datetime
    fetched_at : datetime
    summary : str
    mode : str 
    cluster_size : int


class PipelineProgressEvent(BaseModel) :
    event_type : str
    current_cluster : SynthesizedCluster | None = None 
    processed_count : int
    total_expected : int