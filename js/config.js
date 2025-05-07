// Configuração da API
const API_CONFIG = {
    // URL base da API
    baseUrl: 'https://59bd-2804-18-48aa-5e20-d043-bcd3-7f73-ce0f.ngrok-free.app',
     
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
 