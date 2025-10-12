from fastapi import APIRouter

# APIルーターの初期化
router = APIRouter()

@router.get("/games", tags=["games"])
async def get_games():
    """ゲーム一覧を取得"""
    return {"games": []}

@router.post("/games", tags=["games"])
async def create_game():
    """新しいゲームを作成"""
    return {"message": "Game created", "game_id": "dummy-game-id"}

@router.get("/games/{game_id}", tags=["games"])
async def get_game(game_id: str):
    """特定のゲーム情報を取得"""
    return {"game_id": game_id, "status": "waiting"}

@router.post("/games/{game_id}/start", tags=["games"])
async def start_game(game_id: str):
    """ゲームを開始"""
    return {"message": f"Game {game_id} started"}

@router.post("/games/{game_id}/action", tags=["games"])
async def player_action(game_id: str):
    """プレイヤーアクション"""
    return {"message": f"Action executed in game {game_id}"}