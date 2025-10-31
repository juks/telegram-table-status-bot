"""
Simple options class
"""
from .redis import Redis


class Options():
    valid_options = {}
    valid_types = ['bool', 'int', 'str', 'dict']

    def __init__(self, setup, redis_host='localhost', redis_port=6379, redis_password=None):
        self.redis = Redis(host=redis_host, port=redis_port, password=redis_password)
        for option_name in setup:
            if 'type' not in setup[option_name] or setup[option_name]['type'] not in self.valid_types:
                raise Exception('Invalid option type')

            match setup[option_name]['type']:
                case 'bool':
                    self.valid_options[option_name] = {'type': 'bool'}
                case 'int':
                    self.valid_options[option_name] = {'type': 'int'}
                case 'str':
                    self.valid_options[option_name] = {'type': 'str'}
                case 'dict':
                    self.valid_options[option_name] = {'type': 'dict'}
                case _:
                    raise Exception('Invalid option type')

            if 'is_global_entity' in setup[option_name] and setup[option_name]['is_global_entity'] is True:
                self.valid_options[option_name]['is_global_entity'] = True
            else:
                self.valid_options[option_name]['is_global_entity'] = False

            if 'default' in setup[option_name]:
                self.valid_options[option_name]['default'] = setup[option_name]['default']

            if 'description' in setup[option_name]:
                self.valid_options[option_name]['description'] = setup[option_name]['description']


    def get_option(self, user_id, option_name, option_key = None):
        """ Returns option value """
        if option_name not in self.valid_options:
            raise Exception(f'Unknown option name: {option_name}')

        if self.valid_options[option_name]['type'] == 'dict' and option_key is None:
            raise Exception(f'Need option key for {option_name}')

        storage_key = self.get_storage_key(user_id, option_name, option_key)

        if self.valid_options[option_name]['type'] == 'dict':
            # For dict type, get the entire dict and return the specific key
            result = self.redis.get_dict(storage_key)
            if result is not None and option_key in result:
                return result[option_key]
            elif result is not None:
                return {}
        else:
            # For other types, get the value directly
            result = self.redis.get(storage_key)
            if result is not None:
                # Convert string back to appropriate type
                match self.valid_options[option_name]['type']:
                    case 'bool':
                        return result.lower() in ('true', '1', 'yes', 'on')
                    case 'int':
                        return int(result)
                    case 'str':
                        return result

        # Return default value if not found in Redis
        if option_name in self.valid_options and 'default' in self.valid_options[option_name]:
            return self.valid_options[option_name]['default']
        else:
            match self.valid_options[option_name]['type']:
                case 'bool':
                    return False
                case 'int':
                    return 0
                case 'str':
                    return ''
                case 'dict':
                    return {}

    def set_option(self, user_id, option_name, option_value, option_key = None):
        """ Store option value """
        if option_name not in self.valid_options:
            raise Exception(f'Unknown option {option_name}')

        if self.valid_options[option_name]['type'] == 'dict' and option_key is None:
                raise Exception(f'Need option key for {option_name}')

        storage_key = self.get_storage_key(user_id, option_name, option_key)

        match self.valid_options[option_name]['type']:
            case 'bool':
                self.redis.set(storage_key, bool(option_value))
            case 'int':
                self.redis.set(storage_key, int(option_value))
            case 'str':
                self.redis.set(storage_key, str(option_value))
            case 'dict':
                # For dict type, get existing dict, update it, and save back
                existing_dict = self.redis.get_dict(storage_key) or {}
                existing_dict[option_key] = str(option_value)
                self.redis.set_dict(storage_key, existing_dict)

    def get_storage_key(self, user_id, option_name, option_key):
        storage_key = option_name

        if self.valid_options[option_name]['is_global_entity'] is False:
            storage_key = storage_key + ':' + str(user_id)

        return storage_key

    def get_reference(self):
        """ Returns the list of supported parameters """
        result = ''

        for option_name in self.valid_options:
            result += f'• <b>{option_name}</b> ({self.valid_options[option_name]['type']})'
            if 'default' in self.valid_options[option_name]:
                result += ' default <b>' + str(self.valid_options[option_name]['default']) + '</b>'

            if 'description' in self.valid_options[option_name]:
                result += ': ' + self.valid_options[option_name]['description']

            result += '\n'

        return result

    def close(self):
        """Close Redis connection"""
        if hasattr(self, 'redis'):
            self.redis.close()