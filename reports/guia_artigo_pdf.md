# Guia: como montar o artigo em PDF + figuras para entrega

Objetivo: entregar **1 PDF do artigo** e **1 pasta de figuras/fotos**, de modo que quem for entregar (submeter, enviar ao orientador, à banca ou ao periódico) não precise decidir nada. Tudo abaixo usa só dados que já estão no repositório.

> Pressuposto: o artigo descreve o MIRA-RAUL (agentes médicos simulados em 10 casos públicos, pipeline adaptado de Zhang et al., DOI 10.1038/s41591-026-04609-x). Se o formato exigido tiver regras próprias (periódico, congresso, TCC), as regras deles vencem este guia.

---

## 1. O que entregar (pacote final)

```
entrega_mira_raul/
├── artigo.pdf                  # texto + figuras embutidas, fontes embutidas, < 10 MB
├── figuras/
│   ├── fig1_fluxo.png          # 300 dpi, largura 1800–2400 px
│   ├── fig2_acuracia_modelos.png
│   ├── fig3_custo_por_resolvido.png
│   ├── fig4_cascata_v3.png
│   └── fig5_painel_artifact.png  # captura de tela do painel (opcional)
├── tabelas/                    # CSVs usados nas tabelas e gráficos
│   ├── all_runs.csv
│   └── v3_*.csv
├── LEIAME.txt                  # 5 linhas: título, autores, versão, data, contato
└── (opcional) suplemento.pdf   # relatórios longos: reports/v3_flow.md, v3_cascade_v32.md
```

Regras do pacote:
- Nomes de arquivo sem acento nem espaço (`fig2_acuracia_modelos.png`, não `Figura 2 – Acurácia.png`).
- Cada figura numerada no nome **na mesma ordem em que aparece no texto**.
- Nenhum arquivo com chave, `.secrets/`, `logs/`, `budget.sqlite` ou traces brutos de chamadas (podem conter identificadores de conta).

---

## 2. Estrutura do artigo (modelo)

1. **Título** — direto, com a limitação no próprio título (ex.: "avaliação exploratória em 10 casos publicados").
2. **Resumo** (≤ 250 palavras): objetivo, método, resultado principal com número, limitação principal.
3. **Introdução** — por que simular consulta (anamnese + exames) em vez de pergunta-resposta; lacuna; objetivo.
4. **Métodos**
   - Casos: 10 casos públicos, fatos separados em paciente / investigações / referência (`cases/`, `THIRD_PARTY_NOTICES.md`).
   - Pipeline: médico simulado, paciente simulado, ferramentas de exames, juiz, limite de 10 turnos (`PROTOCOL.md`).
   - Modelos e rotas fixadas sem fallback (`config/run1.json`).
   - Protocolo v3 e cascata: paciente com regras estritas, N trocas antes de exames, GLM-5 propõe → JEF verifica → Sonnet revisa às cegas → adjudicação (`reports/v3_flow.md`, `v3_design.md`).
   - Juiz: Gemini 3.1 (LLM); override do caso 009 declarado.
   - Custos: ledger OpenRouter + custo equivalente de API do braço de assinatura (rotulados à parte).
5. **Resultados**
   - Placar por modelo (3 runs × 10 casos) — `reports/all_runs_summary.md`.
   - Fidelidade do paciente simulado — `reports/fidelity_eval.md`.
   - Evolução v2 → v3.2a/b/c (acerto e custo por caso resolvido) — `reports/v3_cascade_v32.md`.
6. **Discussão** — o que a cascata mostra (decisivo não solicitado → erro; JEF raramente deixa erro passar; Opus raramente decisivo), custo por caso resolvido.
7. **Limitações (obrigatória, não esconder)**
   - 10 casos, não independentes; execuções repetidas do mesmo caso não são pacientes independentes (Wilson é descritivo).
   - **Juiz é um LLM; revisão médica cega ainda pendente.** Não afirmar acurácia clínica nem segurança.
   - Ajustes do v3.2 foram feitos olhando os mesmos casos em que se avalia (risco de sobreajuste); corte 0,86 do JEF escolhido nos mesmos dados.
   - Caso 009: critério alterado por decisão do usuário (aceitar obstrução por stent migrado), depende de revisão médica.
   - Braço Claude pela assinatura: ferramentas emuladas em JSON, sem controle de amostragem; não equivalente aos demais.
   - Parâmetros do Qwen3.8 assumidos iguais aos do Qwen3.5.
   - Paciente simulado pode inventar narrativa; fidelidade medida, não garantida.
8. **Conclusão** — 3 frases, sem superioridade clínica.
9. **Disponibilidade de dados e código** — https://github.com/codecapelo/MIRA-raul (casos públicos, scripts, traces resumidos); atribuição ao código upstream (KatherLab, CC BY 4.0, commit `eea2386c…`).
10. **Referências** — Zhang et al. (DOI acima); onprem-medical-agents; fontes dos 10 casos (`THIRD_PARTY_NOTICES.md` e metadados de `cases/`).

Tamanho típico: 6–10 páginas + figuras. Escrever **números só a partir dos CSVs/relatórios**, nunca de memória.

---

## 3. Figuras e "fotos"

### 3.1 Figuras de dados (gerar, não fotografar)
Gerar com matplotlib a partir de `results/all_runs.csv` e `results/v3_*.csv`. Regras: fundo branco, fonte ≥ 9 pt no tamanho final, eixos rotulados com unidade, cores distinguíveis em escala de cinza, intervalo (Wilson ou bootstrap por caso) quando houver.

| Fig. | Conteúdo | Fonte dos dados |
|---|---|---|
| 1 | Fluxo do encontro v3.2 (diagrama em caixas: GLM-5 → JEF → revisor → adjudicador) | `reports/v3_flow.md` |
| 2 | Corretos/julgados por modelo, 3 runs, com IC | `results/all_runs.csv` |
| 3 | Custo por caso resolvido: v2, v3.2a, v3.2b, v3.2c | `reports/v3_cascade_v32.md` |
| 4 | Mapa caso × modelo (Y/N por run) | `reports/all_runs_summary.md` |
| 5 | Fidelidade do paciente por condição | `results/fidelity_patient.csv` |

Esqueleto para salvar em alta resolução:

```python
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(6.5, 3.5), dpi=300)   # ~largura de coluna dupla
# ... plot ...
fig.tight_layout()
fig.savefig("figuras/fig2_acuracia_modelos.png", dpi=300)
fig.savefig("figuras/fig2_acuracia_modelos.pdf")      # versão vetorial, preferível se aceita
```

### 3.2 Fotos / capturas de tela
O painel (artifact) pode virar figura de apoio:
1. Abrir https://claude.ai/artifact/LgzgXCtbcxMJAxmqWFThpQ (privado, só o dono abre).
2. Tela cheia em janela larga (≥ 1400 px), tema claro.
3. Capturar (macOS: `Cmd+Shift+4`, seleção de área; salva PNG). Uma captura por aba: Visão geral, Fluxo v3.2, um encontro com o mapa da consulta.
4. Conferir que a captura **não mostra** chave, e-mail, nome de pasta pessoal, nem dados de conta.
5. Salvar como PNG (nunca JPEG para texto) e legendar no artigo.

Se for incluir foto de pessoa, equipamento ou tela de terceiros: precisa de autorização por escrito; para este trabalho, **evitar** — os casos são publicados e anonimizados, e não há necessidade de foto de paciente real.

### 3.3 Legenda (todas as figuras)
Formato: **Figura N. Título curto.** Uma frase dizendo o que mostra, uma dizendo a fonte (arquivo ou relatório) e a limitação (ex.: "juiz LLM; 10 casos; sem revisão médica").

---

## 4. Como gerar o PDF

Neste computador **não há** pandoc, LaTeX, typst nem wkhtmltopdf instalados. Escolha um caminho:

**A. Mais simples (sem instalar nada):** escrever no Google Docs ou Word, inserir as figuras PNG, *Arquivo → Baixar/Exportar → PDF*.

**B. Markdown → PDF (recomendado para manter tudo versionado):**
```bash
brew install pandoc tectonic
pandoc artigo.md -o artigo.pdf --pdf-engine=tectonic \
  --citeproc --bibliography=refs.bib -V geometry:margin=2.5cm -V fontsize=11pt
```

**C. HTML → PDF pelo navegador:** montar `artigo.html` com as imagens, abrir no Chrome, *Imprimir → Salvar como PDF*, margens padrão, "gráficos de fundo" ligado.

Conferência do PDF antes de entregar:
- [ ] Todas as figuras aparecem, legíveis ao dar zoom de 100%.
- [ ] Numeração de figuras/tabelas bate com o texto ("Figura 3" existe e é a certa).
- [ ] Caracteres acentuados corretos (ç, ã, é) — se aparecer "�", trocar a fonte.
- [ ] Tamanho do arquivo < 10 MB (se maior, reexportar PNG a 200 dpi).
- [ ] Propriedades do PDF (título/autor) preenchidas e sem nome de usuário do computador.
- [ ] Todos os números do texto conferidos contra `reports/all_runs_summary.md` e `reports/v3_cascade_v32.md`.
- [ ] A seção **Limitações** está presente e a frase "revisão médica pendente" aparece no resumo ou na discussão.

---

## 5. Checklist de entrega

- [ ] `artigo.pdf` abre em outro computador/celular sem erro.
- [ ] Pasta `figuras/` com todos os PNG (e PDF vetorial quando houver), nomes sem espaço.
- [ ] Pasta `tabelas/` com os CSVs que sustentam cada tabela/figura.
- [ ] `LEIAME.txt` com título, autores, data, versão do repositório (hash do commit usado: `git rev-parse HEAD`) e contato.
- [ ] Varredura de segredos feita (nenhuma chave OpenRouter/JEF, nenhum `.secrets/`).
- [ ] Declarações obrigatórias presentes: uso de IA/LLMs como objeto de estudo **e** como ferramenta de análise, financiamento (custo próprio, teto de US$ 18 no OpenRouter), conflito de interesse, disponibilidade de dados e código.
- [ ] Compactar: `zip -r entrega_mira_raul.zip entrega_mira_raul/` e enviar o ZIP (ou os arquivos soltos, se o sistema pedir).
- [ ] Guardar uma cópia do ZIP junto com o hash do commit.

---

## 6. O que NÃO dizer no artigo

- Que os agentes têm "acurácia clínica" ou são "seguros" — só que o juiz LLM classificou X de Y encontros como equivalentes à referência.
- Que um modelo é "superior" com base em 1 execução por caso em 10 casos.
- Que o v3.2c (10/10) é resultado confirmado: foi **uma** rodada, depois de ajustes feitos nos mesmos casos.
- Valores de custo sem dizer qual parte é OpenRouter (real) e qual é custo equivalente de API da assinatura (referência).
