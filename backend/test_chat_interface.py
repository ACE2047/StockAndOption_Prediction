from chat_interface import process_user_input

def test_process_user_input():
    user_input = "What's the latest news on Apple?"
    news_data = "Apple Inc. announced a new product launch."
    result = process_user_input(user_input, news_data)
    assert "User Input: What's the latest news on Apple?" in result
    assert "News Data: Apple Inc. announced a new product launch." in result
    print("Chat interface test passed.")

if __name__ == "__main__":
    test_process_user_input() 