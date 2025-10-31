#!/usr/bin/env python3
"""
Test script to verify Redis integration with Options class
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from lib.options import Options

def test_redis_integration():
    """Test Redis integration with Options class"""
    print("Testing Redis integration with Options class...")
    
    try:
        # Initialize Options with Redis
        options = Options({
            'test_string': {'type': 'str', 'description': 'Test string option', 'is_global_entity': False, 'default': 'default_value'},
            'test_int': {'type': 'int', 'description': 'Test integer option', 'is_global_entity': False, 'default': 42},
            'test_bool': {'type': 'bool', 'description': 'Test boolean option', 'is_global_entity': False, 'default': True},
            'test_dict': {'type': 'dict', 'description': 'Test dictionary option', 'is_global_entity': False, 'default': {}},
        }, redis_host='localhost', redis_port=6379)
        
        print("✓ Options initialized successfully with Redis")
        
        # Test user ID
        user_id = "test_user_123"
        
        # Test setting and getting string option
        options.set_option(user_id, 'test_string', 'Hello Redis!')
        value = options.get_option(user_id, 'test_string')
        assert value == 'Hello Redis!', f"Expected 'Hello Redis!', got {value}"
        print("✓ String option test passed")
        
        # Test setting and getting integer option
        options.set_option(user_id, 'test_int', 100)
        value = options.get_option(user_id, 'test_int')
        assert value == 100, f"Expected 100, got {value}"
        print("✓ Integer option test passed")
        
        # Test setting and getting boolean option
        options.set_option(user_id, 'test_bool', False)
        value = options.get_option(user_id, 'test_bool')
        assert value == False, f"Expected False, got {value}"
        print("✓ Boolean option test passed")
        
        # Test setting and getting dictionary option
        options.set_option(user_id, 'test_dict', 'value1', 'key1')
        options.set_option(user_id, 'test_dict', 'value2', 'key2')
        value1 = options.get_option(user_id, 'test_dict', 'key1')
        value2 = options.get_option(user_id, 'test_dict', 'key2')
        assert value1 == 'value1', f"Expected 'value1', got {value1}"
        assert value2 == 'value2', f"Expected 'value2', got {value2}"
        print("✓ Dictionary option test passed")
        
        # Test default values
        options2 = Options({
            'default_test': {'type': 'str', 'description': 'Test default value', 'is_global_entity': False, 'default': 'default_value'},
        }, redis_host='localhost', redis_port=6379)
        
        value = options2.get_option(user_id, 'default_test')
        assert value == 'default_value', f"Expected 'default_value', got {value}"
        print("✓ Default value test passed")
        
        # Test global entity (same key for all users)
        global_options = Options({
            'global_setting': {'type': 'str', 'description': 'Global setting', 'is_global_entity': True, 'default': 'global_default'},
        }, redis_host='localhost', redis_port=6379)
        
        global_options.set_option('user1', 'global_setting', 'global_value')
        value1 = global_options.get_option('user1', 'global_setting')
        value2 = global_options.get_option('user2', 'global_setting')
        assert value1 == 'global_value', f"Expected 'global_value', got {value1}"
        assert value2 == 'global_value', f"Expected 'global_value', got {value2}"
        print("✓ Global entity test passed")
        
        # Clean up
        options.close()
        options2.close()
        global_options.close()
        
        print("\n🎉 All tests passed! Redis integration is working correctly.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Make sure Redis server is running on localhost:6379")
    print("You can start Redis with: redis-server")
    print()
    
    success = test_redis_integration()
    sys.exit(0 if success else 1)
