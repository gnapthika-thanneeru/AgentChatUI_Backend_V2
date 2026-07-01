def parse_response(data):
    final_text = ""
    chart_spec = None
    tables = []

    content_items = data.get("content", [])
    if not content_items and "raw" in data:
        content_items = data["raw"].get("content", [])

    for item in content_items:
        item_type = item.get("type")
        if item_type == "text":
            final_text += item.get("text", "") + "\n"
        if item_type == "table":
            tables.append(item.get("table"))
        if item_type == "tool_result":
            tool_result = item.get("tool_result", {})
            if tool_result.get("name") == "data_to_chart":
                for c in tool_result.get("content", []):
                    if c.get("type") == "json":
                        charts = c.get("json", {}).get("charts", [])
                        if charts:
                            chart_spec = charts[0]
            if tool_result.get("name") == "system_execute_sql":
                for c in tool_result.get("content", []):
                    if c.get("type") == "json":
                        result_set = c.get("json", {}).get("result_set")
                        if result_set:
                            tables.append(result_set)

    # --- NEW: read thread IDs from response.metadata (per official docs). Safe if absent. ---
    thread_id = None
    assistant_message_id = None
    metadata = data.get("metadata", {}) or {}
    if isinstance(metadata, dict):
        thread_id = metadata.get("thread_id")
        assistant_message_id = metadata.get("assistant_message_id")

    return {
        "answer": final_text.strip(),
        "chart": chart_spec,
        "tables": tables,
        "thread_id": thread_id,                       # NEW (None if not threaded)
        "assistant_message_id": assistant_message_id,  # NEW (None if not threaded)
        "raw": data
    }