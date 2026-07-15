from typing import Optional

import requests
import trafilatura
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl

app = FastAPI(
    title="0050 News Extraction API",
    description="使用 Trafilatura 擷取 0050 相關新聞正文",
    version="1.0.0",
)


class ExtractRequest(BaseModel):
    url: HttpUrl


class ExtractResponse(BaseModel):
    success: bool
    url: str
    title: Optional[str] = None
    author: Optional[str] = None
    publish_date: Optional[str] = None
    content: str
    content_length: int


@app.get("/")
def health_check():
    return {
        "status": "ok",
        "service": "0050 News Extraction API",
        "message": "FastAPI is running",
    }


@app.post("/extract", response_model=ExtractResponse)
def extract_article(request: ExtractRequest):

    url = str(request.url)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/138.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=20,
        )

        response.raise_for_status()

    except requests.RequestException as exc:
        raise HTTPException(
            status_code=400,
            detail=f"網頁下載失敗：{exc}",
        )

    html = response.text

    content = trafilatura.extract(
        html,
        url=url,
        output_format="markdown",
        include_comments=False,
        include_links=False,
        include_images=False,
        include_tables=True,
        favor_precision=True,
    )

    if not content:
        raise HTTPException(
            status_code=422,
            detail="網頁下載成功，但無法擷取文章正文。",
        )

    metadata = trafilatura.extract_metadata(html)

    cleaned_content = "\n".join(
        line.strip()
        for line in content.splitlines()
        if line.strip()
    )

    return ExtractResponse(
        success=True,
        url=url,
        title=metadata.title if metadata else None,
        author=metadata.author if metadata else None,
        publish_date=metadata.date if metadata else None,
        content=cleaned_content,
        content_length=len(cleaned_content),
    )