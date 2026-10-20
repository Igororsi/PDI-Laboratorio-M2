import sys, unittest
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pdi_lab import segment_image, validate_mask, component_rows

class SegmentationTests(unittest.TestCase):
    def test_fixed_threshold_below_equal_above(self):
        gray=np.array([[119,120,121]],dtype=np.uint8)
        out=segment_image(gray,"fixed",120)
        self.assertEqual(out.tolist(),[[0,255,255]])
    def test_mask_binary_and_same_shape(self):
        gray=np.array([[0,10,120,255]],dtype=np.uint8)
        out=segment_image(gray,"fixed",120)
        self.assertTrue(validate_mask(out,gray.shape))
        self.assertEqual(set(np.unique(out).tolist()),{0,255})
    def test_invalid_threshold(self):
        with self.assertRaises(ValueError): segment_image(np.zeros((2,2),np.uint8),"fixed",300)
    def test_unknown_method(self):
        with self.assertRaises(ValueError): segment_image(np.zeros((2,2),np.uint8),"wat",120)

if __name__=="__main__": unittest.main()
