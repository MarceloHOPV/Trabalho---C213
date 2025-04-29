# Sistema de Identificação e Controle

Este projeto implementa um sistema de identificação de modelos e sintonia de controladores PID com uma arquitetura cliente-servidor:

- **Backend**: API em Python usando FastAPI para processamento de dados e algoritmos
- **Frontend**: Interface web em HTML, CSS e JavaScript para interação com o usuário

## Estrutura do Projeto

```
projeto/
├── backend.py            # API FastAPI para processamento de dados
├── datasets/             # Diretório para armazenar arquivos .mat e .csv
├── plots/                # Diretório para armazenar gráficos gerados
├── css/                  # Estilos CSS
│   └── styles.css        # Arquivo de estilos
└── js/                   # Scripts JavaScript
    ├── config.js         # Configuração da API
    └── main.js           # Lógica principal do frontend
```

## Instalação

Para configurar o ambiente virtual e instalar as dependências do projeto, siga os passos abaixo:

```bash
# Crie o ambiente virtual
python -m venv venv

# Ative o ambiente virtual
# No Windows:
venv\Scripts\activate

# No MacOS/Linux:
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
```

## Dependências

Crie um arquivo `requirements.txt` com o seguinte conteúdo:

```
fastapi
uvicorn
python-multipart
pandas
numpy
scipy
matplotlib
control
```

## Funcionalidades

- Upload de arquivos .mat contendo dados de experimentos
- Identificação de modelos usando métodos Smith e Sundaresan
- Suavização de curva com parâmetros ajustáveis
- Análise de diferentes configurações de filtro
- Sintonia de controladores PID usando métodos IMC e ITAE
- Simulação de resposta ao degrau
- Métricas de desempenho para controladores

## Solução para o Problema de Suavização

O problema onde t1 e t2 estavam dando valores iguais foi resolvido através de:

1. **Parâmetros Ajustáveis de Suavização**:
   - Tamanho da janela do filtro Savgol (ajustável via slider)
   - Ordem do polinômio (ajustável via slider)
   - Offset inicial para ignorar ruído (ajustável via slider)

2. **Verificações de Segurança**:
   - Validação explícita se t1 < t2 com mensagens de erro claras
   - Garantia que o tamanho da janela seja sempre ímpar
   - Garantia que a ordem do polinômio seja menor que o tamanho da janela

3. **Ferramenta de Análise de Filtros**:
   - Visualização do efeito de diferentes configurações de filtro
   - Métricas de redução de ruído e preservação de sinal
   - Recomendações para escolha de parâmetros ideais

## Como Usar

### Backend:

```bash
# Ative o ambiente virtual
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Execute o servidor
uvicorn backend:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend:

1. Abra o arquivo `index.html` em um navegador
2. Siga o fluxo de trabalho usando os botões de navegação:
   - Upload → Identificação → Sintonia → Simulação

## Fluxo de Trabalho

1. **Upload de Dados**:
   - Faça upload do arquivo .mat com os dados do experimento
   - Visualize o resumo dos dados e o gráfico inicial

2. **Identificação de Modelo**:
   - Selecione o método (Smith ou Sundaresan)
   - Ajuste os parâmetros de suavização conforme necessário
   - Execute a identificação e visualize os resultados
   - Use a ferramenta "Analisar Filtros" para encontrar os melhores parâmetros

3. **Sintonia de Controladores**:
   - Ajuste o valor de lambda para o método IMC
   - Execute a sintonia e compare os parâmetros dos controladores

4. **Simulação de Resposta**:
   - Configure o tempo de simulação
   - Execute a simulação e compare as respostas dos controladores IMC e ITAE
   - Analise as métricas de desempenho

## Notas Técnicas

### Suavização de Curva

A suavização é implementada usando o filtro Savitzky-Golay, que ajusta polinômios locais a segmentos dos dados. Os parâmetros principais são:

- **window_length**: Tamanho da janela (deve ser ímpar). Valores maiores resultam em mais suavização.
- **polyorder**: Ordem do polinômio. Valores maiores preservam mais características do sinal original.
- **offset_percent**: Percentual inicial dos dados a ignorar, útil para evitar ruído no início da resposta.

### Identificação de Modelo

Os métodos implementados (Smith e Sundaresan) identificam modelos de primeira ordem com tempo morto (FOPDT):

```
G(s) = K * e^(-θs) / (τs + 1)
```

Onde:
- K: Ganho do processo
- τ: Constante de tempo
- θ: Tempo morto

### Sintonia de Controladores

Dois métodos de sintonia são implementados:

1. **IMC (Internal Model Control)**:
   - Permite ajustar o parâmetro lambda para balancear velocidade e robustez
   - Valores menores de lambda resultam em resposta mais rápida

2. **ITAE (Integral of Time-weighted Absolute Error)**:
   - Baseado em fórmulas empíricas otimizadas para minimizar o erro
   - Geralmente resulta em respostas com menor sobressinal
