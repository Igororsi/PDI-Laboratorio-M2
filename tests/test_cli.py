import subprocess, sys, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"pdi_lab.py"

class CliTests(unittest.TestCase):
    def run_cli(self,*args):
        return subprocess.run([sys.executable,str(SCRIPT),*map(str,args)],capture_output=True,text=True)
    def test_missing_input_returns_nonzero(self):
        r=self.run_cli("--input",ROOT/"images/input/nao_existe.png","--output",ROOT/"results/nao.png","--operation","segment")
        self.assertNotEqual(r.returncode,0)
    def test_invalid_threshold_returns_nonzero(self):
        r=self.run_cli("--input",ROOT/"images/input/cena1_favoravel.png","--output",ROOT/"results/invalida.png","--operation","segment","--method","fixed","--threshold","300")
        self.assertNotEqual(r.returncode,0)
    def test_unknown_method_returns_nonzero(self):
        r=self.run_cli("--input",ROOT/"images/input/cena1_favoravel.png","--output",ROOT/"results/invalida.png","--operation","segment","--method","desconhecido")
        self.assertNotEqual(r.returncode,0)
    def test_success_returns_zero(self):
        out=ROOT/"results/test_cli_mask.png"
        r=self.run_cli("--input",ROOT/"images/input/cena1_favoravel.png","--output",out,"--operation","segment","--method","fixed","--threshold","120")
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertTrue(out.exists())

if __name__=="__main__": unittest.main()
