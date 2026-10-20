import sys, unittest
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pdi_lab import component_rows, validate_mask

class AnalysisTests(unittest.TestCase):
    def test_diagonal_connectivity(self):
        m=np.zeros((3,3),np.uint8); m[0,0]=255; m[1,1]=255
        r4,_=component_rows(m,4,0); r8,_=component_rows(m,8,0)
        self.assertEqual(len(r4),2); self.assertEqual(len(r8),1)
    def test_empty_mask(self):
        m=np.zeros((10,10),np.uint8)
        rows,_=component_rows(m,8,0)
        self.assertEqual(len(rows),0)
    def test_border_component(self):
        m=np.zeros((8,8),np.uint8); m[0:3,0:2]=255
        rows,_=component_rows(m,8,0)
        self.assertEqual(len(rows),1); self.assertEqual(rows[0]["x"],0); self.assertEqual(rows[0]["y"],0)
    def test_binary_validation(self):
        with self.assertRaises(ValueError): validate_mask(np.array([[0,1]],dtype=np.uint8))
    def test_opening_removes_isolated_noise(self):
        m=np.zeros((25,25),np.uint8); m[5:20,5:20]=255; m[1,1]=255
        opened=cv2.morphologyEx(m,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3)))
        self.assertEqual(opened[1,1],0)
    def test_closing_fills_small_hole(self):
        m=np.zeros((25,25),np.uint8); m[3:22,3:22]=255; m[12,12]=0
        closed=cv2.morphologyEx(m,cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5)))
        self.assertEqual(closed[12,12],255)

if __name__=="__main__": unittest.main()
