"""Pure author seam before its existing observe_text call; no body/file reads."""
from copy import deepcopy
import derive_saved_title_reference_v3 as proof


def bind_existing_join_request(checkpoint, query, state, provenance, request, modules, input_artifacts, source_artifacts):
    # derive validates actual native-before frame, exact bookkeeping transition,
    # and this parsed state's after-frame/checkpoint/full-Title identity.
    evidence = proof.derive(checkpoint, query, state, provenance, modules)
    evidence['input_artifacts'] = deepcopy(input_artifacts)
    evidence['source_artifacts'] = deepcopy(source_artifacts)
    need = proof.need
    need(request.get('native_reference_binding') is None, 'existing request already contains a reference binding')
    need(request.get('source_head') == modules['reader'].HEAD and request['identity'] == state['identity'], 'author request exact parsed identity')
    need(request['save']['sha256'] == state['checkpoint_sha256'], 'author request exact parsed checkpoint')
    raw_evidence = proof.json_bytes(evidence)
    binding = {'schema': 'lyd.saved-native-reference-binding.v1', 'source_head': modules['reader'].HEAD,
               'evidence_sha256': proof.digest(raw_evidence), 'title_type': evidence['derived_title_type']}
    # Call the exact current legacy binding validator; do not reclassify STATE.
    successor = deepcopy(request)
    successor['native_reference_binding'] = binding
    need(modules['reader'].title_type_binding(successor) == evidence['derived_title_type'], 'legacy binding validator differs')
    return successor, raw_evidence, proof.json_bytes(binding)
