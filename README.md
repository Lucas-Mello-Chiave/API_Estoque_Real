
# 📊 Sistema de Coleta, Limpeza e Consolidação de Vendas & Estoque

Este projeto implementa um **pipeline de ETL (Extract, Transform, Load)** para integrar dados de vendas e estoque de um ERP/Shop9, consolidando-os em relatórios prontos para análise em Excel/Power BI.

---

## 🚀 Visão Geral

O sistema realiza as seguintes etapas:

1. **Autenticação (`auth.py`)**  
   - Gera tokens e assinaturas HMAC-SHA256 para acessar os endpoints da API.
   - Controla `BASE_URL`, `FILIAL`, `SERIE` e `SENHA`.

2. **Coleta de Dados de Vendas (`sales_fetcher.py`)**  
   - Baixa as **saídas (VND)** dos últimos 366 dias, em formato paginado.
   - Mescla registros novos com históricos, evitando duplicatas.
   - Salva dados brutos em `data/raw/saidas_ultimos_366_dias.json`.

3. **Limpeza de Vendas (`data_cleaner.py`)**  
   - Filtra apenas operações `VND`.  
   - Reduz campos para `data`, `codigo`, `quantidade`.  
   - Salva em `data/limpa/vendas.json`.

4. **Coleta de Estoque (`stock_fetcher.py`)**  
   - Consulta o endpoint `/v2/estoque`.  
   - Usa `last_sync_estoque.txt` para buscar somente incrementos.  
   - Consolida os dados novos com o histórico (`dados_de_estoque_compilado.json`).

5. **Geração de Relatório (`report_generator.py`)**  
   - Lê os arquivos de IDs (`data/id.csv`), vendas e estoque.  
   - Calcula:
     - 📈 Média de vendas dos últimos 6 meses.
     - 📅 Vendas no ano atual (2025).
     - 📦 Estoque atual consolidado por filial.
   - Exporta `data/resultados/resultado.csv`.

6. **Atualização de Excel (`excel_updater.py`)**  
   - Importa `resultado.csv` para a aba `info_tempo_real` do Excel `ESTOQUE PRODUTOS REVISTAS.xlsx`.  
   - Adiciona a data de execução na célula `E1`.  
   - Faz merge opcional com `unidade.csv` para incluir coluna **Unidade**.

---

## 📂 Estrutura de Pastas

```

src/modules/
├── auth.py              # Autenticação e assinatura
├── data\_cleaner.py      # Limpeza de vendas
├── excel\_updater.py     # Atualiza planilha Excel
├── report\_generator.py  # Geração de relatório consolidado
├── sales\_fetcher.py     # Coleta de vendas (saídas)
└── stock\_fetcher.py     # Coleta e consolidação de estoque

data/
├── raw/                 # Dados brutos (API)
│   ├── saidas\_ultimos\_366\_dias.json
│   └── dados\_de\_estoque\_compilado.json
├── limpa/               # Dados limpos
│   └── vendas.json
├── resultados/          # Relatórios
│   ├── resultado.csv
│   └── ESTOQUE PRODUTOS REVISTAS.xlsx
├── unidade.csv          # (opcional) arquivo de unidades
├── id.csv               # IDs de produtos a monitorar
└── last\_sync\_estoque.txt # Controle de sincronização de estoque

````

---

## ⚙️ Dependências

- Python **3.11+**
- Bibliotecas:
  ```bash
  pip install requests pandas openpyxl


---

## 🔄 Fluxo de Execução

1. **Buscar dados de vendas:**

   ```bash
   python -m src.modules.sales_fetcher
   ```

2. **Limpar dados de vendas:**

   ```bash
   python -m src.modules.data_cleaner
   ```

3. **Buscar dados de estoque:**

   ```bash
   python -m src.modules.stock_fetcher
   ```

4. **Gerar relatório consolidado:**

   ```bash
   python -m src.modules.report_generator
   ```

5. **Atualizar Excel:**

   ```bash
   python -m src.modules.excel_updater
   ```

---

## 📊 Exemplo de Saída (`resultado.csv`)

```csv
id;media;vendas_2025;estoque
8161;23.5;120;340
8206;10.2;50;200
8479;5.8;30;80
```

---

## 🛡️ Observações Importantes

* **Token de autenticação** é obtido automaticamente pelo `auth.py`.
* **Mesclagem de dados** garante que nenhum histórico será perdido (tanto em vendas quanto em estoque).
* **Datas** seguem o formato `YYYY-MM-DD`.
* Caso algum campo venha inconsistente da API, mensagens de debug são exibidas.

---

## 👨‍💻 Autor

Desenvolvido por **Lucas Mello**
Backend Developer & Data Scientist
📍 Florianópolis - SC
CHIAVE

---

