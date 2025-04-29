// Código principal para interação com a API e manipulação da interface
document.addEventListener('DOMContentLoaded', function() {
    // Elementos da interface
    const uploadForm = document.getElementById('upload-form');
    const identifyForm = document.getElementById('identify-form');
    const tuneForm = document.getElementById('tune-form');
    const simulateForm = document.getElementById('simulate-form');
    const analyzeFiltersBtn = document.getElementById('analyze-filters-btn');
    const filterModal = new bootstrap.Modal(document.getElementById('filter-modal'));
    
    // Elementos de exibição de valores dos sliders
    const windowLengthValue = document.getElementById('window-length-value');
    const polyorderValue = document.getElementById('polyorder-value');
    const offsetPercentValue = document.getElementById('offset-percent-value');
    const lambdaValue = document.getElementById('lambda-value');
    const simTimeValue = document.getElementById('sim-time-value');
    
    // Sliders
    const windowLengthSlider = document.getElementById('window-length');
    const polyorderSlider = document.getElementById('polyorder');
    const offsetPercentSlider = document.getElementById('offset-percent');
    const lambdaSlider = document.getElementById('lambda');
    const simTimeSlider = document.getElementById('sim-time');
    
    // Tabs
    const uploadTab = document.getElementById('upload-tab');
    const identifyTab = document.getElementById('identify-tab');
    const tuneTab = document.getElementById('tune-tab');
    const simulateTab = document.getElementById('simulate-tab');
    
    // Botões de navegação
    const gotoIdentifyBtn = document.getElementById('goto-identify-btn');
    const backToUploadBtn = document.getElementById('back-to-upload-btn');
    const gotoTuneBtn = document.getElementById('goto-tune-btn');
    const backToIdentifyBtn = document.getElementById('back-to-identify-btn');
    const gotoSimulateBtn = document.getElementById('goto-simulate-btn');
    const backToTuneBtn = document.getElementById('back-to-tune-btn');
    
    // Configurar navegação entre abas
    gotoIdentifyBtn.addEventListener('click', () => {
        const tab = new bootstrap.Tab(identifyTab);
        tab.show();
        console.log('Navegando para a aba de Identificação');
    });
    
    backToUploadBtn.addEventListener('click', () => {
        const tab = new bootstrap.Tab(uploadTab);
        tab.show();
        console.log('Navegando de volta para a aba de Upload');
    });
    
    gotoTuneBtn.addEventListener('click', () => {
        const tab = new bootstrap.Tab(tuneTab);
        tab.show();
        console.log('Navegando para a aba de Sintonia');
    });
    
    backToIdentifyBtn.addEventListener('click', () => {
        const tab = new bootstrap.Tab(identifyTab);
        tab.show();
        console.log('Navegando de volta para a aba de Identificação');
    });
    
    gotoSimulateBtn.addEventListener('click', () => {
        const tab = new bootstrap.Tab(simulateTab);
        tab.show();
        console.log('Navegando para a aba de Simulação');
    });
    
    backToTuneBtn.addEventListener('click', () => {
        const tab = new bootstrap.Tab(tuneTab);
        tab.show();
        console.log('Navegando de volta para a aba de Sintonia');
    });
    
    // Atualizar valores dos sliders quando alterados
    windowLengthSlider.addEventListener('input', () => {
        windowLengthValue.textContent = windowLengthSlider.value;
    });
    
    polyorderSlider.addEventListener('input', () => {
        polyorderValue.textContent = polyorderSlider.value;
    });
    
    offsetPercentSlider.addEventListener('input', () => {
        offsetPercentValue.textContent = offsetPercentSlider.value;
    });
    
    lambdaSlider.addEventListener('input', () => {
        lambdaValue.textContent = parseFloat(lambdaSlider.value).toFixed(1);
    });
    
    simTimeSlider.addEventListener('input', () => {
        simTimeValue.textContent = simTimeSlider.value;
    });
    
    // Formulário de upload
    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        console.log("Iniciando upload...");
        
        const fileInput = document.getElementById('file-input');
        const file = fileInput.files[0];
        
        if (!file) {
            showAlert('Por favor, selecione um arquivo .mat', 'danger');
            return;
        }
        
        console.log("Arquivo selecionado:", file.name);
        
        if (!file.name.endsWith('.mat')) {
            showAlert('Apenas arquivos .mat são aceitos', 'danger');
            return;
        }
        
        showLoading();
        
        try {
            console.log("Enviando requisição para:", `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.upload}`);
            
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.upload}`, {
                method: 'POST',
                body: formData
            });
            
            console.log("Resposta recebida, status:", response.status);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error("Erro detalhado:", errorText);
                throw new Error(`Erro ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log("Dados recebidos:", data);
            
            // Armazenar ID do arquivo
            document.getElementById('file-id').value = data.file_id;
            
            // Exibir resumo dos dados
            displayDataSummary(data.data_summary);
            
            // Exibir gráfico
            document.getElementById('raw-plot').src = API_CONFIG.getImageUrl(data.plot_path);
            document.getElementById('data-summary-card').style.display = 'block';
            
            showAlert('Arquivo processado com sucesso!', 'success');
        } catch (error) {
            console.error('Erro completo:', error);
            showAlert(`Erro ao processar arquivo: ${error.message}`, 'danger');
        } finally {
            hideLoading();
        }
    });
    
    // Formulário de identificação
    identifyForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        showLoading();
        
        try {
            console.log("Enviando requisição de identificação...");
            const formData = new FormData(identifyForm);
            
            const response = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.identify}`, {
                method: 'POST',
                body: formData
            });
            
            console.log("Resposta recebida, status:", response.status);
            
            if (!response.ok) {
                const errorData = await response.json();
                console.error("Erro detalhado:", errorData);
                throw new Error(errorData.detail || `Erro ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log("Dados recebidos:", data);
            
            // Armazenar parâmetros do modelo
            document.getElementById('model-k').value = data.k;
            document.getElementById('model-tau').value = data.tau;
            document.getElementById('model-theta').value = data.theta;
            
            // Exibir parâmetros do modelo
            displayModelParams(data);
            
            // Exibir gráfico
            document.getElementById('identify-plot').src = API_CONFIG.getImageUrl(data.plot_path);
            document.getElementById('model-params-card').style.display = 'block';
            
            showAlert('Modelo identificado com sucesso!', 'success');
        } catch (error) {
            console.error('Erro completo:', error);
            showAlert(`Erro ao identificar modelo: ${error.message}`, 'danger');
        } finally {
            hideLoading();
        }
    });
    
    // Botão de análise de filtros
    analyzeFiltersBtn.addEventListener('click', async function() {
        const fileId = document.getElementById('file-id').value;
        
        if (!fileId) {
            showAlert('Nenhum arquivo carregado', 'danger');
            return;
        }
        
        showLoading();
        
        try {
            console.log("Enviando requisição de análise de filtros...");
            const formData = new FormData();
            formData.append('file_id', fileId);
            formData.append('window_lengths', '[11, 21, 31, 51]');
            formData.append('polyorder', document.getElementById('polyorder').value);
            
            const response = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.analyzeFilter}`, {
                method: 'POST',
                body: formData
            });
            
            console.log("Resposta recebida, status:", response.status);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error("Erro detalhado:", errorText);
                throw new Error(`Erro ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log("Dados recebidos:", data);
            
            // Exibir resultados da análise
            displayFilterResults(data.filter_results);
            
            // Exibir gráfico
            document.getElementById('filter-plot').src = API_CONFIG.getImageUrl(data.plot_path);
            
            // Mostrar modal
            filterModal.show();
        } catch (error) {
            console.error('Erro completo:', error);
            showAlert(`Erro ao analisar filtros: ${error.message}`, 'danger');
        } finally {
            hideLoading();
        }
    });
    
    // Formulário de sintonia
    tuneForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        showLoading();
        
        try {
            console.log("Enviando requisição de sintonia...");
            const formData = new FormData(tuneForm);
            
            const response = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.tune}`, {
                method: 'POST',
                body: formData
            });
            
            console.log("Resposta recebida, status:", response.status);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error("Erro detalhado:", errorText);
                throw new Error(`Erro ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log("Dados recebidos:", data);
            
            // Armazenar lambda para simulação
            document.getElementById('sim-k').value = document.getElementById('model-k').value;
            document.getElementById('sim-tau').value = document.getElementById('model-tau').value;
            document.getElementById('sim-theta').value = document.getElementById('model-theta').value;
            document.getElementById('sim-lambda').value = document.getElementById('lambda').value;
            
            // Exibir parâmetros dos controladores
            displayPIDParams(data);
            
            // Exibir card de parâmetros
            document.getElementById('pid-params-card').style.display = 'block';
            
            showAlert('Controladores sintonizados com sucesso!', 'success');
        } catch (error) {
            console.error('Erro completo:', error);
            showAlert(`Erro ao sintonizar controladores: ${error.message}`, 'danger');
        } finally {
            hideLoading();
        }
    });
    
    // Formulário de simulação
    simulateForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        showLoading();
        
        try {
            console.log("Enviando requisição de simulação...");
            const formData = new FormData(simulateForm);
            
            const response = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.plot}`, {
                method: 'POST',
                body: formData
            });
            
            console.log("Resposta recebida, status:", response.status);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error("Erro detalhado:", errorText);
                throw new Error(`Erro ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log("Dados recebidos:", data);
            
            // Exibir métricas de desempenho
            displayResponseMetrics(data.metrics);
            
            // Exibir gráfico
            document.getElementById('response-plot').src = API_CONFIG.getImageUrl(data.plot_path);
            document.getElementById('response-metrics-card').style.display = 'block';
            
            showAlert('Simulação concluída com sucesso!', 'success');
        } catch (error) {
            console.error('Erro completo:', error);
            showAlert(`Erro ao simular resposta: ${error.message}`, 'danger');
        } finally {
            hideLoading();
        }
    });
    
    // Funções auxiliares
    
    // Exibir resumo dos dados
    function displayDataSummary(summary) {
        const container = document.getElementById('data-summary');
        
        container.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <div class="result-card">
                        <div class="mb-2"><strong>Amostras:</strong> <span class="param-value">${summary.samples}</span></div>
                        <div><strong>Faixa de Tempo:</strong> <span class="param-value">${summary.time_range[0].toFixed(2)} a ${summary.time_range[1].toFixed(2)}</span></div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="result-card">
                        <div class="mb-2"><strong>Faixa de Saída:</strong> <span class="param-value">${summary.output_range[0].toFixed(2)} a ${summary.output_range[1].toFixed(2)}</span></div>
                        <div><strong>Faixa de Entrada:</strong> <span class="param-value">${summary.input_range[0].toFixed(2)} a ${summary.input_range[1].toFixed(2)}</span></div>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Exibir parâmetros do modelo
    function displayModelParams(data) {
        const container = document.getElementById('model-params');
        
        container.innerHTML = `
            <div class="row">
                <div class="col-md-4">
                    <div class="result-card">
                        <div class="mb-2"><strong>Ganho (K):</strong> <span class="param-value">${data.k.toFixed(4)}</span></div>
                        <div class="mb-2"><strong>Constante de Tempo (τ):</strong> <span class="param-value">${data.tau.toFixed(2)}</span></div>
                        <div><strong>Tempo Morto (θ):</strong> <span class="param-value">${data.theta.toFixed(2)}</span></div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="result-card">
                        <div class="mb-2"><strong>t1:</strong> <span class="param-value">${data.t1.toFixed(2)}</span></div>
                        <div class="mb-2"><strong>t2:</strong> <span class="param-value">${data.t2.toFixed(2)}</span></div>
                        <div><strong>Δt:</strong> <span class="param-value">${(data.t2 - data.t1).toFixed(2)}</span></div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="result-card">
                        <div class="mb-2"><strong>y1:</strong> <span class="param-value">${data.y1.toFixed(2)}</span></div>
                        <div class="mb-2"><strong>y2:</strong> <span class="param-value">${data.y2.toFixed(2)}</span></div>
                        <div><strong>Filtro:</strong> <span class="param-value">Janela=${data.filter_params.window_length}, Ordem=${data.filter_params.polyorder}</span></div>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Exibir parâmetros dos controladores
    function displayPIDParams(data) {
        const imcContainer = document.getElementById('imc-params');
        const itaeContainer = document.getElementById('itae-params');
        
        imcContainer.innerHTML = `
            <div class="result-card">
                <div class="mb-2"><strong>Kp:</strong> <span class="param-value">${data.IMC.Kp.toFixed(4)}</span></div>
                <div class="mb-2"><strong>Ti:</strong> <span class="param-value">${data.IMC.Ti.toFixed(2)}</span></div>
                <div><strong>Td:</strong> <span class="param-value">${data.IMC.Td.toFixed(2)}</span></div>
            </div>
        `;
        
        itaeContainer.innerHTML = `
            <div class="result-card">
                <div class="mb-2"><strong>Kp:</strong> <span class="param-value">${data.ITAE.Kp.toFixed(4)}</span></div>
                <div class="mb-2"><strong>Ti:</strong> <span class="param-value">${data.ITAE.Ti.toFixed(2)}</span></div>
                <div><strong>Td:</strong> <span class="param-value">${data.ITAE.Td.toFixed(2)}</span></div>
            </div>
        `;
    }
    
    // Exibir métricas de desempenho
    function displayResponseMetrics(metrics) {
        const imcContainer = document.getElementById('imc-metrics-content');
        const itaeContainer = document.getElementById('itae-metrics-content');
        
        imcContainer.innerHTML = `
            <div class="result-card">
                <div class="mb-2"><strong>Tempo de Subida:</strong> <span class="param-value">${metrics.IMC.rise_time.toFixed(2)}s</span></div>
                <div class="mb-2"><strong>Sobressinal:</strong> <span class="param-value">${metrics.IMC.overshoot.toFixed(2)}%</span></div>
                <div><strong>Tempo de Acomodação:</strong> <span class="param-value">${metrics.IMC.settling_time.toFixed(2)}s</span></div>
            </div>
        `;
        
        itaeContainer.innerHTML = `
            <div class="result-card">
                <div class="mb-2"><strong>Tempo de Subida:</strong> <span class="param-value">${metrics.ITAE.rise_time.toFixed(2)}s</span></div>
                <div class="mb-2"><strong>Sobressinal:</strong> <span class="param-value">${metrics.ITAE.overshoot.toFixed(2)}%</span></div>
                <div><strong>Tempo de Acomodação:</strong> <span class="param-value">${metrics.ITAE.settling_time.toFixed(2)}s</span></div>
            </div>
        `;
    }
    
    // Exibir resultados da análise de filtros
    function displayFilterResults(results) {
        const container = document.getElementById('filter-results');
        
        let html = `
            <div class="table-responsive">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Tamanho da Janela</th>
                            <th>Ordem do Polinômio</th>
                            <th>Redução de Ruído</th>
                            <th>Preservação de Sinal</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        results.forEach(result => {
            html += `
                <tr>
                    <td>${result.window_length}</td>
                    <td>${result.polyorder}</td>
                    <td>${(result.noise_reduction * 100).toFixed(2)}%</td>
                    <td>${(result.signal_preservation * 100).toFixed(2)}%</td>
                </tr>
            `;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
            <div class="alert alert-info mt-3">
                <strong>Dica:</strong> Escolha um tamanho de janela que ofereça um bom equilíbrio entre redução de ruído e preservação de sinal.
                Valores maiores de janela resultam em mais suavização, mas podem distorcer o sinal original.
            </div>
        `;
        
        container.innerHTML = html;
    }
    
    // Exibir alerta
    function showAlert(message, type) {
        const alertContainer = document.createElement('div');
        alertContainer.className = `alert alert-${type} alert-dismissible fade show`;
        alertContainer.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        document.querySelector('.container').prepend(alertContainer);
        
        // Remover alerta após 5 segundos
        setTimeout(() => {
            alertContainer.remove();
        }, 5000);
    }
    
    // Exibir loading
    function showLoading() {
        document.getElementById('loading').style.display = 'flex';
    }
    
    // Esconder loading
    function hideLoading() {
        document.getElementById('loading').style.display = 'none';
    }
});
