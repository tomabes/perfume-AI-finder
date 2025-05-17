def make_claude_prompt(user_input, context=None):
    if context:
        return (
            f"Вот база парфюмов в формате JSON:\n{context}\n\n"
            f"Вот мой запрос: {user_input}"
        )
    else:
        return user_input
