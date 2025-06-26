import os
import chess.pgn
from tqdm import tqdm

DATA_DIR = "data"
PGN_DIR = os.path.join(DATA_DIR, "pgn")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")

os.makedirs(PGN_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

def count_games_in_pgn(pgn_path):
    count = 0
    with open(pgn_path, encoding="utf-8", errors="ignore") as pgn:
        while True:
            game = chess.pgn.read_game(pgn)
            if game is None:
                break
            count += 1
    return count

def process_pgn(pgn_path, output_path, min_elo=0, max_games=None):
    """
    Processa um arquivo PGN gigante, filtrando por rating mínimo e salvando jogos válidos em outro arquivo.
    """
    with open(pgn_path, encoding="utf-8", errors="ignore") as pgn, open(output_path, "w", encoding="utf-8") as out:
        processed = 0
        for game in tqdm(iter(lambda: chess.pgn.read_game(pgn), None), desc=f"Processando {os.path.basename(pgn_path)}"):
            try:
                white_elo = int(game.headers.get("WhiteElo", 0))
                black_elo = int(game.headers.get("BlackElo", 0))
                if white_elo < min_elo or black_elo < min_elo:
                    continue
                out.write(str(game) + "\n\n")
                processed += 1
                if max_games and processed >= max_games:
                    break
            except Exception:
                continue
    print(f"Salvo {processed} jogos em {output_path}")

if __name__ == "__main__":
    # Exemplo de uso: processar todos os PGNs em data/pgn/
    min_elo = 1500  # ajuste conforme desejar
    max_games = None  # ou defina um limite
    for fname in os.listdir(PGN_DIR):
        if fname.endswith(".pgn"):
            pgn_path = os.path.join(PGN_DIR, fname)
            output_path = os.path.join(PROCESSED_DIR, f"filtered_{fname}")
            print(f"Contando jogos em {fname}...")
            total = count_games_in_pgn(pgn_path)
            print(f"Total de jogos: {total}")
            process_pgn(pgn_path, output_path, min_elo=min_elo, max_games=max_games)
