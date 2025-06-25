# 🤖 Chess Learning Bot

Um bot de xadrez inteligente que joga no Chess.com e aprende com cada partida usando Machine Learning.

## 🎯 Características

- **Joga automaticamente** no Chess.com via API
- **Aprende continuamente** com cada partida
- **Análise pós-jogo** com Stockfish
- **Múltiplos algoritmos de IA** (Supervised Learning + Reinforcement Learning)
- **Métricas de evolução** em tempo real
- **Interface de monitoramento**

## 🚀 Instalação

```bash
# Clone o repositório
git clone <seu-repo>
cd chess-learning-bot

# Instale as dependências
pip install -r requirements.txt

# Configure as variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais
```

## ⚙️ Configuração

1. **Criar conta de bot no Chess.com**
   - Registre-se no [Chess.com Developer Portal](https://www.chess.com/news/view/published-data-api)
   - Obtenha sua API Key

2. **Instalar Stockfish**
   ```bash
   # Windows (via Chocolatey)
   choco install stockfish
   
   # Linux
   sudo apt install stockfish
   
   # macOS
   brew install stockfish
   ```

3. **Configurar variáveis de ambiente**
   ```env
   CHESS_COM_USERNAME=seu_bot_username
   CHESS_COM_PASSWORD=sua_senha
   CHESS_COM_API_KEY=sua_api_key
   STOCKFISH_PATH=/caminho/para/stockfish
   ```

## 🎮 Uso

```bash
# Treinar o modelo inicial
python train_initial_model.py

# Iniciar o bot
python main.py

# Monitorar performance
python dashboard.py
```

## 📊 Estrutura do Projeto

```
chess-learning-bot/
├── src/
│   ├── bot/                 # Core do bot
│   ├── engine/              # Interface com motores
│   ├── learning/            # Algoritmos de ML
│   ├── analysis/            # Análise de partidas
│   └── database/            # Persistência de dados
├── models/                  # Modelos treinados
├── data/                    # Datasets e logs
├── tests/                   # Testes unitários
└── config/                  # Configurações
```

## 🧠 Algoritmos de Aprendizado

1. **Supervised Learning**: Aprende com partidas de mestres
2. **Reinforcement Learning**: Melhora através de auto-jogo
3. **Online Learning**: Adapta-se durante partidas reais

## 📈 Métricas

- Taxa de vitórias ao longo do tempo
- Número de erros por partida
- Elo estimado
- Tempo médio por jogada

## ⚠️ Aviso Legal

**IMPORTANTE**: Este bot deve ser usado apenas em contas registradas como bot no Chess.com. O uso em contas humanas viola os termos de serviço da plataforma.

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para detalhes.

