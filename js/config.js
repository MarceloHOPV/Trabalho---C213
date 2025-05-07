// Configuração da API
const API_CONFIG = {
    // URL base da API
    baseUrl: 'https://369b-131-221-241-235.ngrok-free.app',
    
    // Endpoints da API
    endpoints: {
        upload: '/upload/',
        identify: '/identify/',
        tune: '/tune/',
        plot: '/plot/',
        analyzeFilter: '/analyze-filter/'
    },
    
    // Função para obter URL completa de uma imagem
    getImageUrl: function(path) {
        // Remove a barra inicial se existir
        if (path.startsWith('/')) {
            path = path.substring(1);
        }
        return `${this.baseUrl}/${path}`;
    }
};
