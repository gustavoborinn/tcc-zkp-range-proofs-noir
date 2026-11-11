"""Tabela editorial a partir de 80 receipts; não executa transações."""
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT/'results/final-gas-20261026-attempt05'
files = [DATA/'status.json', DATA/'records.json', DATA/'summary.json', DATA/'arithmetic-review.json', DATA/'fork-block.json']
load = lambda p: json.loads(p.read_text())
assert load(files[0])['status'] == 'complete'
records = load(files[1]); summaries = load(files[2])
assert len(records) == 40 and len(summaries) == 8
names = ['Field diagnóstico','u8','u32','u64','Field restrito 8','Field restrito 32','Field restrito 64','u64 com compromisso']
number = lambda n: f'{n:,}'.replace(',',r'\,')
lines = [r'\begin{table}[htbp]',r'\centering',r'\caption{Gas de verificação das oito variantes no fork local de Sepolia}',r'\label{tab:gas}',r'\small',r'\begin{tabular}{lrrrr}',r'\hline',r' & \multicolumn{3}{c}{Gas total} & Execução \\',r'Variante & Mínimo & Mediana & Máximo & líquida \\',r'\hline']
for name, summary in zip(names,summaries):
    group = [r for r in records if r['variant']==summary['variant']]
    assert len(group)==5
    totals=[]; executions=[]
    for record in group:
        folder=DATA/record['directory']; datafile=folder/'calldata.txt'; files.append(datafile)
        data=bytes.fromhex(datafile.read_text().strip()[2:]); tokens=data.count(0)+4*(len(data)-data.count(0))
        pair=[]
        for i in (1,2):
            receipt_path=folder/f'run-{i}/receipt.json'; files.append(receipt_path)
            receipt=load(receipt_path); assert int(receipt['status'],16)==1
            gas=int(receipt['gasUsed'],16); assert gas>21000+10*tokens
            pair.append(gas); executions.append(gas-21000-4*tokens)
        assert pair[0]==pair[1]; totals.append(pair[0])
    totals.sort(); assert [totals[0],totals[2],totals[4]]==[summary['min'],summary['median'],summary['max']]
    assert len(set(executions))==1
    lines.append(name+' & '+' & '.join(number(v) for v in (totals[0],totals[2],totals[4],executions[0]))+r' \\')
lines += [r'\hline',r'\end{tabular}',r'\par\smallskip',r'\begin{minipage}{\textwidth}',r'\renewcommand{\baselinestretch}{1}\small',r'Fonte: elaboração própria a partir dos recibos da coleta de 26/10/2026.\par',r'Nota: valores em unidades de gas. Resumo de cinco provas por variante; duas transações por prova, com custos idênticos entre repetições. A execução líquida foi constante nas cinco provas. Fork no bloco 11.999.881, Anvil 1.1.0 com Prague; solc 0.8.28, alvo Cancun e parâmetro optimizer\_runs=1. Field diagnóstico possui relação distinta das variantes de intervalo.',r'\end{minipage}',r'\end{table}']
target=ROOT/'manuscript/tables/gas-costs.tex';target.write_text('\n'.join(lines)+'\n')
files += [Path(__file__),target]
(ROOT/'manuscript/validation/gas-table-provenance.json').write_text(json.dumps({'receipts_checked':80,'fixtures':40,'source_status':'ACTUAL_RUN','hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}},indent=2)+'\n')
print('Tabela gerada; 80 receipts e 8 resumos conferidos.')
