# Diagnóstico passivo externo dos adapters Codex

Arquivo: `scripts/run_with_provider_diagnostics.py`  
SHA-256: `8830e5c2d23d93f04768620d40e0a90595d4949d9d9ed7f0e1e8604cf6475751`

O wrapper foi preparado em 28-09-2026 após erros de provider/runner de causa indeterminada na extensão Terra. Ele **não altera nenhum arquivo congelado**. Na próxima retomada autorizada, importa o adapter correspondente e o scheduler congelado, envolve somente `generate`, chama a implementação original **uma vez** e devolve o mesmo objeto ou repropaga a mesma exception. Não muda mensagens, argumentos, configuração, modelo, esforço, stopping, retries ou escrita dos traces clínicos. O lock/resume do scheduler original continua controlando a execução.

O arquivo adicional de diagnóstico guarda somente `utc`, `model`, `class`, `category`. Categorias derivam de mensagens constantes explicitamente permitidas do adapter: CLI indisponível, status de autenticação, exit code numérico, ausência de final action, JSON da ação, quantidade de calls, JSON/tipo de argumentos e incompatibilidade de configuração congelada. Timeout tem categoria própria. Qualquer outra mensagem vira `unknown_adapter_exception`; o texto da exception não é escrito. Nenhum stdout/stderr, prompt, dado clínico, credencial ou stack trace é guardado. Falha de I/O do diagnóstico não altera o resultado/exception original.

## Uso

Do diretório `benchmark/`, somente depois que o executor anterior encerrar:

```bash
python3 -B scripts/run_with_provider_diagnostics.py --model gpt-5.6-terra
python3 -B scripts/run_with_provider_diagnostics.py --model gpt-6-luna
```

Os demais argumentos, se fornecidos, são passados sem modificação ao scheduler congelado. Não executar duas instâncias do mesmo braço; o lock original rejeita a segunda. O diagnóstico fica em `results/provider_diagnostics_2026-09-28/{model}.jsonl`. A primeira linha de cada invocação usa `class=instrumentation`, `category=start` e registra o **UTC real do início da instrumentação**. A instrumentação ainda não estava ativa na chamada Terra já em andamento quando este arquivo foi preparado.

## Verificação

Uma verificação local com classes sintéticas confirmou: retorno com identidade de objeto preservada; exception com identidade preservada; exatamente uma chamada original; somente as quatro chaves permitidas no log; mensagem desconhecida convertida em categoria genérica sem conteúdo. Nenhuma inferência clínica nem alteração de controle foi usada para essa verificação.

## Primeira ativação

Terra: `2026-09-28T19:47:19.969821Z`, na retomada de `case_004`, repetição 3, tentativa 2, após o executor anterior encerrar com um erro de causa indeterminada. Hash do wrapper permanece `8830e5c2d23d93f04768620d40e0a90595d4949d9d9ed7f0e1e8604cf6475751`. As onze combinações terminais existentes foram preservadas pelo scheduler. A instrumentação passa a ser identificada temporalmente; ela não permite reclassificar a causa dos erros anteriores que não tinham esse diagnóstico.

## Primeiro erro classificado

Em `2026-09-28T20:09:01.325548Z`, o sidecar Terra registrou `class=OpenAIAccountError`, `category=arguments_json_invalid`, na primeira tentativa de `case_006`, repetição 2. A exception constante do adapter confirma falha de formato do campo `arguments_json` dessa chamada. A tentativa ficou preservada em `results/extension_terra_2026-09-28/incomplete/1727002e-8af1-46ae-92bc-d90faaf181b5.jsonl`; havia oito ações válidas antes da falha no turno 9. A saída/uso do turno que falhou não é retornada pelo adapter congelado, logo esse consumo permanece indisponível. Não aplicar essa categoria retrospectivamente aos erros anteriores sem sidecar. A retomada repete somente a combinação não terminal e não repara argumentos nem modifica mensagens ou configuração.
