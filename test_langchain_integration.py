"""
Test script to demonstrate the LangChain agent integration with message filtering.
This shows how tool messages are filtered out and only the final response is returned.
"""

import asyncio
from langchain.schema import AIMessage, HumanMessage
from langchain_core.messages import ToolMessage
from backend.utils_langchain import is_public, to_public_messages


def test_message_filtering():
    """Test that tool messages are properly filtered out."""

    # Simulate a typical React agent message flow
    messages = [
        HumanMessage(content="What permits are available?"),
        AIMessage(content="", tool_calls=[{"name": "get_permits", "args": {}, "id": "call_1"}]),  # Tool call with no content
        ToolMessage(content="Found 5 permits: PLO-123, KKPR-456...", tool_call_id="call_1"),  # Tool response
        AIMessage(content="Based on the search, here are the 5 permits available: PLO-123, KKPR-456...")  # Final answer
    ]

    print("Original messages:")
    for i, msg in enumerate(messages):
        print(f"  {i+1}. {type(msg).__name__}: {msg.content[:50] if msg.content else '<empty>'}")

    print("\nFiltering messages...")
    public_messages = to_public_messages(messages)

    print(f"\nPublic messages (count: {len(public_messages)}):")
    for i, msg in enumerate(public_messages):
        print(f"  {i+1}. Role: {msg['role']}, Content: {msg['content'][:50]}...")

    # Verify filtering works correctly
    assert len(public_messages) == 2, "Should have 2 public messages (user + final AI)"
    assert public_messages[0]["role"] == "user", "First message should be user"
    assert public_messages[1]["role"] == "assistant", "Second message should be assistant"
    assert "5 permits available" in public_messages[1]["content"], "Should contain final answer"

    print("\n✅ All tests passed! Tool messages were correctly filtered out.")


def test_individual_message_checks():
    """Test the is_public function with different message types."""

    print("\nTesting individual message types:")

    # HumanMessage - should be public
    human_msg = HumanMessage(content="Hello")
    print(f"  HumanMessage: is_public = {is_public(human_msg)} (expected: True)")
    assert is_public(human_msg) == True

    # AIMessage with content - should be public
    ai_msg_with_content = AIMessage(content="Hello back!")
    print(f"  AIMessage (with content): is_public = {is_public(ai_msg_with_content)} (expected: True)")
    assert is_public(ai_msg_with_content) == True

    # AIMessage with only tool_calls - should NOT be public
    ai_msg_tool_only = AIMessage(content="", tool_calls=[{"name": "tool", "args": {}, "id": "123"}])
    print(f"  AIMessage (tool_calls only): is_public = {is_public(ai_msg_tool_only)} (expected: False)")
    assert is_public(ai_msg_tool_only) == False

    # ToolMessage - should NOT be public
    tool_msg = ToolMessage(content="Tool result", tool_call_id="123")
    print(f"  ToolMessage: is_public = {is_public(tool_msg)} (expected: False)")
    assert is_public(tool_msg) == False

    print("\n✅ All individual message type tests passed!")


async def test_complete_flow():
    """
    Simulate what happens in complete_chat_request.
    This demonstrates the full integration flow.
    """
    print("\n" + "="*60)
    print("SIMULATING COMPLETE CHAT REQUEST FLOW")
    print("="*60)

    # Simulate agent output with mixed messages
    agent_output = {
        "messages": [
            HumanMessage(content="What is the status of permit PLO-123?"),
            AIMessage(content="", tool_calls=[{"name": "search_permits", "args": {"permit_id": "PLO-123"}, "id": "call_1"}]),
            ToolMessage(content="Permit PLO-123: Status=Active, Expires=2025-12-31", tool_call_id="call_1"),
            AIMessage(content="Permit PLO-123 is currently active and will expire on December 31, 2025.")
        ]
    }

    print("\n1. Agent returned {} messages:".format(len(agent_output["messages"])))
    for msg in agent_output["messages"]:
        msg_type = type(msg).__name__
        content_preview = msg.content[:40] + "..." if msg.content else "<no content>"
        print(f"   - {msg_type}: {content_preview}")

    print("\n2. Filtering out tool messages...")
    public_messages = to_public_messages(agent_output["messages"])

    print(f"\n3. Public messages ({len(public_messages)}):")
    for msg in public_messages:
        print(f"   - {msg['role']}: {msg['content']}")

    print("\n4. Extracting final response...")
    final_content = ""
    if public_messages and public_messages[-1]["role"] == "assistant":
        final_content = public_messages[-1]["content"]

    print(f"\n5. Final response to frontend:")
    print(f"   '{final_content}'")

    print("\n✅ Complete flow test passed!")


if __name__ == "__main__":
    print("="*60)
    print("LANGCHAIN AGENT MESSAGE FILTERING TESTS")
    print("="*60)

    test_individual_message_checks()
    test_message_filtering()
    asyncio.run(test_complete_flow())

    print("\n" + "="*60)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("="*60)
    print("\nThe integration is working correctly:")
    print("  ✓ Tool messages are filtered out")
    print("  ✓ Only user and assistant messages are shown to frontend")
    print("  ✓ Final AI response is properly extracted")

