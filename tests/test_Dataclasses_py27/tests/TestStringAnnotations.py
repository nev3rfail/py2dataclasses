from load_test import *

class TestStringAnnotations(unittest.TestCase):
    def test_classvar(self):
        # Some expressions recognized as ClassVar really aren't.  But
        #  if you're using string annotations, it's not an exact
        #  science.
        # These tests assume that both "import typing" and "from
        # typing import *" have been run in this file.
        for typestr in ('ClassVar[int]',
                        'ClassVar [int]',
                        ' ClassVar [int]',
                        'ClassVar',
                        ' ClassVar ',
                        'typing.ClassVar[int]',
                        'typing.ClassVar[str]',
                        ' typing.ClassVar[str]',
                        'typing .ClassVar[str]',
                        'typing. ClassVar[str]',
                        'typing.ClassVar [str]',
                        'typing.ClassVar [ str]',

                        # Not syntactically valid, but these will
                        #  be treated as ClassVars.
                        'typing.ClassVar.[int]',
                        'typing.ClassVar+',
                        ):
            with self.subTest(typestr=typestr):
                @dataclass
                class C(object):
                    pass
                C.__annotations__ = {'x': typestr}

                # x is a ClassVar, so C() takes no args.
                C()

                # And it won't appear in the class's dict because it doesn't
                # have a default.
                self.assertNotIn('x', C.__dict__)

    def test_isnt_classvar(self):
        for typestr in ('CV',
                        't.ClassVar',
                        't.ClassVar[int]',
                        'typing..ClassVar[int]',
                        'Classvar',
                        'Classvar[int]',
                        'typing.ClassVarx[int]',
                        'typong.ClassVar[int]',
                        'dataclasses.ClassVar[int]',
                        'typingxClassVar[str]',
                        ):
            with self.subTest(typestr=typestr):
                @dataclass
                class C(object):
                    x = field(typestr)
                #C.__annotations__ = {'x': typestr}

                # x is not a ClassVar, so C() takes one arg.
                self.assertEqual(C(10).x, 10)

    def test_initvar(self):

        # These tests assume that both "import dataclasses" and "from
        #  dataclasses import *" have been run in this file.
        # typestr = 'dataclasses.InitVar[int]'
        # @dataclass
        # class CSSS(object):
        #     x = field(typestr)
        #     y = field('InitVar[int]')
        # #s = CSSS(1).x
        for typestr in ('InitVar[int]',
                        'InitVar [int]'
                        ' InitVar [int]',
                        'InitVar',
                        ' InitVar ',
                        'dataclasses.InitVar[int]', # 'dataclasses.InitVar[int]'
                        'dataclasses.InitVar[str]',
                        ' dataclasses.InitVar[str]',
                        'dataclasses .InitVar[str]',
                        'dataclasses. InitVar[str]',
                        'dataclasses.InitVar [str]',
                        'dataclasses.InitVar [ str]',

                        # Not syntactically valid, but these will
                        #  be treated as InitVars.
                        'dataclasses.InitVar.[int]',
                        'dataclasses.InitVar+',
                        ):
            with self.subTest(typestr=typestr):
                @dataclass
                class C(object):
                    x = field(typestr)

                # x is an InitVar, so doesn't create a member.
                with self.assertRaisesRegexp(AttributeError,
                                             "object has no attribute 'x'"):
                    C(1).x

    def test_isnt_initvar(self):
        for typestr in ('IV',
                        'dc.InitVar',
                        'xdataclasses.xInitVar',
                        'typing.xInitVar[int]',
                        ):
            with self.subTest(typestr=typestr):
                @dataclass
                class C(object):
                    x = field(typestr)

                # x is not an InitVar, so there will be a member x.
                self.assertEqual(C(10).x, 10)

    def test_classvar_module_level_import(self):
        from .dataclass_module_1 import CV as CV_1, IV as IV_1, USING_STRINGS as USING_STRINGS_1
        from .dataclass_module_1_str import CV as CV_1_str, IV as IV_1_str, USING_STRINGS as USING_STRINGS_1_str
        from .dataclass_module_2 import CV as CV_2, IV as IV_2, USING_STRINGS as USING_STRINGS_2
        from .dataclass_module_2_str import CV as CV_2_str, IV as IV_2_str, USING_STRINGS as USING_STRINGS_2_str

        modules_and_flags = [
            (CV_1, IV_1, USING_STRINGS_1),
            (CV_1_str, IV_1_str, USING_STRINGS_1_str),
            (CV_2, IV_2, USING_STRINGS_2),
            (CV_2_str, IV_2_str, USING_STRINGS_2_str),
        ]

        for cv_class, iv_class, using_strings in modules_and_flags:
            with self.subTest(cv_class=cv_class):
                # There's a difference in how the ClassVars are
                # interpreted when using string annotations or
                # not. See the imported modules for details.
                if using_strings:
                    c = cv_class(10)
                else:
                    c = cv_class()
                self.assertEqual(c.cv0, 20)

            with self.subTest(iv_class=iv_class):
                # There's a difference in how the InitVars are
                # interpreted when using string annotations or
                # not. See the imported modules for details.
                c = iv_class(0, 1, 2, 3, 4)

                for field_name in ('iv0', 'iv1', 'iv2', 'iv3'):
                    with self.subTest(field_name=field_name):
                        with self.assertRaisesRegexp(AttributeError, "object has no attribute"):
                            # Since field_name is an InitVar, it's
                            # not an instance field.
                            getattr(c, field_name)

                if using_strings:
                    # iv4 is interpreted as a normal field.
                    self.assertIn('not_iv4', c.__dict__)
                    self.assertEqual(c.not_iv4, 4)
                else:
                    # iv4 is interpreted as an InitVar, so it
                    # won't exist on the instance.
                    self.assertNotIn('not_iv4', c.__dict__)

    def test_text_annotations(self):
        from dataclass_textanno import Bar, Foo

        # Skip this test as it requires get_type_hints functionality
        # that may not be fully compatible in Python 2.7
        pass
