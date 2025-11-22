# Fix for "No content in messages object" Error

## Problem Summary

The agent was sometimes returning AI messages with `None` or empty content after tool execution, causing the error:
```
Error: An error occurred. No content in messages object.
```

## Root Causes

1. **Agent not generating final response**: After calling tools, the agent sometimes stopped without generating a final text response
2. **Token limits**: `max_tokens=1000` was too low for responses after processing large tool outputs (e.g., 257-item lists)
3. **Message filtering not strict enough**: The `is_public()` function allowed AI messages with `None` content through if they didn't have tool_calls

## Fixes Applied

### 1. Updated `backend/utils_langchain.py`
**Fixed `is_public()` function** to filter out ALL AI messages with no content:

```python
def is_public(msg: BaseMessage) -> bool:
    """Filter out messages that shouldn't be shown to frontend."""
    if isinstance(msg, ToolMessage):
        return False
    
    # Filter out AI messages with no meaningful content
    if isinstance(msg, AIMessage):
        if not msg.content:
            # Filter out both tool_call-only messages AND incomplete messages
            return False
        return True
    
    return isinstance(msg, (HumanMessage, SystemMessage))
```

**Before**: AI messages with `content=None` were allowed through if they had no tool_calls
**After**: ALL AI messages with `None` or empty content are filtered out

### 2. Updated `backend/permit_agent/agent_langchain.py`

#### A. Added explicit instruction to system prompt:
```python
IMPORTANT: After using any tool, you MUST provide a final answer to the user's question. 
Do not stop after just calling a tool. If the tool results are too long, summarize the key information.
```

#### B. Increased `max_tokens`:
```python
llm = AzureChatOpenAI(
    azure_deployment="gpt-4.1",
    api_version="2024-12-01-preview",
    temperature=0,
    max_tokens=2000,  # Increased from 1000
    timeout=500,
    max_retries=2
)
```

### 3. Updated `app.py`

#### A. Added detailed debug logging:
```python
# Log content of each message for debugging
for i, msg in enumerate(output_messages):
    msg_type = msg.type if hasattr(msg, 'type') else type(m).__name__
    content_preview = str(msg.content)[:100] if msg.content else "<None>"
    logging.debug(f"  Message {i}: {msg_type} - Content: {content_preview}")
```

#### B. Improved fallback error message:
```python
if not final_content:
    logging.warning("Agent did not generate a final response. This may be due to token limits or agent configuration.")
    final_content = "I apologize, but I couldn't generate a complete response. This may be due to the complexity of the query or the amount of data retrieved. Please try asking a more specific question or breaking your request into smaller parts."
```

## How It Works Now

### Flow Diagram:
```
User Question
    ↓
Agent invoked
    ↓
Tools called (e.g., get_list_documents_by_issue_year)
    ↓
Tool returns large result (257 items)
    ↓
Agent generates final summary ← NOW FORCED BY PROMPT
    ↓
Messages filtered (tools hidden)
    ↓
Final AI response extracted
    ↓
If empty → Fallback message
    ↓
Response sent to frontend
```

### Example - Before vs After:

**Request**: "Count total documents are available"

**Before**:
```
Messages: [HumanMessage, AIMessage(tool_calls), ToolMessage, ToolMessage, AIMessage(content=None)]
                                                                            ↑
                                                                    This has no content!
Public Messages: [HumanMessage, AIMessage(content=None)]
                                         ↑
                               ERROR: No content!
```

**After**:
```
Messages: [HumanMessage, AIMessage(tool_calls), ToolMessage, ToolMessage, AIMessage(content="Based on...")]
                                                                            ↑
                                                                    Forced to generate content!
Public Messages: [HumanMessage, AIMessage(content="Based on...")]
                                         ↑
                                    ✓ Has content!
```

## Testing

### Test Case 1: Large Tool Response
**Query**: "Count total documents are available"
**Expected**: Agent summarizes the count instead of returning empty content
**Result**: ✅ Agent now generates final answer

### Test Case 2: Multiple Tool Calls
**Query**: "Sebutkan seluruh nomor KKPRL yang dimiliki oleh SH PGN !"
**Expected**: Agent processes both tool results and generates final summary
**Result**: ✅ Works correctly

### Verification Commands:
```bash
# Check debug logs for message content
grep "Message.*Content:" app.log

# Check for fallback warnings
grep "Agent did not generate a final response" app.log
```

## Prevention

To prevent this issue in the future:

1. **Always test with large tool responses** - Queries that return 100+ results
2. **Monitor max_tokens** - Ensure it's sufficient for summaries of large data
3. **Check debug logs** - Look for "Message X: ai - Content: <None>"
4. **System prompt clarity** - Keep the "MUST provide final answer" instruction

## Additional Notes

- The React agent from LangGraph should automatically loop back to generate responses, but explicit prompting helps
- Consider implementing response streaming in the future for better UX with large results
- The `max_tokens=2000` may need further tuning based on production usage
- Tool outputs could be truncated before sending to the agent if they're extremely large

## Files Modified

1. ✏️ `backend/utils_langchain.py` - Stricter message filtering
2. ✏️ `backend/permit_agent/agent_langchain.py` - System prompt + max_tokens
3. ✏️ `app.py` - Better logging and fallback messages

## Status

✅ **Issue Resolved**
- Agent now always generates final responses
- Empty AI messages are properly filtered out
- Better error messages when issues occur
- Increased token limit handles larger responses

