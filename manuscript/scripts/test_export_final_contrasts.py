import importlib.util,json,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('exporter',Path(__file__).with_name('export_final_contrasts.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ExportTests(unittest.TestCase):
    def report(self):
        row={'ratio':2.,'p':.001,'p_holm':.016,'reject':True,'pointwise_95':[1.5,2.5],'simultaneous_bonferroni':[1.2,3.]}
        return {'validated_pairs':20,'complete_allocation':True,'inference':{'available':True,'contrasts':{k:row.copy() for k in m.EXPECTED}}}
    def run_export(self,report):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);source=p/'synthetic.json';source.write_text(json.dumps(report))
            m.export(source,p/'out')
            self.assertEqual(len((p/'out/contrasts.csv').read_text().splitlines()),17)
            with self.assertRaises(FileExistsError):m.export(source,p/'out')
    def test_synthetic_and_no_overwrite(self):self.run_export(self.report())
    def test_partial(self):
        r=self.report();r['validated_pairs']=10
        with self.assertRaises(ValueError):self.run_export(r)
    def test_missing_contrast(self):
        r=self.report();r['inference']['contrasts'].pop('C:native')
        with self.assertRaises(ValueError):self.run_export(r)
    def test_nonfinite_interval(self):
        r=self.report();r['inference']['contrasts']['C:native']['pointwise_95']=[1,float('inf')]
        with self.assertRaises(ValueError):self.run_export(r)
    def test_wrong_decision(self):
        r=self.report();r['inference']['contrasts']['C:native']['reject']=False
        with self.assertRaises(ValueError):self.run_export(r)
if __name__=='__main__':unittest.main()
