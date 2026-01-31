# Python 2.x
import unicodedata

# PEP 3131 categories
_XID_START = frozenset(('Lu', 'Ll', 'Lt', 'Lm', 'Lo', 'Nl'))
_XID_CONTINUE = _XID_START | frozenset(('Mn', 'Mc', 'Nd', 'Pc'))

# Category cache (very important for speed)
_category_cache = {}


def _category(ch):
    cat = _category_cache.get(ch)
    if cat is None:
        cat = unicodedata.category(ch)
        _category_cache[ch] = cat
    return cat


def PyUnicode_IsIdentifier(s):
    if not s:
        return False

    # ASCII fast path
    if isinstance(s, str):
        # First character
        c = s[0]
        if not (c == '_' or ('a' <= c <= 'z') or ('A' <= c <= 'Z')):
            return False

        for c in s[1:]:
            if not (c == '_' or c.isalnum()):
                return False

        return True

    # Ensure unicode
    if not isinstance(s, unicode):
        s = unicode(s)

    # First character
    ch = s[0]
    if ch != u'_' and _category(ch) not in _XID_START:
        return False

    # Remaining characters
    for ch in s[1:]:
        if _category(ch) not in _XID_CONTINUE:
            return False

    return True

isidentifier = PyUnicode_IsIdentifier