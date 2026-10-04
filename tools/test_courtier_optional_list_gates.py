"""Source-bound synthetic checks of optional courtier list gates; not CK3 engine proof."""
from pathlib import Path
import unittest
from extract_courtier_traits import matching_brace, tokenize, top_level_blocks

ROOT = Path(__file__).resolve().parent.parent
FILES = {
    "xar": "XenoAmess_s_Eternal_Recurrence/common/scripted_triggers/xar_courtier_creator_triggers.txt",
    "ervc": "Eternal_Recurrence_Vivhite_Courtier/common/scripted_triggers/ervc_courtier_creator_triggers.txt",
}

def entries(tokens):
    result, index = [], 0
    while index < len(tokens):
        key, operation, value = [item.value for item in tokens[index:index+3]]
        if value == "{":
            closing = matching_brace(tokens, index+2)
            result.append((key, operation, entries(tokens[index+3:closing])))
            index = closing+1
        else:
            result.append((key, operation, value))
            index += 3
    return result

def count_gate(prefix, category):
    text = (ROOT / FILES[prefix]).read_text(encoding="utf-8-sig")
    blocks = dict(top_level_blocks(tokenize(text)))
    body = entries(blocks[f"{prefix}_cc_valid_configuration_trigger"])
    count = f"var:{prefix}_cc_{category}_count"
    name = f"{prefix}_cc_selected_{category}"
    bounds = [item for item in body if item[0] == count]
    branches = [index for index,item in enumerate(body) if item[0] == "trigger_if" and
                item[2][0] == ("limit", "=", [("has_variable_list", "=", name)])]
    if len(bounds) != 2 or len(branches) != 1:
        raise ValueError("missing unique presence-gated count contract")
    index = branches[0]
    if body[index+1] != ("trigger_else", "=", [(count, "=", "0")]):
        raise ValueError("absent list must still require count=0")
    return bounds + body[index:index+2]

def evaluate(block, *, present, size, count, reads):
    results, index = [], 0
    while index < len(block):
        key, operation, value = block[index]
        if key == "trigger_if":
            limit = value[0]
            if limit[0] != "limit" or block[index+1][0] != "trigger_else":
                raise ValueError("unsupported conditional shape")
            branch = value[1:] if evaluate(limit[2], present=present, size=size, count=count, reads=reads) else block[index+1][2]
            results.append(evaluate(branch, present=present, size=size, count=count, reads=reads))
            index += 2
            continue
        if key == "has_variable_list":
            result = present
        elif key == "variable_list_size":
            reads.append(key)
            if not present:
                raise ValueError("missing list read")
            if value[0][0] != "name" or value[1][0] != "value":
                raise ValueError("unsupported list size shape")
            operation, right = value[1][1:]
            left = size
            right = count if right.startswith("var:") else int(right)
            result = compare(left, operation, right)
        elif key.startswith("var:") and key.endswith("_count"):
            result = compare(count, operation, int(value))
        else:
            raise ValueError(f"unsupported test subset: {key}")
        results.append(result)
        index += 1
    return all(results)

def compare(left, operation, right):
    if operation == "=": return left == right
    if operation == "<=": return left <= right
    if operation == ">=": return left >= right
    raise ValueError(f"unsupported comparison: {operation}")

class OptionalListGateTests(unittest.TestCase):
    def test_missing_list_never_reads_size_and_nonzero_or_invalid_count_is_rejected(self):
        for prefix in FILES:
            for category, maximum in [("commander",2),("personality",3)]:
                gate = count_gate(prefix,category)
                for count in [0,1,-1,maximum+1]:
                    with self.subTest(prefix=prefix,category=category,count=count):
                        reads=[]
                        accepted=evaluate(gate,present=False,size=None,count=count,reads=reads)
                        self.assertEqual(accepted,count==0)
                        self.assertEqual(reads,[])

    def test_present_list_bounds_and_exact_count_remain_required(self):
        for prefix in FILES:
            for category, maximum in [("commander",2),("personality",3)]:
                gate = count_gate(prefix,category)
                cases=[(0,0,True),(1,1,True),(maximum,maximum,True),
                       (1,0,False),(0,1,False),(maximum+1,maximum+1,False),
                       (1,-1,False),(maximum,maximum+1,False)]
                for size,count,expected in cases:
                    with self.subTest(prefix=prefix,category=category,size=size,count=count):
                        reads=[]
                        self.assertEqual(evaluate(gate,present=True,size=size,count=count,reads=reads),expected)
                        self.assertEqual(reads,["variable_list_size"]*2)

if __name__ == "__main__":
    unittest.main()
