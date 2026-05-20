from __future__ import print_function
from tests.load_fixtures import *

# Tests: nested dataclasses
# ---------------------------------------------------------------------------

class TestNested(unittest.TestCase):

    def test_nested_dataclass(self):
        data = {'name': 'John', 'address': {'city': 'NYC', 'zip_code': '10001'}}
        obj = load(UserWithAddress, data)
        self.assertEqual(obj.name, 'John')
        self.assertIsInstance(obj.address, Address)
        self.assertEqual(obj.address.city, 'NYC')
        self.assertEqual(obj.address.zip_code, '10001')

    def test_deeply_nested(self):
        data = {
            'name': 'group1',
            'groups': [
                {
                    'name': 'Alice',
                    'address': {'city': 'NYC', 'zip_code': '10001'}
                },
                {
                    'name': 'Bob',
                    'address': {'city': 'LA', 'zip_code': '90001'}
                },
            ]
        }
        obj = load(DeeplyNested, data)
        self.assertEqual(obj.name, 'group1')
        self.assertEqual(len(obj.groups), 2)
        self.assertIsInstance(obj.groups[0], UserWithAddress)
        self.assertEqual(obj.groups[0].address.city, 'NYC')
        self.assertEqual(obj.groups[1].name, 'Bob')

    def test_nested_wrong_type(self):
        data = {'name': 'John', 'address': 'not_a_dict'}
        with self.assertRaises(TypeError):
            load(UserWithAddress, data)

    def test_nested_inner_validation(self):
        data = {'name': 'John', 'address': {'city': 123, 'zip_code': '10001'}}
        with self.assertRaises(TypeError):
            load(UserWithAddress, data)


# ---------------------------------------------------------------------------
# Tests: generic types
# ---------------------------------------------------------------------------

class TestGenerics(unittest.TestCase):

    def test_list_of_int(self):
        obj = load(WithList, {'values': [1, 2, 3]})
        self.assertEqual(obj.values, [1, 2, 3])

    def test_list_of_int_wrong_element(self):
        with self.assertRaises(TypeError):
            load(WithList, {'values': [1, 'two', 3]})

    def test_list_not_a_list(self):
        with self.assertRaises(TypeError):
            load(WithList, {'values': 'not_a_list'})

    def test_dict_str_int(self):
        obj = load(WithDict, {'mapping': {'a': 1, 'b': 2}})
        self.assertEqual(obj.mapping, {'a': 1, 'b': 2})

    def test_dict_wrong_value_type(self):
        with self.assertRaises(TypeError):
            load(WithDict, {'mapping': {'a': 'not_int'}})

    def test_tuple_from_list(self):
        obj = load(WithTuple, {'pair': [42, 'hello']})
        self.assertIsInstance(obj.pair, tuple)
        self.assertEqual(obj.pair, (42, 'hello'))

    def test_tuple_wrong_length(self):
        with self.assertRaises(TypeError):
            load(WithTuple, {'pair': [1, 'a', 'extra']})

    def test_tuple_wrong_element_type(self):
        with self.assertRaises(TypeError):
            load(WithTuple, {'pair': ['not_int', 'hello']})

    def test_variadic_tuple_from_list(self):
        obj = load(WithVarTuple, {'values': [1, 2, 3]})
        self.assertIsInstance(obj.values, tuple)
        self.assertEqual(obj.values, (1, 2, 3))

    def test_variadic_tuple_wrong_element_type(self):
        with self.assertRaises(TypeError):
            load(WithVarTuple, {'values': [1, 'bad', 3]})

    def test_variadic_tuple_collects_element_path(self):
        with self.assertRaises(ValidationError) as cm:
            validate(WithVarTuple, {'values': [1, 'bad', False]},
                     collect_errors=True)

        self.assertEqual(
            [issue.path for issue in cm.exception.errors],
            ['values[1]', 'values[2]'])

    def test_list_of_dataclass(self):
        data = {'users': [{'name': 'Alice', 'age': 30}, {'name': 'Bob', 'age': 25}]}
        obj = load(WithNestedList, data)
        self.assertEqual(len(obj.users), 2)
        self.assertIsInstance(obj.users[0], User)
        self.assertEqual(obj.users[0].name, 'Alice')
        self.assertEqual(obj.users[1].age, 25)

    def test_empty_list(self):
        obj = load(WithList, {'values': []})
        self.assertEqual(obj.values, [])

    def test_empty_dict(self):
        obj = load(WithDict, {'mapping': {}})
        self.assertEqual(obj.mapping, {})


# ---------------------------------------------------------------------------
# Tests: nested collections (List[List[...]], Dict[str, List[...]], etc.)
# ---------------------------------------------------------------------------

class TestNestedCollections(unittest.TestCase):

    def test_list_of_lists(self):
        data = {'matrix': [[1, 2], [3, 4], [5, 6]]}
        obj = load(WithNestedListOfLists, data)
        self.assertEqual(obj.matrix, [[1, 2], [3, 4], [5, 6]])

    def test_list_of_lists_wrong_inner_type(self):
        with self.assertRaises(TypeError):
            load(WithNestedListOfLists, {'matrix': [[1, 'bad'], [3, 4]]})

    def test_list_of_lists_inner_not_list(self):
        with self.assertRaises(TypeError):
            load(WithNestedListOfLists, {'matrix': [1, 2, 3]})

    def test_list_of_lists_empty(self):
        obj = load(WithNestedListOfLists, {'matrix': []})
        self.assertEqual(obj.matrix, [])

    def test_list_of_lists_empty_inner(self):
        obj = load(WithNestedListOfLists, {'matrix': [[], [1]]})
        self.assertEqual(obj.matrix, [[], [1]])

    def test_list_of_dicts(self):
        data = {'records': [{'a': 1, 'b': 2}, {'c': 3}]}
        obj = load(WithListOfDicts, data)
        self.assertEqual(obj.records, [{'a': 1, 'b': 2}, {'c': 3}])

    def test_list_of_dicts_wrong_value(self):
        with self.assertRaises(TypeError):
            load(WithListOfDicts, {'records': [{'a': 'not_int'}]})

    def test_list_of_dicts_inner_not_dict(self):
        with self.assertRaises(TypeError):
            load(WithListOfDicts, {'records': ['not_a_dict']})

    def test_dict_of_lists(self):
        data = {'groups': {'evens': [2, 4, 6], 'odds': [1, 3, 5]}}
        obj = load(WithDictOfLists, data)
        self.assertEqual(obj.groups, {'evens': [2, 4, 6], 'odds': [1, 3, 5]})

    def test_dict_of_lists_wrong_element(self):
        with self.assertRaises(TypeError):
            load(WithDictOfLists, {'groups': {'a': [1, 'bad']}})

    def test_dict_of_lists_value_not_list(self):
        with self.assertRaises(TypeError):
            load(WithDictOfLists, {'groups': {'a': 'not_list'}})

    def test_list_of_tuples(self):
        data = {'pairs': [['alice', 1], ['bob', 2]]}
        obj = load(WithListOfTuples, data)
        self.assertEqual(obj.pairs, [('alice', 1), ('bob', 2)])
        self.assertIsInstance(obj.pairs[0], tuple)

    def test_list_of_tuples_wrong_inner(self):
        with self.assertRaises(TypeError):
            load(WithListOfTuples, {'pairs': [['alice', 'not_int']]})

    def test_tuple_rejects_non_sequence(self):
        with self.assertRaises(TypeError):
            load(WithTuple, {'pair': 'not-a-tuple'})

    def test_dict_of_dataclasses(self):
        data = {'users': {
            'alice': {'name': 'Alice', 'age': 30},
            'bob': {'name': 'Bob', 'age': 25},
        }}
        obj = load(WithDictOfDataclasses, data)
        self.assertEqual(len(obj.users), 2)
        self.assertIsInstance(obj.users['alice'], User)
        self.assertEqual(obj.users['alice'].name, 'Alice')
        self.assertEqual(obj.users['bob'].age, 25)

    def test_dict_of_dataclasses_wrong_value(self):
        with self.assertRaises(TypeError):
            load(WithDictOfDataclasses, {'users': {'alice': 'not_a_dict'}})

    def test_list_of_optional(self):
        data = {'values': [1, None, 3, None]}
        obj = load(WithListOfOptional, data)
        self.assertEqual(obj.values, [1, None, 3, None])

    def test_list_of_optional_wrong_type(self):
        with self.assertRaises(TypeError):
            load(WithListOfOptional, {'values': [1, 'bad', 3]})

    def test_set_generic_accepts_sequence(self):
        obj = load(WithSet, {'values': [1, 2, 2]})

        self.assertEqual(obj.values, set([1, 2]))

    def test_set_generic_rejects_non_sequence(self):
        with self.assertRaises(TypeError):
            load(WithSet, {'values': 'not-a-set'})

    def test_set_generic_rejects_wrong_element(self):
        with self.assertRaises(TypeError):
            load(WithSet, {'values': [1, 'bad']})

    def test_union_generic_accepts_first_type(self):
        obj = load(WithUnion, {'value': 42})

        self.assertEqual(obj.value, 42)

    def test_union_generic_accepts_second_type(self):
        obj = load(WithUnion, {'value': 'forty-two'})

        self.assertEqual(obj.value, 'forty-two')

    def test_union_generic_rejects_unknown_type(self):
        with self.assertRaises(TypeError):
            load(WithUnion, {'value': []})

    def test_nested_dataclass_instance_passthrough(self):
        address = Address('NYC', '10001')

        obj = load(UserWithAddress, {'name': 'Bob', 'address': address})

        self.assertIs(obj.address, address)

    def test_roundtrip_nested_collections(self):
        obj = WithNestedListOfLists(matrix=[[1, 2], [3, 4]])
        obj2 = WithNestedListOfLists.loads(obj.dumps())
        self.assertEqual(obj, obj2)

    def test_roundtrip_dict_of_lists(self):
        obj = WithDictOfLists(groups={'a': [1, 2], 'b': [3]})
        obj2 = WithDictOfLists.loads(obj.dumps())
        self.assertEqual(obj, obj2)

    def test_roundtrip_dict_of_dataclasses(self):
        obj = WithDictOfDataclasses(users={
            'a': User('Alice', 30),
            'b': User('Bob', 25),
        })

        obj2 = load(WithDictOfDataclasses, dump(obj))

        self.assertEqual(obj, obj2)

    def test_nested_error_path_list_of_lists(self):
        with self.assertRaises(TypeError) as cm:
            load(WithNestedListOfLists, {'matrix': [[1, 2], [3, 'bad']]})

        self.assertIn('matrix[1]', str(cm.exception))

    def test_nested_error_path_dict_of_lists(self):
        with self.assertRaises(TypeError) as cm:
            load(WithDictOfLists, {'groups': {'evens': [2, 'bad']}})

        self.assertIn('groups', str(cm.exception))

    def test_nested_error_path_dict_of_dataclasses(self):
        with self.assertRaises(TypeError) as cm:
            load(WithDictOfDataclasses, {
                'users': {'alice': {'name': 123, 'age': 30}}
            })

        msg = str(cm.exception)
        self.assertIn('name', msg)
        self.assertIn('str', msg)


# ---------------------------------------------------------------------------
# Tests: ClassVar, InitVar, init=False
# ---------------------------------------------------------------------------

class TestClassVarInitVar(unittest.TestCase):

    # --- ClassVar ---

    def test_classvar_skipped_on_load(self):
        obj = load(WithClassVar, {'x': 42})
        self.assertEqual(obj.x, 42)
        self.assertEqual(WithClassVar.class_val, 10)

    def test_classvar_in_data_raises_by_default(self):
        with self.assertRaises(TypeError):
            load(WithClassVar, {'x': 42, 'class_val': 999})

    def test_classvar_in_data_excluded(self):
        obj = load(WithClassVar, {'x': 42, 'class_val': 999},
                   unknown=EXCLUDE)
        self.assertEqual(obj.x, 42)
        self.assertEqual(WithClassVar.class_val, 10)

    def test_classvar_not_in_fields(self):
        from dataclasses import fields as dc_fields
        fs = dc_fields(WithClassVar)
        names = [f.name for f in fs]
        self.assertNotIn('class_val', names)
        self.assertIn('x', names)

    # --- InitVar ---

    def test_initvar_with_value(self):
        obj = load(WithInitVar, {'x': 5, 'scale': 3})
        self.assertEqual(obj.x, 15)

    def test_initvar_uses_default(self):
        obj = load(WithInitVar, {'x': 5})
        self.assertEqual(obj.x, 5)  # scale defaults to 1

    def test_initvar_required_present(self):
        obj = load(WithInitVarRequired, {'x': 5, 'multiplier': 4})
        self.assertEqual(obj.x, 20)

    def test_initvar_required_missing(self):
        with self.assertRaises(ValueError):
            load(WithInitVarRequired, {'x': 5})

    @unittest.skipIf(sys.version_info >= (3,), "InitVar type validation differs on Python 3")
    def test_initvar_type_validated(self):
        with self.assertRaises(TypeError):
            load(WithInitVar, {'x': 5, 'scale': 'not_int'})

    def test_initvar_not_in_fields(self):
        from dataclasses import fields as dc_fields
        obj = load(WithInitVar, {'x': 5, 'scale': 3})
        # InitVar is not in fields() output (not a stored field)
        names = [f.name for f in dc_fields(obj)]
        self.assertNotIn('scale', names)

    # --- init=False ---

    def test_init_false_computed(self):
        obj = load(WithInitFalse, {'x': 5})
        self.assertEqual(obj.x, 5)
        self.assertEqual(obj.y, 10)  # set by __post_init__

    def test_init_false_in_data_raises_by_default(self):
        with self.assertRaises(TypeError):
            load(WithInitFalse, {'x': 5, 'y': 999})

    def test_init_false_in_data_excluded(self):
        obj = load(WithInitFalse, {'x': 5, 'y': 999}, unknown=EXCLUDE)
        self.assertEqual(obj.y, 10)  # __post_init__ sets it, not the data

    def test_init_false_in_data_unknown_raise(self):
        with self.assertRaises(TypeError):
            load(WithInitFalse, {'x': 5, 'y': 999}, unknown=RAISE)

    # --- Combined ClassVar + InitVar + init=False ---

    def test_combined_classvar_initvar_initfalse(self):
        obj = load(WithClassVarAndInitVar, {'x': 5, 'scale': 3})
        self.assertEqual(obj.x, 5)
        self.assertEqual(obj.computed, 15)  # x * scale via __post_init__
        self.assertEqual(WithClassVarAndInitVar.class_name, 'MyClass')

    def test_combined_defaults(self):
        obj = load(WithClassVarAndInitVar, {'x': 7})
        self.assertEqual(obj.x, 7)
        self.assertEqual(obj.computed, 7)  # scale defaults to 1

    def test_combined_dump_excludes_initvar(self):
        obj = load(WithClassVarAndInitVar, {'x': 5, 'scale': 3})
        d = dump(obj)
        self.assertIn('x', d)
        self.assertIn('computed', d)
        self.assertNotIn('scale', d)       # InitVar not stored
        self.assertNotIn('class_name', d)  # ClassVar not in fields

    def test_combined_loads_json(self):
        obj = WithClassVarAndInitVar.loads('{"x": 10, "scale": 2}')
        self.assertEqual(obj.x, 10)
        self.assertEqual(obj.computed, 20)


# ---------------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
