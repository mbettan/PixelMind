import asyncio
from playwright.async_api import async_playwright, Page, Browser
import numpy as np
from PIL import Image
import io

class PlaywrightWrapper:
    def __init__(self):
        self.pw = None
        self.browser = None
        self.context = None
        self.page = None

    async def start(self, headless: bool = True, slow_mo: int = 50, timeout: int = 30000):
        self.pw = await async_playwright().start()
        self.browser = await self.pw.chromium.launch(headless=headless, slow_mo=slow_mo)
        self.context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 800}
        )
        self.page = await self.context.new_page()
        self.page.set_default_timeout(timeout)
        self.timeout = timeout
        
        # Setup automatic alert handling
        self.page.on("dialog", lambda dialog: asyncio.create_task(self._handle_dialog(dialog)))

    async def _handle_dialog(self, dialog):
        print(f"[Engine] Automation auto-accepting dialog: {dialog.message}")
        await dialog.accept()

    async def stop(self):
        if self.browser:
            await self.browser.close()
        if self.pw:
            await self.pw.stop()

    async def navigate(self, url: str):
        """Navigate to a URL with fallback strategy."""
        print(f"[Engine] Navigating to: {url}")
        try:
            # Try networkidle first (preferred for stable UI)
            await self.page.goto(url, wait_until="networkidle", timeout=self.timeout)
        except Exception:
            print(f"[Warning] Network idle timeout for {url}, falling back to load")
            try:
                await self.page.goto(url, wait_until="load", timeout=self.timeout)
            except Exception as e:
                print(f"[Error] Navigation failed completely: {e}")
                raise

    async def get_screenshot(self) -> bytes:
        return await self.page.screenshot(full_page=False)

    async def _to_viewport(self, norm_x: float, norm_y: float) -> tuple[float, float]:
        """Convert 0–1000 normalized coords to actual viewport pixels."""
        viewport = self.page.viewport_size
        vx = (norm_x / 1000.0) * viewport['width']
        vy = (norm_y / 1000.0) * viewport['height']
        return vx, vy

    async def click_at(self, x: float, y: float):
        """Clicks at normalized coordinates (0-1000)."""
        vx, vy = await self._to_viewport(x, y)
        await self.page.mouse.click(vx, vy)

    async def select_option(self, x: float, y: float, option_text: str):
        """Selects an option from a native dropdown by coordinates."""
        vx, vy = await self._to_viewport(x, y)
        await self.page.mouse.click(vx, vy)
        try:
            # Attempt native select interaction
            await self.page.select_option(f"select >> nth=0", label=option_text)
            await asyncio.sleep(0.5)
        except Exception:
            # Fallback to coordinate-based click if select_option fails
            await self.page.mouse.click(vx, vy)

    async def type_at(self, x: float, y: float, text: str):
        """Types text at normalized coordinates."""
        vx, vy = await self._to_viewport(x, y)
        await self.page.mouse.click(vx, vy)
        await self.page.keyboard.type(text)

    async def wait_for_ui_settle(self, threshold: float = 0.95, timeout: float = 10.0, interval: float = 0.5):
        """
        Polls for UI stability using SSIM.
        Returns True if settled, False if timeout reached.
        """
        from engine.visual_perception import VisualPerception
        perception = VisualPerception()
        
        last_screenshot = await self.get_screenshot()
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            await asyncio.sleep(interval)
            current_screenshot = await self.get_screenshot()
            score = perception.calculate_ssim(last_screenshot, current_screenshot)
            
            if score >= threshold:
                print(f"[Engine] UI settled (SSIM: {score:.4f} >= {threshold})")
                return True
            
            last_screenshot = current_screenshot
        
        print(f"[Warning] UI stability timeout after {timeout}s")
        return False

    async def get_page_info(self) -> dict:
        """
        Returns metadata about the current page state.
        """
        return {
            "url": self.page.url,
            "title": await self.page.title()
        }
