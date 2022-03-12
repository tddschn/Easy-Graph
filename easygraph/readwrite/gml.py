
"""
Read graphs in GML format.

"GML, the Graph Modelling Language, is our proposal for a portable
file format for graphs. GML's key features are portability, simple
syntax, extensibility and flexibility. A GML file consists of a
hierarchical key-value lists. Graphs can be annotated with arbitrary
data structures. The idea for a common file format was born at the
GD'95; this proposal is the outcome of many discussions. GML is the
standard file format in the Graphlet graph editor system. It has been
overtaken and adapted by several other systems for drawing graphs."

GML files are stored using a 7-bit ASCII encoding with any extended
ASCII characters (iso8859-1) appearing as HTML character entities.
You will need to give some thought into how the exported data should
interact with different languages and even different Python versions.
Re-importing from gml is also a concern.

Without specifying a `stringizer`/`destringizer`, the code is capable of
writing `int`/`float`/`str`/`dict`/`list` data as required by the GML 
specification.  For writing other data types, and for reading data other
than `str` you need to explicitly supply a `stringizer`/`destringizer`.

For additional documentation on the GML file format, please see the
`GML website <https://web.archive.org/web/20190207140002/http://www.fim.uni-passau.de/index.php?id=17297&L=1>`_.

Several example graphs in GML format may be found on Mark Newman's
`Network data page <http://www-personal.umich.edu/~mejn/netdata/>`_.
"""

from contextlib import AsyncExitStack
from errno import E2BIG
from io import StringIO
from ast import literal_eval
from collections import defaultdict
from enum import Enum
from lib2to3.pgen2 import token
from typing import Any, NamedTuple
from unicodedata import category
import easygraph as eg
import warnings
import re
import html.entities as htmlentitydefs

from easygraph.utils.exception import EasyGraphError
from easygraph.utils import open_file

__all__ = ["read_gml", "parse_gml", "generate_gml", "write_gml"]

LIST_START_VALUE = "_easygraph_list_start"

def escape(text):
    """Use XML character references to escape characters.

    Use XML character references for unprintable or non-ASCII
    characters, double quotes and ampersands in a string
    """

    def fixup(m):
        ch = m.group(0)
        return "&#" + str(ord(ch)) + ";"
    
    text = re.sub('[^ -~]|[&"]', fixup, text)
    return text if isinstance(text, str) else str(text)

def unescape(text):
    """Replace XML character references with the referenced characters"""

    def fixup(m):
        text = m.group(0)
        if text[1] == "#":
            # Character reference
            if text[2] == "x":
                code = int(text[3:-1], 16)
            else:
                code = int(text[2:-1])
        else:
            # Named entity
            try:
                code = htmlentitydefs.name2codepoint[text[1:-1]]
            except KeyError:
                return text  # leave unchanged
        try:
            return chr(code)
        except (ValueError, OverflowError):
            return text  # leave unchanged
    
    return re.sub("&(?:[0-9A-Za-z]+|#(?:[0-9]+|x[0-9A-Fa-f]+));", fixup, text)

def literal_destringizer(rep):
    """Convert a Python literal to the value it represents.

    Parameters
    ----------
    rep : string
        A Python literal.

    Returns
    -------
    value : object
        The value of the Python literal.

    Raises
    ------
    ValueError
        If `rep` is not a Python literal.
    """
    msg = "literal_destringizer is deprecated and will be removed in 3.0."
    warnings.warn(msg, DeprecationWarning)
    if isinstance(rep, str):
        orig_rep = rep
        try:
            return literal_eval(rep)
        except SyntaxError as err:
            raise ValueError(f"{orig_rep!r} is not a valid Python literal") from err
    else:
        raise ValueError(f"{rep!r} is not a string")

class Pattern(Enum):
    """encodes the index of each token-matching pattern in `tokenize`."""

    KEYS = 0
    REALS = 1
    INTS = 2
    STRINGS = 3
    DICT_START = 4
    DICT_END = 5
    COMMENT_WHITESPACE = 6

class Token(NamedTuple):
    category: Pattern
    value: Any
    line: int
    position: int

def parse_gml(lines, label="label", destringizer=None):
    def decode_line(line):
        if isinstance(line, bytes):
            try:
                line.decode("ascii")
            except UnicodeDecodeError as err:
                raise EasyGraphError("input is not ASCII-encoded") from err
        if not isinstance(line, str):
            line = str(line)
        return line

    def filter_lines(lines):
        if isinstance(lines, str):
            lines = decode_line(lines)
            lines = lines.splitlines()
            yield from lines
        else:
            for line in lines:
                line = decode_line(line)
                if line and line[-1] == "\n":
                    line = line[:-1]
                if line.find("\n") != -1:
                    raise EasyGraphError("input line contains newline")
                yield line

    G = parse_gml_lines(filter_lines(lines), label, destringizer)
    return G

def parse_gml_lines(lines, label, destringizer):
    """Parse GML `lines` into a graph."""

    def tokenize():
        patterns = [
            r"[A-Za-z][0-9A-Za-z_]*\b",  # keys
            # reals
            r"[+-]?(?:[0-9]*\.[0-9]+|[0-9]+\.[0-9]*|INF)(?:[Ee][+-]?[0-9]+)?",
            r"[+-]?[0-9]+",  # ints
            r'".*?"',  # strings
            r"\[",  # dict start
            r"\]",  # dict end
            r"#.*$|\s+",  # comments and whitespaces
        ]
        tokens = re.compile("|".join(f"({pattern})" for pattern in patterns))
        lineno = 0
        for line in lines:
            length = len(line)
            pos = 0
            while pos < length:
                match = tokens.match(line, pos)
                if match is None:
                    m = f"cannot tokenize {line[pos:]} at ({lineno + 1}, {pos + 1})"
                    raise EasyGraphError(m)
                for i in range(len(patterns)):
                    group = match.group(i + 1)
                    if group is not None:
                        if i == 0:  # keys
                            value = group.rstrip()
                        elif i == 1:  # reals
                            value = float(group)
                        elif i == 2:  # ints
                            value = int(group)
                        else:
                            value = group
                        if i != 6:  # comments and whitespaces
                            yield Token(Pattern(i), value, lineno + 1, pos + 1)
                        pos += len(group)
                        break
            lineno += 1
        yield Token(None, None, lineno + 1, 1)  # EOF

    def unexpected(curr_token, expected):
        category, value, lineno, pos = curr_token
        value = repr(value) if value is not None else "EOF"
        raise EasyGraphError(f"expected {expected}, found {value} at ({lineno}, {pos})")

    def consume(curr_token, category, expected):
        if curr_token.category == category:
            return next(tokens)
        unexpected(curr_token, expected)

    def parse_dict(curr_token):
        # dict start
        curr_token = consume(curr_token, Pattern.DICT_START, "'['")
        # dict contents
        curr_token, dct = parse_kv(curr_token)
        # dict end
        curr_token = consume(curr_token, Pattern.DICT_END, "']'")
        return curr_token, dct

    def parse_kv(curr_token):
        dct = defaultdict(list)
        while curr_token.category == Pattern.KEYS:
            key = curr_token.value
            curr_token = next(tokens)
            category = curr_token.category
            if category == Pattern.REALS or category == Pattern.INTS:
                value = curr_token.value
                curr_token = next(tokens)
            elif category == Pattern.STRINGS:
                value = unescape(curr_token.value[1:-1])
                if destringizer:
                    try:
                        value = destringizer(value)
                    except ValueError:
                        pass
                curr_token = next(tokens)
            elif category == Pattern.DICT_START:
                curr_token, value = parse_dict(curr_token)
            else:
                if key in ("id", "label", "source", "target"):
                    try:
                        # String convert the token value
                        value = unescape(str(curr_token.value))
                        if destringizer:
                            try:
                                value = destringizer(value)
                            except ValueError:
                                pass
                        curr_token = next(tokens)
                    except Exception:
                        msg = (
                            "an int, float, string, '[' or string"
                            + " convertable ASCII value for node id or label"
                        )
                        unexpected(curr_token, msg)
                elif curr_token.value in {"NAN", "INF"}:
                    value = float(curr_token.value)
                    curr_token = next(tokens)
                else:  # Otherwise error out
                    unexpected(curr_token, "an int, float, string or '['")
            dct[key].append(value)

        def clean_dict_value(value):
            if not isinstance(value, list):
                return value
            if len(value) == 1:
                return value[0]
            if value[0] == LIST_START_VALUE:
                return value[1:]
            return value

        dct = {key: clean_dict_value(value) for key, value in dct.items()}
        return curr_token, dct

    def parse_graph():
        curr_token, dct = parse_kv(next(tokens))
        if curr_token.category is not None:  # EOF
            unexpected(curr_token, "EOF")
        if "graph" not in dct:
            raise AssertionError("input contains no graph")
        graph = dct["graph"]
        if isinstance(graph, list):
            raise AssertionError("input contains more than one graph")
        return graph

    tokens = tokenize()
    graph = parse_graph()
    directed = graph.pop("directed", False)
    multigraph = graph.pop("multigraph", False)
    if not multigraph:
        G = eg.DiGraph() if directed else eg.Graph()
    graph_attr = {k: v for k, v in graph.items() if k not in ("node", "edge")}
    G.graph.update(graph_attr)

    def pop_attr(dct, category, attr, i):
        try:
            return dct.pop(attr)
        except KeyError as err:
            raise AssertionError(f"{category} #{i} has no {attr!r} attribute") from err

    nodes = graph.get("node", [])
    mapping = {}
    node_labels = set()
    for i, node in enumerate(nodes if isinstance(nodes, list) else [nodes]):
        id = pop_attr(node, "node", "id", i)
        if id in G:
            raise AssertionError(f"node id {id!r} is duplicated")
        if label is not None and label != "id":
            node_label = pop_attr(node, "node", label, i)
            if node_label in node_labels:
                raise AssertionError(f"node label {node_label!r} is duplicated")
            node_labels.add(node_label)
            mapping[id] = node_label
        G.add_node(id, **node)
    
    edges = graph.get("edge", [])
    for i, edge in enumerate(edges if isinstance(edges, list) else [edges]):
        source = pop_attr(edge, "edge", "source", i)
        target = pop_attr(edge, "edge", "target", i)
        if source not in G:
            raise AssertionError(f"edge #{i} has undefined source {source!r}")
        if target not in G:
            raise AssertionError(f"edge #{i} has undefined target {target!r}")
        if not multigraph:
            if not G.has_edge(source, target):
                G.add_edge(source, target, **edge)
            else:
                arrow = "->" if directed else "--"
                msg = f"edge #{i} ({source!r}{arrow}{target!r}) is duplicated"
                raise AssertionError(msg)
        else:
            key = edge.pop("key", None)
            if key is not None and G.has_edge(source, target, key):
                arrow = "->" if directed else "--"
                msg = f"edge #{i} ({source!r}{arrow}{target!r}, {key!r})"
                msg2 = 'Hint: If multigraph add "multigraph 1" to file header.'
                raise AssertionError(msg + " is duplicated\n" + msg2)
            G.add_edge(source, target, key, **edge)

    if label is not None and label != "id":
        G = eg.relabel_nodes(G, mapping)
    return G

def generate_gml(G, stringizer=None):
    valid_keys = re.compile("^[A-Za-z][0-9A-Za-z_]*$")

    def stringize(key, value, ignored_keys, indent, in_list=False):
        if not isinstance(key, str):
            raise EasyGraphError(f"{key!r} is not a string")
        if not valid_keys.match(key):
            raise EasyGraphError(f"{key!r} is not a valid key")
        if not isinstance(key, str):
            key = str(key)
        if key not in ignored_keys:
            if isinstance(value, (int, bool)):
                if key == "label":
                    yield indent + key + ' "' + str(value) + '"'
                elif value is True:
                    # python bool is an instance of int
                    yield indent + key + " 1"
                elif value is False:
                    yield indent + key + " 0"
                # GML only supports signed 32-bit integers
                elif value < -(2 ** 31) or value >= 2 ** 31:
                    yield indent + key + ' "' + str(value) + '"'
                else:
                    yield indent + key + " " + str(value)
            elif isinstance(value, float):
                text = repr(value).upper()
                # GML matches INF to keys, so prepend + to INF. Use repr(float(*))
                # instead of string literal to future proof against changes to repr.
                if text == repr(float("inf")).upper():
                    text = "+" + text
                else:
                    # GML requires that a real literal contain a decimal point, but
                    # repr may not output a decimal point when the mantissa is
                    # integral and hence needs fixing.
                    epos = text.rfind("E")
                    if epos != -1 and text.find(".", 0, epos) == -1:
                        text = text[:epos] + "." + text[epos:]
                if key == "label":
                    yield indent + key + ' "' + text + '"'
                else:
                    yield indent + key + " " + text
            elif isinstance(value, dict):
                yield indent + key + " ["
                next_indent = indent + "  "
                for key, value in value.items():
                    yield from stringize(key, value, (), next_indent)
                yield indent + "]"
            elif (
                isinstance(value, (list, tuple))
                and key != "label"
                and value
                and not in_list
            ):
                if len(value) == 1:
                    yield indent + key + " " + f'"{LIST_START_VALUE}"'
                for val in value:
                    yield from stringize(key, val, (), indent, True)
            else:
                if stringizer:
                    try:
                        value = stringizer(value)
                    except ValueError as err:
                        raise EasyGraphError(
                            f"{value!r} cannot be converted into a string"
                        ) from err
                if not isinstance(value, str):
                    raise EasyGraphError(f"{value!r} is not a string")
                yield indent + key + ' "' + escape(value) + '"'

    yield "graph ["

    if G.is_directed():
        yield "  directed 1"

    ignored_keys = {"directed", "node", "edge"}
    for attr, value in G.graph.items():
        yield from stringize(attr, value, ignored_keys, "  ")

    # Output node data
    node_id = dict(zip(G, range(len(G))))
    ignored_keys = {"id", "label"}
    for node, attrs in G.nodes.items():
        yield "  node ["
        yield "    id " + str(node_id[node])
        yield from stringize("label", node, (), "    ")
        for attr, value in attrs.items():
            yield from stringize(attr, value, ignored_keys, "    ")
        yield "  ]"

    # Output edge data
    ignored_keys = {"source", "target"}
    for e in G.edges:
        yield "  edge ["
        yield "    source " + str(node_id[e[0]])
        yield "    target " + str(node_id[e[1]])
        for attr, value in e[-1].items():
            yield from stringize(attr, value, ignored_keys, "    ")
        yield "  ]"
    yield "]"


@open_file(0, mode="rb")
def read_gml(path, label="label", destringizer=None):
    def filter_lines(lines):
        for line in lines:
            try:
                line = line.decode("ascii")
            except UnicodeDecodeError as err:
                raise EasyGraphError("input is not ASCII-encoded") from err
            if not isinstance(line, str):
                lines = str(lines)
            if line and line[-1] == "\n":
                line = line[:-1]
            yield line

    G = parse_gml_lines(filter_lines(path), label, destringizer)
    return G

@open_file(1, mode="wb")
def write_gml(G, path, stringizer=None):
    for line in generate_gml(G, stringizer):
        path.write((line + "\n").encode("ascii"))

def literal_stringizer(value):
    msg = "literal_stringizer is deprecated and will be removed in 3.0."
    warnings.warn(msg, DeprecationWarning)

    def stringize(value):
        if isinstance(value, (int, bool)) or value is None:
            if value is True:  # GML uses 1/0 for boolean values.
                buf.write(str(1))
            elif value is False:
                buf.write(str(0))
            else:
                buf.write(str(value))
        elif isinstance(value, str):
            text = repr(value)
            if text[0] != "u":
                try:
                    value.encode("latin1")
                except UnicodeEncodeError:
                    text = "u" + text
            buf.write(text)
        elif isinstance(value, (float, complex, str, bytes)):
            buf.write(repr(value))
        elif isinstance(value, list):
            buf.write("[")
            first = True
            for item in value:
                if not first:
                    buf.write(",")
                else:
                    first = False
                stringize(item)
            buf.write("]")
        elif isinstance(value, tuple):
            if len(value) > 1:
                buf.write("(")
                first = True
                for item in value:
                    if not first:
                        buf.write(",")
                    else:
                        first = False
                    stringize(item)
                buf.write(")")
            elif value:
                buf.write("(")
                stringize(value[0])
                buf.write(",)")
            else:
                buf.write("()")
        elif isinstance(value, dict):
            buf.write("{")
            first = True
            for key, value in value.items():
                if not first:
                    buf.write(",")
                else:
                    first = False
                stringize(key)
                buf.write(":")
                stringize(value)
            buf.write("}")
        elif isinstance(value, set):
            buf.write("{")
            first = True
            for item in value:
                if not first:
                    buf.write(",")
                else:
                    first = False
                stringize(item)
            buf.write("}")
        else:
            msg = "{value!r} cannot be converted into a Python literal"
            raise ValueError(msg)

    buf = StringIO()
    stringize(value)
    return buf.getvalue()
