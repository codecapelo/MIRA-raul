# Pré-registro — braço v6 (Gatekeeper v6 + revisores Claude), 14-11-2026

Escrito antes dos encontros do estudo. Condição congelada em `config/frozen/v6.json` (SHA-256 de 42 arquivos; `freeze_condition.py --name v6 --check` sem diferenças; **código ainda não commitado**, o manifesto é o registro). A v5 segue congelada (`--name v5 --check` sem diferenças).

## Pergunta
Trocar (a) a mesa de exames pelo Gatekeeper v6 e (b) os revisores Sol/Astra por Sonnet 5.5 (primeiro) e Fable 5.2 (final) muda o resultado, nos casos em que a proposta do médico veio errada na v5full1? Os dois pacotes entram juntos (decisão do usuário): **a rodada não separa o efeito de cada um.**

## Desenho
- **Casos (7):** 001, 002, 003, 004, 011, 017, 018 (proposta do médico errada na v5full1; em três deles, um público e dois fechados, o juiz final também rejeitou). Conhecidos, usados no desenvolvimento: não é validação.
- **Médicos (3), um encontro por caso e por médico (21 encontros):** Gemini 3.1 Flash-Lite (Google AI Studio), GLM 5.3 Flash (Z.AI, fp8), DeepSeek V4.1 Flash 1017 (DeepInfra, fp8). Rotas fixadas, sem fallback, amostragem padrão do provedor.
- **Gatekeeper v6:** itens que o artigo relata para a apresentação e que a conversão não tinha (citação literal conferida no texto do PDF, só fase de apresentação, sem itens com tempo anterior ao encontro nem nomes genéricos), rotulados `recovered_from_article_unreviewed`; resultado normal sintético sinalizado só se o artigo disser que "os demais exames do grupo" foram normais (classe sangue/urina, nunca exame que define o diagnóstico); caso contrário "não realizado". Nos 7 casos não há licença desse tipo: o caminho sintético fica inativo. Casos de origem em `cases/` intocados; cópias em `runs/v5/v6/cases_v6` (Git-ignorado); impressão digital agregada dos 7: `af2e8769491f479477012954a2dfe5be54552b67bd9a40fb5ee9a4e81b1c3c01`.
- **Custo em CPT:** tabela Medicare RVU26D (PFS, nacional, instalação não hospitalar); exames laboratoriais ficam sem preço sem a CLFS; registro por pedido (`v6_cpt_cost`).
- **Revisores:** Sonnet 5.5 high no lugar do Sol e Fable 5.2 high no lugar do Astra, pela assinatura Claude, mesma cascata, prompts e validadores da v5 (os rótulos de etapa `sol` e `astra` indicam as vagas). CLI do Claude atualizado de 2.1.284 para 2.1.325 (o Fable exige ≥ 2.1.290); versão registrada pelo cliente.
- **Inalterado:** paciente Sonnet 5.5 (assinatura), associador, associador estrito, juiz Gemini 3.1 Pro, protocolo e prompts da v5.
- **Ensaio de encanamento** (`gemini_v6plumb`, case_005, fora do estudo e dos denominadores): terminal, juiz aceitou, usou Sonnet e Fable, eventos de CPT presentes, US$ 0,025.

## Medidas (decididas antes)
Juiz binário da pipeline e, depois, juiz de 1 a 5 com justificativa (Gemini 3.1 Pro + segundo juiz de outra família); acerto da proposta do médico; custo OpenRouter por encontro; custo CPT por encontro (preço onde existir); cobertura de observações, itens "não consta", itens recuperados entregues; trocas com o paciente. Comparação com a v5full1 (mesmos 7 casos, um encontro cada, Gemini): contagens e leitura caso a caso; **sem teste de significância** (n = 7, uma execução).

## Orçamento
Ledger do teste dos médicos, teto US$ 2,00, compartilhado com o teste anterior (US$ 0,144 e o ensaio). Estimativa para os 21 encontros: US$ 0,5 a 0,6. Sem retentativa automática de terminal; falha operacional para a execução e é reconciliada, não repetida às cegas.

## Limites
Casos conhecidos; juiz LLM; sem revisão médica (itens recuperados não revisados); dois pacotes de mudança juntos; um encontro por caso; o juiz de 1 a 5 é rascunho sem validação médica; modelos revisores e escritores da mesma família Claude no braço novo (por isso o segundo juiz é de outra família).
