from pyngrok import ngrok

# Abre o túnel para a porta 8000
public_url = ngrok.connect(8000)
print("Sua API está acessível em:", public_url)

# Mantenha o script rodando
input("Pressione ENTER para encerrar o túnel...\n")
