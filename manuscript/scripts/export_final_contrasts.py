"""Export an eligible final report; never compute inference or accept partial data."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

VARIANTS = ['field','u8','u32','u64','field_asserted_8','field_asserted_32','field_asserted_64','committed_u64']
EXPECTED = {f'A:{v}' for v in VARIANTS}
EXPECTED |= {f'B:{e}:{w}' for e in ('native','wasm') for w in (8,32,64)} | {'C:native','C:wasm'}

def export(source, output):
    report = json.loads(source.read_text())
    inference = report.get('inference', {})
    if (report.get('validated_pairs') != 20 or report.get('complete_allocation') is not True
            or inference.get('available') is not True):
        raise ValueError('Final report unavailable or allocation incomplete')
    rows = inference.get('contrasts', {})
    if set(rows) != EXPECTED:
        raise ValueError('The fixed family must contain 16 contrasts')
    for key, row in rows.items():
        for field in ('ratio','p','p_holm'):
            value = row[field]
            if type(value) not in (int,float) or not math.isfinite(value):
                raise ValueError('Invalid numeric result')
        if row['ratio'] <= 0 or not 0 <= row['p'] <= row['p_holm'] <= 1:
            raise ValueError('Invalid ratio or probabilities')
        if type(row['reject']) is not bool or row['reject'] != (row['p_holm'] <= .05):
            raise ValueError('Inconsistent Holm decision')
        for field in ('pointwise_95','simultaneous_bonferroni'):
            interval = row[field]
            if len(interval) != 2 or any(type(x) not in (int,float) or not math.isfinite(x) or x <= 0 for x in interval):
                raise ValueError('Nonfinite interval: explicit editorial treatment required')
            if not interval[0] <= row['ratio'] <= interval[1]:
                raise ValueError('Invalid interval order')
    output.mkdir(parents=True, exist_ok=False)
    with (output/'contrasts.csv').open('w',newline='') as stream:
        writer=csv.writer(stream)
        writer.writerow(['contrast','ratio','pointwise95_low','pointwise95_high','simultaneous_low','simultaneous_high','p','p_holm','reject'])
        for key,row in sorted(rows.items()):
            writer.writerow([key,row['ratio'],*row['pointwise_95'],*row['simultaneous_bonferroni'],row['p'],row['p_holm'],row['reject']])
    (output/'provenance.json').write_text(json.dumps({
        'source':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'limits':'Export of report only; does not establish IID or authorize conclusions.',
        'family_size':16},indent=2)+'\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args()
    export(args.report,args.output)
