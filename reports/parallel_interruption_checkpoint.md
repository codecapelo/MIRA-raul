# Checkpoint após interrupção do pool

36 primeiras requisições sem resposta (35 pending + 1 uncertain) foram conciliadas administrativamente a custo zero. Três snapshots sem cache mantiveram total_usage US$ 0,300752618 e total_credits US$ 20; o uso total coincide exatamente com as 450 chamadas já liquidadas. Nenhum usage.cost de provedor foi criado ou inferido como resposta. A classificação é uma conciliação de cobrança no nível da conta.

As 36 traces originais completas, todas sem response/case_complete, foram preservadas com hash em logs/incomplete/parallel_pool_interruption_v1. Prefixos de chamadas pagas ficaram intactos. Ledger final: 486 settled, zero pending/uncertain; custo conhecido permanece US$ 0,300752618. Backup prévio e detalhes por request_id constam no JSON de conciliação. Nenhum runner foi executado.
