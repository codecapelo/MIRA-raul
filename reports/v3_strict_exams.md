# v3.3: exame estrito ("entregar o que foi pedido") e casos privados

## Por que
No caso externo 011 o médico pediu "Serum IgE" e a ferramenta devolveu a IgE específica para o antígeno do diagnóstico. Nas rodadas anteriores o mesmo comportamento aparece em outros casos (por exemplo "Cardiac CT" devolvendo angiografia coronariana, "Urinalysis" devolvendo urocultura, "Stool ova and parasites" devolvendo sorologia). O prompt do associador original manda mapear "um pedido a vários candidatos quando clinicamente apropriado".

## Regra
O associador entrega o que foi pedido, nem mais nem outro exame. Uma relação por pedido (`src/mira_runner/matcher_v3.py`):
- `same`: é o próprio exame (sinônimos e descritores que não mudam o exame valem).
- `component`: um analito que o resultado de um pacote traz por escrito; só o trecho pedido é liberado (cópia literal validada; se não der para isolar, não libera).
- `panel_part`: painel padrão do qual o caso traz só parte; a nota avisa.
- `too_generic`: categoria ou pedido incompleto (por exemplo "painel de parasitose", "IgE específica" sem o antígeno): volta como `ambiguous_request` pedindo ao médico que especifique o exame.
- `none`: tudo o mais, inclusive pedido mais amplo que o candidato (genérico para específico), outro espécime, organismo, antígeno, analito, sítio, modalidade ou ensaio.
Pedido de hemograma completo devolve o hemograma completo (eosinófilos incluídos). Pedido de uma amostra de fezes nunca é respondido com sorologia ou exame de sangue. A dica de ferramenta errada vem da mesma decisão estrita. Exame de analito único é recuperável pelo próprio nome (PCR, D-dímero, LDH, VHS).

## Como usar
`--strict-exams` (junto de `--v32`): tag com sufixo `sx`; as variantes anteriores não mudam. O texto do prompt do médico ganha uma frase sobre a regra. Estado: 18 testes novos (sem custo) passam; a avaliação paga do associador (`scripts/matcher_eval.py`, 56 pedidos rotulados em casos públicos) ainda não foi executada.

## Casos privados (não open access)
`cases/case_011` a `case_015`, `runs/v3/*api*`, `runs/v3/*prv*`, `results/v3_*api*` e `results/v3_*prv*` ficam fora do git. `--private` põe traces e resultados em pastas `prv`. Cada caso guarda a procedência (DOI e sha256 do PDF) em `provenance.json`; as discussões e resultados que só existem depois do diagnóstico ou do tratamento não foram usados como fatos.

## Sonnet e Opus
Pela assinatura Pro (CLI) por padrão; `--opus-tiebreak` põe o Opus 5.5 no desempate de três vias, como no braço por API. O custo estimado se fosse pela API vem dos eventos `cli_call`: `claude_api_equiv_usd` (revisores e mapa, parte da implantação) e `claude_all_equiv_usd` (inclui o paciente).
