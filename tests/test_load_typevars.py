from __future__ import print_function
from tests.load_fixtures import *

# Tests: TypeVar / generics with type_vars
# ---------------------------------------------------------------------------

class TestTypeVars(unittest.TestCase):

    # --- Without type_vars: TypeVar fields skip validation ---

    def test_typevar_no_binding_accepts_anything(self):
        obj = load(Box, {'value': 'hello'})
        self.assertEqual(obj.value, 'hello')
        obj2 = load(Box, {'value': 42})
        self.assertEqual(obj2.value, 42)

    def test_list_typevar_no_binding_accepts_mixed(self):
        obj = load(GenericList, {'items': [1, 'two', None]})
        self.assertEqual(obj.items, [1, 'two', None])

    # --- With type_vars: validates resolved types ---

    def test_typevar_resolved_int(self):
        obj = load(Box, {'value': 42}, type_vars={T: int})
        self.assertEqual(obj.value, 42)

    def test_typevar_resolved_str(self):
        obj = load(Box, {'value': 'hello'}, type_vars={T: str})
        self.assertEqual(obj.value, 'hello')

    def test_typevar_resolved_rejects_wrong_type(self):
        with self.assertRaises(TypeError):
            load(Box, {'value': 'bad'}, type_vars={T: int})

    def test_typevar_resolved_rejects_none(self):
        with self.assertRaises(TypeError):
            load(Box, {'value': None}, type_vars={T: int})

    def test_parameterized_dataclass_alias_top_level(self):
        obj = load(Box[int], {'value': 42})
        obj2 = loads(Box[int], '{"value": 7}')
        validate_result = validate(Box[int], {'value': 99})
        validates_result = validates(Box[int], '{"value": 100}')

        self.assertIsInstance(obj, Box)
        self.assertEqual(obj.value, 42)
        self.assertEqual(obj2.value, 7)
        self.assertTrue(validate_result)
        self.assertTrue(validates_result)

    def test_parameterized_dataclass_alias_top_level_rejects(self):
        with self.assertRaises(TypeError):
            load(Box[int], {'value': 'bad'})

        with self.assertRaises(ValidationError) as cm:
            validate(Box[int], {'value': 'bad'}, collect_errors=True)
        self.assertEqual([issue.path for issue in cm.exception.errors],
                         ['value'])

    def test_future_annotations_preserve_type_vars(self):
        if sys.version_info < (3,):
            self.skipTest('future annotations are Python 3 only')

        sentinel = object()
        names = ('FutureLoadT', 'FutureBox', 'FutureListBox',
                 'FutureOptionalBox')
        previous = dict((name, globals().get(name, sentinel)) for name in names)
        try:
            six.exec_(
                'from __future__ import annotations\n'
                'FutureLoadT = TypeVar("FutureLoadT")\n'
                '@dataclass\n'
                'class FutureBox(Generic[FutureLoadT]):\n'
                '    value: FutureLoadT\n'
                '@dataclass\n'
                'class FutureListBox(Generic[FutureLoadT]):\n'
                '    items: List[FutureLoadT]\n'
                '@dataclass\n'
                'class FutureOptionalBox(Generic[FutureLoadT]):\n'
                '    maybe: Optional[FutureLoadT]\n',
                globals())
            FutureBox = globals()['FutureBox']
            FutureListBox = globals()['FutureListBox']
            FutureOptionalBox = globals()['FutureOptionalBox']
            FutureT = globals()['FutureLoadT']

            obj = load(FutureBox[int], {'value': 42})
            explicit_obj = load(FutureBox, {'value': 7},
                                type_vars={FutureT: int})
            list_obj = load(FutureListBox[int], {'items': [1, 2]})
            optional_obj = load(FutureOptionalBox[int], {'maybe': None})

            self.assertEqual(obj.value, 42)
            self.assertEqual(explicit_obj.value, 7)
            self.assertEqual(list_obj.items, [1, 2])
            self.assertIsNone(optional_obj.maybe)

            with self.assertRaises(TypeError):
                load(FutureBox[int], {'value': 'bad'})

            with self.assertRaises(TypeError):
                load(FutureBox, {'value': 'bad'}, type_vars={FutureT: int})

            with self.assertRaises(TypeError):
                load(FutureListBox[int], {'items': [1, 'bad']})

            with self.assertRaises(TypeError):
                load(FutureOptionalBox[int], {'maybe': 'bad'})

            with self.assertRaises(ValidationError) as cm:
                validate(FutureOptionalBox[int], {'maybe': 'bad'},
                         collect_errors=True)
            self.assertEqual([issue.path for issue in cm.exception.errors],
                             ['maybe'])
        finally:
            for name, value in previous.items():
                if value is sentinel:
                    globals().pop(name, None)
                else:
                    globals()[name] = value

    def test_future_annotations_preserve_pep604_type_vars(self):
        if sys.version_info < (3, 10):
            self.skipTest('PEP 604 annotations require Python 3.10+')

        sentinel = object()
        names = ('FuturePipeT', 'FuturePipeBox')
        previous = dict((name, globals().get(name, sentinel)) for name in names)
        try:
            six.exec_(
                'from __future__ import annotations\n'
                'FuturePipeT = TypeVar("FuturePipeT")\n'
                '@dataclass\n'
                'class FuturePipeBox(Generic[FuturePipeT]):\n'
                '    maybe: FuturePipeT | None\n'
                '    either: FuturePipeT | str\n',
                globals())
            FuturePipeBox = globals()['FuturePipeBox']

            obj = load(FuturePipeBox[int], {'maybe': None, 'either': 42})
            str_union_obj = load(
                FuturePipeBox[int], {'maybe': 7, 'either': 'ok'})

            self.assertIsNone(obj.maybe)
            self.assertEqual(obj.either, 42)
            self.assertEqual(str_union_obj.maybe, 7)
            self.assertEqual(str_union_obj.either, 'ok')

            with self.assertRaises(TypeError):
                load(FuturePipeBox[int], {'maybe': 'bad', 'either': 42})

            with self.assertRaises(TypeError):
                load(FuturePipeBox[int], {'maybe': 1, 'either': []})

            with self.assertRaises(ValidationError) as cm:
                validate(FuturePipeBox[int],
                         {'maybe': 'bad', 'either': []},
                         collect_errors=True)
            self.assertEqual([issue.path for issue in cm.exception.errors],
                             ['maybe', 'either'])
        finally:
            for name, value in previous.items():
                if value is sentinel:
                    globals().pop(name, None)
                else:
                    globals()[name] = value

    def test_future_annotations_preserve_nested_generic_type_vars(self):
        if sys.version_info < (3,):
            self.skipTest('future annotations are Python 3 only')

        sentinel = object()
        names = ('FutureNestedT', 'FutureInner', 'FutureOuter')
        previous = dict((name, globals().get(name, sentinel)) for name in names)
        try:
            six.exec_(
                'from __future__ import annotations\n'
                'FutureNestedT = TypeVar("FutureNestedT")\n'
                '@dataclass\n'
                'class FutureInner(Generic[FutureNestedT]):\n'
                '    value: FutureNestedT\n'
                '@dataclass\n'
                'class FutureOuter(Generic[FutureNestedT]):\n'
                '    inner: FutureInner[FutureNestedT]\n'
                '    mapping: Dict[str, FutureInner[FutureNestedT]]\n',
                globals())
            FutureInner = globals()['FutureInner']
            FutureOuter = globals()['FutureOuter']

            obj = load(FutureOuter[int], {
                'inner': {'value': 1},
                'mapping': {'a': {'value': 2}},
            })

            self.assertIsInstance(obj.inner, FutureInner)
            self.assertIsInstance(obj.mapping['a'], FutureInner)
            self.assertEqual(obj.inner.value, 1)
            self.assertEqual(obj.mapping['a'].value, 2)

            with self.assertRaises(TypeError):
                load(FutureOuter[int], {
                    'inner': {'value': 'bad'},
                    'mapping': {'a': {'value': 2}},
                })

            with self.assertRaises(TypeError):
                load(FutureOuter[int], {
                    'inner': {'value': 1},
                    'mapping': {'a': {'value': 'bad'}},
                })

            with self.assertRaises(ValidationError) as cm:
                validate(FutureOuter[int], {
                    'inner': {'value': 'bad'},
                    'mapping': {'a': {'value': 'bad'}},
                }, collect_errors=True)
            self.assertEqual([issue.path for issue in cm.exception.errors],
                             ['inner.value', 'mapping[a].value'])
        finally:
            for name, value in previous.items():
                if value is sentinel:
                    globals().pop(name, None)
                else:
                    globals()[name] = value

    def test_typevar_resolved_optional(self):
        obj = load(Box, {'value': None}, type_vars={T: Optional[int]})
        self.assertIsNone(obj.value)
        obj2 = load(Box, {'value': 42}, type_vars={T: Optional[int]})
        self.assertEqual(obj2.value, 42)

    # --- Two TypeVars ---

    def test_two_typevars(self):
        obj = load(Pair, {'first': 1, 'second': 'hello'}, type_vars={T: int, U: str})
        self.assertEqual(obj.first, 1)
        self.assertEqual(obj.second, 'hello')

    def test_two_typevars_wrong_first(self):
        with self.assertRaises(TypeError):
            load(Pair, {'first': 'bad', 'second': 'ok'}, type_vars={T: int, U: str})

    def test_two_typevars_wrong_second(self):
        with self.assertRaises(TypeError):
            load(Pair, {'first': 1, 'second': 99}, type_vars={T: int, U: str})

    # --- List[T] resolved ---

    def test_list_typevar_resolved(self):
        obj = load(GenericList, {'items': [1, 2, 3]}, type_vars={T: int})
        self.assertEqual(obj.items, [1, 2, 3])

    def test_list_typevar_resolved_rejects(self):
        with self.assertRaises(TypeError):
            load(GenericList, {'items': [1, 'bad']}, type_vars={T: int})

    def test_list_typevar_resolved_empty(self):
        obj = load(GenericList, {'items': []}, type_vars={T: int})
        self.assertEqual(obj.items, [])

    # --- Dict[str, T] resolved ---

    def test_dict_typevar_resolved(self):
        obj = load(GenericDict, {'mapping': {'a': 1, 'b': 2}}, type_vars={T: int})
        self.assertEqual(obj.mapping, {'a': 1, 'b': 2})

    def test_dict_typevar_resolved_rejects(self):
        with self.assertRaises(TypeError):
            load(GenericDict, {'mapping': {'a': 'bad'}}, type_vars={T: int})

    def test_generic_alias_inside_generic_field(self):
        data = {
            'box': {'value': 1},
            'boxes': [{'value': 2}, {'value': 3}],
            'mapping': {'a': {'value': 4}},
        }

        obj = load(GenericAliasFields[int], data)

        self.assertEqual(obj.box.value, 1)
        self.assertEqual([box.value for box in obj.boxes], [2, 3])
        self.assertEqual(obj.mapping['a'].value, 4)
        self.assertIsInstance(obj.box, Box)
        self.assertIsInstance(obj.boxes[0], Box)
        self.assertIsInstance(obj.mapping['a'], Box)

    def test_generic_alias_inside_generic_field_rejects(self):
        data = {
            'box': {'value': 'bad'},
            'boxes': [{'value': 1}, {'value': 'bad'}],
            'mapping': {'a': {'value': 'bad'}},
        }

        with self.assertRaises(ValidationError) as cm:
            validate(GenericAliasFields[int], data, collect_errors=True)

        self.assertEqual([issue.path for issue in cm.exception.errors],
                         ['box.value', 'boxes[1].value',
                          'mapping[a].value'])

    def test_generic_optional_union_fields(self):
        none_data = {'maybe': None, 'either': 1}
        str_union_data = {'maybe': 2, 'either': 'ok'}

        none_obj = load(GenericOptionalUnion[int], none_data)
        str_union_obj = load(GenericOptionalUnion[int], str_union_data)

        self.assertIsNone(none_obj.maybe)
        self.assertEqual(none_obj.either, 1)
        self.assertEqual(str_union_obj.maybe, 2)
        self.assertEqual(str_union_obj.either, 'ok')

    def test_generic_optional_union_fields_rejects(self):
        data = {'maybe': 'bad', 'either': []}

        with self.assertRaises(ValidationError) as cm:
            validate(GenericOptionalUnion[int], data, collect_errors=True)

        self.assertEqual([issue.path for issue in cm.exception.errors],
                         ['maybe', 'either'])

    def test_string_generic_annotations_resolve(self):
        data = {
            'item': 1,
            'maybe': None,
            'box': {'value': 2},
            'boxes': [{'value': 3}],
        }

        obj = load(StringGenericAnnotations[int], data)

        self.assertEqual(obj.item, 1)
        self.assertIsNone(obj.maybe)
        self.assertEqual(obj.box.value, 2)
        self.assertEqual(obj.boxes[0].value, 3)

    def test_string_generic_annotations_reject(self):
        data = {
            'item': 'bad',
            'maybe': 'bad',
            'box': {'value': 'bad'},
            'boxes': [{'value': 'bad'}],
        }

        with self.assertRaises(ValidationError) as cm:
            validate(StringGenericAnnotations[int], data, collect_errors=True)

        self.assertEqual([issue.path for issue in cm.exception.errors],
                         ['item', 'maybe', 'box.value', 'boxes[0].value'])

    # --- T resolved to a dataclass ---

    def test_typevar_resolved_to_dataclass(self):
        obj = load(Box, {'value': {'name': 'Alice', 'age': 30}}, type_vars={T: User})
        self.assertIsInstance(obj.value, User)
        self.assertEqual(obj.value.name, 'Alice')

    def test_typevar_resolved_in_nested_dataclass(self):
        obj = load(GenericNested, {'name': 'nested', 'box': {'value': 42}},
                   type_vars={T: int})
        self.assertEqual(obj.box.value, 42)

    def test_typevar_resolved_in_nested_dataclass_rejects(self):
        with self.assertRaises(TypeError):
            load(GenericNested, {'name': 'nested', 'box': {'value': 'bad'}},
                 type_vars={T: int})

    def test_parameterized_nested_dataclass_field(self):
        obj = load(WithParameterizedBox, {'box': {'value': 42}})

        self.assertIsInstance(obj.box, Box)
        self.assertEqual(obj.box.value, 42)

    def test_parameterized_nested_dataclass_field_rejects(self):
        with self.assertRaises(TypeError) as cm:
            load(WithParameterizedBox, {'box': {'value': 'bad'}})

        msg = str(cm.exception)
        self.assertIn('box.value', msg)
        self.assertIn('int', msg)

    def test_parameterized_nested_dataclass_list_field(self):
        obj = load(WithParameterizedBoxList,
                   {'boxes': [{'value': 1}, {'value': 2}]})

        self.assertEqual([box.value for box in obj.boxes], [1, 2])
        self.assertIsInstance(obj.boxes[0], Box)

    def test_parameterized_nested_dataclass_list_field_rejects(self):
        with self.assertRaises(TypeError) as cm:
            load(WithParameterizedBoxList,
                 {'boxes': [{'value': 1}, {'value': 'bad'}]})

        msg = str(cm.exception)
        self.assertIn('boxes[1].value', msg)
        self.assertIn('int', msg)

    def test_parameterized_nested_dataclass_dict_field(self):
        obj = load(WithParameterizedBoxDict,
                   {'boxes': {'first': {'value': 1}, 'second': {'value': 2}}})

        self.assertEqual(obj.boxes['first'].value, 1)
        self.assertEqual(obj.boxes['second'].value, 2)

    def test_parameterized_nested_dataclass_dict_field_rejects(self):
        with self.assertRaises(TypeError) as cm:
            load(WithParameterizedBoxDict,
                 {'boxes': {'first': {'value': 1}, 'bad': {'value': 'bad'}}})

        msg = str(cm.exception)
        self.assertIn('boxes[bad].value', msg)
        self.assertIn('int', msg)

    def test_parameterized_nested_dataclass_field_resolved_to_dataclass(self):
        obj = load(WithParameterizedUserBox,
                   {'box': {'value': {'name': 'Alice', 'age': 30}}})

        self.assertIsInstance(obj.box.value, User)
        self.assertEqual(obj.box.value.name, 'Alice')

    def test_parameterized_nested_dataclass_field_resolved_to_dataclass_rejects(self):
        with self.assertRaises(TypeError) as cm:
            load(WithParameterizedUserBox,
                 {'box': {'value': {'name': 'Alice', 'age': 'bad'}}})

        msg = str(cm.exception)
        self.assertIn('box.value.age', msg)
        self.assertIn('int', msg)

    def test_list_typevar_resolved_to_dataclass(self):
        data = {'items': [{'name': 'Alice', 'age': 30}, {'name': 'Bob', 'age': 25}]}
        obj = load(GenericList, data, type_vars={T: User})
        self.assertEqual(len(obj.items), 2)
        self.assertIsInstance(obj.items[0], User)

    # --- Classmethod with type_vars ---

    def test_generic_classmethod_requires_type_vars(self):
        with self.assertRaises(TypeError):
            Box.load({'value': 42})

        with self.assertRaises(TypeError):
            Box.load({'value': 42}, type_vars={})

        with self.assertRaises(TypeError):
            Box.loads('{"value": 42}')

        with self.assertRaises(TypeError):
            Box.loads('{"value": 42}', type_vars={})

        with self.assertRaises(TypeError):
            Box[int].load({'value': 42})

        with self.assertRaises(TypeError):
            Box[int].loads('{"value": 42}')

    def test_classmethod_with_type_vars(self):
        obj = Box.load({'value': 42}, type_vars={T: int})
        self.assertEqual(obj.value, 42)

    def test_classmethod_loads_with_type_vars(self):
        obj = Box.loads('{"value": 42}', type_vars={T: int})
        self.assertEqual(obj.value, 42)

    def test_classmethod_type_vars_rejects(self):
        with self.assertRaises(TypeError):
            Box.load({'value': 'bad'}, type_vars={T: int})

    # --- Error messages ---

    def test_typevar_error_message(self):
        with self.assertRaises(TypeError) as cm:
            load(Box, {'value': 'bad'}, type_vars={T: int})

        msg = str(cm.exception)
        self.assertIn('value', msg)
        self.assertIn('int', msg)

    def test_list_typevar_error_path(self):
        with self.assertRaises(TypeError) as cm:
            load(GenericList, {'items': [1, 'bad']}, type_vars={T: int})

        self.assertIn('items[1]', str(cm.exception))


# ---------------------------------------------------------------------------
# Tests: generic inheritance (auto-resolution from class hierarchy)
# ---------------------------------------------------------------------------

class TestGenericInheritance(unittest.TestCase):

    # --- Basic: IntBox inherits TypedBox[int] ---

    def test_int_box_accepts_int(self):
        obj = load(IntBox, {'value': 42})
        self.assertEqual(obj.value, 42)

    def test_int_box_rejects_str(self):
        with self.assertRaises(TypeError):
            load(IntBox, {'value': 'bad'})

    def test_str_box_accepts_str(self):
        obj = load(StrBox, {'value': 'hello'})
        self.assertEqual(obj.value, 'hello')

    def test_str_box_rejects_int(self):
        with self.assertRaises(TypeError):
            load(StrBox, {'value': 42})

    def test_inherited_generic_transform_accepts(self):
        obj = load(IntListBoxWithOwn, {'value': [1, 2], 'item': 3})
        alias_obj = load(ListBoxWithOwn[int], {'value': [4, 5], 'item': 6})

        self.assertEqual(obj.value, [1, 2])
        self.assertEqual(obj.item, 3)
        self.assertEqual(alias_obj.value, [4, 5])
        self.assertEqual(alias_obj.item, 6)

    def test_inherited_generic_transform_with_explicit_type_vars(self):
        obj = load(ListBoxWithOwn, {'value': [1, 2], 'item': 3},
                   type_vars={T: int})

        self.assertEqual(obj.value, [1, 2])
        self.assertEqual(obj.item, 3)

        with self.assertRaises(ValidationError) as cm:
            validate(ListBoxWithOwn, {'value': [1, 'bad'], 'item': 'bad'},
                     type_vars={T: int}, collect_errors=True)

        self.assertEqual([issue.path for issue in cm.exception.errors],
                         ['value[1]', 'item'])

    def test_inherited_generic_transform_rejects_base_field_element(self):
        with self.assertRaises(TypeError) as cm:
            load(IntListBoxWithOwn, {'value': [1, 'bad'], 'item': 3})

        self.assertIn('value[1]', str(cm.exception))

    def test_inherited_generic_transform_rejects_owner_field(self):
        with self.assertRaises(TypeError) as cm:
            load(IntListBoxWithOwn, {'value': [1, 2], 'item': 'bad'})

        self.assertIn('item', str(cm.exception))

    def test_inherited_generic_transform_collects_errors(self):
        with self.assertRaises(ValidationError) as cm:
            validate(IntListBoxWithOwn, {'value': [1, 'bad'], 'item': 'bad'},
                     collect_errors=True)

        self.assertEqual([issue.path for issue in cm.exception.errors],
                         ['value[1]', 'item'])

    # --- Two TypeVars: IntStrPair inherits TypedPair[int, str] ---

    def test_int_str_pair_accepts(self):
        obj = load(IntStrPair, {'first': 1, 'second': 'hello'})
        self.assertEqual(obj.first, 1)
        self.assertEqual(obj.second, 'hello')

    def test_int_str_pair_rejects_wrong_first(self):
        with self.assertRaises(TypeError):
            load(IntStrPair, {'first': 'bad', 'second': 'ok'})

    def test_int_str_pair_rejects_wrong_second(self):
        with self.assertRaises(TypeError):
            load(IntStrPair, {'first': 1, 'second': 99})

    def test_inherited_generic_reordered_type_vars_accepts(self):
        obj = load(SwappedIntStrPair, {'first': 'hello', 'second': 42})
        alias_obj = load(SwappedPair[int, str],
                         {'first': 'world', 'second': 7})

        self.assertEqual(obj.first, 'hello')
        self.assertEqual(obj.second, 42)
        self.assertEqual(alias_obj.first, 'world')
        self.assertEqual(alias_obj.second, 7)

    def test_inherited_generic_reordered_type_vars_rejects(self):
        with self.assertRaises(ValidationError) as cm:
            validate(SwappedIntStrPair, {'first': 1, 'second': 'bad'},
                     collect_errors=True)

        self.assertEqual([issue.path for issue in cm.exception.errors],
                         ['first', 'second'])

    def test_future_annotations_inherited_generic_transform(self):
        if sys.version_info < (3,):
            self.skipTest('future annotations are Python 3 only')

        sentinel = object()
        names = ('FutureInheritedT', 'FutureInheritedBase',
                 'FutureInheritedListBase', 'FutureInheritedIntList')
        previous = dict((name, globals().get(name, sentinel)) for name in names)
        try:
            six.exec_(
                'from __future__ import annotations\n'
                'FutureInheritedT = TypeVar("FutureInheritedT")\n'
                '@dataclass\n'
                'class FutureInheritedBase(Generic[FutureInheritedT]):\n'
                '    value: FutureInheritedT\n'
                '@dataclass\n'
                'class FutureInheritedListBase('
                'FutureInheritedBase[List[FutureInheritedT]], '
                'Generic[FutureInheritedT]):\n'
                '    item: FutureInheritedT\n'
                '@dataclass\n'
                'class FutureInheritedIntList('
                'FutureInheritedListBase[int]):\n'
                '    pass\n',
                globals())
            FutureInheritedIntList = globals()['FutureInheritedIntList']

            obj = load(FutureInheritedIntList, {
                'value': [1, 2],
                'item': 3,
            })

            self.assertEqual(obj.value, [1, 2])
            self.assertEqual(obj.item, 3)

            with self.assertRaises(ValidationError) as cm:
                validate(FutureInheritedIntList, {
                    'value': [1, 'bad'],
                    'item': 'bad',
                }, collect_errors=True)

            self.assertEqual([issue.path for issue in cm.exception.errors],
                             ['value[1]', 'item'])
        finally:
            for name, value in previous.items():
                if value is sentinel:
                    globals().pop(name, None)
                else:
                    globals()[name] = value

    # --- Generic container: IntContainer inherits TypedContainer[int] -> List[int] ---

    def test_int_container_accepts(self):
        obj = load(IntContainer, {'items': [1, 2, 3]})
        self.assertEqual(obj.items, [1, 2, 3])

    def test_int_container_rejects_wrong_element(self):
        with self.assertRaises(TypeError):
            load(IntContainer, {'items': [1, 'bad']})

    def test_int_container_empty(self):
        obj = load(IntContainer, {'items': []})
        self.assertEqual(obj.items, [])

    # --- Mixed fields: IntBoxWithExtra has T=int + regular str ---

    def test_mixed_fields(self):
        obj = load(IntBoxWithExtra, {'value': 42, 'label': 'test'})
        self.assertEqual(obj.value, 42)
        self.assertEqual(obj.label, 'test')

    def test_mixed_fields_rejects_wrong_generic(self):
        with self.assertRaises(TypeError):
            load(IntBoxWithExtra, {'value': 'bad', 'label': 'test'})

    def test_mixed_fields_rejects_wrong_regular(self):
        with self.assertRaises(TypeError):
            load(IntBoxWithExtra, {'value': 42, 'label': 123})

    # --- Explicit type_vars override inferred ---

    def test_explicit_overrides_inferred(self):
        # IntBox infers T=int, but explicit type_vars={T: str} should override
        obj = load(IntBox, {'value': 'hello'}, type_vars={T: str})
        self.assertEqual(obj.value, 'hello')

    # --- Classmethod works with auto-resolution ---

    def test_classmethod_auto_resolution(self):
        obj = IntBox.load({'value': 42})
        self.assertEqual(obj.value, 42)

    def test_classmethod_auto_resolution_rejects(self):
        with self.assertRaises(TypeError):
            IntBox.load({'value': 'bad'})

    def test_classmethod_loads_auto_resolution(self):
        obj = IntBox.loads('{"value": 42}')
        self.assertEqual(obj.value, 42)

    # --- Roundtrip ---

    def test_roundtrip_generic_inheritance(self):
        obj = IntBox(42)
        obj2 = IntBox.loads(obj.dumps())
        self.assertEqual(obj, obj2)

    # --- Parent class (still generic) works as before ---

    def test_parent_still_generic_no_validation(self):
        # TypedBox[T] without type_vars -- accepts anything
        obj = load(TypedBox, {'value': 'anything'})
        self.assertEqual(obj.value, 'anything')

    def test_parent_with_explicit_type_vars(self):
        obj = load(TypedBox, {'value': 42}, type_vars={T: int})
        self.assertEqual(obj.value, 42)


# ---------------------------------------------------------------------------
# Tests: bound TypeVar
# ---------------------------------------------------------------------------

class TestBoundTypeVar(unittest.TestCase):

    def test_bound_accepts_exact_type(self):
        a = Animal('Buddy')
        obj = load(Shelter, {'pet': a})
        self.assertIs(obj.pet, a)

    def test_bound_accepts_subclass(self):
        d = Dog('Rex')
        obj = load(Shelter, {'pet': d})
        self.assertIs(obj.pet, d)

    def test_bound_accepts_another_subclass(self):
        c = Cat('Whiskers')
        obj = load(Shelter, {'pet': c})
        self.assertIs(obj.pet, c)

    def test_bound_rejects_wrong_type(self):
        with self.assertRaises(TypeError):
            load(Shelter, {'pet': 'not an animal'})

    def test_bound_rejects_int(self):
        with self.assertRaises(TypeError):
            load(Shelter, {'pet': 42})

    def test_bound_rejects_none(self):
        with self.assertRaises(TypeError):
            load(Shelter, {'pet': None})

    def test_bound_int_accepts_int(self):
        obj = load(BoundIntBox, {'value': 42})
        self.assertEqual(obj.value, 42)

    def test_bound_int_rejects_str(self):
        with self.assertRaises(TypeError):
            load(BoundIntBox, {'value': 'bad'})

    def test_bound_int_rejects_bool(self):
        # bool is subclass of int, but runtime validation rejects bool for int
        with self.assertRaises(TypeError):
            load(BoundIntBox, {'value': True})


# ---------------------------------------------------------------------------
# Tests: constrained TypeVar
# ---------------------------------------------------------------------------

class TestConstrainedTypeVar(unittest.TestCase):

    def test_constrained_accepts_int(self):
        obj = load(ConstrainedBox, {'value': 42})
        self.assertEqual(obj.value, 42)

    def test_constrained_accepts_str(self):
        obj = load(ConstrainedBox, {'value': 'hello'})
        self.assertEqual(obj.value, 'hello')

    def test_constrained_coerces_float_to_int(self):
        obj = load(ConstrainedBox, {'value': 3.14})

        self.assertEqual(obj.value, 3)

    def test_constrained_rejects_float_with_strict_types(self):
        with self.assertRaises(TypeError):
            load(ConstrainedBox, {'value': 3.14}, strict_types=True)

    def test_constrained_rejects_list(self):
        with self.assertRaises(TypeError):
            load(ConstrainedBox, {'value': [1, 2]})

    def test_constrained_rejects_none(self):
        with self.assertRaises(TypeError):
            load(ConstrainedBox, {'value': None})

    def test_constrained_rejects_bool(self):
        # bool is subclass of int but runtime validation rejects it
        with self.assertRaises(TypeError):
            load(ConstrainedBox, {'value': True})

    def test_constrained_list_accepts_ints(self):
        obj = load(ConstrainedList, {'items': [1, 2, 3]})
        self.assertEqual(obj.items, [1, 2, 3])

    def test_constrained_list_accepts_strs(self):
        obj = load(ConstrainedList, {'items': ['a', 'b']})
        self.assertEqual(obj.items, ['a', 'b'])

    def test_constrained_list_coerces_float_to_int(self):
        obj = load(ConstrainedList, {'items': [1, 3.14]})

        self.assertEqual(obj.items, [1, 3])

    def test_constrained_list_rejects_float_with_strict_types(self):
        with self.assertRaises(TypeError):
            load(ConstrainedList, {'items': [1, 3.14]},
                 strict_types=True)

    def test_constrained_error_message(self):
        with self.assertRaises(TypeError) as cm:
            load(ConstrainedBox, {'value': []})

        msg = str(cm.exception)
        self.assertIn('value', msg)
        self.assertIn('constraint', msg)


# ---------------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
