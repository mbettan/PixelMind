import argparse
import os
import asyncio
from dotenv import load_dotenv
from engine.playwright_wrapper import PlaywrightWrapper
from agents.planner import PlannerAgent
from agents.actor import ActorAgent
from agents.validator import ValidatorAgent
from engine.discovery_sweep import DiscoverySweep
from engine.embeddings import verify_destination
from utils.logger import ExecutionLogger
from utils.dashboard_generator_v2 import generate_dashboard

async def run_test(test_goal: str, start_url: str = "https://www.example.com", update_callback=None):
    logger = ExecutionLogger(test_goal)
    
    def log_status(msg: str):
        logger.info(msg)
        if update_callback:
            asyncio.create_task(update_callback(msg))

    log_status(f"Target URL: {start_url}")
    
    # Initialize components
    wrapper = PlaywrightWrapper()
    planner = PlannerAgent()
    actor = ActorAgent()
    validator = ValidatorAgent()
    
    await wrapper.start(headless=True, slow_mo=50)
    step_results = []
    try:
        # 1. Planning Phase
        log_status("[Planner] Generating execution graph...")
        await wrapper.navigate(start_url) 
        await wrapper.wait_for_ui_settle()
        
        # Save initial state screenshot
        initial_ss = await wrapper.get_screenshot()
        logger.save_screenshot("initial_state", initial_ss)

        plan_text = await planner.process(test_goal)
        plan = planner.parse_plan(plan_text)
        
        if not plan:
            logger.error(f"Failed to generate a valid plan. Raw Output: {plan_text}")
            return

        logger.save_plan(plan)
        log_status(f"[Planner] Plan generated with {len(plan)} steps.")

        # 2. Execution Phase
        for i, step in enumerate(plan, 1):
            step_id = step.get('id', i)
            logger.step(i, step.get('description', 'No description'))
            if update_callback:
                asyncio.create_task(update_callback(f"Step {i}: {step.get('description')}"))
            
            step_fulfilled = False
            for attempt in range(1, 4):
                if attempt > 1:
                    logger.warning(f"--- Retrying Step {i} (Attempt {attempt}/3) ---")
                
                # Capture BEFORE state
                before_screenshot = await wrapper.get_screenshot()
                logger.save_screenshot(f"step_{step_id}_attempt_{attempt}_before", before_screenshot)
                
                # Actor decides on coordinates/actions (returns a list)
                logger.agent_call("Actor", f"Deciding actions for step {i}...")
                actor_output = await actor.process(step, before_screenshot, context=f"start_url: {start_url}")
                actor_data = actor.parse_action(actor_output)
                
                if not actor_data or 'actions' not in actor_data:
                    logger.error(f"Actor failed to produce actions for step {step_id}")
                    logger.info(f"[Debug] Raw Output: {actor_output}")
                    break
                
                actions = actor_data['actions']
                reasoning = actor_data.get('reasoning', 'No reasoning provided')
                logger.info(f"Actor Reasoning: {reasoning}")

                # Execute Action Sequence
                for action in actions:
                    act_type = action.get('type')
                    x, y = action.get('x'), action.get('y')
                    conf = action.get('confidence', 0.0)
                    elem = action.get('element_description', 'unknown element')
                    
                    if act_type == 'click' and x is not None:
                        logger.agent_call("Playwright", f"Click {elem} (conf:{conf}) at normalized ({x}, {y})")
                        await wrapper.click_at(x, y)
                    elif act_type == 'type' and x is not None:
                        text = action.get('text', 'test data')
                        logger.agent_call("Playwright", f"Type '{text}' into {elem} at ({x}, {y})")
                        await wrapper.type_at(x, y, text)
                    elif act_type == 'select' and x is not None:
                        text = action.get('text', '')
                        logger.agent_call("Playwright", f"Select Option '{text}' for {elem} at ({x}, {y})")
                        await wrapper.select_option(x, y, text)
                    elif act_type == 'navigate':
                        url = action.get('url', start_url)
                        logger.agent_call("Playwright", f"Navigate to {url}")
                        await wrapper.navigate(url)
                    elif act_type == 'scroll':
                        direction = action.get('direction', 'down')
                        amount = action.get('amount', 300)
                        logger.agent_call("Playwright", f"Scroll {direction} {elem}")
                        await wrapper.page.mouse.wheel(0, amount if direction == 'down' else -amount)
                    elif act_type == 'press_key':
                        key = action.get('key', 'Enter')
                        logger.agent_call("Playwright", f"Press {key}")
                        await wrapper.page.keyboard.press(key)
                    elif act_type == 'wait':
                        logger.info("Waiting for stability...")
                        await wrapper.wait_for_ui_settle()

                # Perceptual wait after action sequence (SSIM Polling)
                await wrapper.wait_for_ui_settle(timeout=5.0)
                
                # 3. Validation Phase (Comparative)
                logger.agent_call("Validator", f"Verifying Step {step_id} (Attempt {attempt})...")
                after_screenshot = await wrapper.get_screenshot()
                logger.save_screenshot(f"step_{step_id}_attempt_{attempt}_after", after_screenshot)
                
                validation_output = await validator.process(
                    action_taken=f"{step.get('action')}: {step.get('description')}",
                    expected_outcome=step.get('expected_outcome', 'Goal achieved'),
                    before_screenshot=before_screenshot,
                    after_screenshot=after_screenshot
                )
                validation = validator.parse_validation(validation_output)
                
                # 3.4. Semantic Destination Verification (Inspired by Claude)
                # If the action was a click or navigate, and we expect a new page, verify semantically
                if any(kw in actor_data.get('action_type', '').lower() for kw in ['click', 'navigate']):
                    page_text = await wrapper.page.inner_text("body")
                    is_semantic_match, confidence_score = await verify_destination(
                        source_intent=step.get('expected_outcome', ''),
                        destination_text=page_text[:2000]
                    )
                    if not is_semantic_match:
                        logger.warning(f"Semantic mismatch detected (score: {confidence_score:.2f}). Expected: {step.get('expected_outcome')}")
                        # We don't fail immediately, but we log the warning for the validator to consider
                        # or we could force a retry if score is very low (< 0.5)
                        if confidence_score < 0.5:
                            logger.error(f"High-risk routing failure (score: {confidence_score:.2f})")
                            # Trigger retry by setting validation to failed if not already
                            if validation: validation['passed'] = False

                if validation and validation.get('passed'):
                    logger.info(f"[bold green]PASS:[/bold green] {validation.get('reasoning')}")
                    step_fulfilled = True
                    step_results.append({
                        "step_number": i,
                        "description": step.get('description'),
                        "action": actor_data.get('reasoning', 'Action performed'),
                        "passed": True
                    })
                    break
                else:
                    reason = validation.get('reasoning', 'Step not yet fulfilled') if validation else "Parsing error"
                    issues = validation.get('issues', []) if validation else []
                    if issues:
                        for issue in issues:
                            logger.warning(f"  [ISSUE] {issue.get('type')} ({issue.get('severity')}): {issue.get('description')}")
                    logger.warning(f"Step not fulfilled: {reason}")
            
            if not step_fulfilled:
                logger.error(f"Step {step_id} failed after 3 attempts. Aborting.")
                step_results.append({
                    "step_number": i,
                    "description": step.get('description'),
                    "passed": False
                })
                break

        # 4. Final Goal Validation
        if step_fulfilled:
            log_status("[Validator] Performing final goal sanity check...")
            final_ss = await wrapper.get_screenshot()
            logger.save_screenshot("final_state", final_ss)
            
            final_output = await validator.validate_final_goal(
                goal=test_goal,
                final_screenshot=final_ss,
                scenario_context=f"Tested against {start_url}",
                step_results=step_results
            )
            final_val = validator.parse_validation(final_output)
            
            if final_val and final_val.get('passed'):
                logger.info(f"[bold green]FINAL PASS:[/bold green] {final_val.get('reasoning')}")
            else:
                msg = final_val.get('reasoning', 'Final goal validation failed') if final_val else "Final validation parse error"
                logger.error(f"Final Goal Validation Failed: {msg}")
    finally:
        await wrapper.stop()
        # Close GenAI clients
        await planner.close()
        await actor.close()
        await validator.close()
        
        logger.info("\n--- Test Execution Finished ---")
        
        # Update dashboard
        try:
            generate_dashboard()
            logger.info("[Dashboard] Result visualization updated in dashboard/index.html")
        except Exception as e:
            logger.error(f"[Error] Failed to update dashboard: {e}")
            
    return logger.run_id

async def main():
    load_dotenv(override=True)
    parser = argparse.ArgumentParser(description="PixelMind: Autonomous AI-Driven Web Testing Framework")
    parser.add_argument("--test", type=str, help="Natural language test instruction")
    parser.add_argument("--url", type=str, default="https://www.example.com", help="Starting URL for the test")
    parser.add_argument("--discover", action="store_true", help="Perform autonomous discovery sweep")
    
    args = parser.parse_args()
    
    if args.test:
        await run_test(args.test, args.url)
    elif args.discover:
        wrapper = PlaywrightWrapper()
        await wrapper.start(headless=True)
        try:
            await wrapper.navigate(args.url)
            discovery = DiscoverySweep(wrapper)
            catalog = await discovery.execute()
            await discovery.audit_fields(catalog)
        finally:
            await wrapper.stop()
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())
