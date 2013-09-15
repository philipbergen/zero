def main():
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
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

    from zero import Zero, ZeroSetup, zauto
    setup, loop = ZeroSetup.argv()
    zero = Zero(setup)
    for msg in zauto(zero, loop):
        sys.stdout.write(json.dumps(msg) + '\n')
        sys.stdout.flush()
    if setup.args['--wait']:
        raw_input('Press enter when done.')
    zero.close()
    
if __name__ == '__main__':
    main()
