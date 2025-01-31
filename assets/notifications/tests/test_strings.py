import pytest
from notifications.utils.strings import format_key_name

def test_format_key_name():
    # Test basic underscore case
    assert format_key_name("hello_world") == "Hello World"
    
    # Test multiple underscores
    assert format_key_name("this_is_a_test") == "This Is A Test"
    
    # Test already capitalized words
    assert format_key_name("Hello_World") == "Hello World"
    
    # Test single word
    assert format_key_name("hello") == "Hello"
    
    # Test empty string
    assert format_key_name("") == ""
    
    # Test multiple consecutive underscores
    assert format_key_name("hello__world") == "Hello World" 