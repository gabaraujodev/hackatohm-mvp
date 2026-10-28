# Estrutura de desenvolvimento proposta

## Problema
Inspeções térmicas periódicas não revelam necessariamente a evolução da temperatura entre visitas técnicas. A proposta é monitorar a superfície visível de uma ou mais escovas sem contato físico do sensor com a escova, armazenando histórico e informando desvios.

## Diagrama
```
Escova (superfície visível) --> sensor IR --> ESP32 --> Wi-Fi de bancada --> API local
                                                     --> SQLite --> painel web + CSV
```

## Dados a registrar
- ID da máquina, do anel, da escova e da posição física
- Data/hora UTC e origem da medição (real/simulada)
- Temperatura de superfície estimada, °C
- Temperatura ambiente do compartimento (sensor adicional recomendado)
- Qualidade/confiança da medição (visada, distância, emissividade e validade)
- Estado do instrumento, data da calibração, falha de comunicação
- Carga e corrente da máquina quando disponível (futuro)

## Plano de apresentação
- Dor: anomalias podem surgir entre inspeções termográficas.
- Solução: sensor sem contato + aquisição contínua + alarmes e tendências.
- Demo: gráfico normal e aquecimento simulado na escova E03.
- Robustez: discutir os pontos ainda abertos (proteção óptica, isolamento e vibração).
- Próximos passos: validação termográfica, configuração por máquina e piloto autorizado.

## Incertezas que devem ser resolvidas com o time da DATA
- Medir temperatura da escova ou do contato escova–anel? Há linha de visada?
- Distância e geometria disponíveis, modelo do porta-escovas, quantas escovas e anéis?
- Qual é o ambiente operacional real? Até que temperatura? Qual a vibração e poeira?
- O que exatamente significa 'não invasivo' para a DATA? Suporte fixo na carcaça é permitido?
- Valores atuais de medição, frequência desejada e tolerância de erro?
- Existe infraestrutura para rede, PoE, PLC ou SCADA?
- A temperatura medida será usada só para manutenção ou para alarmes operacionais?
