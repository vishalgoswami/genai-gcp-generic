# 🔍 Data Privacy (DLP) Guide

Complete guide to using Google Cloud Data Loss Prevention (DLP) with the ADK Agent.

## Overview

The DLP integration automatically detects and protects sensitive information in user messages before sending to the LLM. This ensures PII (Personally Identifiable Information) and other sensitive data is handled according to your privacy requirements.

## What Does DLP Protect?

The scanner detects 18 types of sensitive information by default:

### Personal Identifiers
- **EMAIL_ADDRESS** - Email addresses
- **PHONE_NUMBER** - Phone numbers (various formats)
- **PERSON_NAME** - Full names
- **DATE_OF_BIRTH** - Birth dates

### Financial Information
- **CREDIT_CARD_NUMBER** - Credit/debit card numbers
- **IBAN_CODE** - International bank account numbers
- **SWIFT_CODE** - Bank routing codes
- **US_BANK_ROUTING_MICR** - US bank routing numbers

### Government IDs
- **US_SOCIAL_SECURITY_NUMBER** - SSN
- **US_PASSPORT** - Passport numbers
- **US_DRIVER_LICENSE_NUMBER** - Driver's licenses
- **US_DEA_NUMBER** - DEA numbers

### Healthcare
- **US_HEALTHCARE_NPI** - National Provider Identifiers
- **MEDICAL_RECORD_NUMBER** - Medical records
- **FDA_CODE** - FDA registration codes

### Technical
- **IP_ADDRESS** - IPv4/IPv6 addresses
- **MAC_ADDRESS** - Hardware addresses
- **LOCATION** - Geographic locations

## DLP Modes

### 1. INSPECT_ONLY (Default for Testing)

**What it does:**
- Scans message for sensitive data
- Reports findings (count, types detected)
- Does NOT modify the message

**Use when:**
- Monitoring compliance
- Understanding what sensitive data users are sharing
- Testing without data modification
- Generating audit logs

**Example:**
```
Input:  "My email is john@example.com"
Output: "My email is john@example.com"  (unchanged)
Report: "Found 1 EMAIL_ADDRESS"
```

### 2. DEIDENTIFY

**What it does:**
- Replaces sensitive data with tokens or masks
- Maintains message structure and context
- Two methods available:
  - **Masking**: Replace with asterisks (`***`)
  - **Tokenization**: Crypto-based reversible tokens

**Use when:**
- Production deployments
- Need to maintain message context
- Reversibility is important (tokenization)
- Balancing privacy with functionality

**Example (Masking):**
```
Input:  "My email is john@example.com and phone is 555-1234"
Output: "My email is *** and phone is ***"
```

**Example (Tokenization):**
```
Input:  "Contact me at john@example.com"
Output: "Contact me at TOKEN(52):AQHGh7..."
```

### 3. REDACT

**What it does:**
- Completely removes sensitive data
- Replaces with `[REDACTED]` placeholder
- Permanent removal (not reversible)

**Use when:**
- Maximum privacy protection required
- Compliance with strict regulations
- No need to preserve original data
- Audit requirements demand removal

**Example:**
```
Input:  "My SSN is 123-45-6789 and email john@example.com"
Output: "My SSN is [REDACTED] and email [REDACTED]"
```

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# DLP Configuration
DLP_ENABLED=true                    # Enable/disable DLP scanner
DLP_MODE=inspect_only               # Options: inspect_only, deidentify, redact
DLP_METHOD=masking                  # Options: masking, tokenization (for deidentify)
DLP_INFO_TYPES=EMAIL_ADDRESS,PHONE_NUMBER  # Optional: Specific info types only
```

### Programmatic Configuration

```python
from safety_config import SafetyConfig
from agent import FriendlyAgentRunner

# Configure with DLP
config = SafetyConfig(
    dlp_enabled=True,
    dlp_mode="deidentify",      # inspect_only | deidentify | redact
    dlp_method="masking",       # masking | tokenization
    dlp_info_types=None         # None = all default types
)

# Create agent with config
runner = FriendlyAgentRunner(safety_config=config)
```

## Streamlit UI Integration

The Streamlit UI provides interactive DLP controls in the sidebar:

### Location
Navigate to: **Sidebar → 🔍 Data Privacy (DLP)**

### Controls

1. **Enable DLP Scanner** (Checkbox)
   - Toggle DLP on/off
   - Default: Off

2. **Processing Mode** (Radio Buttons)
   - Inspect Only - Detection without modification
   - Deidentify - Replace with tokens/masks
   - Redact - Remove completely

3. **Deidentification Method** (Radio - appears when Deidentify selected)
   - Masking - Replace with asterisks
   - Tokenization - Crypto tokens

4. **Detection Settings** (Expandable)
   - View list of default info types
   - Shows what will be detected

### UI Indicators

- **🔍 Blue Info Box** - Inspect only mode (detection without changes)
- **🔒 Yellow Warning Box** - Deidentify mode active
- **🚫 Red Error Box** - Redact mode (maximum protection)

## Testing

### With Streamlit UI

```bash
cd frontend/streamlit
streamlit run app.py
```

1. Enable "Use Local Agent with Safety Controls"
2. Open "🔍 Data Privacy (DLP)" expander
3. Check "Enable DLP Scanner"
4. Select your mode
5. Send test messages with sensitive data

### Without UI (Default: Inspect Only)

```bash
cd basic-agent

# Set environment variables
export DLP_ENABLED=true
export DLP_MODE=inspect_only

# Run test
python test_agent.py
```

When testing without UI, DLP defaults to `inspect_only` mode if enabled.

### Test Messages

Try these test messages to see DLP in action:

```
"My email is john.doe@example.com"
"Call me at (555) 123-4567"
"My SSN is 123-45-6789"
"Credit card: 4111 1111 1111 1111"
"I live at 123 Main St, San Francisco, CA"
"Contact John Smith at john@company.com or 555-1234"
```

## Code Examples

### Basic Usage

```python
import asyncio
from agent import FriendlyAgentRunner
from safety_config import SafetyConfig

async def main():
    # Create config with DLP
    config = SafetyConfig(
        dlp_enabled=True,
        dlp_mode="deidentify",
        dlp_method="masking"
    )
    
    # Initialize agent
    runner = FriendlyAgentRunner(safety_config=config)
    await runner.initialize()
    
    # Send message with sensitive data
    message = "My email is john@example.com and phone is 555-1234"
    response, safety_info = await runner.send_message(message)
    
    # Check DLP results
    if safety_info.dlp_prompt_result:
        dlp = safety_info.dlp_prompt_result
        if dlp.has_findings:
            print(f"\n🔍 DLP Scan Results:")
            print(f"   {dlp.get_summary()}")
            print(f"   Detected: {dlp.info_type_summary}")
            print(f"\n   Original: {message}")
            print(f"   Processed: {dlp.processed_text}")
    
    print(f"\nResponse: {response}")

asyncio.run(main())
```

### Inspect Only Mode

```python
config = SafetyConfig(
    dlp_enabled=True,
    dlp_mode="inspect_only"  # Just detect, don't modify
)

runner = FriendlyAgentRunner(safety_config=config)
await runner.initialize()

message = "Email me at sensitive@company.com"
response, safety_info = await runner.send_message(message)

# Message sent unchanged, but we have detection info
dlp_result = safety_info.dlp_prompt_result
print(f"Findings: {len(dlp_result.findings)}")
print(f"Types: {dlp_result.info_type_summary}")
# Message sent to LLM: "Email me at sensitive@company.com" (unchanged)
```

### Deidentify with Masking

```python
config = SafetyConfig(
    dlp_enabled=True,
    dlp_mode="deidentify",
    dlp_method="masking"  # Replace with ***
)

runner = FriendlyAgentRunner(safety_config=config)
await runner.initialize()

message = "Contact John at john@company.com or call 555-1234"
response, safety_info = await runner.send_message(message)

# Message sent to LLM: "Contact *** at *** or call ***"
```

### Redact Mode

```python
config = SafetyConfig(
    dlp_enabled=True,
    dlp_mode="redact"  # Remove completely
)

runner = FriendlyAgentRunner(safety_config=config)
await runner.initialize()

message = "My SSN is 123-45-6789"
response, safety_info = await runner.send_message(message)

# Message sent to LLM: "My SSN is [REDACTED]"
```

### Custom Info Types

```python
config = SafetyConfig(
    dlp_enabled=True,
    dlp_mode="deidentify",
    dlp_method="masking",
    dlp_info_types=["EMAIL_ADDRESS", "PHONE_NUMBER"]  # Only these two
)

# Will only detect emails and phone numbers, ignoring other types
```

## Architecture

### Message Flow with DLP

```
User Input
    ↓
[DLP Scanner]  ← Inspect/Deidentify/Redact
    ↓
Processed Message
    ↓
[Model Armor] (if enabled)
    ↓
[Vertex AI Safety]
    ↓
LLM (Gemini)
    ↓
Response
```

### DLP Processing Pipeline

```python
# 1. Original message
original = "My email is john@example.com"

# 2. DLP inspection
findings = dlp_scanner.inspect_text(original)
# → Found: 1 EMAIL_ADDRESS at byte range 12-29

# 3. Processing (mode-dependent)
if mode == INSPECT_ONLY:
    processed = original  # No change
elif mode == DEIDENTIFY:
    if method == MASKING:
        processed = "My email is ***"
    elif method == TOKENIZATION:
        processed = "My email is TOKEN(52):AQHGh7..."
elif mode == REDACT:
    processed = "My email is [REDACTED]"

# 4. Send to LLM
send_to_llm(processed)
```

## Requirements

### GCP API

Enable the DLP API in your project:

```bash
gcloud services enable dlp.googleapis.com
```

### Python Package

Install the DLP client library:

```bash
pip install google-cloud-dlp>=3.12.0
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

### Authentication

DLP uses Application Default Credentials (ADC):

```bash
gcloud auth application-default login
```

## Error Handling

DLP is configured to **fail-open** by default:

```python
# If DLP scanner fails:
# 1. Log the error
# 2. Continue with original message
# 3. Don't block the conversation

try:
    dlp_result = dlp_scanner.process_text(message)
    message = dlp_result.processed_text
except Exception as e:
    logging.warning(f"DLP scan error: {e}")
    # Continue with original message (fail-open)
```

This ensures DLP errors don't break your application.

## Best Practices

### 1. Choose the Right Mode

- **Development/Testing**: `inspect_only` - understand what's being shared
- **Production**: `deidentify` with `masking` - balance privacy and context
- **High Security**: `redact` - maximum protection
- **Compliance**: `deidentify` with `tokenization` - reversible for audit

### 2. Monitor DLP Findings

```python
# Log DLP detections for compliance
if dlp_result.has_findings:
    logger.info(f"DLP detected {len(dlp_result.findings)} items")
    logger.info(f"Types: {dlp_result.info_type_summary}")
```

### 3. Inform Users

When using deidentify or redact modes, inform users that sensitive data will be protected.

### 4. Test Thoroughly

Use the test messages above to verify DLP works as expected in each mode.

### 5. Combine with Safety

DLP works alongside Vertex AI and Model Armor safety systems:

```python
config = SafetyConfig(
    # Safety
    mode=SafetyMode.BOTH,  # Vertex AI + Model Armor
    
    # DLP
    dlp_enabled=True,
    dlp_mode="deidentify",
    dlp_method="masking"
)
# Maximum protection: DLP + Model Armor + Vertex AI
```

## Troubleshooting

### DLP Not Working

1. **Check API is enabled:**
   ```bash
   gcloud services list --enabled | grep dlp
   ```

2. **Verify authentication:**
   ```bash
   gcloud auth application-default login
   ```

3. **Check environment variables:**
   ```bash
   echo $DLP_ENABLED
   echo $DLP_MODE
   ```

4. **Check logs:**
   - Look for "✓ DLP scanner initialized" on startup
   - Look for "⚠️ DLP initialization failed" errors

### No Findings Detected

If DLP doesn't detect expected sensitive data:

1. **Verify info types** - Some patterns might not match default types
2. **Check format** - "5551234" vs "(555) 123-4567"
3. **Likelihood threshold** - Very low confidence detections are filtered

### Import Errors

If you see import errors:

```bash
pip install google-cloud-dlp>=3.12.0
```

## Reference

- **DLP API Documentation**: https://cloud.google.com/dlp/docs
- **Python DLP Samples**: https://github.com/GoogleCloudPlatform/python-docs-samples/tree/main/dlp/snippets
- **Info Types Reference**: https://cloud.google.com/dlp/docs/infotypes-reference
- **DLP Pricing**: https://cloud.google.com/dlp/pricing

## Summary

The DLP integration provides flexible, production-ready sensitive data protection:

✅ **18 default info types** - Covers most common PII
✅ **3 processing modes** - Inspect, deidentify, or redact
✅ **2 deidentification methods** - Masking or tokenization
✅ **Fail-open design** - Errors don't block conversations
✅ **UI integration** - Easy configuration in Streamlit
✅ **Environment config** - Works with or without UI
✅ **Official GCP API** - Production-grade detection

Use DLP to ensure your AI agent handles sensitive information responsibly and in compliance with privacy regulations.
