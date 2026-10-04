"""Resource audit workloads, deliberately separate from product code."""
import json
import ast
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


def extra_case(name, source, root, measure, load):
    if name == 'imports':
        # Runtime owners stay independent; this checks their deliberately
        # vendored stdlib-only launch primitive against the core source.
        functions = []
        for relative in ('knowledge/mindie_knowledge/windows_process.py',
                         'audit-remote-dev/remote_dev/core/local_process.py',
                         'mindie-agent-codex/plugins/mindie-agent/scripts/windows_process.py',
                         'mindie-agent-kimi/scripts/bounded.py',
                         'mindie-agent-cc/scripts/bounded.py'):
            tree = ast.parse((source/relative).read_text(encoding='utf-8'))
            found = [n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name == '_resume_windows_process']
            # Older baselines predate the shared fast primitive.
            if found and 'NtResumeProcess' in ast.unparse(found[0]):
                functions.append(ast.dump(found[0],include_attributes=False))
        assert not functions or len(functions) == 5 and len(set(functions)) == 1
        return None
    if name.startswith('hook_'):
        harness = name.removeprefix('hook_')
        if harness == 'codex':
            scripts = source/'mindie-agent-codex/plugins/mindie-agent/scripts'
            # This module's imports follow the same native script directory.
            sys.path.insert(0, str(scripts))
            updater = load(scripts/'auto_update.py', 'audit_updater')
            commands = updater.stop_hook_commands([sys.executable, str(scripts/'bridge.py'), 'stop'])
            if os.name == 'nt':
                command = [shutil.which('pwsh') or shutil.which('powershell'),
                           '-NoLogo','-NoProfile','-NonInteractive','-Command',commands['commandWindows']]
            else:
                command = ['sh', '-c', commands['command']]
        else:
            command = [sys.executable, str(source/f'mindie-agent-{harness}/scripts/mindie_launch.py'), 'hook','stop']
        def run():
            for _ in range(10):
                result = subprocess.run(command, input=b'{}', capture_output=True, timeout=10,
                                        creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                assert result.returncode == 0, result.stderr
                assert json.loads(result.stdout) == {}, result.stdout
            return {'invocations':10,'mode':'unconfigured quiet native entrypoint'}
        return measure(run, root)
    if name == 'remote_local':
        from remote_dev.core.local_process import OwnedProcess
        from remote_dev.core.state_store import atomic_write_json
        payload = b'Public process transport measurement.\n' * 14000
        def run():
            for i in range(10):
                with OwnedProcess([sys.executable,'-c','import sys;sys.stdout.buffer.write(sys.stdin.buffer.read())'],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as owner:
                    stdout, stderr = owner.process.communicate(payload, timeout=10)
                    assert owner.process.returncode == 0 and stdout == payload and not stderr
                atomic_write_json(root/'state/remote-dev'/f'receipt-{i}.json', {'bytes':len(stdout),'completed':True})
            return {'owned_processes':10,'pipe_bytes':len(payload)*20,
                    'scope':'local ownership, pipes and durable receipts; excludes SSH/network/NPU'}
        return measure(run, root)
    if name == 'diagnostic_ingest':
        from mindie_diagnostics import get_recorder
        from mindie_diagnostics.ingestion import ingest
        from mindie_diagnostics.outbox import Outbox
        recorder = get_recorder('resource-ingest')
        for _ in range(1000):
            recorder.event('INFO','synthetic.event',count=1)
        recorder.close()
        queue = Outbox(root/'state/diagnostic-queue.db')
        def run():
            rounds = [ingest(root/'state/diagnostics',queue) for _ in range(10)]
            assert rounds[0]['scanned_bytes'] > 0
            assert all(r['scanned_bytes'] == 0 for r in rounds[1:])
            return {'rounds':rounds}
        return measure(run, root)
    return None


def store_case(name, store, root, measure):
    if name == 'history_poll':
        from mindie_knowledge.loop.budget import MaintenanceBudget
        MaintenanceBudget(store)
        with store.db:
            store.db.executemany(
                "INSERT INTO captures(id,root_session,session,turn,summary,status,detail,created) "
                "VALUES(?,'r','s','t','','organized','',0)", ((str(i),) for i in range(50000)))
            store.db.executemany("INSERT INTO transcript_tasks VALUES(?,?,'c','d','complete','',0,0)",
                                 ((str(i), str(i)) for i in range(50000)))
            store.db.executemany("INSERT INTO maintenance_attempts(id,session,role,started,status) "
                                 "VALUES(?,'s','organize',0,'succeeded')", ((str(i),) for i in range(50000)))
        def run():
            calls = [0]
            def count():
                calls[0] += 1
                return 0
            store.db.set_progress_handler(count,1000)
            try:
                for _ in range(100):
                    assert store.due_capture() is None
                    assert store.due_application() is None
                    assert store.db.execute("SELECT * FROM transcript_tasks WHERE summary_status='pending' "
                                            "AND summary_due<=? ORDER BY updated LIMIT 1",(time.time(),)).fetchone() is None
            finally:
                store.db.set_progress_handler(None,0)
            return {'polls':100,'completed_rows_per_table':50000,'sqlite_vm_steps_floor':calls[0]*1000}
        return measure(run,root)
    if name == 'search':
        for i in range(200):
            store.create_draft(kind='experience',title=f'Operator {i}',summary='RMS observation',
                               content=('torch_npu.npu_rms_norm measurement 测量正确. ' * 200) + f' case_{i}')
        def run():
            hits = 0
            for _ in range(100):
                result = store.query('rms_norm measurement')
                assert result['results']
                hits += len(result['results'])
            return {'queries':100,'entries':200,'returned_hits':hits}
        return measure(run, root)
    raise ValueError(name)
