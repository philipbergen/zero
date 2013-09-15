''' Base classes for use by workers (not intended to be used outside this module.
'''
import json
from itertools import izip

__all__ = ('ZeroRPC', 'ConfiguredRPC', 'zrpc')


class ZeroRPC(object):
    ''' Inherit and implement your own methods on from this.
        Then supply to ZeroSetup:

        Zero(ZeroSetup('pull', 8000)).activated(ZeroRPC())
    '''
    def __call__(self, obj):
        'Calls the method from obj (always of the form [<method name>, {<kwargs>}]).'
        from traceback import format_exc
        try:
            if obj[0][:1] == '_':
                raise Exception('Method not available')
            if len(obj) == 1:
                obj = [obj[0], {}]
            if not hasattr(self, obj[0]):
                return self._unsupported(obj[0], **obj[1])
            func = getattr(self, obj[0])
            return func(**obj[1])
        except:
            self.zero.setup.err('Exception: ' + format_exc())
            return ['ERROR', format_exc()]

    def _unsupported(self, func, **kwargs):
        'Catch-all method for when the object received does not fit.'
        return ['UnsupportedFunc', func, kwargs]

    @staticmethod
    def _test_rpc():
        ''' For doctest
            >>> from zero.rpc import ZeroRPC
            >>> ZeroRPC._test_rpc()
            REP u'hello'
            REP 100
        '''
        from zero import Zero, ZeroSetup
        class Z(ZeroRPC):
            def hi(self):
                return "hello"

            def sqr(self, x):
                return x*x

        def listen():
            zero = Zero(ZeroSetup('rep', 8000)).activated(Z())
            for _, msg in izip(range(2), zero):
                zero(msg)
            zero.close()

        from threading import Thread
        t = Thread(name='TestRPC', target=listen)
        t.daemon = True
        t.start()

        zero = Zero(ZeroSetup('req', 8000))
        msg = ['hi']
        rep = zero(msg)
        print 'REP %r' % rep
        msg = ['sqr', {'x': 10}]
        rep = zero(msg)
        print 'REP %r' % rep
        zero.close()
        t.join()


class ConfiguredRPC(ZeroRPC):
    ''' Does not implement any RPC methods. This class adds methods and members for accessing 
        system configuration.

        System configuration as json looks like this:
        {
            "workers": {
                "imagestore": {
                    "module": "noep.workers.store",
                    "class": "ImageStoreRPC",
                    "zmq": {
                        "method": "rep",
                        "port": 8805,
                        "debug": true,
                        "host": "localhost"
                    }
                },
                "gphoto": {
                    "module": "noep.workers.gphoto",
                    "class": "GphotoRPC",
                    "zmq": {
                        "method": "rep",
                        "port": 8804,
                        "debug": true,
                        "host": "localhost"
                    },
                    "filename": "gphoto-%n.%C"
                }
            }
        }

        Each worker has a module and class name as well as a zmq configuration. Additional keys
        may be added. zero.rpc will ignore everything outside of "workers" -> (worker type) -> 
        ["module", "class", "zmq" -> ["method", "port", "debug"*, "bind"*, "host"*]].

        *) optional

        To instantiate a worker from the config do something similar to this:

        from zero.rpc import zrpc
        from json import load
        with open('config.json') as fin:
            sysconfig = load(fin)
        rpc = zrpc(sysconfig, 'gphoto')
    '''
    def __init__(self, configuration, workertype):
        self._config = (configuration, workertype)

    def _worker_config(self, workertype=None):
        if not workertype:
            workertype = self._config[1]
        return self._config[0]['workers'][workertype]

    def _system_config(self):
        return self._config[0]

    
def zrpc(sysconfig, workertype):
    ''' Returns an activated Zero with RPC worker of type workertype as specified in sysconfig.
        >>> from .test import _get_test_config
        >>> from zero import zbg
        >>> from itertools import izip
        >>> from socket import gethostname
        >>> from time import time
        >>> cfg = _get_test_config()
        >>> z = zrpc(cfg, 'common')
        >>> o = z.opposite()
        >>> z  # doctest: +ELLIPSIS
        Zero(ZeroSetup('rep', 8000).binding(True)).activated(<zero.test.CommonRPC object at ...>)
        >>> o
        Zero(ZeroSetup('req', 8000).binding(False))
        >>> t = zbg(o, [['ping'], ['echo', {'msg': 'Hello'}], ['hostname'], ['time']], lambda x: x)
        >>> reps = []
        >>> for _, msg in izip(range(4), z):  # doctest: +ELLIPSIS
        ...     reps.append(msg)
        ...     z(msg)
        >>> reps[0]
        'pong'
        >>> reps[1]
        u'Hello'
        >>> reps[2] == gethostname()
        True
        >>> abs(time() - reps[3]) < 1
        True
        >>> t.join()
    '''
    from zero import Zero, ZeroSetup
    wconf = sysconfig['workers'][workertype]
    zconf = wconf['zmq']
    setup = ZeroSetup(zconf['method'], zconf['port']).debugging(zconf.get('debug', False))
    if 'bind' in zconf:
        setup.binding(zconf['bind'])
    if 'host' in zconf and not setup.bind:
        setup._point = 'tcp://%(host)s:%(port)s' % zconf
    mod = __import__(wconf['module'])
    for modpart in wconf['module'].split('.')[1:]:
        mod = getattr(mod, modpart)
    klass = getattr(mod, wconf['class'])
    return Zero(setup).activated(klass(sysconfig, workertype))


def _test():
    import doctest
    return doctest.testmod()


if __name__ == '__main__':
    from zero import Zero, ZeroSetup
    _test()
