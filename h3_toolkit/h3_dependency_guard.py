def _isH3Present():
    try:
        # not best practice. TODO: check with pkg_resources module instead and install via
        #                          pip + subprocess + sys.executable?
        # import pkg_resources
        import h3
    except ImportError:
        return False

    return True

IS_H3_PRESENT = _isH3Present()