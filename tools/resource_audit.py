"""Reproducible local CPU/RSS/logical-I/O scenarios; no network publication.

Run each case in a fresh process against explicit sibling source checkouts.
RSS is sampled at 20 ms. Process I/O counters include cached/pipe I/O and are
not physical-disk traffic. Self CPU excludes child CPU. Linux process I/O
also includes waited-for children; Windows process I/O does not. Compare
I/O within one platform and never add sampled child I/O to Linux totals.
Synthetic inputs and all writable state live under --work-root.
"""
from __future__ import annotations

import argparse
import cProfile
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

import psutil


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def footprint(root):
    return sum(p.stat().st_size for p in root.rglob('*') if p.is_file())


PROFILE = False


def measure(function, root):
    proc = psutil.Process()
    stop = threading.Event()
    rss_start = proc.memory_info().rss
    peak = [rss_start]
    def sample():
        while not stop.wait(.02):
            peak[0] = max(peak[0], proc.memory_info().rss)
    sampler = threading.Thread(target=sample, daemon=True)
    profile = cProfile.Profile()
    before = proc.io_counters()
    disk_before = footprint(root/'state')
    cpu = time.process_time()
    start = time.perf_counter()
    sampler.start()
    # Profile the same path in every run; report this instrumentation explicitly.
    if PROFILE:
        profile.enable()
    try:
        outcome = function()
    finally:
        profile.disable()
        elapsed, cpu_elapsed = time.perf_counter()-start, time.process_time()-cpu
        stop.set()
        sampler.join()
    after = proc.io_counters()
    if PROFILE:
        profile.dump_stats(root/'profile.pstats')
    return dict(wall_seconds=elapsed, self_cpu_seconds=cpu_elapsed,
                rss_start_bytes=rss_start, rss_peak_bytes=max(peak[0],proc.memory_info().rss),
                self_io_delta={k:getattr(after,k)-getattr(before,k) for k in before._fields},
                state_bytes_before=disk_before,state_bytes_after=footprint(root/'state'),
                outcome=outcome)


def prepare(args):
    source, root = args.source_root, args.work_root
    root.mkdir(parents=True,exist_ok=False,mode=0o700)
    (root/'state').mkdir(mode=0o700)
    os.environ['MINDIE_DIAGNOSTICS_ROOT'] = str(root/'state/diagnostics')
    os.environ['MINDIE_DIAGNOSTICS_CONFIG'] = str(root/'disabled-reporting.json')
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    sys.dont_write_bytecode = True
    for name in ('knowledge','audit-diagnostics','audit-remote-dev'):
        sys.path.insert(0,str(source/name))
    os.environ['PYTHONPATH'] = os.pathsep.join(str(source/name) for name in
        ('knowledge','audit-diagnostics','audit-remote-dev'))
    os.environ['REMOTE_DEV_STATE_DIR'] = str(root/'state/remote-dev')
    os.environ['MINDIE_AGENT_CONFIG'] = str(root/'unconfigured.json')
    os.environ['MINDIE_KIMI_CONFIG'] = str(root/'unconfigured.json')
    os.environ['MINDIE_CC_CONFIG'] = str(root/'unconfigured.json')
    return source, root


def scenario(args):
    source, root = prepare(args)
    name = args.case
    from resource_cases import extra_case
    extra = extra_case(name, source, root, measure, load)
    if extra is not None:
        return extra
    if name == 'imports':
        def run():
            import mindie_knowledge.loop.cli
            import mindie_diagnostics.cli
            import remote_dev.mcp.server
            return {'modules':len(sys.modules)}
        return measure(run,root)
    if name in {'tokenize','fallback'}:
        body = ('测量公开文本 torch_npu.npu_rms_norm result=correct\n' * 24000)
        if name == 'tokenize':
            from mindie_knowledge.retrieval import index_text
            function = lambda: {'input_bytes':len(body.encode()),'output_chars':len(index_text(body))}
        else:
            from mindie_knowledge.loop.transcript_capture import fallback_header
            function = lambda: {'input_bytes':len(body.encode()),'header':fallback_header(body)}
        return measure(function,root)
    if name == 'diagnostic_events':
        from mindie_diagnostics import get_recorder
        recorder = get_recorder('mindie-performance')
        def run():
            for _ in range(2000):
                with recorder.operation('synthetic.local') as operation:
                    operation.event('INFO','measured',count=1)
            return {'operations':2000}
        return measure(run,root)

    from mindie_knowledge.loop.store import Store, digest
    from mindie_knowledge.loop import settings
    from mindie_knowledge.loop.engine import Engine
    from mindie_knowledge.loop.activation import Admission
    from mindie_knowledge.loop.transcript_redaction import install_scanner
    store = Store(root/'state/knowledge','performance')
    config = root/'community.json'
    settings_state = settings.write(config,enabled=True,repository='example/knowledge',
                                    project_roots=[str(root)],idle_seconds=86400)
    generation = settings_state.generation
    if name in {'history_poll', 'search'}:
        from resource_cases import store_case
        result = store_case(name, store, root, measure)
        store.close()
        return result
    if name.startswith('idle_'):
        count = 40 if name == 'idle_pending' else 0
        content = 'Public measurement note. ' * (256*1024//25)
        for index in range(count):
            store.create_draft(kind='experience',title=f'Public case {index}',summary='Synthetic measurement',
                               content=content,generation=generation)
        engine = Engine(store,settings_path=config)
        def run():
            engine.start()
            time.sleep(6)
            engine.shutdown()
            return {'drafts':count,'body_bytes':len(content.encode())*count,'errors':engine.errors}
        result = measure(run,root)
        store.close()
        return result
    if name.startswith('capture_'):
        scanner = install_scanner()
        harness = name.removeprefix('capture_')
        support = load(source/'knowledge/tests/lane_support.py', 'resource_lane_support')
        parser_file = (source/'mindie-agent-codex/plugins/mindie-agent/scripts/codex_transcript.py' if harness == 'codex'
                       else source/f'mindie-agent-{harness}/scripts/transcript.py')
        parser = load(parser_file, 'audit_parser')
        session = support.SESSIONS[harness]
        admission = Admission(root/'state/admission.sqlite3')
        admission.activate(session,project_root=str(root))
        engine = Engine(store,settings_path=config,admission=admission,transcript_adapter=parser,
                        capture_mode='public-transcript',redactor_executable=scanner)
        path = support.transcript_path(harness, root, session)
        path.write_bytes(support.encode_header(harness, session, time.time()))
        def run():
            for turn in range(24):
                text = f'public-marker-{turn}\n' + 'Valid synthetic observation 测量通过. ' * 900
                # Retain fractional timestamps; authority is established just
                # before capture, so second-rounded fixtures can predate it.
                blob = json.loads(support.encode_record(harness, session, text, time.time()))
                if harness in {'codex', 'cc'}:
                    from datetime import datetime, timezone
                    blob['timestamp'] = datetime.now(timezone.utc).isoformat()
                with path.open('ab') as stream:
                    stream.write(json.dumps(blob,ensure_ascii=False).encode() + b'\n')
                event = engine.capture(session_id=session,turn_id=str(turn),transcript_path=str(path))
                engine._process(event['id'])
                row = store.capture_row(event['id'])
                assert row['status']=='organized',row
            docs = store.drafts_changed(generation=generation)
            assert len(docs)==1
            assert all(docs[0]['content'].count(f'public-marker-{i}\n')==1 for i in range(24))
            return dict(turns=24,body_bytes=len(docs[0]['content'].encode()),
                        revisions=store.db.execute('SELECT count(*) FROM revisions').fetchone()[0],
                        cursor=store.cursor(str(path.resolve()))['ok_finish'],transcript_bytes=path.stat().st_size)
        result = measure(run,root)
        store.close()
        return result
    raise ValueError(name)


CASES = ('imports','tokenize','fallback','diagnostic_events','diagnostic_ingest',
         'idle_empty','idle_pending','history_poll','search',
         'hook_codex','hook_kimi','hook_cc','remote_local',
         'capture_codex','capture_kimi','capture_cc')

def main():
    global PROFILE
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root',type=lambda p:Path(p).resolve(),required=True)
    parser.add_argument('--work-root',type=lambda p:Path(p).resolve(),required=True)
    parser.add_argument('--case',choices=CASES)
    parser.add_argument('--profile',action='store_true',help='Hotspot diagnosis only; changes measured timing')
    args=parser.parse_args()
    PROFILE=args.profile
    if args.case:
        result=scenario(args)
        result.update(case=args.case,platform=sys.platform,python=sys.version,
                      instrumentation=('cProfile + ' if PROFILE else '') + '20ms self RSS sampler; external 50ms whole-case tree sampler',
                      child_accounting='sampled lower bound; short-lived children can be missed',
                      io_accounting=('process-only logical I/O' if os.name == 'nt' else
                                     'process I/O includes waited-for children; read_chars/write_chars are logical I/O'))
        (args.work_root/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(result,ensure_ascii=False),flush=True)
        return
    args.work_root.mkdir(parents=True,exist_ok=False)
    results=[]
    for case in CASES:
        command=[sys.executable,str(Path(__file__).resolve()),'--source-root',str(args.source_root),
                 '--work-root',str(args.work_root/case),'--case',case]
        if PROFILE:
            command.append('--profile')
        tree_peak = 0
        children = {}
        with (args.work_root/(case+'.stdout')).open('w',encoding='utf-8') as stdout:
            with subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=stdout,stderr=subprocess.STDOUT,
                                  creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)) as child:
                watched = psutil.Process(child.pid)
                deadline = time.monotonic() + 300
                while child.poll() is None:
                    try:
                        rss = watched.memory_info().rss
                        for item in watched.children(recursive=True):
                            try:
                                cpu = item.cpu_times()
                                children[(item.pid,item.create_time())] = dict(
                                    cpu_seconds=cpu.user+cpu.system,io=item.io_counters()._asdict())
                                rss += item.memory_info().rss
                            except psutil.Error:
                                pass
                        tree_peak = max(tree_peak,rss)
                    except psutil.Error:
                        pass
                    if time.monotonic() > deadline:
                        child.kill()
                        raise TimeoutError(case)
                    time.sleep(.05)
        if child.returncode:
            raise RuntimeError(f'{case} failed; see {args.work_root/(case+".stdout")}')
        result=json.loads((args.work_root/case/'result.json').read_text(encoding='utf-8'))
        result.update(whole_case_sampled_tree_peak_bytes=tree_peak,
                      whole_case_sampled_children=list(children.values()))
        (args.work_root/case/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        results.append(result)
        print(json.dumps(dict(case=case,wall_seconds=result['wall_seconds'],self_cpu_seconds=result['self_cpu_seconds'],
                             rss_peak_mb=result['rss_peak_bytes']/1048576,state_mb=result['state_bytes_after']/1048576)),flush=True)
    (args.work_root/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':
    main()
