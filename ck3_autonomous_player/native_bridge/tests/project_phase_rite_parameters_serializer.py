"""Project the actual commander/knight serializer bodies for the new fixture."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

from project_knight_context_serializer import literal_function

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    source_bytes = args.source.read_bytes()
    source = source_bytes.decode('utf-8-sig')
    names = ('SignedNumber', 'AppendJsonString', 'AppendUnavailableReason',
             'CombatStatusName', 'AppendCombatCommander', 'AppendCombatKnights')
    functions = {name: literal_function(source, name) for name in names}
    output = (
        '#include "xar_bridge/game_contract.hpp"\n'
        '#include "xar_bridge/phase_rite_parameters_v1_serializer.hpp"\n'
        '#include "xar_bridge/phase_warmonger_core_v1_serializer.hpp"\n'
        '#include "xar_bridge/phase_berserker_validity_inputs_v1_serializer.hpp"\n'
        '#include <array>\n#include <charconv>\n#include <cstdint>\n'
        '#include <string>\n#include <string_view>\n#include <system_error>\n'
        'namespace phase_rite_wire {\nusing namespace xar;\n' + '\n'.join(functions.values()) +
        '\nstd::string SerializeCommander(const xar::game::CombatCommanderSnapshot &value) {\n'
        '  std::string result; AppendCombatCommander(result, value); return result;\n}\n'
        '\nstd::string SerializeKnights(const xar::game::CombatKnightsSnapshot &value) {\n'
        '  std::string result; AppendCombatKnights(result, value); return result;\n}\n}\n'
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding='utf-8', newline='\n')
    receipt = {
        'schema': 'phase_rite_parameters_literal_serializer_projection_v1',
        'source': str(args.source), 'source_sha256': hashlib.sha256(source_bytes).hexdigest(),
        'literal_function_sha256': {name: hashlib.sha256(body.encode('utf-8')).hexdigest() for name, body in functions.items()},
        'generated_source': str(args.output), 'generated_sha256': hashlib.sha256(args.output.read_bytes()).hexdigest(),
        'value_origin': 'literal production serializer source; synthetic fixture callbacks; no CK3 operation',
    }
    args.receipt.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')

if __name__ == '__main__':
    main()
