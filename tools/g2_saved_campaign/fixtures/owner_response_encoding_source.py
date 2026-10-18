"""Small test-only production source extraction, never a live owner.

Source: root_p50r9_sdk_queue.py, 247130 bytes, SHA256 0daed169d5fb94cf0261e00e06c6fd14428ae86abb6e1639921ebb593129061f.
Extracted atomic (252-302), decoded (326-360), FreshQueue.call (3575-3687).
AST-unparsed after only the three identity substitutions below. Other owner
methods, launch data, profiles, SDKs and business payloads are not copied.
Imports/globals and the observer/classifier are supplied by the test harness;
this fixture grants no Native/Game qualification and issues no real RPC.
Original Path.rename create-only semantics are Windows-specific; this source
fixture does not emulate that behavior on POSIX.
"""

ORIGINAL_OWNER_SOURCE_SHA256 = '0daed169d5fb94cf0261e00e06c6fd14428ae86abb6e1639921ebb593129061f'
EXTRACTED_ORIGINAL_AST_SHA256 = '3ecb228e2ff6f846586ff7a32d752ceb74d3fb7b5c383bdab0776253986fdfaa'
IDENTITY_NORMALIZED_AST_SHA256 = '151b3976a4e79cd4cd2b82c6fc3b574c7e8a89fb737b14be04c1dc02a18e9708'
IDENTITY_REWRITES = {'CURRENT-REQUEST-P50R9.json': 'CURRENT-REQUEST.json', 'p50r9-display-responses': 'display-responses', 'root_p50r9_overlay_relay': 'owner_response_fixture_observer'}

def atomic(path, value, *, replace=False, limit=REPLY_RESERVE):
    payload = json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    if len(payload) > limit:
        raise ValueError('finite receipt bound exceeded: ' + str(path))
    pending = path.with_name(path.name + '.' + uuid.uuid4().hex + '.pending')
    try:
        with pending.open('xb') as stream:
            stream.write(payload)
            stream.flush()
        if replace:
            deadline = time.monotonic() + 2.0
            while True:
                try:
                    os.replace(pending, path)
                    break
                except PermissionError:
                    if time.monotonic() >= deadline:
                        raise
                    time.sleep(0.025)
        else:
            pending.rename(path)
    finally:
        pending.unlink(missing_ok=True)

def decoded(row):
    if row.get('client_error'):
        raise RuntimeError('client outcome unknown; original request must not be resent')
    result = row.get('result')
    if not isinstance(result, dict) or result.get('is_error', result.get('isError', False)):
        raise RuntimeError('SDK error; original result retained; no automatic retry')
    value = result.get('structured_content', result.get('structuredContent'))
    if isinstance(value, dict):
        return value
    for block in result.get('content', []):
        if isinstance(block, dict) and block.get('type') == 'text':
            try:
                value = json.loads(block['text'])
            except (TypeError, ValueError):
                continue
            if isinstance(value, dict):
                return value
    raise ValueError('SDK returned no actual decoded object')

class OwnerCallSourceFixture:

    async def call(self, session, request, path):
        self.current_attempt = None
        tool = request.get('tool')
        arguments = request.get('arguments', {})
        self.check_before(tool, arguments)
        budget = self.call_budget(tool)
        sequence = self.consume_sequence(request)
        if tool == INITIAL_CAMERA:
            self.camera_attempted = True
        response = OUTBOX / f'{sequence:04d}-1-result.json'
        if response.exists() or (Q / f'INFLIGHT-{sequence:04d}.json').exists():
            raise FileExistsError('original request already attempted; no retry')
        context = {'sequence': sequence, 'tool': tool, 'arguments': arguments, 'request_file': str(path), 'at_utc': now().isoformat(), 'replay_allowed': False}
        atomic(N / 'CURRENT-REQUEST.json', context, replace=True, limit=16384)
        atomic(Q / f'INFLIGHT-{sequence:04d}.json', context, limit=16384)
        atomic(Q / f'{sequence:04d}-before-action.json', context, limit=16384)
        started, mono = (now().isoformat(), time.monotonic())
        try:
            result = await session.call_tool(tool, arguments, read_timeout_seconds=budget)
            dumped = result.model_dump(mode='json')
            row = {'started_at_utc': started, 'ended_at_utc': now().isoformat(), 'elapsed_seconds': time.monotonic() - mono, 'request': request, 'result': dumped, 'mcp_result_projection_json_utf8_bytes': len(json.dumps(dumped, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))}
        except Exception as error:
            preserve_first_exception(error, stage='sdk_call', request=request)
            row = {'started_at_utc': started, 'ended_at_utc': now().isoformat(), 'elapsed_seconds': time.monotonic() - mono, 'request': request, 'client_error': repr(error), 'replay_allowed': False}
        atomic(response, row)
        self.current_attempt = {'request': request, 'row': row, 'response': str(response)}
        from owner_response_fixture_observer import relay_compact, error_projection
        try:
            body = decoded(row)
        except Exception:
            relay_compact(response, error_projection(row))
            raise
        relay_compact(response, display_projection(row, body))
        self.check_after(tool, arguments, body)
        if tool == AUTO:
            atomic(Q / f'{sequence:04d}-ordinary-result-credit.json', {'at_utc': row['ended_at_utc'], 'source_response': str(response), 'observation': self.last_auto_observation}, limit=16384)
        projected = display_projection(row, body)
        try:
            atomic(N / 'display-responses' / response.name, projected, limit=16384)
        except ValueError:
            atomic(Q / f'{sequence:04d}-display-omitted.json', {'source_response': str(response), 'reason': 'projection_exceeds_16KiB'}, limit=16384)
        atomic(Q / f'{sequence:04d}-after-result.json', {'at_utc': row['ended_at_utc'], 'request': str(path), 'response': str(response), 'tool': tool, 'actual_status': body.get('status'), 'selected_step': body.get('selected_step'), 'checkpoint_status': (body.get('checkpoint') or {}).get('status')}, limit=16384)
        print('DONE', sequence, tool, 'seconds', round(row['elapsed_seconds'], 3), flush=True)
        return (body, response)
