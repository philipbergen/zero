def main():
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        # Running tests, not zeros
        import doctest
        sys.path.insert(0, '..')
        import zero
        import zero.rpc
        fails, tests = doctest.testmod(zero)
        fails2, tests2 = doctest.testmod(zero.rpc)
        tests += tests2
        if fails + fails2:
            msg = 'Completed %d tests, %d failed. Run zero test -v for more information.'
            sys.exit(msg % (tests, fails + fails2))
        print 'Successfully completed %d tests.' % tests
        return

    import json
    from zero import Zero, ZeroSetup, zauto, UnsupportedZmqMethod
    try:
        # Regular zero run
        setup, loop = ZeroSetup.argv()
        zero = Zero(setup)

        for msg in zauto(zero, loop, setup.args['--wait']):
            sys.stdout.write(json.dumps(msg) + '\n')
            sys.stdout.flush()
    except UnsupportedZmqMethod, e:
        args = e.args[2]
        if args['rpc']:
            # Configured RPC not supported by zauto
            from zero.rpc import zrpc
            with open(args['<config>']) as fin:
                config = json.load(fin)
            if len(args['<type>']) == 1:
                zero = zrpc(config, args['<type>'][0])
                setup = zero.setup
                if args['--dbg']:
                    setup.debugging(True)
                for msg in zero:
                    if setup.transmits:
                        zero(msg)
            else:
                raise ValueError('Multiple RPC workers not yet supported.', args['<type>'])
        else:
            # Something happened...
            raise e
        if setup.args['--wait']:
            raw_input('Press enter when done.')
        zero.close()
    
if __name__ == '__main__':
    main()
