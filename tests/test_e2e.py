import os
import asyncio
import pytest
from pathlib import Path
from src.main import run_test
import shutil

# Mark all tests as E2E and skip if no API Key is available
pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.e2e,
    pytest.mark.skipif(
        not os.environ.get("GOOGLE_API_KEY") and not os.environ.get("GOOGLE_CLOUD_PROJECT"),
        reason="Neither GOOGLE_API_KEY nor GOOGLE_CLOUD_PROJECT set — skipping E2E tests"
    ),
]

class TestFrameworkE2E:
    """End-to-end tests for the AI-Driven Web Testing Framework."""

    async def test_mrgnyc_rentals(self, tmp_path):
        """
        Verifies that the framework can successfully navigate and interact with mrgnyc.com.
        """
        test_goal = "Verify the availability of 1 bedroom apartments"
        start_url = "https://www.mrgnyc.com/"
        
        # Override run_logs to a temporary directory if possible, 
        # but run_test currently has a hardcoded 'run_logs' relative path.
        # For now, we'll let it create in the project root and then check for the latest run.
        
        # ACT
        await run_test(test_goal, start_url)
        
        # ASSERT
        # Find the latest run_log directory
        run_logs_path = Path("run_logs")
        dirs = sorted([d for d in run_logs_path.iterdir() if d.is_dir()], key=lambda x: x.name, reverse=True)
        assert len(dirs) > 0, "No run logs were created"
        
        latest_run = dirs[0]
        assert "Verify_the_availability_of_1_bedroom_apartments" in latest_run.name
        
        # Check for essential artifacts
        assert (latest_run / "plan.json").exists()
        assert (latest_run / "execution.log").exists()
        assert (latest_run / "initial_state.png").exists()
        
        # Verify dashboard was updated
        assert Path("dashboard/index.html").exists()

    async def test_udr_view34(self):
        """
        Verifies that the framework can navigate to UDR View 34.
        """
        test_goal = "Verify the availability of 1-bedroom apartments"
        start_url = "https://www.udr.com/new-york-city-apartments/murray-hill/view-34/"
        
        # ACT
        await run_test(test_goal, start_url)
        
        # ASSERT
        run_logs_path = Path("run_logs")
        dirs = sorted([d for d in run_logs_path.iterdir() if d.is_dir()], key=lambda x: x.name, reverse=True)
        latest_run = dirs[0]
        
        assert (latest_run / "plan.json").exists()
        assert (latest_run / "execution.log").exists()

    

    # --- Batch 1: Heroku 'The Internet' ---

    async def test_dropdown_simple(self):
        test_goal = "Verify that a user can select Option 1 from the dropdown successfully"
        run_id = await run_test(test_goal, "https://the-internet.herokuapp.com/dropdown")
        await self._verify_run(run_id)

    async def test_checkboxes_simple(self):
        test_goal = "Verify that both checkboxes can be checked and unchecked correctly"
        run_id = await run_test(test_goal, "https://the-internet.herokuapp.com/checkboxes")
        await self._verify_run(run_id)

    

    async def test_file_upload_simple(self):
        test_goal = "Verify that a user can upload a file successfully and see the uploaded filename"
        # Note: This might require the agent to find an 'upload' button and potentially use a local dummy file.
        # The agent should autonomously handle the file picker if possible, or we might need to provide a mock.
        run_id = await run_test(test_goal, "https://the-internet.herokuapp.com/upload")
        await self._verify_run(run_id)

    async def test_dynamic_loading(self):
        test_goal = "Verify that dynamically loaded content appears after clicking the Start button"
        run_id = await run_test(test_goal, "https://the-internet.herokuapp.com/dynamic_loading/1")
        await self._verify_run(run_id)

    # --- Batch 2: Automation Exercise ---

    async def test_ecommerce_homepage(self):
        test_goal = "Verify that the homepage loads successfully and main navigation links are visible"
        run_id = await run_test(test_goal, "https://automationexercise.com/")
        await self._verify_run(run_id)

    async def test_ecommerce_search(self):
        test_goal = "Verify that product search returns relevant matching products"
        run_id = await run_test(test_goal, "https://automationexercise.com/products")
        await self._verify_run(run_id)

    async def test_ecommerce_product_details(self):
        test_goal = "Verify that the product details page displays product information correctly"
        run_id = await run_test(test_goal, "https://automationexercise.com/product_details/1")
        await self._verify_run(run_id)

    async def test_ecommerce_cart(self):
        test_goal = "Verify that the cart page loads correctly for a guest user"
        run_id = await run_test(test_goal, "https://automationexercise.com/view_cart")
        await self._verify_run(run_id)

    async def test_ecommerce_contact_us(self):
        test_goal = "Verify that the contact us form can be filled and submitted successfully"
        run_id = await run_test(test_goal, "https://automationexercise.com/contact_us")
        await self._verify_run(run_id)

    async def test_ecommerce_category(self):
        test_goal = "Verify that category filtering displays the expected category products"
        run_id = await run_test(test_goal, "https://automationexercise.com/category_products/2")
        await self._verify_run(run_id)

    # --- Batch 3: Expand Testing ---

    async def test_practice_dropdown(self):
        test_goal = "Verify that a user can select an option from the dropdown list"
        run_id = await run_test(test_goal, "https://practice.expandtesting.com/dropdown")
        await self._verify_run(run_id)

    async def test_practice_checkboxes(self):
        test_goal = "Verify that checkbox states change correctly when clicked"
        run_id = await run_test(test_goal, "https://practice.expandtesting.com/checkboxes")
        await self._verify_run(run_id)

    async def test_practice_radio(self):
        test_goal = "Verify that only one radio button can be selected at a time"
        run_id = await run_test(test_goal, "https://practice.expandtesting.com/radio-buttons")
        await self._verify_run(run_id)

    async def test_practice_upload(self):
        test_goal = "Verify that a file can be uploaded successfully on the upload page"
        run_id = await run_test(test_goal, "https://practice.expandtesting.com/upload")
        await self._verify_run(run_id)

    async def _verify_run(self, run_id):
        """Helper to verify run artifacts using the specific run_id."""
        run_logs_path = Path("run_logs")
        latest_run = next(run_logs_path.glob(f"{run_id}*"), None)
        
        assert latest_run is not None, f"Could not find log directory for run_id: {run_id}"
        assert latest_run.is_dir()
        
        assert (latest_run / "plan.json").exists()
        assert (latest_run / "execution.log").exists()
        
        # Verify functional success in the log
        log_content = (latest_run / "execution.log").read_text()
        
        # We must see the finish marker
        assert "--- Test Execution Finished ---" in log_content
        
        # We must NOT see any step-level failures
        # Note: We ignore general 'ERROR' due to async cleanup noise (asyncio),
        # but capture specific operational error markers.
        assert "Step failed after 3 attempts" not in log_content
        assert "[FRAMEWORK_ERROR]" not in log_content
        assert "Agent Failed" not in log_content
