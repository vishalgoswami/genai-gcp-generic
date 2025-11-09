# DLP UI Demo Guide

Quick guide to see the DLP UI enhancements in action.

## Prerequisites

1. GCP project with DLP API enabled
2. Application Default Credentials configured
3. Streamlit app dependencies installed

## Quick Start

### 1. Start the Streamlit App

```bash
cd /Users/vishal/genai/1/frontend/streamlit
streamlit run app.py
```

### 2. Configure DLP in Sidebar

In the left sidebar, find the **"🔍 Data Privacy (DLP)"** section:

1. Enable DLP: Toggle the checkbox
2. Select DLP Mode:
   - **INSPECT_ONLY** - Detect only, don't modify
   - **DEIDENTIFY** - Mask/tokenize sensitive data
   - **REDACT** - Remove sensitive data completely
3. Select Method (for DEIDENTIFY mode):
   - **MASKING** - Replace with asterisks (***)
   - **TOKENIZATION** - Crypto-reversible tokens

### 3. Test Messages

Try these messages to see different behaviors:

#### Test 1: INSPECT_ONLY Mode
```
Hi, my email is john.doe@example.com and phone is 555-123-4567
```

**Expected Result:**
- Message unchanged
- DLP bubble shows: 4 findings (PERSON_NAME, EMAIL_ADDRESS, PHONE_NUMBER)
- No "Message sent to LLM" section (text unchanged)

#### Test 2: DEIDENTIFY Mode
```
Contact me at jane@company.com or call 555-987-6543
```

**Expected Result:**
- Original message visible
- DLP bubble shows: 3 findings
- "Message sent to LLM" shows: `Contact me at ******************** or call ************`

#### Test 3: REDACT Mode
```
I live at 123 Main Street, New York, NY
```

**Expected Result:**
- Original message visible
- DLP bubble shows: 4-5 findings (LOCATION, STREET_ADDRESS, US_STATE)
- "Message sent to LLM" shows: `I live at [REDACTED][REDACTED][REDACTED][REDACTED]`

#### Test 4: No Sensitive Data
```
What's the weather like today?
```

**Expected Result:**
- Normal message display
- No DLP bubble (no findings)

## What to Look For

### ✅ Success Indicators

1. **DLP Bubble Appears**: Only on user messages with findings
2. **Findings Count**: Matches expected sensitive data in message
3. **Info Types List**: Shows detected types (EMAIL_ADDRESS, PHONE_NUMBER, etc.)
4. **Processed Text**: 
   - INSPECT_ONLY: Not shown (text unchanged)
   - DEIDENTIFY: Shows asterisks (***)
   - REDACT: Shows [REDACTED] markers
5. **Clean UI**: No bubble on safe messages

### ❌ Troubleshooting

**DLP bubble doesn't appear:**
- Check DLP is enabled in sidebar
- Verify message contains sensitive data (email, phone, etc.)
- Check browser console for errors

**Text not modified (DEIDENTIFY/REDACT):**
- Verify mode is not INSPECT_ONLY
- Check DLP API is enabled in GCP
- Look for API errors in terminal/logs

**"Local agent not available" error:**
- Ensure you're in the correct directory
- Check Python path includes `basic-agent` folder
- Verify all dependencies installed (`pip install -r requirements.txt`)

## UI Components

### User Message Structure
```
┌────────────────────────────────────┐
│ 👤 User              [timestamp]   │  ← Header
├────────────────────────────────────┤
│ [Your original message]            │  ← Message content
│                                    │
│ ┌────────────────────────────────┐ │
│ │ 🔍 DLP Scan Results:           │ │  ← DLP info bubble
│ │ ⚠️ Found X instance(s)         │ │     (only if findings)
│ │ Detected: [types]              │ │
│ │                                │ │
│ │ Message sent to LLM:           │ │  ← Processed text
│ │ [processed text]               │ │     (only if modified)
│ └────────────────────────────────┘ │
└────────────────────────────────────┘
```

### Assistant Response
```
┌────────────────────────────────────┐
│ 🤖 Assistant         [timestamp]   │  ← Header
├────────────────────────────────────┤
│ [AI response based on processed    │  ← Response content
│  message, not original if DLP      │
│  modified it]                      │
└────────────────────────────────────┘
```

## Testing Checklist

Use this checklist to verify all features work:

- [ ] DLP toggle enables/disables scanning
- [ ] INSPECT_ONLY mode shows findings without modification
- [ ] DEIDENTIFY mode masks sensitive data with ***
- [ ] REDACT mode replaces sensitive data with [REDACTED]
- [ ] Info types are correctly identified
- [ ] Findings count matches detected items
- [ ] Processed text differs from original (when it should)
- [ ] No DLP bubble on messages without sensitive data
- [ ] DLP bubble only appears on user messages (not assistant)
- [ ] Chat history persists DLP info across refreshes

## Performance Notes

- DLP API calls add ~500ms-2s to message processing
- UI rendering has minimal overhead (< 10ms)
- No impact on messages without sensitive data
- DLP bubble only renders when findings exist

## Privacy Considerations

**What users see:**
- Their original message (always visible)
- What sensitive data was detected
- What text was sent to the LLM (if modified)

**What LLM sees:**
- INSPECT_ONLY: Original message
- DEIDENTIFY: Masked message (e.g., `***@***.com`)
- REDACT: Redacted message (e.g., `[REDACTED]`)

**What is logged:**
- Both original and processed messages (if logging enabled)
- DLP findings and info types
- Safety ratings and blocks

## Next Steps

After verifying the UI works:

1. **Customize info types**: Edit `DEFAULT_INFO_TYPES` in `dlp_scanner.py`
2. **Adjust thresholds**: Modify likelihood thresholds in DLP settings
3. **Add custom templates**: Create custom deidentification templates
4. **Export DLP logs**: Add functionality to download DLP scan history

## Support

For issues or questions:
- Check `DLP_GUIDE.md` for detailed documentation
- Review `DLP_TEST_RESULTS.md` for expected behaviors
- See `DLP_UI_ENHANCEMENT.md` for implementation details
- Look at `DLP_UI_EXAMPLES.md` for visual examples

## Quick Reference

| Mode | Text Modified? | UI Shows |
|------|---------------|----------|
| INSPECT_ONLY | ❌ No | Findings only |
| DEIDENTIFY | ✅ Yes | Findings + masked text |
| REDACT | ✅ Yes | Findings + redacted text |
| DISABLED | ❌ No | Nothing |
