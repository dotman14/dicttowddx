import base64
import re
from collections.abc import Iterable
from yattag import Doc, indent


class DictToWDDX:
    """This class is used to convert a simple python dict to wddx data format"""

    def __init__(
        self,
        data: dict,
        force_type: bool = False,
        format_output: bool = False,
        indent: int = 4,
    ):
        if not data or not isinstance(data, dict):
            raise TypeError(f"Data must be of type dict, type {type(data)} given")
        self.data = data
        self.format_output = format_output
        self.indent = indent
        self.force_output = force_type
        self.doc, self.tag, self.text = Doc().tagtext()

    def to_type(self, value):
        """This function is used to convert a value to a type"""
        non_str = {
            "bool": "boolean",
            "int": "number",
            "float": "number",
            "bytes": "binary",
        }
        original_type = type(value).__name__
        if original_type != "str":
            return non_str.get(original_type, "string")

        _type = "string"
        type_dict = {
            # "binary": re.compile(r"^[A-Za-z0-9+/=]+$"),
            # "boolean": re.compile(r"^(?:True|False)$"),
            # "int": re.compile(r"^\d+$"),
            "dateTime": re.compile(
                r"^\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}:\d{2}(\.\d+)?(?:Z|[+-]\d{2}:\d{2})?| \d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})?)$"
            ),
        }
        for k, v in type_dict.items():
            if v.match(str(value)):
                _type = k
                break
        return _type

    def wddx_type(self, value):
        """This function is used to force the type of the value"""
        return self.to_type(value) if self.force_output else "string"

    def is_binary(self, value):
        """This function is used to check if the value is binary"""
        if self.wddx_type(value) == "binary":
            return self.text(base64.b64encode(value).decode())
        return self.text(str(value))

    def to_wddx(self):
        """This function is used to convert a simple python dict to wddx data format"""

        self.doc.asis("<wddxPacket version='1.0'><header/>")
        with self.tag("data"):
            with self.tag("struct"):
                for key in self.data:
                    if key is None:
                        raise KeyError("Key cannot be None", "{}".format(key))
                    if isinstance(self.data.get(key), Iterable) and (
                        not isinstance(self.data.get(key), str | bytes)
                    ):
                        with self.tag("var", name=key):
                            with self.tag("array", length=len(self.data.get(key))):
                                for elem in self.data.get(key):
                                    if elem is None:
                                        self.doc.asis("<null/>")
                                    else:
                                        with self.tag(self.wddx_type(elem)):
                                            self.is_binary(elem)
                    else:
                        with self.tag("var", name=key):
                            if self.data.get(key) is None:
                                self.doc.asis("<null/>")
                            else:
                                with self.tag(self.wddx_type(self.data.get(key))):
                                    self.is_binary(self.data.get(key))
        self.doc.asis("</wddxPacket>")
        val = self.doc.getvalue()
        return (
            val
            if not self.format_output
            else indent(val, indentation=" " * self.indent, newline="\n")
        )
