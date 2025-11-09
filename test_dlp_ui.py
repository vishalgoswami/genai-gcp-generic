#!/usr/bin/env python3
"""
Test DLP UI Display
Quick test to verify DLP information is properly displayed in the Streamlit UI
"""

import os
import sys
import asyncio

# Add basic-agent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'basic-agent'))

from agent import FriendlyAgentRunner
from safety_config import SafetyConfig, SafetyMode
from dlp_scanner import DLPMode

async def test_dlp_ui_data():
    """Test that DLP scanner returns the expected data structure for UI display"""
    
    print("=" * 80)
    print("Testing DLP UI Data Structure")
    print("=" * 80)
    
    # Test messages with different info types
    test_cases = [
        {
            "name": "INSPECT_ONLY Mode",
            "message": "Hi, my email is john.doe@example.com and phone is 555-123-4567",
            "mode": "inspect_only",
            "method": "masking"
        },
        {
            "name": "DEIDENTIFY Mode",
            "message": "Contact me at jane@company.com or call 555-987-6543",
            "mode": "deidentify",
            "method": "masking"
        },
        {
            "name": "REDACT Mode",
            "message": "I live at 123 Main Street, New York, NY and my email is test@example.com",
            "mode": "redact",
            "method": "redaction"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n{'=' * 80}")
        print(f"Test Case: {test_case['name']}")
        print(f"{'=' * 80}")
        print(f"Original Message: {test_case['message']}")
        print(f"DLP Mode: {test_case['mode']}")
        print(f"DLP Method: {test_case['method']}")
        print()
        
        # Create config with DLP enabled
        config = SafetyConfig(
            mode=SafetyMode.VERTEX_AI_ONLY,
            enable_logging=True,
            fail_open=True,
            dlp_enabled=True,
            dlp_mode=test_case['mode'],
            dlp_method=test_case['method']
        )
        
        # Create agent runner
        runner = FriendlyAgentRunner(safety_config=config)
        
        # Initialize
        init_success = await runner.initialize()
        if not init_success:
            print("❌ Failed to initialize agent")
            continue
        
        # Send test message
        try:
            response, safety_info = await runner.send_message(test_case['message'])
            
            # Display UI data structure
            print("UI Data Structure:")
            print("-" * 80)
            
            # Safety info that would be stored in message
            if safety_info.dlp_prompt_result:
                dlp_result = safety_info.dlp_prompt_result
                
                # Data for UI display
                ui_data = {
                    "dlp_enabled": safety_info.dlp_enabled,
                    "dlp_mode": config.dlp_mode,
                    "dlp_findings": len(dlp_result.findings) if dlp_result.has_findings else 0,
                    "dlp_summary": dlp_result.get_summary(),
                    "dlp_info_types": dlp_result.info_type_summary if dlp_result.has_findings else None,
                    "dlp_processed_text": dlp_result.processed_text,
                    "original_text": test_case['message']
                }
                
                print(f"✅ DLP Enabled: {ui_data['dlp_enabled']}")
                print(f"✅ DLP Mode: {ui_data['dlp_mode']}")
                print(f"✅ Findings Count: {ui_data['dlp_findings']}")
                print(f"✅ Summary: {ui_data['dlp_summary']}")
                print(f"✅ Info Types: {ui_data['dlp_info_types']}")
                print(f"\n📝 Original Text:")
                print(f"   {ui_data['original_text']}")
                print(f"\n📝 Processed Text (sent to LLM):")
                print(f"   {ui_data['dlp_processed_text']}")
                
                # Verify the processed text is different from original (except for INSPECT_ONLY)
                if test_case['mode'] == 'inspect_only':
                    assert ui_data['dlp_processed_text'] == ui_data['original_text'], \
                        "INSPECT_ONLY should not modify text"
                    print("\n✅ INSPECT_ONLY: Text unchanged (correct)")
                else:
                    assert ui_data['dlp_processed_text'] != ui_data['original_text'], \
                        f"{test_case['mode'].upper()} should modify text"
                    print(f"\n✅ {test_case['mode'].upper()}: Text modified (correct)")
                
                # UI Display Format
                print("\n" + "=" * 80)
                print("How this would appear in Streamlit UI:")
                print("=" * 80)
                print(f"🔍 DLP Scan Results:")
                print(f"   {ui_data['dlp_summary']}")
                if ui_data['dlp_info_types']:
                    print(f"   Detected: {ui_data['dlp_info_types']}")
                
                if ui_data['dlp_processed_text'] != ui_data['original_text']:
                    print(f"\n📤 Message sent to LLM:")
                    print(f"   {ui_data['dlp_processed_text']}")
                
            else:
                print("❌ No DLP result found")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("✅ All DLP UI tests completed!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_dlp_ui_data())
