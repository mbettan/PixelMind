import pytest
import asyncio
from engine.playwright_wrapper import PlaywrightWrapper

@pytest.mark.asyncio
async def test_playwright_wrapper():
    wrapper = PlaywrightWrapper()
    await wrapper.start(headless=True)
    try:
        await wrapper.navigate("https://www.google.com")
        info = await wrapper.get_page_info()
        assert "Google" in info["title"]
        screenshot = await wrapper.get_screenshot()
        assert len(screenshot) > 0
        print(f"Successfully navigated to {info['url']}")
    finally:
        await wrapper.stop()

if __name__ == "__main__":
    asyncio.run(test_playwright_wrapper())
