# HACKATOHM — MVP de monitoramento térmico de escovas

## Situação do projeto

**Prova de conceito funcional de software para demonstração local. Não é um produto industrial.** O sistema simula quatro pontos de medição, recebe medições reais via HTTP, registra dados em SQLite, apresenta gráficos, sinaliza estados de atenção/crítico e exporta CSV.

## Rodar agora (somente Python 3.10 ou superior)

```bash
python server.py
```

Abra **http://127.0.0.1:8000** no navegador. O banco de dados é criado automaticamente com amostras identificadas como `simulado`. Use **Simular superaquecimento**, **Restaurar simulação** e **Exportar CSV**.

Não há dependências Python externas para o servidor.

## Enviar uma leitura por HTTP (bancada)

Em outro terminal:

```bash
curl -X POST http://127.0.0.1:8000/api/reading \
  -H "Content-Type: application/json" \
  -d '{"escova":"E01","temperatura_c":48.5,"ambiente_c":29.0}'
```

Exemplo de JSON de entrada:

```json
{"escova":"E01","temperatura_c":48.5,"ambiente_c":29.0}
```

Consultar todas as escovas: `GET /api/overview`. Exportar dados: `GET /api/export.csv`.

## Hardware de bancada — ESP32 + MLX90614

Arquivo: `firmware/esp32_mlx90614.ino`. No Arduino IDE, instale a placa ESP32 e as bibliotecas Adafruit MLX90614 e Adafruit BusIO. Configure SSID, senha, IP do servidor e ID da escova. Para que outro dispositivo na rede veja o servidor, inicie **somente em uma rede de teste confiável**:

```bash
HACKATOHM_HOST=0.0.0.0 HACKATOHM_API_KEY=troque-por-uma-chave python server.py
```

No **Windows (PowerShell)**, o equivalente é:

```powershell
$env:HACKATOHM_HOST="0.0.0.0"
$env:HACKATOHM_API_KEY="troque-por-uma-chave"
python server.py
```

Preencha a mesma chave em `CHAVE_API` no firmware. As ações de gerar/reiniciar a simulação são permitidas somente para navegadores abertos no próprio computador servidor; a coleta real requer a chave definida. **HTTP transmite dados sem criptografia e a chave também fica exposta na rede**: esta integração é exclusivamente didática. Em ambiente industrial, usar segmentação, TLS, gestão de credenciais e protocolos aprovados pela área responsável.

O MLX90614 mede a radiação térmica da superfície dentro do seu campo de visão. Essa leitura **não equivale** automaticamente à temperatura no ponto de contato com o anel. A temperatura ambiente indicada pelo dispositivo é a do próprio sensor; não é necessariamente a temperatura real do compartimento em todas as condições.

## Limiares de demonstração

`server.py` define 70 °C para atenção e 85 °C para crítico **APENAS PARA ILUSTRAR A INTERFACE**. Essas temperaturas NÃO são limiares recomendados, validados ou seguros para motores/geradores. **Nunca conecte um alarme demonstrativo a parada, proteção ou controle de máquinas.** Em campo, limites dependem de fabricante, material da escova, máquina, região medida e projeto de instrumentação.

## Matriz resumida de validação

| Critério | Teste de bancada | Critério inicial sugerido (a validar) |
|---|---|---|
| Visada | Variação de distância/ângulo | Alvo ocupa campo de medição adequado |
| Repetibilidade | 30 leituras em alvo estável | Desvio-padrão documentado |
| Comparação | Instrumento de referência | Erro máximo definido pelo projeto |
| Latência | Aquecimento controlado | Tempo de resposta e alarmes registrados |
| Ruído | Simular flutuação de temperatura | Nenhum falso alarme persistente |
| Falha de comunicação | Desligar Wi-Fi | Exibir estado de dado indisponível (A IMPLEMENTAR) |
| Robustez | Ensaios aprovados por especialistas | Vibração/poeira/temperatura especificadas (A IMPLEMENTAR) |

## O que falta para transformar em sistema industrial

1. Caracterização da máquina, modelos e dimensões de escovas, distâncias elétricas e níveis de tensão.
2. Aprovação da área de segurança e responsável por máquinas antes de qualquer montagem em equipamento real.
3. Seleção óptica a partir do menor alvo, da distância e da emissividade; referência termográfica calibrada.
4. Suportes e invólucros adequados; ensaios de vibração, poeira e calor.
5. Protocolos industriais, credenciais, retenção, redundância, relógio, alarmes de falha de sensor e auditoria.
6. Calibração e validação com testes repetidos em operação representativa.

## Dados e autoria

Este MVP é um código inicial demonstrativo preparado a partir do desafio da DATA e de referências públicas Carbex, Optris e Melexis. Não copia o conteúdo confidencial da apresentação da DATA. Evite publicar os arquivos originais da empresa sem autorização.
