# Verificação independente — piloto em andamento

**Atualização após terminal Mancer:** o piloto GPT-OSS/case_001 foi concluído sob nova condição documentada. Houve alucinação do paciente simulado que contaminou a conclusão STEMI. A análise terminal está em `reports/patient_fidelity_case001_gptoss.md`; o texto abaixo preserva a fotografia anterior AkashML interrompida e não deve ser atribuído ao terminal Mancer.

Escopo: leitura de código, configuração, casos e rastros existentes; nenhuma chamada paga, execução do runner ou alteração em código/configuração/casos. A documentação foi atualizada para registrar AkashML BF16 e a compressão temporal. Este relatório é uma fotografia parcial do piloto GPT-OSS/case_001 e não certifica a execução completa.

## Achado crítico observado

O associador GLM-4.5-Air/Novita recebeu pedido válido de troponina, BNP, hemograma, painel metabólico, lactato e coagulação. Sua resposta veio truncada dentro do JSON, com teto de 2.048 tokens. O parser gerou erro; o bloco genérico de correção do runner classificou esse erro como argumentos inválidos do médico e devolveu instrução para repetir a ferramenta. Essa classificação é incorreta: a lista de exames enviada pelo médico era JSON válido. A falha consumiu uma das correções limitadas; nova falha pode interromper o encontro. Não houve modificação durante o piloto ativo.

Evidência: `logs/raw/openai__gpt-oss-120b/case_001.jsonl`, eventos `request`/`response` com papel `matcher` e evento `tool` de `request_blood_test` no turno 4; `src/mira_runner/runner.py:26–32` e `:42–50`. A resposta `gen-1791062879-kgiiKpnagW950jVXqSOz` informa `finish_reason=length`, 2.048 tokens de saída, dos quais 1.877 de raciocínio. A tentativa corretiva seguinte produziu JSON completo (`finish_reason=stop`), permitindo continuar. A resposta bruta e os custos permanecem registrados. Recomenda-se separar erro do associador de erro de argumentos do médico e dimensionar o orçamento de saída/raciocínio do associador em uma condição posterior identificada, sem alterar silenciosamente o piloto em andamento.

## Evidência favorável até a fotografia

- Respostas médicas e do paciente vieram de AkashML, compatível com `config/run1.json`; respostas do associador vieram de Novita, também compatíveis. Não foi observado fallback ou provedor inesperado nessa amostra.
- O paciente respondeu que localização/qualidade/duração da dor não estavam registradas; não revelou pseudoaneurisma, ruptura de stent ou referência final.
- A associação de ultrassom cardíaco à ecocardiografia transtóracica usou o item existente `ecg_008`. O resultado devolvido coincide com `cases/case_001/investigations.json`; não foi criado resultado novo. O prefixo `ecg` desse identificador não transforma o exame em eletrocardiograma.
- A ferramenta física devolveu o choque descrito no caso. A chamada incluiu `{"": {}}`, apesar de o schema não definir argumentos; a execução aceitou esse formato. É uma divergência de validação, sem fabricação de resultado observada.
- Filtros originais de tempo/pré-requisitos foram removidos da execução de ferramentas, preservados nos dados; `unavailable_for_immediate_care` continua excluído. Essa compressão temporal está documentada em `PROTOCOL.md`.

## Interrupção posterior observada

Após 21 respostas e cinco execuções de ferramenta, a rota AkashML também devolveu HTTP 429 (`provider_error_code=queue_timeout`, `limit_source=upstream_provider_shared_pool`) no pedido `ac32b0cf-dc2d-43f5-b838-15728a9eef0f`. O rastro registrou `halt`; não havia `case_complete` nem resposta de juiz na fotografia. Essa rejeição pertence à rota AkashML atual e deve ser distinguida das rejeições Deka anteriores. O estado/custo do pedido precisa ser reconciliado antes de retomada, conforme controle do runner. Uma indicação de `Retry-After` não demonstra custo zero ou autorização para repetição automática.

## Limites e fontes

A ausência de vazamento ou troca de provedor observada vale somente para as respostas já inspecionadas. Não certifica o restante do piloto, outros casos, correção diagnóstica ou segurança clínica. O matcher não realizou a avaliação final; os critérios do juiz ainda precisam ser observados em resposta real.

Fontes da revisão: `config/run1.json`; `src/mira_runner/client.py` (roteamento, validação e liquidação); `src/mira_runner/runner.py` (papéis e parser); `src/mira_runner/tools.py` (pool e associação); `cases/case_001/patient.json`; `cases/case_001/investigations.json`; rastro bruto acima. A rejeição anterior permanece em `logs/incomplete/initial_429/case_001.jsonl`; `reports/pilot_recovery.json` descreve uma recuperação anterior específica e não deve ser usado isoladamente como prova de todas as mudanças de rota.
