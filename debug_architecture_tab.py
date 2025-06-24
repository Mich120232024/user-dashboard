#!/usr/bin/env python3
"""
Debug script for architecture tab issues in the user dashboard.
Uses browser automation to interact with the UI and diagnose the problems.
"""

import asyncio
import json
import time
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

class ArchitectureTabDebugger:
    def __init__(self):
        self.dashboard_url = "http://localhost:8000/professional-dashboard.html"
        self.api_base = "http://localhost:8420/api/v1"
        self.results = {
            "test_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "issues_found": [],
            "dom_inspection": {},
            "network_analysis": {},
            "user_interaction_tests": {},
            "recommendations": []
        }

    async def run_debug_session(self):
        """Main debug session."""
        print("🔍 Starting Architecture Tab Debug Session...")
        
        async with async_playwright() as p:
            # Launch browser in headed mode to see what's happening
            browser = await p.chromium.launch(
                headless=False,  # Show browser for debugging
                slow_mo=1000,    # Slow down actions for visibility
                args=['--disable-web-security', '--disable-features=VizDisplayCompositor']
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            
            # Enable console logging
            context.on("console", self._handle_console)
            context.on("request", self._handle_request)
            context.on("response", self._handle_response)
            
            page = await context.new_page()
            
            try:
                await self._test_initial_load(page)
                await self._test_architecture_tab_navigation(page)
                await self._test_file_list_rendering(page)
                await self._test_file_click_behavior(page)
                await self._test_iframe_functionality(page)
                await self._analyze_dom_structure(page)
                
            except Exception as e:
                self.results["issues_found"].append(f"Critical error during testing: {str(e)}")
                print(f"❌ Critical error: {e}")
                
            finally:
                await browser.close()
                
        self._generate_report()

    async def _test_initial_load(self, page):
        """Test initial page load and basic functionality."""
        print("📄 Testing initial page load...")
        
        try:
            response = await page.goto(self.dashboard_url, wait_until="networkidle")
            
            if response.status != 200:
                self.results["issues_found"].append(f"Page load failed with status {response.status}")
                return
                
            # Wait for dashboard initialization
            await page.wait_for_function("window.dashboard !== undefined", timeout=10000)
            
            # Check if nav items are present
            nav_items = await page.query_selector_all('.nav-item')
            print(f"✅ Found {len(nav_items)} navigation items")
            
            # Look for architecture tab specifically
            arch_tab = await page.query_selector('[data-tab="research"]')
            if arch_tab:
                print("✅ Architecture tab found")
            else:
                self.results["issues_found"].append("Architecture tab not found in navigation")
                
        except PlaywrightTimeoutError:
            self.results["issues_found"].append("Page load timeout - dashboard may not be initializing properly")

    async def _test_architecture_tab_navigation(self, page):
        """Test clicking on the architecture tab."""
        print("🔗 Testing architecture tab navigation...")
        
        try:
            # Click on architecture tab
            arch_tab = await page.query_selector('[data-tab="research"]')
            if arch_tab:
                await arch_tab.click()
                print("✅ Successfully clicked architecture tab")
                
                # Wait for tab content to become active
                await page.wait_for_selector('#research.active', timeout=5000)
                print("✅ Architecture tab content is now active")
                
                # Check if loadArchitecture function was called
                console_logs = getattr(self, '_console_logs', [])
                load_arch_called = any("loadArchitecture called" in log for log in console_logs)
                if load_arch_called:
                    print("✅ loadArchitecture function was called")
                else:
                    self.results["issues_found"].append("loadArchitecture function may not be called on tab switch")
                    
            else:
                self.results["issues_found"].append("Could not find architecture tab to click")
                
        except PlaywrightTimeoutError:
            self.results["issues_found"].append("Architecture tab content did not become active within timeout")

    async def _test_file_list_rendering(self, page):
        """Test if files are properly rendered in the list."""
        print("📁 Testing file list rendering...")
        
        try:
            # Wait for architecture files to load
            await page.wait_for_selector('#architecture-files', timeout=5000)
            
            # Wait a bit for the API call to complete
            await page.wait_for_timeout(3000)
            
            # Check if files are displayed
            file_elements = await page.query_selector_all('.file-item')
            print(f"📊 Found {len(file_elements)} file items in DOM")
            
            if len(file_elements) == 0:
                # Check if there's a loading state
                loading_element = await page.query_selector('#architecture-files .loading')
                if loading_element:
                    self.results["issues_found"].append("Files are stuck in loading state")
                else:
                    # Check if there's an error message
                    error_element = await page.query_selector('#architecture-files .empty-state')
                    if error_element:
                        error_text = await error_element.inner_text()
                        self.results["issues_found"].append(f"Error loading files: {error_text}")
                    else:
                        self.results["issues_found"].append("No files displayed and no error message")
            
            # Check categories
            category_elements = await page.query_selector_all('.file-category')
            print(f"📂 Found {len(category_elements)} categories")
            
            if len(category_elements) > 0:
                for i, category in enumerate(category_elements[:3]):  # Check first 3 categories
                    category_header = await category.query_selector('.category-header')
                    if category_header:
                        header_text = await category_header.inner_text()
                        print(f"📂 Category {i+1}: {header_text}")
                        
        except PlaywrightTimeoutError:
            self.results["issues_found"].append("Architecture files container not found within timeout")

    async def _test_file_click_behavior(self, page):
        """Test what happens when clicking on files."""
        print("🖱️ Testing file click behavior...")
        
        try:
            # Wait for file items to be present
            await page.wait_for_selector('.file-item', timeout=5000)
            
            file_items = await page.query_selector_all('.file-item')
            if len(file_items) > 0:
                print(f"🖱️ Testing click on first file...")
                
                # Get the file info before clicking
                first_file = file_items[0]
                file_text = await first_file.inner_text()
                print(f"📄 Clicking on file: {file_text}")
                
                # Monitor for download attempts
                download_started = False
                
                def handle_download(download):
                    nonlocal download_started
                    download_started = True
                    print(f"❌ Download started for: {download.url}")
                    
                page.on("download", handle_download)
                
                # Click the file
                await first_file.click()
                
                # Wait a moment to see what happens
                await page.wait_for_timeout(2000)
                
                if download_started:
                    self.results["issues_found"].append("File click triggered download instead of iframe display")
                else:
                    print("✅ No download triggered by file click")
                    
                # Check if iframe was updated
                iframe = await page.query_selector('#architecture-iframe')
                if iframe:
                    iframe_src = await iframe.get_attribute('src')
                    print(f"🖼️ Iframe src after click: {iframe_src}")
                    
                    if iframe_src and iframe_src != "about:blank":
                        print("✅ Iframe src was updated")
                        
                        # Check if iframe actually loads content
                        try:
                            await page.wait_for_load_state('networkidle', timeout=5000)
                            print("✅ Network activity settled after iframe update")
                        except:
                            print("⚠️ Network activity did not settle - iframe may not be loading")
                    else:
                        self.results["issues_found"].append("Iframe src was not updated after file click")
                else:
                    self.results["issues_found"].append("Architecture iframe not found")
                    
            else:
                self.results["issues_found"].append("No file items found to test clicking")
                
        except PlaywrightTimeoutError:
            self.results["issues_found"].append("File items not found within timeout")

    async def _test_iframe_functionality(self, page):
        """Test if the iframe properly loads and displays content."""
        print("🖼️ Testing iframe functionality...")
        
        try:
            iframe = await page.query_selector('#architecture-iframe')
            if iframe:
                iframe_src = await iframe.get_attribute('src')
                print(f"🔗 Current iframe src: {iframe_src}")
                
                if iframe_src and iframe_src != "about:blank":
                    # Test if we can access iframe content
                    try:
                        iframe_content = await page.frame_locator('#architecture-iframe').locator('body').first.wait_for(timeout=5000)
                        if iframe_content:
                            print("✅ Iframe content is accessible")
                        else:
                            self.results["issues_found"].append("Iframe content is not accessible")
                    except:
                        print("⚠️ Could not access iframe content - may be cross-origin or not loaded")
                        
                    # Check iframe dimensions
                    iframe_box = await iframe.bounding_box()
                    if iframe_box:
                        print(f"📏 Iframe dimensions: {iframe_box['width']}x{iframe_box['height']}")
                        if iframe_box['width'] < 100 or iframe_box['height'] < 100:
                            self.results["issues_found"].append("Iframe dimensions are too small")
                    else:
                        self.results["issues_found"].append("Could not get iframe bounding box")
                        
                else:
                    print("ℹ️ Iframe has no source set or is blank")
                    
            else:
                self.results["issues_found"].append("Architecture iframe element not found")
                
        except Exception as e:
            self.results["issues_found"].append(f"Error testing iframe: {str(e)}")

    async def _analyze_dom_structure(self, page):
        """Analyze the DOM structure for potential issues."""
        print("🔍 Analyzing DOM structure...")
        
        try:
            # Check architecture container structure
            arch_container = await page.query_selector('.architecture-container')
            if arch_container:
                print("✅ Architecture container found")
                
                # Check layout structure
                arch_layout = await page.query_selector('.architecture-layout')
                if arch_layout:
                    print("✅ Architecture layout found")
                    
                    # Get CSS properties
                    layout_styles = await arch_layout.evaluate("el => getComputedStyle(el)")
                    if layout_styles:
                        display = layout_styles.get('display', '')
                        grid_template_columns = layout_styles.get('gridTemplateColumns', '')
                        print(f"🎨 Layout display: {display}")
                        print(f"🎨 Grid template columns: {grid_template_columns}")
                        
                else:
                    self.results["issues_found"].append("Architecture layout container not found")
                    
                # Check file list and viewer containers
                file_list = await page.query_selector('.file-list')
                file_viewer = await page.query_selector('.file-viewer')
                
                if file_list and file_viewer:
                    print("✅ Both file list and viewer containers found")
                else:
                    if not file_list:
                        self.results["issues_found"].append("File list container not found")
                    if not file_viewer:
                        self.results["issues_found"].append("File viewer container not found")
                        
            else:
                self.results["issues_found"].append("Architecture container not found")
                
            # Check for JavaScript errors in console
            if hasattr(self, '_console_logs'):
                error_logs = [log for log in self._console_logs if 'error' in log.lower()]
                if error_logs:
                    self.results["issues_found"].extend([f"Console error: {log}" for log in error_logs])
                    
        except Exception as e:
            self.results["issues_found"].append(f"Error analyzing DOM: {str(e)}")

    def _handle_console(self, msg):
        """Handle console messages from the browser."""
        if not hasattr(self, '_console_logs'):
            self._console_logs = []
        
        log_entry = f"[{msg.type}] {msg.text}"
        self._console_logs.append(log_entry)
        
        # Print important console messages
        if msg.type in ['error', 'warning'] or 'loadArchitecture' in msg.text:
            print(f"🖥️ Console {msg.type}: {msg.text}")

    def _handle_request(self, request):
        """Handle network requests."""
        if '/architecture/' in request.url:
            print(f"🌐 Request: {request.method} {request.url}")

    def _handle_response(self, response):
        """Handle network responses."""
        if '/architecture/' in response.url:
            print(f"🌐 Response: {response.status} {response.url}")
            if response.status >= 400:
                self.results["issues_found"].append(f"API error: {response.status} for {response.url}")

    def _generate_report(self):
        """Generate a comprehensive debug report."""
        print("\n" + "="*60)
        print("🔍 ARCHITECTURE TAB DEBUG REPORT")
        print("="*60)
        
        print(f"\n📅 Test Date: {self.results['test_timestamp']}")
        
        print(f"\n❌ Issues Found ({len(self.results['issues_found'])}):")
        if self.results['issues_found']:
            for i, issue in enumerate(self.results['issues_found'], 1):
                print(f"   {i}. {issue}")
        else:
            print("   ✅ No issues found!")
            
        # Generate recommendations
        self._generate_recommendations()
        
        print(f"\n💡 Recommendations ({len(self.results['recommendations'])}):")
        for i, rec in enumerate(self.results['recommendations'], 1):
            print(f"   {i}. {rec}")
            
        # Save detailed report to file
        report_file = Path(__file__).parent / "architecture_debug_report.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📄 Detailed report saved to: {report_file}")

    def _generate_recommendations(self):
        """Generate recommendations based on found issues."""
        issues = self.results['issues_found']
        recommendations = []
        
        if any("download" in issue.lower() for issue in issues):
            recommendations.append("Check file click event handlers - they may be using window.location.href instead of iframe.src")
            recommendations.append("Verify the selectArchitectureFile function is properly updating the iframe")
            
        if any("iframe" in issue.lower() for issue in issues):
            recommendations.append("Check iframe src URL construction and API endpoint accessibility")
            recommendations.append("Verify Content-Security-Policy allows iframe loading of local content")
            
        if any("loading" in issue.lower() for issue in issues):
            recommendations.append("Check API endpoint responsiveness and data format")
            recommendations.append("Add better error handling for failed API calls")
            
        if any("not found" in issue.lower() for issue in issues):
            recommendations.append("Check DOM element IDs and class names match between HTML and JavaScript")
            recommendations.append("Verify tab initialization and event binding is working correctly")
            
        if not issues:
            recommendations.append("Architecture tab appears to be working correctly!")
            recommendations.append("If users still report issues, check for browser-specific problems or race conditions")
            
        self.results['recommendations'] = recommendations

async def main():
    """Main entry point."""
    debugger = ArchitectureTabDebugger()
    await debugger.run_debug_session()

if __name__ == "__main__":
    print("🚀 Architecture Tab Debugger Starting...")
    print("   Dashboard URL: http://localhost:8000/professional-dashboard.html")
    print("   API Base: http://localhost:8420/api/v1")
    print("   This will open a browser window to debug the issues\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Debug session interrupted by user")
    except Exception as e:
        print(f"\n❌ Debug session failed: {e}")