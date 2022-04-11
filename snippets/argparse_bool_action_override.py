import argparse
import functools
unittest


PROG = 'testy_mctestface'
TRUE_OPT = '--test_option'
OVR_OPT = '--test_option_override'

class TestStoreBoolOverrides(unittest.TestCase):

    def setUp(self):
        # A _proper_ unit test would mock this, but since our ultimate goal is
        # that we maintain consistency with argparse, I think this is right for
        # here.
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument('others', nargs='*')
        self.parser.add_argument(
            TRUE_OPT, dest='test_option',
            action=plugin.action_store_true_overridable)

        self.parser.add_argument(
            OVR_OPT, dest='test_option',
            action=plugin.action_store_true_overrider)

    def test_not_used(self):
        namespace = self.parser.parse_args([PROG])
        self.assertFalse(namespace.test_option)

    def test_not_overridden(self):
        namespace = self.parser.parse_args([PROG, TRUE_OPT])
        self.assertTrue(namespace.test_option)

    def test_override_only(self):
        namespace = self.parser.parse_args([PROG, OVR_OPT])
        self.assertFalse(namespace.test_option)

    # `argparse` honors the last assignment to a dest, so it is prudent to test
    # both orders

    def test_overide(self):
        namespace = self.parser.parse_args([PROG, TRUE_OPT, OVR_OPT])
        self.assertFalse(namespace.test_option)

        namespace = self.parser.parse_args([PROG, OVR_OPT, TRUE_OPT])
        self.assertFalse(namespace.test_option)



class OptionStoreBoolOverride(argparse.Action):
    """
    I'd base this off of argparse.Action._StoreConstAction were it not in the
    private interface.
    """
    overridden = set()

    def __init__(self, const, *args, overrider=False, nargs=0, default=False, type=bool, **kwargs):
        self.overrider = overrider
        super().__init__(*args, const=const, default=default, nargs=nargs, type=type, **kwargs)

    def __call__(self, parser, namespace, values, option_strings=None):

        if not self.overrider and self.dest in self.overridden:
            return False

        setattr(namespace, self.dest, self.const)

        if self.overrider:
            self.overridden.add(self.dest)


action_store_true_overridable = functools.partial(OptionStoreBoolOverride,
                                                  True,
                                                  overrider=False,
                                                  default=False)

action_store_true_overrider = functools.partial(OptionStoreBoolOverride,
                                                False,
                                                overrider=True,
                                                default=False)
