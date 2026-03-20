import os
import subprocess
import sys
import shutil

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
env = os.environ.copy()
env['PYTHONPATH'] = os.path.join(REPO_ROOT, 'src')
env['PYTHONIOENCODING'] = 'utf-8'

input_atf = os.path.join(REPO_ROOT, 'tests', 'integration_refs', 'L_I.2_Poem_of_Creation_SB_II.atf')
outdir = os.path.join(REPO_ROOT, 'outputs', 'integration_test')

if os.path.exists(outdir):
    shutil.rmtree(outdir)
os.makedirs(outdir, exist_ok=True)

cmd = [sys.executable, '-m', 'akkapros.cli.fullprosmaker', input_atf, '-p', 'test', '--outdir', outdir]
print('Running:', ' '.join(cmd))
rc = subprocess.run(cmd, cwd=REPO_ROOT, env=env)
print('Return code:', rc.returncode)
sys.exit(rc.returncode)
