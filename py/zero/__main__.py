def main():
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        import doctest
        sys.path.insert(0, '..')
        import zero
        import zero.rpc
        return doctest.testmod(zero, zero.rpc)

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
