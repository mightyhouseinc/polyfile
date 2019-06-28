from collections import deque, Sequence
from typing import IO, Sequence, Union


class TrieNode:
    def __init__(self, value=None, sources=None, _children=None):
        if _children is None:
            self._children = {}
        else:
            self._children = _children
        self._value = value
        if sources is not None:
            self._sources = set(sources)
        else:
            self._sources = set()

    @property
    def value(self):
        return self._value

    def __repr__(self):
        return f"{self.__class__.__name__}(value={self.value!r}, sources={self.sources!r}, _children={self._children!r})"

    def __len__(self):
        return len(self._children)

    def __iter__(self):
        return iter(self._children.values())

    def __hash__(self):
        return hash(self._value)

    def __eq__(self, other):
        return self.value == other.value

    def __ne__(self, other):
        return not (self == other)

    def __getitem__(self, key):
        return self._children[key]

    def __contains__(self, value):
        first, _, n = self._car_cdr_len(value)
        if n == 1:
            return first in self._children
        else:
            return self.find(value)

    @staticmethod
    def _car_cdr_len(sequence):
        if isinstance(sequence, Sequence):
            n = len(sequence)
            if n == 0:
                first = None
            else:
                first = sequence[0]
            return first, sequence[1:], n
        else:
            return sequence, (), 1

    def find(self, sequence):
        first, remainder, n = self._car_cdr_len(sequence)
        if n == 0:
            return len(self._sources) > 0
        if first not in self:
            return False
        return self[first].find(remainder)

    @property
    def children(self):
        return dict(self._children)

    @property
    def sources(self):
        return frozenset(self._sources)

    def _add_child(self, value, sources=None):
        new_child = TrieNode(value, sources)
        self._children[value] = new_child
        return new_child

    def _add(self, sequence, source):
        node = self
        while True:
            first, sequence, n = self._car_cdr_len(sequence)
            if n == 0:
                break
            if first in node:
                node = node[first]
            else:
                node = node._add_child(first)
                break
        node._sources.add(source)
        return node

    def add(self, sequence):
        return self._add(sequence, sequence)

    def find_prefix(self, prefix):
        first, remainder, n = self._car_cdr_len(prefix)
        if n == 0:
            yield from iter(self._sources)
            for child in self:
                yield from child.find_prefix(prefix)
        else:
            if first in self:
                yield from self[first].find_prefix(remainder)

    def bfs(self):
        queue = deque([self])
        while queue:
            head = queue.popleft()
            yield head
            queue.extend(head._children.values())


class ACNode(TrieNode):
    """A data structure for implementing the Aho-Corasick multi-string matching algorithm"""
    def __init__(self, value=None, sources=None, _children=None, parent=None):
        super().__init__(value=value, sources=sources, _children=_children)
        self._parent = parent
        self._fall = None

    @property
    def parent(self):
        return self._parent

    @property
    def fall(self):
        return self._fall

    def _add_child(self, value, sources=None):
        new_child = ACNode(value, sources, parent=self)
        self._children[value] = new_child
        return new_child

    def finalize(self):
        self._fall = self
        for n in self.bfs():
            if n is self:
                continue
            new_fall = n.parent.fall
            while n.value not in new_fall and new_fall is not self:
                new_fall = new_fall.fall
            if n.value not in new_fall:
                # there is no suffix
                n._fall = self
            else:
                n._fall = new_fall[n.value]
                if n.fall is n:
                    n._fall = self


class MultiSequenceSearch:
    """A datastructure for efficiently searching a sequence for multiple strings"""
    def __init__(self, *sequences_to_find):
        self.trie = ACNode()
        for seq in sequences_to_find:
            self.trie.add(seq)
        self.trie.finalize()

    def search(self, source_sequence: Union[Sequence, IO]):
        """The Aho-Corasick Algorithm"""
        if hasattr(source_sequence, 'read'):
            def iterator():
                while True:
                    b = source_sequence.read(1)
                    if not b:
                        return
                    yield b[0]
        else:
            def iterator():
                return iter(source_sequence)

        state = self.trie
        for stream_offset, c in enumerate(iterator()):
            n = state

            while c not in n and n is not self.trie:
                n = n.fall

            if n is self.trie:
                if c in n:
                    n = n[c]
            else:
                n = n[c]

            state = n

            while n is not self.trie:
                yield from ((stream_offset, source) for source in n.sources)
                n = n.fall


if __name__ == '__main__':
    root = TrieNode()
    root.add('The quick brown fox jumps over the lazy dog')
    root.add('The quick person')
    root.add('The best')
    print(list(root.find_prefix('The')))
    print(list(root.find_prefix('The quick')))
    print(root.find('The'))
    print(root.find('The best'))

    mss = MultiSequenceSearch(b'hack', b'hacker', b'crack', b'ack', b'kool')
    to_search = b'This is a test to see if hack or hacker is in this string.'\
                b'Can you crack it? If so, please ack, \'cause that would be kool.'
    for offset, match in mss.search(to_search):
        assert to_search[offset:offset+len(match)] == match
        print(offset, match)
