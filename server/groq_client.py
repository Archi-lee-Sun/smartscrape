import html
import os
from groq import Groq
from .models import RawItem
from .prompts import SHORT_MODE_PROMPT, STORY_MODE_PROMPT  
import re
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SOURCE_MODE = {
    "BBC Sport": "short",
    "Transfermarkt": "short",
    "World History Encyclopedia": "story",
    "The Football History Podcast": "story",
    "Holding Midfield": "story",
    "Spielverlagerung.com": "story",       
    "American Songwriter": "story",        

    "Far Out Magazine": "story",           
    "Greek Reporter": "story",             
    "Coaches' Voice": "story",             
    "These Football Times": "story",      
    "Achtung Radio": "story",             
    "11v11": "story",                     

    "FabrizioRomanoTG": "short",           
    "FootballHistor": "story",            
    "ClassicRockNews": "story",            
    "OasisProtocolFoundation": "short",  
    "OasisProtocolCommunity": "short",     
}

MODEL_FOR_MODE = {
    "short": "openai/gpt-oss-20b",
    "story": "openai/gpt-oss-120b",
}

def get_mode_for_cluster(group: list[RawItem]) -> str:
    modes = {SOURCE_MODE.get(item.source_name, "story") for item in group}
    if len(modes) > 1 :
        raise ValueError(
            f"Cluster has mixed modes: {modes} — sources: "
            f"{[item.source_name for item in group]}"
        )
    return modes.pop()


def format_articles(group: list[RawItem]) -> str:
    xml_output = ""
    for index , item in enumerate(group , start = 1) :
        clean_title = html.unescape(item.title)
        clean_content = html.unescape(item.content)
        
        clean_title = re.sub(r'<[^>]+>' , '' , clean_title)
        clean_content = re.sub(r'<[^>]+>' , '' , clean_content)

        article_xml = (
            f'<article n="{index}">\n'
            f'  <title>{clean_title}</title>\n'
            f'  <content>{clean_content}</content>\n'
            f'</article>\n\n'
        )

        xml_output += article_xml

    return xml_output.strip()


def extract_summary(raw_text: str) -> str:
    match = re.search(r"<summary>(.*?)</summary>" , raw_text , re.DOTALL)
    if match :
        summary = match.group(1).strip()
        if summary :
            return summary
        
    print(f"WARNING: no valid <summary> tags found, falling back to raw text: {raw_text[:100]!r}")
    return raw_text.strip()

def synthesize_cluster(group: list[RawItem]) -> str | None:
    mode = get_mode_for_cluster(group)
    system_prompt = SHORT_MODE_PROMPT if mode == "short" else STORY_MODE_PROMPT
    model = MODEL_FOR_MODE[mode]
    articles_xml = format_articles(group)
    
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": articles_xml},
            ],
            temperature=0.2,
        )
    except Exception as e:
        print(f"Error synthesizing cluster (mode={mode}): {e}")
        return None

    return extract_summary(completion.choices[0].message.content)
