"""Final render-plan admission requires actual boundary PTS and pixel review.

This supersedes estimate-only candidate plans as the final-render entry point.
No encoder is launched. Root obtains mapping/review evidence only after media
closure; preparation does not fabricate any alignment or visual acceptance.
"""
import argparse
from copy import deepcopy
import math
import stall_edl as engine
from collect_stall_edl import policy


def aligned_edl(edl, mapping, pixels):
    if (mapping.get('schema') != 'xar.recording-stall-actual-PTS-boundaries/v1'
            or mapping.get('status') != 'ACTUAL_PTS_ALIGNED'
            or pixels.get('schema') != 'xar.recording-stall-boundary-pixel-review/v1'
            or pixels.get('status') != 'ROOT_REVIEWED_ACCEPTED'
            or not pixels.get('reviewer') or not pixels.get('reviewed_at_utc')):
        raise ValueError('Actual PTS alignment and Root boundary pixel acceptance required')
    result = deepcopy(edl)
    rows = mapping.get('boundaries') or []
    accepted = set(pixels.get('accepted_boundary_ids') or [])
    seen = set()
    for interval in result['intervals']:
        middle = [a for a in interval['edit_actions'] if a['role'] == 'waiting_middle']
        for action in middle:
            key = interval['id'] + '/' + action['session_id']
            match = [r for r in rows if r.get('boundary_id') == key]
            if len(match) != 1 or key not in accepted:
                raise ValueError('Every edited middle requires its own actual mapping and pixel review')
            row = match[0]
            start, end = row.get('source_start_pts_seconds'), row.get('source_end_pts_seconds')
            if (not isinstance(start, (int, float)) or not isinstance(end, (int, float))
                    or not math.isfinite(start) or not math.isfinite(end) or not 0 <= start < end
                    or row.get('actual_PTS_read') is not True
                    or row.get('normal_gameplay_after_first_progress_excluded') is not True
                    or not row.get('mapping_evidence_pin') or not row.get('boundary_pixel_pins')):
                raise ValueError('Boundary proof is incomplete; estimated wallclock alone is insufficient')
            action.update(estimated_source_start_seconds=start, estimated_source_end_seconds=end,
                raw_seconds=end-start, PTS_mapping='ACTUAL_PTS_BOUNDARIES_ROOT_PIXEL_REVIEWED')
            seen.add(key)
        raw = sum(a['raw_seconds'] for a in middle)
        target = min(raw, result['policy']['max_recorded_middle_seconds'])
        factor = raw/target if target else None
        for action in middle:
            action.update(speed_factor=factor, output_seconds=action['raw_seconds']/factor if factor else 0)
        interval.update(recorded_middle_seconds=raw, edited_middle_seconds=target, speed_factor=factor)
    if not seen:
        raise ValueError('No qualified edit boundaries')
    result['boundary_qualification'] = {'actual_PTS_read': True, 'Root_pixels_accepted': True,
        'frame_exact_claimed': False, 'normal_gameplay_after_first_progress_preserved': True}
    return result


def main():
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('edl', 'policy', 'mapping', 'pixel-review', 'closed-sources', 'quota-admission', 'media-output', 'ffmpeg', 'output'):
        parser.add_argument('--'+key, type=Path, required=True)
    args = parser.parse_args()
    policy(args.policy)
    mapping, review = engine.read(args.mapping), engine.read(args.pixel_review)
    # Read only bounded evidence files to confirm the exact declared hashes.
    for row in mapping.get('boundaries') or []:
        for item in [row.get('mapping_evidence_pin'), *(row.get('boundary_pixel_pins') or [])]:
            if not isinstance(item, dict) or engine.pin(item['path']) != item:
                raise ValueError('Original actual boundary evidence changed')
    edl = aligned_edl(engine.read(args.edl), mapping, review)
    plan = engine.render_plan(edl, engine.read(args.closed_sources), engine.read(args.quota_admission),
        args.media_output, args.ffmpeg, accept_estimated=True)
    plan.update(mapping_acceptance='ACTUAL_PTS_AND_ROOT_BOUNDARY_PIXELS',
        mapping_pin=engine.pin(args.mapping), pixel_review_pin=engine.pin(args.pixel_review),
        policy_pin=engine.pin(args.policy), final_render_authorization='ROOT_EXECUTION_AFTER_REVIEW_ONLY')
    engine.create(args.output, plan)

if __name__ == '__main__': main()
