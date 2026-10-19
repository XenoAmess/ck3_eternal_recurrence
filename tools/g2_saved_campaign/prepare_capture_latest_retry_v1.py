"""Pure, exact 950d projection; sole runtime may create ONE sibling capture leaf."""
import argparse
import ast
import hashlib
from pathlib import Path

BASE_SHA256 = '950d156551da3579ee6902a1c945e5a343bffecb4addcff9cee86249f99b2161'
REPLACEMENTS = ((b'pending.replace(path)', b'_replace_mutable_latest(pending, path)'),
                (b'pending.replace(latest)', b'_replace_mutable_latest(pending, latest)'),
                (b'pending.replace(dest)', b'_replace_mutable_latest(pending, dest)'))


def project_capture_latest_retry_v1(original, helper_source):
    if len(original) != 70587 or hashlib.sha256(original).hexdigest() != BASE_SHA256:
        raise ValueError('only the actual C11 950d baseline is qualified')
    text = helper_source.decode('utf-8')
    nodes = [n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef)
             and n.name == '_replace_mutable_latest']
    if len(nodes) != 1:
        raise ValueError('one reviewed bounded helper required')
    helper = ast.get_source_segment(text, nodes[0]).encode('utf-8') + b'\n\n'
    result = original
    for old, new in REPLACEMENTS:
        if result.count(old) != 1:
            raise ValueError('actual baseline mutable replace seam changed')
        result = result.replace(old, new, 1)
    anchor = b'def _replace_json(path, value):'
    if result.count(anchor) != 1 or b'def _replace_mutable_latest(' in result:
        raise ValueError('unknown or already transformed baseline')
    result = result.replace(anchor, helper + anchor, 1)
    recovered = result.replace(helper, b'', 1)
    for old, new in REPLACEMENTS:
        recovered = recovered.replace(new, old, 1)
    if recovered != original:
        raise ValueError('bytes outside the helper and three replace calls changed')
    compile(result, 'qualified-c11-capture-retry', 'exec')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--helper-source', type=Path, required=True)
    parser.add_argument('--helper-source-sha256', required=True)
    parser.add_argument('--expected-output-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    helper = args.helper_source.read_bytes()
    if hashlib.sha256(helper).hexdigest() != args.helper_source_sha256:
        raise ValueError('reviewed helper source changed')
    result = project_capture_latest_retry_v1(args.input.read_bytes(), helper)
    if (hashlib.sha256(result).hexdigest() != args.expected_output_sha256
            or len(result) > 96 * 1024 or args.output.exists()
            or args.output.resolve().parent != args.input.resolve().parent
            or args.output.name != 'ck3_obs_capture_png_retry_c13.py'):
        raise ValueError('one exact create-only C11 sibling source required')
    with args.output.open('xb') as stream:
        stream.write(result)
    print({'path': str(args.output), 'bytes': len(result), 'sha256': hashlib.sha256(result).hexdigest()})


if __name__ == '__main__':
    main()
