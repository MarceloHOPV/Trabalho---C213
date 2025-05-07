import os
import sys
import logging
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
from io import StringIO
from scipy.io import loadmat
from control import tf, pade, feedback, series, step_response
import matplotlib.pyplot as plt
import uuid
from scipy.signal import savgol_filter
import json
from fastapi.staticfiles import StaticFiles


# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criar a aplicação FastAPI
app = FastAPI(title="API de Identificação de Sistemas e Sintonia PID")

# Configurar CORS para permitir requisições do frontend hospedado no GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir a pasta plots como arquivos estáticos
app.mount("/plots", StaticFiles(directory="plots"), name="plots")


# Diretórios para armazenamento
DATASETS_DIR = "datasets"
PLOTS_DIR = "plots"
os.makedirs(DATASETS_DIR, exist_ok=True)
os.makedirs(PLOTS_DIR, exist_ok=True)

@app.get("/")
def read_root():
    return {"message": "API de Identificação de Sistemas e Sintonia PID"}

@app.post("/upload/")
async def upload_mat(file: UploadFile = File(...)):
    """
    Recebe um arquivo .mat contendo dados de experimento.
    """
    # Verificar extensão do arquivo
    if not file.filename.endswith('.mat'):
        raise HTTPException(status_code=400, detail="Apenas arquivos .mat são aceitos")
    
    # Gerar ID único para o arquivo
    file_id = str(uuid.uuid4())
    path = f"{DATASETS_DIR}/{file_id}.mat"
    
    try:
        # Salvar .mat no disco
        logger.info(f"Salvando arquivo {file.filename} como {path}")
        with open(path, "wb") as f:
            f.write(await file.read())
        
        # Carregar dados do arquivo .mat
        logger.info(f"Carregando dados do arquivo {path}")
        try:
            mat_data = loadmat(path)
            logger.info(f"Chaves disponíveis no arquivo .mat: {mat_data.keys()}")
            
            # Verificar se a estrutura esperada existe
            if 'reactionExperiment' not in mat_data:
                # Tentar encontrar outras estruturas de dados
                data_keys = [k for k in mat_data.keys() if not k.startswith('__')]
                logger.info(f"Estrutura 'reactionExperiment' não encontrada. Chaves disponíveis: {data_keys}")
                
                if len(data_keys) > 0:
                    # Usar a primeira estrutura de dados disponível
                    key = data_keys[0]
                    logger.info(f"Usando a estrutura '{key}' como fonte de dados")
                    
                    # Tentar extrair dados dessa estrutura
                    try:
                        dados = mat_data[key]
                        # Verificar se é uma matriz ou estrutura
                        if isinstance(dados, np.ndarray):
                            if dados.ndim == 2:
                                # Assumir que as colunas são tempo, saída, entrada
                                if dados.shape[1] >= 3:
                                    tempo = dados[:, 0]
                                    saida = dados[:, 1]
                                    entrada = dados[:, 2]
                                else:
                                    raise ValueError(f"A matriz '{key}' não tem colunas suficientes (precisa de pelo menos 3)")
                            else:
                                raise ValueError(f"A estrutura '{key}' não é uma matriz 2D")
                        else:
                            raise ValueError(f"A estrutura '{key}' não é uma matriz numpy")
                    except Exception as e:
                        logger.error(f"Erro ao extrair dados da estrutura '{key}': {str(e)}")
                        raise HTTPException(
                            status_code=400, 
                            detail=f"Não foi possível extrair dados da estrutura '{key}': {str(e)}"
                        )
                else:
                    raise HTTPException(
                        status_code=400, 
                        detail="Estrutura de dados não reconhecida no arquivo .mat"
                    )
            else:
                # Extrair dados da estrutura reactionExperiment
                try:
                    dados = mat_data["reactionExperiment"][0, 0]
                    tempo = dados[0].ravel()
                    saida = dados[1].ravel()
                    entrada = dados[2].ravel()
                except Exception as e:
                    logger.error(f"Erro ao extrair dados da estrutura 'reactionExperiment': {str(e)}")
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Erro ao extrair dados da estrutura 'reactionExperiment': {str(e)}"
                    )
        except Exception as e:
            logger.error(f"Erro ao carregar arquivo .mat: {str(e)}")
            raise HTTPException(
                status_code=400, 
                detail=f"Erro ao carregar arquivo .mat: {str(e)}"
            )
        
        # Criar DataFrame e salvar como CSV
        df = pd.DataFrame({
            "tempo": tempo,
            "saida": saida,
            "entrada": entrada
        })
        
        csv_path = f"{DATASETS_DIR}/{file_id}.csv"
        df.to_csv(csv_path, index=False)
        
        # Gerar visualização inicial dos dados
        plt.figure(figsize=(10, 6))
        plt.subplot(2, 1, 1)
        plt.plot(tempo, saida, 'b-', label='Saída')
        plt.grid(True)
        plt.legend()
        plt.title('Dados do Experimento')
        
        plt.subplot(2, 1, 2)
        plt.plot(tempo, entrada, 'r-', label='Entrada')
        plt.grid(True)
        plt.legend()
        plt.xlabel('Tempo')
        
        # Salvar gráfico
        plot_path = f"{PLOTS_DIR}/{file_id}_raw.png"
        plt.savefig(plot_path)
        plt.close()
        
        logger.info(f"Arquivo processado com sucesso: {file_id}")
        return {
            "file_id": file_id,
            "message": "Arquivo .mat processado com sucesso",
            "plot_path": plot_path,
            "data_summary": {
                "samples": len(tempo),
                "time_range": [float(tempo.min()), float(tempo.max())],
                "output_range": [float(saida.min()), float(saida.max())],
                "input_range": [float(entrada.min()), float(entrada.max())]
            }
        }
    
    except Exception as e:
        # Remover arquivo em caso de erro
        if os.path.exists(path):
            os.remove(path)
        logger.error(f"Erro ao processar arquivo .mat: {str(e)}")
        return JSONResponse(
            status_code=500, 
            content={"erro": f"Erro ao processar arquivo .mat: {str(e)}"}
        )

@app.post("/identify/")
async def identificar_modelo(
    file_id: str = Form(...),
    metodo: str = Form("smith"),  # smith ou sundaresan
    window_length: int = Form(11),  # Parâmetro ajustável para o filtro Savgol
    polyorder: int = Form(3),  # Ordem do polinômio para o filtro Savgol
    offset_percent: float = Form(15.0)  # Percentual inicial a ignorar (para evitar ruído inicial)
):
    """
    Identifica os parâmetros do modelo a partir dos dados.
    Permite ajustar os parâmetros de suavização para melhorar a identificação.
    """
    try:
        # Verificar se o arquivo existe
        csv_path = f"{DATASETS_DIR}/{file_id}.csv"
        if not os.path.exists(csv_path):
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")
        
        # Verificar método
        if metodo not in ["smith", "sundaresan"]:
            raise HTTPException(status_code=400, detail="Método inválido. Use 'smith' ou 'sundaresan'")
        
        # Verificar parâmetros do filtro
        if window_length % 2 == 0:
            window_length += 1  # Garantir que window_length seja ímpar
        
        if window_length < 3:
            window_length = 3
        
        if polyorder >= window_length:
            polyorder = window_length - 1
        
        # Carregar dados
        df = pd.read_csv(csv_path)
        t = df.iloc[:, 0].values
        y_original = df.iloc[:, 1].values
        entrada = df.iloc[:, 2].values
        
        # Aplicar filtro Savgol para suavização
        y = savgol_filter(y_original, window_length=window_length, polyorder=polyorder)
        
        # Valores iniciais e finais
        y_inicial = y[0]
        y_final = y[-1]
        dy = y_final - y_inicial
        
        # Calcular pontos de interesse baseado no método escolhido
        if metodo == "smith":
            y1 = y_inicial + 0.283 * dy
            y2 = y_inicial + 0.632 * dy
        else:  # sundaresan
            y1 = y_inicial + 0.353 * dy
            y2 = y_inicial + 0.853 * dy
        
        # Calcular offset baseado em percentual
        offset = int(len(t) * offset_percent / 100)
        if offset < 1:
            offset = 1
        
        # Encontrar índices onde a resposta atinge y1 e y2
        idx1 = np.where(y[offset:] >= y1)[0]
        idx2 = np.where(y[offset:] >= y2)[0]
        
        if len(idx1) == 0 or len(idx2) == 0:
            raise HTTPException(
                status_code=400, 
                detail="A resposta não atingiu os níveis necessários para identificação. Tente ajustar os parâmetros."
            )
        
        # Corrigir índices para compensar o offset
        t1 = t[offset + idx1[0]]
        t2 = t[offset + idx2[0]]
        
        if t1 >= t2:
            raise HTTPException(
                status_code=400, 
                detail=f"t1 ({t1}) não é menor que t2 ({t2}). Tente ajustar os parâmetros de suavização."
            )
        
        # Cálculo dos parâmetros do modelo
        if metodo == "smith":
            tau = 1.5 * (t2 - t1)
            theta = t2 - tau
        else:  # sundaresan
            tau = 2/3 * (t2 - t1)
            theta = 1.3 * t1 - 0.29 * t2
        
        # Cálculo do ganho
        k = dy / (entrada.max() - entrada.min())
        
        # Gerar gráfico com visualização da suavização e pontos identificados
        plt.figure(figsize=(12, 8))
        
        # Plot dos dados originais e suavizados
        plt.subplot(2, 1, 1)
        plt.plot(t, y_original, 'b-', alpha=0.5, label='Dados Originais')
        plt.plot(t, y, 'r-', label='Dados Suavizados')
        plt.axhline(y1, color='g', linestyle='--', label=f'y1 ({y1:.2f})')
        plt.axhline(y2, color='m', linestyle='--', label=f'y2 ({y2:.2f})')
        plt.axvline(t1, color='g', linestyle='-.')
        plt.axvline(t2, color='m', linestyle='-.')
        plt.grid(True)
        plt.legend()
        plt.title(f'Identificação de Modelo - Método {metodo.capitalize()}')
        
        # Plot da entrada
        plt.subplot(2, 1, 2)
        plt.plot(t, entrada, 'k-', label='Entrada')
        plt.grid(True)
        plt.legend()
        plt.xlabel('Tempo')
        
        # Salvar gráfico
        plot_path = f"{PLOTS_DIR}/{file_id}_identify_{metodo}.png"
        plt.savefig(plot_path)
        plt.close()
        
        # Retornar resultados
        return {
            "k": float(k),
            "tau": float(tau),
            "theta": float(theta),
            "t1": float(t1),
            "t2": float(t2),
            "y1": float(y1),
            "y2": float(y2),
            "plot_path": plot_path,
            "filter_params": {
                "window_length": window_length,
                "polyorder": polyorder,
                "offset_percent": offset_percent
            }
        }
    
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Erro ao identificar modelo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao identificar modelo: {str(e)}")

@app.post("/tune/")
async def sintonizar_pid(
    k: float = Form(...),
    tau: float = Form(...),
    theta: float = Form(...),
    lam: float = Form(1.0)  # Lambda ajustável para IMC
):
    """
    Sintoniza controladores PID usando métodos IMC e ITAE.
    """
    try:
        # Verificar parâmetros
        if k <= 0 or tau <= 0 or theta < 0:
            raise HTTPException(
                status_code=400, 
                detail="Parâmetros inválidos. k e tau devem ser positivos, theta deve ser não-negativo."
            )
        
        # IMC (lambda ajustável)
        kp_imc = (2*tau + theta) / (k * (2*lam + theta))
        ti_imc = tau + theta/2
        td_imc = (tau * theta) / (2*tau + theta)
        
        # ITAE (constantes da tabela)
        A, B, C, D, E, F = 0.965, -0.85, 0.796, -0.147, 0.308, 0.929
        theta_tau = theta / tau
        kp_itae = (A / k) * (theta_tau ** B)
        ti_itae = tau * (C + D * theta_tau)
        td_itae = tau * E * (theta_tau ** F)
        
        # Retornar resultados
        return {
            "IMC": {
                "Kp": float(kp_imc),
                "Ti": float(ti_imc),
                "Td": float(td_imc),
                "lambda": float(lam)
            },
            "ITAE": {
                "Kp": float(kp_itae),
                "Ti": float(ti_itae),
                "Td": float(td_itae)
            }
        }
    
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Erro ao sintonizar PID: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao sintonizar PID: {str(e)}")

@app.post("/plot/")
async def plotar_resposta(
    k: float = Form(...),
    tau: float = Form(...),
    theta: float = Form(...),
    lam: float = Form(1.0),  # Lambda ajustável para IMC
    simulation_time: float = Form(50.0),  # Tempo de simulação
    num_points: int = Form(1000)  # Número de pontos na simulação
):
    """
    Gera gráficos de resposta ao degrau para os controladores sintonizados.
    """
    try:
        # Verificar parâmetros
        if k <= 0 or tau <= 0 or theta < 0:
            raise HTTPException(
                status_code=400, 
                detail="Parâmetros inválidos. k e tau devem ser positivos, theta deve ser não-negativo."
            )
        
        # Parâmetros IMC
        kp_imc = (2*tau + theta) / (k * (2*lam + theta))
        ti_imc = tau + theta/2
        td_imc = (tau * theta) / (2*tau + theta)
        
        # Parâmetros ITAE
        A, B, C, D, E, F = 0.965, -0.85, 0.796, -0.147, 0.308, 0.929
        theta_tau = theta / tau
        kp_itae = (A / k) * (theta_tau ** B)
        ti_itae = tau * (C + D * theta_tau)
        td_itae = tau * E * (theta_tau ** F)
        
        # Sistema planta com atraso (aproximação de Padé)
        num_pade, den_pade = pade(theta, 20)
        planta = series(tf(k, [tau, 1]), tf(num_pade, den_pade))
        
        # PID - IMC
        pid_imc = tf([kp_imc * td_imc, kp_imc, kp_imc / ti_imc], [1, 0])
        malha_fechada_imc = feedback(series(pid_imc, planta), 1)
        
        # PID - ITAE
        pid_itae = tf([kp_itae * td_itae, kp_itae, kp_itae / ti_itae], [1, 0])
        malha_fechada_itae = feedback(series(pid_itae, planta), 1)
        
        # Resposta ao degrau
        t = np.linspace(0, simulation_time, num_points)
        t1, y1 = step_response(malha_fechada_imc, t)
        t2, y2 = step_response(malha_fechada_itae, t)
        
        # Calcular métricas de desempenho
        # Tempo de subida (10% a 90%)
        def calc_rise_time(t, y):
            y_norm = (y - y[0]) / (y[-1] - y[0]) if y[-1] != y[0] else np.ones_like(y)
            t_10 = t[np.where(y_norm >= 0.1)[0][0]]
            t_90 = t[np.where(y_norm >= 0.9)[0][0]]
            return t_90 - t_10
        
        # Sobressinal
        def calc_overshoot(y):
            if y[-1] <= 0:
                return 0
            return max(0, (np.max(y) / y[-1] - 1) * 100)
        
        # Tempo de acomodação (5%)
        def calc_settling_time(t, y):
            y_norm = (y - y[0]) / (y[-1] - y[0]) if y[-1] != y[0] else np.ones_like(y)
            settled = np.where(np.abs(y_norm - 1) <= 0.05)[0]
            if len(settled) > 0:
                idx = settled[0]
                # Verificar se permanece dentro da faixa
                for i in range(idx, len(y_norm)):
                    if np.abs(y_norm[i] - 1) > 0.05:
                        return calc_settling_time(t[i:], y[i:])
                return t[idx]
            return t[-1]
        
        # Calcular métricas
        metrics_imc = {
            "rise_time": float(calc_rise_time(t1, y1)),
            "overshoot": float(calc_overshoot(y1)),
            "settling_time": float(calc_settling_time(t1, y1))
        }
        
        metrics_itae = {
            "rise_time": float(calc_rise_time(t2, y2)),
            "overshoot": float(calc_overshoot(y2)),
            "settling_time": float(calc_settling_time(t2, y2))
        }
        
        # Plot
        plt.figure(figsize=(12, 8))
        
        # Resposta ao degrau
        plt.subplot(2, 1, 1)
        plt.plot(t1, y1, 'b-', linewidth=2, label="IMC")
        plt.plot(t2, y2, 'r-', linewidth=2, label="ITAE")
        plt.axhline(1, color='gray', linestyle='--')
        plt.grid(True)
        plt.legend()
        plt.title("Comparação de Respostas - IMC vs ITAE")
        plt.ylabel("Saída")
        
        # Erro
        plt.subplot(2, 1, 2)
        plt.plot(t1, 1 - y1, 'b-', linewidth=2, label="Erro IMC")
        plt.plot(t2, 1 - y2, 'r-', linewidth=2, label="Erro ITAE")
        plt.axhline(0, color='gray', linestyle='--')
        plt.grid(True)
        plt.legend()
        plt.xlabel("Tempo (s)")
        plt.ylabel("Erro")
        
        # Salvar gráfico
        plot_id = str(uuid.uuid4())
        plot_path = f"{PLOTS_DIR}/response_{plot_id}.png"
        plt.savefig(plot_path)
        plt.close()
        
        # Retornar resultados
        return {
            "plot_path": plot_path,
            "metrics": {
                "IMC": metrics_imc,
                "ITAE": metrics_itae
            },
            "controllers": {
                "IMC": {
                    "Kp": float(kp_imc),
                    "Ti": float(ti_imc),
                    "Td": float(td_imc)
                },
                "ITAE": {
                    "Kp": float(kp_itae),
                    "Ti": float(ti_itae),
                    "Td": float(td_itae)
                }
            }
        }
    
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Erro ao gerar gráfico: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao gerar gráfico: {str(e)}")

@app.post("/analyze-filter/")
async def analisar_filtro(
    file_id: str = Form(...),
    window_lengths: str = Form("[11, 21, 31, 51]"),  # Lista de tamanhos de janela para testar
    polyorder: int = Form(2)  # Ordem do polinômio
):
    """
    Analisa o efeito de diferentes parâmetros de filtro nos dados.
    """
    try:
        # Verificar se o arquivo existe
        csv_path = f"{DATASETS_DIR}/{file_id}.csv"
        if not os.path.exists(csv_path):
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")
        
        # Converter string para lista
        try:
            window_lengths = json.loads(window_lengths)
            if not isinstance(window_lengths, list):
                window_lengths = [11, 21, 31, 51]
        except:
            window_lengths = [11, 21, 31, 51]
        
        # Garantir que todos os tamanhos de janela sejam ímpares
        window_lengths = [w if w % 2 == 1 else w + 1 for w in window_lengths]
        
        # Carregar dados
        df = pd.read_csv(csv_path)
        t = df.iloc[:, 0].values
        y_original = df.iloc[:, 1].values
        
        # Aplicar diferentes filtros
        plt.figure(figsize=(12, 8))
        plt.plot(t, y_original, 'k-', alpha=0.5, label='Original')
        
        results = []
        for window in window_lengths:
            if window < 3:
                continue
                
            if polyorder >= window:
                po = window - 1
            else:
                po = polyorder
                
            y_filtered = savgol_filter(y_original, window_length=window, polyorder=po)
            plt.plot(t, y_filtered, '-', label=f'Janela={window}, Ordem={po}')
            
            # Calcular métricas de suavização
            noise_reduction = np.std(y_original - y_filtered) / np.std(y_original)
            signal_preservation = np.corrcoef(y_original, y_filtered)[0, 1]
            
            results.append({
                "window_length": window,
                "polyorder": po,
                "noise_reduction": float(noise_reduction),
                "signal_preservation": float(signal_preservation)
            })
        
        plt.grid(True)
        plt.legend()
        plt.title('Comparação de Diferentes Parâmetros de Filtro')
        plt.xlabel('Tempo')
        plt.ylabel('Saída')
        
        # Salvar gráfico
        plot_path = f"{PLOTS_DIR}/{file_id}_filter_analysis.png"
        plt.savefig(plot_path)
        plt.close()
        
        return {
            "plot_path": plot_path,
            "filter_results": results
        }
    
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Erro ao analisar filtro: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao analisar filtro: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
