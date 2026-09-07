import httpx
import pytest

from notion_exporter import NotionExporter

_PAGE_ID = "11111111-1111-1111-1111-111111111111"


def _handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path.startswith("/v1/pages/"):
        return httpx.Response(
            200,
            json={
                "id": _PAGE_ID,
                "url": "https://notion.so/page",
                "created_by": {"id": "u1"},
                "last_edited_by": {"id": "u1"},
                "last_edited_time": "2026-01-01T00:00:00.000Z",
                "parent": {"type": "workspace", "workspace": True},
                "properties": {"title": {"type": "title", "title": []}},
            },
        )
    if path.startswith("/v1/blocks/"):
        return httpx.Response(200, json={"results": [], "has_more": False, "next_cursor": None})
    if path.startswith("/v1/users/"):
        return httpx.Response(200, json={"name": "Alice"})
    return httpx.Response(200, json={})


@pytest.mark.asyncio
async def test_request_hook_is_wired_into_client():
    async def request_hook(_request: httpx.Request) -> None:
        ...

    exporter = NotionExporter(notion_token="fake-token", request_hook=request_hook)
    assert request_hook in exporter.notion.client.event_hooks["request"]


@pytest.mark.asyncio
async def test_request_hook_fires_for_every_request():
    call_count = 0

    async def request_hook(_request: httpx.Request) -> None:
        nonlocal call_count
        call_count += 1

    exporter = NotionExporter(notion_token="fake-token", request_hook=request_hook)
    # keep the constructor-wired hooks, but route requests through a mock transport
    exporter.notion.client = httpx.AsyncClient(
        transport=httpx.MockTransport(_handler),
        event_hooks=exporter.notion.client.event_hooks,
    )

    await exporter._async_export_pages(page_ids={_PAGE_ID}, database_ids=set())
    await exporter.notion.client.aclose()

    # one export fans out into several requests (page meta, users, child blocks);
    # the hook must fire per request, not once per export
    assert call_count >= 3


@pytest.mark.asyncio
async def test_no_request_hook_leaves_default_client_unhooked():
    exporter = NotionExporter(notion_token="fake-token")
    assert exporter.notion.client.event_hooks.get("request") in (None, [])
