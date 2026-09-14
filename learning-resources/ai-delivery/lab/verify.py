"""Verify expected red/green learning outcomes; does not approve production code."""
import json, os, pathlib, platform, subprocess, sys
base = pathlib.Path(__file__).resolve().parent
scenarios = [('smoke-naive', 'naive', 'test_contract.Smoke', 0),
             ('contract-naive', 'naive', 'test_contract.Acceptance', 1),
             ('contract-fixed', 'contract', 'test_contract.Acceptance', 0)]
results=[]
for name, variant, target, expected in scenarios:
    env = dict(os.environ, LAB_VARIANT=variant, PYTHONDONTWRITEBYTECODE='1')
    run = subprocess.run([sys.executable, '-m', 'unittest', '-v', target],
                         cwd=base, env=env, text=True, capture_output=True)
    evidence = (run.stdout + run.stderr).replace(str(base) + os.sep, "")
    expected_failures = ('test_same_customer_retry_returns_same_id_and_one_record',
                         'test_reused_key_with_different_amount_rejected_without_write',
                         'test_non_positive_amount_rejected_without_write')
    diagnostic_ok = (all(('FAIL: ' + test) in evidence for test in expected_failures)
                     and 'ERROR:' not in evidence) if name == 'contract-naive' else 'OK' in evidence
    matched = run.returncode == expected and diagnostic_ok
    results.append(dict(name=name, variant=variant, command=f'LAB_VARIANT={variant} python3 -m unittest -v {target}',
                        expected_exit=expected, actual_exit=run.returncode,
                        matched=matched, diagnostic_verified=diagnostic_ok, output=evidence))
    print(f'{name}: exit={run.returncode}; expected={expected}; matched={matched}')
report=dict(python=platform.python_version(), fixture='Original offline teaching example',
            scope='Sequential requests in memory; no database, persistence, concurrency, network or deployment verification',
            results=results)
(base/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
sys.exit(0 if all(r['matched'] for r in results) else 1)
