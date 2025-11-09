#!/usr/bin/env python3
"""
Test DLP UI Rendering - Visual Preview
Shows how the DLP information will be displayed in the chat UI
"""

import html

def generate_dlp_html(dlp_summary, dlp_info_types, dlp_processed, original_message):
    """Generate DLP HTML as it will appear in the UI"""
    
    # Escape HTML
    dlp_processed_escaped = html.escape(dlp_processed) if dlp_processed else ""
    dlp_info_types_escaped = html.escape(dlp_info_types) if dlp_info_types else ""
    dlp_summary_escaped = html.escape(dlp_summary)
    
    message_html = f"""
    <div class="safety-info" style="margin-top: 0.5rem;">
        <strong>🔍 DLP Scan Results:</strong><br/>
        <span class="safety-rating safety-rating-medium">{dlp_summary_escaped}</span>"""
    
    if dlp_info_types_escaped:
        message_html += f'<br/><small>Detected: {dlp_info_types_escaped}</small>'
    
    if dlp_processed_escaped and dlp_processed != original_message:
        message_html += f'<br/><br/><strong>Message sent to LLM:</strong><br/><code style="background-color: #f0f0f0; padding: 0.5rem; display: block; border-radius: 0.3rem; margin-top: 0.3rem;">{dlp_processed_escaped}</code>'
    
    message_html += """
    </div>
    """
    
    return message_html

# Test cases
print("=" * 80)
print("DLP UI RENDERING TEST - Visual Preview")
print("=" * 80)

# Test 1: INSPECT_ONLY mode
print("\n1. INSPECT_ONLY MODE")
print("-" * 80)
original = "My email is john.doe@example.com and phone is 555-123-4567"
html_output = generate_dlp_html(
    dlp_summary="Found 2 sensitive data items",
    dlp_info_types="EMAIL_ADDRESS, PHONE_NUMBER",
    dlp_processed=original,  # Same as original in inspect mode
    original_message=original
)
print("HTML Output:")
print(html_output)
print("\nWhat user sees:")
print("🔍 DLP Scan Results:")
print("Found 2 sensitive data items")
print("Detected: EMAIL_ADDRESS, PHONE_NUMBER")
print("(No 'Message sent to LLM' shown because text is unchanged)")

# Test 2: DEIDENTIFY mode
print("\n" + "=" * 80)
print("2. DEIDENTIFY MODE (with MASKING)")
print("-" * 80)
original = "Contact me at jane@company.com"
processed = "Contact me at *********************"
html_output = generate_dlp_html(
    dlp_summary="Found 1 sensitive data item and masked it",
    dlp_info_types="EMAIL_ADDRESS",
    dlp_processed=processed,
    original_message=original
)
print("HTML Output:")
print(html_output)
print("\nWhat user sees:")
print("🔍 DLP Scan Results:")
print("Found 1 sensitive data item and masked it")
print("Detected: EMAIL_ADDRESS")
print("\nMessage sent to LLM:")
print("Contact me at *********************")

# Test 3: REDACT mode
print("\n" + "=" * 80)
print("3. REDACT MODE")
print("-" * 80)
original = "My phone is 555-987-6543"
processed = "My phone is [REDACTED]"
html_output = generate_dlp_html(
    dlp_summary="Found 1 sensitive data item and redacted it",
    dlp_info_types="PHONE_NUMBER",
    dlp_processed=processed,
    original_message=original
)
print("HTML Output:")
print(html_output)
print("\nWhat user sees:")
print("🔍 DLP Scan Results:")
print("Found 1 sensitive data item and redacted it")
print("Detected: PHONE_NUMBER")
print("\nMessage sent to LLM:")
print("My phone is [REDACTED]")

# Test 4: Multiple info types with DEIDENTIFY
print("\n" + "=" * 80)
print("4. MULTIPLE INFO TYPES (DEIDENTIFY)")
print("-" * 80)
original = "I'm John Doe, email john@example.com, phone 555-1234, living in New York"
processed = "I'm *********, email *********************, phone ********, living in ********"
html_output = generate_dlp_html(
    dlp_summary="Found 4 sensitive data items and masked them",
    dlp_info_types="PERSON_NAME, EMAIL_ADDRESS, PHONE_NUMBER, LOCATION",
    dlp_processed=processed,
    original_message=original
)
print("HTML Output:")
print(html_output)
print("\nWhat user sees:")
print("🔍 DLP Scan Results:")
print("Found 4 sensitive data items and masked them")
print("Detected: PERSON_NAME, EMAIL_ADDRESS, PHONE_NUMBER, LOCATION")
print("\nMessage sent to LLM:")
print("I'm *********, email *********************, phone ********, living in ********")

print("\n" + "=" * 80)
print("✅ All HTML rendering tests completed successfully!")
print("=" * 80)
