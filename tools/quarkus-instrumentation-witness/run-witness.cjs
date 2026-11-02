// One create-only software reactor. Never attaches to the business dev host or Game.
const fs = require('fs'), cp = require('child_process'), path = require('path');
const assert = require('assert'), net = require('net'), crypto = require('crypto');
assert.equal(process.platform, 'win32', 'this archived raw-command-line runner is Windows-only');
const base = __dirname;
const requestedWorkspace = process.env.INSTRUMENTATION_FIXTURE_WORKSPACE;
assert(requestedWorkspace && path.isAbsolute(requestedWorkspace), 'explicit absolute fresh workspace is required');
const fixture = path.resolve(requestedWorkspace);
const evidence = path.join(fixture, 'evidence');
const port = Number(process.env.INSTRUMENTATION_FIXTURE_PORT || '8127');
assert(Number.isSafeInteger(port) && port > 0 && port <= 65535, 'valid private port required');
const mvn = process.env.INSTRUMENTATION_MVN;
const javaHome = process.env.INSTRUMENTATION_JAVA_HOME;
assert(mvn && path.isAbsolute(mvn) && javaHome && path.isAbsolute(javaHome), 'explicit Maven executable and Java21 home required');
const repoHead = path.join(fixture, 'repository').replace(/\\/g, '/');
const repoTail = process.env.INSTRUMENTATION_REPOSITORY_TAIL || '';
const machine_id = process.env.INSTRUMENTATION_MACHINE_ID || 'not-recorded';
// Public path domain is intentionally narrower than Windows filenames. The fixed private
// witness used this domain; no general CMD quoting or inner JVM-argument parser is claimed.
function requireSupportedCmdPath(value, label) {
  assert(typeof value === 'string' && value.length > 0, label + ' is required');
  assert(!/[\s\u0000-\u001f\u007f&|<>^%!"()]/u.test(value),
      label + ' must contain no whitespace/control or CMD expansion/metacharacters');
  assert(path.isAbsolute(value), label + ' must be absolute');
}
requireSupportedCmdPath(requestedWorkspace, 'workspace');
requireSupportedCmdPath(mvn, 'Maven executable');
requireSupportedCmdPath(javaHome, 'Java home');
requireSupportedCmdPath(process.env.SystemRoot, 'SystemRoot');
if (repoTail !== '') for (const entry of repoTail.split(',')) requireSupportedCmdPath(entry, 'repository tail');

const nonce = crypto.randomUUID();
let child, ended = true, childExit = null, childError = null, initial = null, actual = null;
let startedAt = null, logOut, logErr;
const responses = [];
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const now = () => new Date().toISOString();
function sha(bytes) { return crypto.createHash('sha256').update(bytes).digest('hex'); }
function pin(file) { const b = fs.readFileSync(file); return {path: file, bytes: b.length, sha256: sha(b)}; }
function save(name, data) {
  fs.writeFileSync(path.join(evidence, name), JSON.stringify(data, null, 2) + '\n', {flag: 'wx'});
}
function inFixture(relative) {
  const target = path.resolve(fixture, relative), prefix = path.resolve(fixture) + path.sep;
  assert(target.startsWith(prefix), 'write must stay in the create-only fixture');
  return target;
}
function put(relative, bytes) {
  const target = inFixture(relative);
  fs.mkdirSync(path.dirname(target), {recursive: true});
  fs.writeFileSync(target, bytes, {flag: 'wx'});
  return target;
}
async function portFree() {
  return new Promise(resolve => {
    const server = net.createServer();
    server.once('error', () => resolve(false));
    server.listen(port, '127.0.0.1', () => server.close(() => resolve(true)));
  });
}
async function http(route = '/instrumentation-probe', method = 'GET') {
  const at = now();
  let record;
  try {
    const response = await fetch('http://127.0.0.1:' + port + route, {
      method, headers: {'X-Fixture-Nonce': nonce}, signal: AbortSignal.timeout(5000)
    });
    const text = await response.text();
    assert(Buffer.byteLength(text) <= 131072, 'bounded private response');
    let json = null;
    if (response.status === 200) json = JSON.parse(text);
    if (json) assert.equal(json.nonce, nonce, 'never consume another server as this fixture');
    record = {at_utc: at, route, status: response.status, body: text};
    fs.appendFileSync(path.join(evidence, 'HTTP.jsonl'), JSON.stringify(record) + '\n');
    responses.push(record); if (responses.length > 12) responses.shift();
    return {...record, json};
  } catch (error) {
    record = {at_utc: at, route, error: String(error)};
    fs.appendFileSync(path.join(evidence, 'HTTP.jsonl'), JSON.stringify(record) + '\n');
    responses.push(record); if (responses.length > 12) responses.shift();
    // A successful response with the wrong nonce is a hard failure, not a polling condition.
    if (/never consume another server/.test(String(error))) throw error;
    return record;
  }
}
async function until(fn, label, milliseconds) {
  const limit = Date.now() + milliseconds;
  while (Date.now() < limit) {
    if (childError) throw childError;
    const value = await fn(); if (value) return value;
    await sleep(500);
  }
  throw new Error('bounded fixture timeout: ' + label);
}
async function cleanup() {
  if (!child) return;
  const before = now();
  let stopped = null, forced = null;
  // Only the private nonce-identified server receives this request.
  if (initial) {
    const view = await http('/probe/loader');
    if (view.json) {
      assert.equal(view.json.pid, initial.pid);
      assert.equal(view.json.start_instant, initial.start_instant);
      stopped = await http('/probe/stop', 'POST');
    }
  }
  const limit = Date.now() + 12000;
  while (!ended && Date.now() < limit) await sleep(200);
  if (!ended) {
    // Only the still-owned, newly spawned private wrapper tree may be forced.
    const result = cp.spawnSync(path.join(process.env.SystemRoot, 'System32/taskkill.exe'), ['/PID', String(child.pid), '/T', '/F'],
      {windowsHide: true, encoding: 'utf8', timeout: 15000});
    forced = {wrapper_pid: child.pid, exit_code: result.status, error: result.error ? String(result.error) : null,
      stdout: result.stdout, stderr: result.stderr};
    const end = Date.now() + 5000;
    while (!ended && Date.now() < end) await sleep(100);
  }
  const free = await portFree();
  save('CLEANUP.json', {at_utc: before, end_utc: now(), wrapper_pid: child.pid, wrapper_ended: ended,
    wrapper_exit_code: childExit, nonce_bound_stop_response: stopped, owned_wrapper_tree_force: forced,
    private_port_free: free, business_host_or_Game_attached: false});
  assert(ended && free, 'owned fixture cleanup incomplete; no further host is started');
}

(async () => {
  assert(!fs.existsSync(fixture), 'new fixture directory must be absent');
  const source = JSON.parse(fs.readFileSync(path.join(base, 'fixture-manifest.json'), 'utf8'));
  for (const file of source.frozen_inputs) {
    const bytes = fs.readFileSync(path.join(base, file.path));
    assert.equal(bytes.length, file.bytes); assert.equal(sha(bytes), file.sha256);
  }
  assert(await portFree(), 'private fixture port must be free before any owned host starts');
  fs.mkdirSync(fixture); fs.mkdirSync(evidence); fs.mkdirSync(path.join(fixture, 'tmp'));
  const templatePaths = {
    'pom.xml': 'pom.xml', 'business-pom.xml': 'business/pom.xml', 'host-pom.xml': 'host/pom.xml',
    'BusinessRevision.java': 'business/src/main/java/org/xar/research/newclass310/BusinessRevision.java',
    'ProbeResource.java': 'host/src/main/java/org/xar/research/newclass310/ProbeResource.java'
  };
  const template = name => fs.readFileSync(path.join(base, templatePaths[name]));
  put('pom.xml', template('pom.xml'));
  for (const module of ['business', 'host']) put(module + '/pom.xml', template(module + '-pom.xml'));
  const businessSource = put('business/src/main/java/org/xar/research/newclass310/BusinessRevision.java', template('BusinessRevision.java'));
  put('host/src/main/java/org/xar/research/newclass310/ProbeResource.java', template('ProbeResource.java'));
  put('host/src/main/java/org/xar/research/newclass310/InstrumentationProbe311.java', fs.readFileSync(path.join(base, 'host/src/main/java/org/xar/research/newclass310/InstrumentationProbe311.java')));
  put('host/src/main/resources/application.properties', fs.readFileSync(path.join(base, 'host/src/main/resources/application.properties')));
  const tmp = path.join(fixture, 'tmp').replace(/\\/g, '/');
  const output = path.join(fixture, 'business/target/classes').replace(/\\/g, '/');
  const command = [mvn, '-nsu', '-B', '-ntp', '-f', path.join(fixture, 'pom.xml'),
    '-pl', 'host', '-am', '-Dmaven.repo.local=' + repoHead,
    '-Dmaven.repo.local.tail=' + repoTail,
    '-Dmaven.repo.local.tail.ignoreAvailability=false',
    '-Dmaven.test.skip=true', '-DskipTests=true', '-Dquarkus.bootstrap.effective-model-builder=false',
    '-DnoDeps=false', '-Ddebug=false', '-Dquarkus.console.enabled=false', '-Dquarkus.test.continuous-testing=disabled',
    '-Dquarkus.analytics.disabled=true', '-Dquarkus.live-reload.instrumentation=true',
    '-Dquarkus.http.host=127.0.0.1', '-Dquarkus.http.port=' + port,
    '-Djvm.args=-Xmx512m -XX:MaxMetaspaceSize=256m -XX:ActiveProcessorCount=1 -Djava.io.tmpdir=' + tmp + ' -Dfixture.nonce=' + nonce + ' -Dmaven.repo.local=' + repoHead + ' -Dmaven.repo.local.tail=' + repoTail + ' -Dmaven.repo.local.tail.ignoreAvailability=false',
    'compile', 'io.quarkus.platform:quarkus-maven-plugin:3.40.1.1:dev'];
  save('PREPARED.json', {schema: 'xar.instrumentation-private-fixture/v1', at_utc: now(), machine_id,
    fixture, port, nonce, inputs: source, command,
    limits: {Maven_heap_MiB: 512, fork_heap_MiB: 512, fork_metaspace_MiB: 256, expected_executor_OS_CPU_count: 1, actual_OS_affinity_checked_by_public_runner: false},
    scope: 'Fresh isolated standard vendor Maven dev reactor, compatible existing method body only; actual delegate/loader/thread identity must persist. No new source/type after initial compile; no custom entry, current Dev, Game or fallback.',
    repository_write_claim: 'necessary fixed-version artifact resolution permitted only into new private primary repository; no shared artifact install/deploy or invented provenance; no OS filesystem sandbox claim',
    root_or_dependency_production_adopted: false});
  logOut = fs.openSync(path.join(evidence, 'maven.stdout.log'), 'wx');
  logErr = fs.openSync(path.join(evidence, 'maven.stderr.log'), 'wx');
  const line = command.map(item => /\s/.test(item) ? '"' + item + '"' : item).join(' ');
  startedAt = now();
  child = cp.spawn('cmd.exe', ['/d', '/s', '/c', line], {cwd: fixture, windowsHide: true, windowsVerbatimArguments: true,
    env: {...process.env, JAVA_HOME: javaHome, QUARKUS_LOCAL_REPO: repoHead, MAVEN_OPTS: '-Xmx512m -XX:ActiveProcessorCount=1 -Djava.io.tmpdir=' + tmp,
      TMP: tmp, TEMP: tmp}, stdio: ['pipe', logOut, logErr]});
  ended = false;
  child.stdin.on('error', () => {});
  child.on('error', error => {childError = error; ended = true;});
  child.on('exit', (code, signal) => {
    ended = true; childExit = code;
    save('MAVEN-END.json', {at_utc: now(), wrapper_pid: child.pid, exit_code: code, signal});
    fs.closeSync(logOut); fs.closeSync(logErr);
  });
  save('MAVEN-BEGIN.json', {at_utc: startedAt, wrapper_pid: child.pid, command, raw_windows_command_line: line});
  console.log(JSON.stringify({event: 'PRIVATE_MAVEN_BEGIN', at_utc: startedAt, wrapper_pid: child.pid, fixture}));
  initial = await until(async () => {
    if (ended) throw new Error('Maven ended before initial probe: ' + childExit);
    const response = await http();
    return response.status === 200 && response.json.worker_alive && response.json.progress > 0 ? response.json : null;
  }, 'standard Maven instrumentation host', 180000);
  assert.equal(initial.new_invocation_value, 'BEFORE_NEW_PUBLIC_CLASS');
  assert.equal(initial.worker_last_value, 'BEFORE_NEW_PUBLIC_CLASS');
  assert.equal(initial.class_change_agent_argument_present, true, 'actual owned JVM must carry official class-change agent');
  assert.equal(initial.closed, false);
  const sourceBefore = fs.readFileSync(businessSource, 'utf8');
  const existingClass = inFixture('business/target/classes/org/xar/research/newclass310/BusinessRevision.class');
  const beforeClass = pin(existingClass);
  const beforeListing = fs.readdirSync(path.dirname(existingClass)).sort();
  save('BEFORE.json', {at_utc: now(), identity: initial, existing_class: beforeClass, source: pin(businessSource), class_listing: beforeListing});
  const changedAt = now();
  const sourceAfter = sourceBefore.replace('return "BEFORE_NEW_PUBLIC_CLASS";', 'return "AFTER_INSTRUMENTED_BODY311";');
  assert.notEqual(sourceAfter, sourceBefore);
  assert.equal(sourceAfter.replace('return "AFTER_INSTRUMENTED_BODY311";', 'return "BEFORE_NEW_PUBLIC_CLASS";'), sourceBefore);
  fs.writeFileSync(businessSource, sourceAfter, 'utf8');
  save('SOURCE-CHANGE.json', {at_utc: changedAt, changed_source: pin(businessSource), only_existing_method_return_literal_changed: true});
  const after = await until(async () => {
    if (ended) throw new Error('Maven ended during instrumentation: ' + childExit);
    const response = await http();
    if (response.status !== 200) return null;
    const value = response.json;
    for (const field of ['pid', 'start_instant', 'application_loader', 'application_loader_identity', 'dependency_loader',
                         'delegate_token', 'delegate_identity', 'worker_thread_id'])
      assert.equal(value[field], initial[field], 'original host/delegate/loader/thread changed: ' + field);
    assert.equal(value.worker_alive, true); assert.equal(value.closed, false);
    return value.new_invocation_value === 'AFTER_INSTRUMENTED_BODY311' && value.worker_last_value === 'AFTER_INSTRUMENTED_BODY311'
        && value.progress > initial.progress ? value : null;
  }, 'existing-method instrumentation with original delegate', 90000);
  const log = fs.readFileSync(path.join(evidence, 'maven.stdout.log'), 'utf8');
  const created = log.split('INSTRUMENTATION311_DELEGATE_CREATED token=').length - 1;
  assert.equal(created, 1, 'must not replace the original delegate');
  assert.equal(log.includes('INSTRUMENTATION311_DELEGATE_CLOSED token='), false, 'original delegate must still be alive');
  assert(log.includes('Live reload performed via instrumentation, no restart needed'), 'official successful instrumentation branch must be observed');
  assert.equal(log.includes('Restarting quarkus due to changes'), false, 'full runtime restart is not the positive result');
  assert.deepEqual(fs.readdirSync(path.dirname(existingClass)).sort(), beforeListing, 'no added or deleted dependency class');
  const afterClass = pin(existingClass);
  assert.notEqual(afterClass.sha256, beforeClass.sha256, 'real compiled existing class bytes must change');
  actual = {schema: 'xar.instrumentation-existing-body-actual/v1', at_utc: now(), machine_id,
    outcome: 'SAME_LOADER_DELEGATE_THREAD_OBSERVED_NEW_METHOD_BODY', command_started_at: startedAt, class_changed_at: changedAt,
    initial, after, compiled_before: beforeClass, compiled_after: afterClass,
    existing_source_after: pin(businessSource), source_addition_or_deletion: false,
    same_pid_birth_loader_delegate_thread: true, original_counter_progressed: true,
    official_instrumentation_success_log: true, actual_standard_Maven_dev: true,
    full_runtime_restart_or_cold_fallback: false, current_business_Dev_or_Game_touched: false, production_adoption: false};
  save('ACTUAL.json', actual);
  console.log(JSON.stringify({event: 'EXISTING_BODY_INSTRUMENTED', pid: after.pid, start_instant: after.start_instant}));

})().catch(error => {
  if (fs.existsSync(evidence)) save('FAILED.json', {at_utc: now(), error: String(error), stack: error.stack,
    wrapper_pid: child ? child.pid : null, initial, actual, recent_responses: responses});
  console.error(error); process.exitCode = 1;
}).finally(async () => {
  try {
    await cleanup();
    if (actual) {
      const finalLog = fs.readFileSync(path.join(evidence, 'maven.stdout.log'), 'utf8');
      assert.equal(finalLog.split('INSTRUMENTATION311_DELEGATE_CLOSED token=' + initial.delegate_token).length - 1, 1,
          'owned counter delegate must close exactly once after successful observation');
      save('DELEGATE-CLEANUP.json', {at_utc: now(), delegate_token: initial.delegate_token,
        closed_log_count: 1, owned_counter_joined_by_pre_destroy: true});
    }
  }
  catch (error) { console.error('OWNED CLEANUP FAILED: ' + error); process.exitCode = 1; }
  if (fs.existsSync(evidence)) save('TERMINAL.json', {at_utc: now(), outcome: actual ? actual.outcome : 'FAILED',
    assertion_exit_code: process.exitCode || 0, wrapper_ended: ended, wrapper_exit_code: childExit,
    no_business_dev_or_Game_action: true});
});
