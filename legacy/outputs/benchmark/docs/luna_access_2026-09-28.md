# GPT-6 Luna high — acesso e transporte

Em 28-09-2026, `gpt-6-luna` com esforço `high` passou autenticação e inferência sintética `ping({})` pelo Codex CLI usando a conta ChatGPT. Nenhuma chave de API foi utilizada. O cache local de catálogo também inclui esse ID e suporta `high`. A CLI registra o modelo solicitado e aceita a inferência, mas não devolve um slug de modelo observado no envelope: não tratamos `model_requested` como prova independente de snapshot servido.

CLI observada: `codex-cli 0.158.0-alpha.2.1`, executável `/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex`. No painel anterior Sol, a versão era `0.155.0-alpha.16.4` e o executável estava em outro caminho. As flags e o prompt do adapter são os mesmos do Sol; a mudança de versão do transporte e a execução em outra data são limites da comparação.

Adapter novo: `providers/openai_luna.py`, cópia do adapter Sol congelado com somente ID/nome e caminho atual do executável alterados. Preserva ação JSON emulada, uma ação EHR por invocação, `high`, `read-only`, sessão efêmera, configuração/regras do usuário ignoradas e schema de saída. Como no Sol v5, ferramentas internas não são auditadas no trace: instrução de não usar shell/arquivos/web não comprova isolamento estrito. O protocolo não será descrito como uma avaliação clínica sem risco de vazamento demonstrado.

Preflight não clínico, fora do painel: `input_tokens=14012`, `cached_input_tokens=0`, `cache_write_input_tokens=0`, `output_tokens=49`, `reasoning_output_tokens=20`, `cli_error_events=0`; ação `ping` correta. `high` foi aceito. Temperatura e seed não foram controladas pela CLI.

Segundo a [página oficial GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna), consultada em 28-09-2026, as tarifas API textuais por milhão de tokens são US$ 0,10 de entrada, US$ 0,01 de entrada lida do cache, US$ 0,125 de gravação de cache e US$ 0,50 de saída. `high` é suportado. As tarifas servirão apenas como proxy hipotético sobre os tokens da CLI; assinatura não é faturação API e sua cobrança real por run não é informada. Raciocínio já integra os tokens de saída, cache lido já integra os tokens totais de entrada.

Os novos runs ficam em `results/extension_2026-09-28/`, com os mesmos dez casos, três repetições, prompt/EHR/schemas/stopping v5 e manifest separado. Os 150 traces anteriores permanecem intactos. O crédito gratuito de reset será preservado.
