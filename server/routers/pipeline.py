from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
from ..schemas import PipelineProgressEvent, SynthesizedCluster
from ..aggregator import aggregate_all_sources
from ..dedup.similarity import group_duplicates, select_representative_items
from ..groq_client import synthesize_cluster
from ..routing import get_mode_for_cluster

router = APIRouter()

async def run_pipeline_stream() :
    items = await aggregate_all_sources()
    
    yield PipelineProgressEvent(
        event_type = "fetched" , 
        processed_count = 0 ,
        total_expected = len(items)
    )

    groups = group_duplicates(items , threshold = 0.82)

    yield PipelineProgressEvent(
        event_type = "clustered" ,
        processed_count = 0 ,
        total_expected = len(groups)
    )

    representatives = select_representative_items(groups)

    for index , group in enumerate(groups , start = 1) :
        try :
            mode = get_mode_for_cluster(group)
            summary = await asyncio.to_thread(synthesize_cluster, group)
            
            if summary is None :
                print(f"WARNING: synthesis failed for cluster {index}; skipping.")
                continue

            representative = representatives[index - 1]

            cluster_data = SynthesizedCluster(
                title=representative.title,
                content=representative.content,
                url=str(representative.url),
                source_name=representative.source_name,
                source_type=representative.source_type,
                published_at=representative.published_at,
                fetched_at=representative.fetched_at,
                summary=summary,
                mode=mode,
                cluster_size=len(group)
            )

            yield PipelineProgressEvent(
                event_type = "cluster_ready" ,
                processed_count = index , 
                total_expected = len(groups) ,
                current_cluster = cluster_data
            )

        except Exception as e:
            print(f"WARNING: error synthesizing cluster {index}: {e}")
            continue

    
    yield PipelineProgressEvent(
        event_type="completed", 
        processed_count=len(groups), 
        total_expected=len(groups)
    )

@router.websocket("/ws/pipeline/run")
async def pipeline_ws(websocket: WebSocket) :
    await websocket.accept()

    try :
        async for event in run_pipeline_stream() :
            await websocket.send_text(event.model_dump_json())
    except WebSocketDisconnect :
        print("INFO: PyQt client disconnected mid-run. Stopping pipeline to save Groq costs.")
    except Exception as e :
        print(f"ERROR: Something went wrong in WebSocket: {e}")
    finally :
        try :
            await websocket.close()
        except : 
            pass          

