''' Simple RPC functions that can be used for testing.
'''

__all__ = ('CommonRPC', '_get_test_config')
from zero.rpc import ConfiguredRPC

def _get_test_config():
    return {
        'workers': {
            'common': {
                'module': 'zero.test',
                'class': 'CommonRPC',
                'zmq': {
                    'port': 8000,
                    'method': 'rep'
                }
            }
        }
    }


class CommonRPC(ConfiguredRPC):
    'Simple network functions.'
    def ping(self):
        return 'pong'

    def echo(self, msg):
        return msg

    def hostname(self):
        from socket import gethostname
        return gethostname()

    def time(self):
        import time
        return time.time()
