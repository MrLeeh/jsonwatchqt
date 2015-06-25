"""
    Copyright © 2015 by Stefan Lehmann

"""
from jsonwatch.jsonobject import JsonObject
from jsonwatch.jsonvalue import JsonValue


class MapItem:
    def __init__(self, key, obj, getter='value', setter='setValue'):
        self.key = key
        self.obj = obj
        self.setter = setter
        self.getter = getter


class JsonMapper:
    def __init__(self, node: JsonObject):
        self.mappings = []
        self.node = node

    def map(self, key, obj, getter='value', setter='setValue'):
        item = MapItem(key, obj, getter, setter)
        self.mappings.append(item)

    def map_from_node(self):
        for item in self.mappings:
            fset = getattr(item.obj, item.setter)
            try:
                fset(self.node[item.key].value)
            except KeyError as e:
                pass

    def map_to_node(self):
        for item in self.mappings:
            fget = getattr(item.obj, item.getter)
            try:
                jsonvalue = self.node[item.key]
            except KeyError:
                jsonvalue = JsonValue(item.key)
                self.node.add_child(jsonvalue)
            jsonvalue.value = fget()
        print(self.node.to_json())