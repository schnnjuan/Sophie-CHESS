import requests
import chess
import chess.pgn
import time
from typing import List

# Exemplo de uso com ChessBase Online Database
CHESSBASE_API = "https://database.chessbase.com/"

# Para Lichess, use: https://explorer.lichess.ovh/lichess?fen=<FEN>

class OnlineOpeningExplorer:
    def __init__(self, api_url: str = CHESSBASE_API):
        self.api_url = api_url.rstrip('/')

    def get_moves(self, fen: str) -> List[str]:
        """
        Consulta a API online e retorna os lances possíveis a partir da FEN.
        Para ChessBase, a API pública não é documentada, então este é um exemplo genérico.
        Para Lichess, troque a URL e o parsing.
        """
        # Exemplo para Lichess (troque a URL se quiser usar Lichess):
        url = f"https://explorer.lichess.ovh/lichess?fen={fen}"
        resp = requests.get(url)
        if resp.status_code != 200:
            return []
        data = resp.json()
        moves = [move['uci'] for move in data.get('moves', [])]
        return moves

    def find_longest_line(self, board: chess.Board, max_time: float = 5.0) -> List[str]:
        """
        Busca a linha mais longa possível a partir da posição, consultando a API online, dentro do tempo limite.
        """
        start = time.time()
        sequence = []
        current_board = board.copy()
        while time.time() - start < max_time:
            fen = current_board.fen()
            moves = self.get_moves(fen)
            if not moves:
                break
            move = moves[0]  # Pega o lance mais popular
            sequence.append(move)
            current_board.push_uci(move)
        return sequence

if __name__ == "__main__":
    explorer = OnlineOpeningExplorer()
    board = chess.Board()  # posição inicial
    line = explorer.find_longest_line(board, max_time=5.0)
    print("Linha mais longa encontrada em 5s:")
    print(line)
