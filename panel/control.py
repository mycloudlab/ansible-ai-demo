"""Privileged fixed operations for the isolated demonstration; no caller-supplied paths."""
import json, os, pwd, subprocess, sys
from pathlib import Path
CONTROL = Path('/var/lib/caixa-demo/control')
def state(unit):
    return subprocess.run(['/usr/bin/systemctl', 'is-active', unit], capture_output=True, text=True, timeout=8).stdout.strip()
def main(action):
    if action == 'status':
        print(json.dumps({'application': state('caixa-demo'), 'database': state('postgresql@16-main'), 'oom_pending': (CONTROL/'oom-once').exists()})); return
    if action not in ('database', 'oom'):
        raise ValueError('Unknown action')
    if state('caixa-demo') != 'active' or state('postgresql@16-main') != 'active' or (CONTROL/'oom-once').exists():
        raise ValueError('Restore the baseline before another scenario')
    if action == 'database':
        subprocess.run(['/usr/bin/systemctl', 'stop', 'postgresql@16-main'], check=True, timeout=20)
    else:
        user = pwd.getpwnam('caixademo')
        p = CONTROL/'oom-once'
        fd = os.open(p, os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'w') as f:
            os.fchown(f.fileno(), user.pw_uid, user.pw_gid); f.write('presenter-trigger\n')
if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) == 2 else '')
