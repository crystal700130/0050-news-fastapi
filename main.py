from typing import Optional

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

    downloaded = trafilatura.fetch_url(url)

    if not downloaded:
        raise HTTPException(
            status_code=400,
            detail="網頁下載失敗，可能是網址錯誤或網站禁止存取。",
        )

    content = trafilatura.extract(
        downloaded,
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

    metadata = trafilatura.extract_metadata(downloaded)

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