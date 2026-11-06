# Integração portátil da documentação final

Copiar o gerador para scripts/fill_v4_fast_docs.py e este diretório para scripts/templates_v4_fast_docs. Ou indicar qualquer catálogo por --templates. Nenhum caminho /private/tmp é obrigatório. O gerador lê somente documentos e relatórios agregados; não realiza inferência, consulta de credencial ou modificação de ledger.

Prévia sem alterar o repositório:

```sh
python3 scripts/fill_v4_fast_docs.py --base . --output /caminho/da/previa
```

Aplicação explícita após confirmar os relatórios finais:

```sh
python3 scripts/fill_v4_fast_docs.py --base . --apply
```

--final-date-local aceita a data local escolhida e torna o texto estável nas reexecuções. O gerador exige a condição congelada b3d7d00, vinte terminais, gate público 10/10 e conciliação final exata, sem reservas incertas. Valores ausentes provocam erro antes da escrita.

O aviso inicial obsoleto do README é removido; demais checkpoints permanecem históricos. Os blocos finais têm marcadores para evitar duplicação. CHANGELOG recebe a entrada logo após o título. A contagem financeira separa respostas com usage.cost e metadados de geração da rejeição sem uso retornado, atribuída a zero por evidência de conta. Manifestos integrais e metadados privados permanecem locais; exports públicos usam digests opacos. A auditoria fechada é somente agregada.

Validação clínica anterior: 321 testes; consolidação/artifact: 17 testes offline e Node, total 338, separados da inferência. Sete regressões específicas deste gerador foram executadas em TMP e não foram somadas à contagem do estudo. Confirmar links, artifact e secret/privacy scan antes de publicar. Revisão médica permanece pendente.
