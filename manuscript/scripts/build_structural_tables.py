"""Gera tabelas estruturais; não executa experimentos."""
import csv
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
source = ROOT / 'results/final-readiness-20261024/coverage.csv'
manifest = ROOT / 'results/spec008/final-correctness/manifest.json'
rows = list(csv.DictReader(source.open()))
records = {r['package']: r for r in json.loads(manifest.read_text())['records']}
names = ['Field diagnóstico', 'u8', 'u32', 'u64', 'Field restrito 8', 'Field restrito 32', 'Field restrito 64', 'u64 com compromisso']
assert len(rows) == len(records) == len(names) == 8
for row in rows:
    for key in ('acir_opcodes', 'backend_gates', 'proof_bytes'):
        assert int(row[key]) == records[row['variant']][key]
    assert 24576-int(row['runtime_template_bytes']) == int(row['eip170_margin_bytes'])
def number(value):
    return f'{int(value):,}'.replace(',', r'\,')
def table(filename, title, label, headers, keys, note):
    content = [r'\begin{table}[htbp]', r'\centering', r'\caption{'+title+'}', r'\label{'+label+'}', r'\begin{tabular}{l'+'r'*len(keys)+'}', r'\hline', 'Variante & '+' & '.join(headers)+r' \\', r'\hline']
    content += [name+' & '+' & '.join(number(row[k]) for k in keys)+r' \\' for name,row in zip(names,rows)]
    content += [r'\hline', r'\end{tabular}', r'\par\smallskip', r'\begin{minipage}{\textwidth}', r'\renewcommand{\baselinestretch}{1}\small', r'Fonte: elaboração própria a partir dos artefatos validados do experimento (2026).\par', 'Nota: '+note, r'\end{minipage}', r'\end{table}']
    (ROOT/'manuscript/tables'/filename).write_text('\n'.join(content)+'\n')
table('circuit-costs.tex','Operações e tamanho das provas das oito variantes','tab:circuitos',['ACIR','Gates','Prova (bytes)'],['acir_opcodes','backend_gates','proof_bytes'],'ACIR e gates são contagens de camadas distintas. Provas canônicas com alvo EVM; entradas e versões descritas na Seção~\\ref{cap:implementacao}. Field diagnóstico não verifica pertencimento ao intervalo.')
table('verifier-sizes.tex','Tamanho dos modelos compilados de código dos verificadores','tab:verificadores',['Runtime (bytes)','Margem (bytes)'],['runtime_template_bytes','eip170_margin_bytes'],'Margem calculada em relação a 24.576 bytes (EIP-170). Os tamanhos correspondem aos modelos compilados, incluindo posições de vinculação de bibliotecas; não substituem a conferência do código efetivamente implantado. Não são medidas de gas.')
provenance = {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (source,manifest,Path(__file__))}
(ROOT/'manuscript/validation/structural-tables-provenance.json').write_text(json.dumps({'sources_and_generator':provenance,'rows':8,'checked_manifest_values':24,'checked_margins':8},indent=2)+'\n')
print('8 variantes; 24 valores conferidos no manifesto; 8 margens conferidas.')
