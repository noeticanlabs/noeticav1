# NK-1 ValueCanon: Type-tagged canonical representation per docs/nk1/1_canon.md

from typing import Any, Union, Tuple, List, Dict
from dataclasses import dataclass
import base64
import unicodedata


@dataclass(frozen=True)
class ValueCanon:
    """
    Type-tagged canonical representation of values.
    
    Per NK-1 §1.3 ValueCanon tagging:
    - i:<decimal> for integers
    - q:<scale>:<int> for fixed-point
    - b64:<base64url_no_padding> for bytes
    - s:<NFC> for strings
    
    Maps are encoded as sorted [key, value] arrays.
    Lists preserve order.
    """
    
    @staticmethod
    def canon(value: Any) -> Any:
        """
        Convert a value to its canonical tagged representation.
        
        Returns the value in its canonical form with type tags.
        """
        if value is None:
            return None
        elif isinstance(value, bool):
            # Bool must be distinguished from int
            return {"t": "bool", "v": value}
        elif isinstance(value, int) and not isinstance(value, bool):
            # Integer: i:<decimal>
            return f"i:{value}"
        elif isinstance(value, tuple) and len(value) == 2:
            # Rational as (num, denom) - treat as fixed-point q:<scale>:<int>
            # For now, assume scale of 1
            return f"q:1:{value[0]}" if value[1] == 1 else f"q:{value[1]}:{value[0]}"
        elif isinstance(value, float):
            # Float - not allowed in strict mode, but handle for compatibility
            raise ValueError("Float not allowed in ValueCanon strict mode")
        elif isinstance(value, str):
            # String: s:<NFC normalized>
            nfc = unicodedata.normalize('NFC', value)
            return f"s:{nfc}"
        elif isinstance(value, bytes):
            # Bytes: b64:<base64url_no_padding>
            b64 = base64.urlsafe_b64encode(value).rstrip(b'=').decode('ascii')
            return f"b64:{b64}"
        elif isinstance(value, dict):
            # Map: sorted [key, value] arrays
            # Sort by key bytes
            sorted_items = sorted(value.items(), key=lambda kv: kv[0].encode('utf-8'))
            return [[ValueCanon.canon(k), ValueCanon.canon(v)] for k, v in sorted_items]
        elif isinstance(value, list):
            # List: preserve order, canon each element
            return [ValueCanon.canon(item) for item in value]
        else:
            raise ValueError(f"Unsupported value type: {type(value)}")
    
    @staticmethod
    def canon_to_bytes(value: Any) -> bytes:
        """
        Convert a canonical value to bytes for hashing.
        
        Returns UTF-8 encoded string representation.
        """
        if value is None:
            return b"null"
        elif isinstance(value, str):
            return value.encode('utf-8')
        elif isinstance(value, bool):
            return str(value).encode('utf-8')
        elif isinstance(value, list):
            # For arrays, concatenate all elements
            result = b"["
            for i, item in enumerate(value):
                if i > 0:
                    result += b","
                result += ValueCanon.canon_to_bytes(item)
            result += b"]"
            return result
        elif isinstance(value, dict):
            # For maps, we've already converted to sorted pairs
            result = b"{"
            for i, (k, v) in enumerate(value):
                if i > 0:
                    result += b","
                result += ValueCanon.canon_to_bytes(k) + b":" + ValueCanon.canon_to_bytes(v)
            result += b"}"
            return result
        else:
            return str(value).encode('utf-8')
    
    @staticmethod
    def parse(value: str) -> Any:
        """
        Parse a tagged value back to its Python representation.
        
        Inverse of canon().
        """
        if value is None:
            return None
        elif isinstance(value, str):
            if value.startswith("i:"):
                return int(value[2:])
            elif value.startswith("q:"):
                parts = value[2:].split(":", 1)
                return (int(parts[1]), int(parts[0]))  # (num, denom)
            elif value.startswith("b64:"):
                b64 = value[4:]
                # Add padding if needed
                padding = 4 - len(b64) % 4
                if padding != 4:
                    b64 += '=' * padding
                return base64.urlsafe_b64decode(b64)
            elif value.startswith("s:"):
                return value[2:]
            elif value == "true":
                return True
            elif value == "false":
                return False
            else:
                return value
        return value


def canon_field_value(field_type: str, value: Any) -> Any:
    """
    Canon a field value based on its type.
    
    Args:
        field_type: The type of the field (integer, nonneg, rational, bool, string, bytes)
        value: The value to canon
    
    Returns:
        Canonically tagged representation
    """
    if field_type in ("integer", "nonneg"):
        return f"i:{value}"
    elif field_type == "rational":
        if isinstance(value, tuple):
            num, denom = value
            return f"q:{denom}:{num}"
        return value
    elif field_type == "bool":
        return "true" if value else "false"
    elif field_type == "string":
        nfc = unicodedata.normalize('NFC', str(value))
        return f"s:{nfc}"
    elif field_type == "bytes":
        b64 = base64.urlsafe_b64encode(value).rstrip(b'=').decode('ascii')
        return f"b64:{b64}"
    return value


# Test the ValueCanon implementation
if __name__ == "__main__":
    # Test integer
    assert ValueCanon.canon(42) == "i:42"
    
    # Test string with NFC
    # NFC normalized forms
    assert ValueCanon.canon("café") == "s:café"
    
    # Test bytes
    test_bytes = b"hello"
    result = ValueCanon.canon(test_bytes)
    assert result.startswith("b64:")
    
    # Test round-trip
    assert ValueCanon.parse(result) == test_bytes
    
    print("All ValueCanon tests passed!")
