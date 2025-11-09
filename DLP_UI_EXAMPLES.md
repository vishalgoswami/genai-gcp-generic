# DLP UI Display Examples

This document shows how DLP information appears in the Streamlit chat UI for different modes and scenarios.

## Example 1: INSPECT_ONLY Mode

### User Message
```
Hi, my email is john.doe@example.com and phone is 555-123-4567
```

### UI Display
```
┌─────────────────────────────────────────────────────────────────┐
│ 👤 User                                         09:15:23        │
├─────────────────────────────────────────────────────────────────┤
│ Hi, my email is john.doe@example.com and phone is 555-123-4567 │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 🔍 DLP Scan Results:                                        │ │
│ │ ⚠️ Found 4 sensitive data instance(s):                      │ │
│ │   • PERSON_NAME: 2 instance(s)                              │ │
│ │   • EMAIL_ADDRESS: 1 instance(s)                            │ │
│ │   • PHONE_NUMBER: 1 instance(s)                             │ │
│ │ Detected: EMAIL_ADDRESS, PERSON_NAME, PHONE_NUMBER          │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

**What the user sees:**
- Original message unchanged
- Clear indication of what sensitive data was detected
- Breakdown by info type with counts
- No modification to the text sent to LLM

---

## Example 2: DEIDENTIFY Mode

### User Message
```
Contact me at jane@company.com or call 555-987-6543
```

### UI Display
```
┌─────────────────────────────────────────────────────────────────┐
│ 👤 User                                         09:16:45        │
├─────────────────────────────────────────────────────────────────┤
│ Contact me at jane@company.com or call 555-987-6543            │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 🔍 DLP Scan Results:                                        │ │
│ │ ⚠️ Found 3 sensitive data instance(s):                      │ │
│ │   • PERSON_NAME: 1 instance(s)                              │ │
│ │   • EMAIL_ADDRESS: 1 instance(s)                            │ │
│ │   • PHONE_NUMBER: 1 instance(s)                             │ │
│ │ ℹ️ Sensitive data has been deidentified                     │ │
│ │ Detected: EMAIL_ADDRESS, PERSON_NAME, PHONE_NUMBER          │ │
│ │                                                             │ │
│ │ Message sent to LLM:                                        │ │
│ │ ┌─────────────────────────────────────────────────────────┐ │ │
│ │ │ Contact me at ******************** or call ************ │ │ │
│ │ └─────────────────────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

**What the user sees:**
- Original message with sensitive data visible
- Detection summary with info types
- **NEW**: Side-by-side comparison showing masked version
- Clear indication that LLM received masked data, not original

---

## Example 3: REDACT Mode

### User Message
```
I live at 123 Main Street, New York, NY and my email is test@example.com
```

### UI Display
```
┌─────────────────────────────────────────────────────────────────┐
│ 👤 User                                         09:18:12        │
├─────────────────────────────────────────────────────────────────┤
│ I live at 123 Main Street, New York, NY and my email is        │
│ test@example.com                                                │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 🔍 DLP Scan Results:                                        │ │
│ │ ⚠️ Found 5 sensitive data instance(s):                      │ │
│ │   • US_STATE: 1 instance(s)                                 │ │
│ │   • LOCATION: 2 instance(s)                                 │ │
│ │   • STREET_ADDRESS: 1 instance(s)                           │ │
│ │   • EMAIL_ADDRESS: 1 instance(s)                            │ │
│ │ ℹ️ Sensitive data has been deidentified                     │ │
│ │ Detected: EMAIL_ADDRESS, LOCATION, STREET_ADDRESS, US_STATE │ │
│ │                                                             │ │
│ │ Message sent to LLM:                                        │ │
│ │ ┌─────────────────────────────────────────────────────────┐ │ │
│ │ │ I live at [REDACTED][REDACTED][REDACTED][REDACTED] and │ │ │
│ │ │ my email is [REDACTED]                                  │ │ │
│ │ └─────────────────────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

**What the user sees:**
- Original message with full address and email
- Detection of multiple overlapping location entities
- **NEW**: Final redacted message showing [REDACTED] markers
- Complete transparency about what LLM actually sees

---

## Example 4: No Sensitive Data (Any Mode)

### User Message
```
What's the weather like today?
```

### UI Display
```
┌─────────────────────────────────────────────────────────────────┐
│ 👤 User                                         09:19:30        │
├─────────────────────────────────────────────────────────────────┤
│ What's the weather like today?                                  │
└─────────────────────────────────────────────────────────────────┘
```

**What the user sees:**
- Normal message display
- No DLP bubble (no sensitive data detected)
- Clean, uncluttered interface for safe messages

---

## Example 5: DLP Disabled

### User Message
```
My email is admin@company.com
```

### UI Display
```
┌─────────────────────────────────────────────────────────────────┐
│ 👤 User                                         09:20:45        │
├─────────────────────────────────────────────────────────────────┤
│ My email is admin@company.com                                   │
└─────────────────────────────────────────────────────────────────┘
```

**What the user sees:**
- Normal message display
- No DLP processing or bubble
- Original message sent directly to LLM

---

## Visual Hierarchy

The DLP info bubble uses visual cues to indicate severity and action:

### Colors (CSS Classes)
- **Blue border** (`safety-info`): Informational, scan results
- **Yellow background** (`safety-rating-medium`): Warning, sensitive data found
- **Gray code block**: Processed text display

### Icons
- 🔍 **DLP Scan Results**: Indicates inspection occurred
- ⚠️ **Found X instance(s)**: Warning about sensitive data
- ℹ️ **Deidentified**: Information about modification
- ✅ **No sensitive data**: All clear

### Layout
1. **Scan Results Header**: Always visible when DLP enabled and findings exist
2. **Summary**: Count and breakdown by info type
3. **Info Types List**: Comma-separated list of detected types
4. **Processed Text**: Only shown if different from original (DEIDENTIFY/REDACT modes)

---

## Comparison: Before vs After

### Before This Enhancement
```
┌─────────────────────────────────────────────────────────────────┐
│ 👤 User                                         09:15:23        │
├─────────────────────────────────────────────────────────────────┤
│ Hi, my email is john.doe@example.com                            │
└─────────────────────────────────────────────────────────────────┘

(User has no idea DLP scanned the message or what was found)
```

### After This Enhancement
```
┌─────────────────────────────────────────────────────────────────┐
│ 👤 User                                         09:15:23        │
├─────────────────────────────────────────────────────────────────┤
│ Hi, my email is john.doe@example.com                            │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 🔍 DLP Scan Results:                                        │ │
│ │ ⚠️ Found 2 sensitive data instance(s):                      │ │
│ │   • EMAIL_ADDRESS: 1 instance(s)                            │ │
│ │   • PERSON_NAME: 1 instance(s)                              │ │
│ │ Detected: EMAIL_ADDRESS, PERSON_NAME                        │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘

(User sees exactly what was detected and how it was handled)
```

---

## Benefits

1. **Transparency**: Users see exactly what sensitive data was detected
2. **Verification**: Users can verify DLP is working correctly
3. **Confidence**: Clear indication of what data LLM receives
4. **Education**: Users learn what types of data are considered sensitive
5. **Control**: Easy to verify mode selection (inspect/deidentify/redact) is working

---

## Technical Implementation

The DLP info bubble is conditionally rendered only when:
1. DLP is enabled (`safety_info.dlp_enabled == True`)
2. Sensitive data was found (`safety_info.dlp_findings > 0`)
3. Message is from user role (`message.role == "user"`)

This ensures minimal UI clutter and only shows relevant information when needed.
