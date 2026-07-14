import html
import os
from groq import Groq
from .models import RawItem
from .prompts import SHORT_MODE_PROMPT, STORY_MODE_PROMPT  
from .routing import  get_mode_for_cluster
import re
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL_FOR_MODE = {
    "short": "openai/gpt-oss-20b",
    "story": "openai/gpt-oss-120b",
}

def format_articles(group: list[RawItem]) -> str:
    xml_output = ""
    for index , item in enumerate(group , start = 1) :
        clean_title = html.unescape(item.title)
        clean_title = re.sub(r'<[^>]+>' , '' , clean_title)
        safe_title = html.escape(clean_title, quote=False)
        safe_content = html.escape(item.content, quote=False)

        article_xml = (
            f'<article n="{index}">\n'
            f'  <title>{safe_title}</title>\n'
            f'  <content>{safe_content}</content>\n'
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
