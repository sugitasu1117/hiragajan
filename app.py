import streamlit as st

# 30符固定の点数テーブル (親・子の点数計算用)
# [子ロン, 子ツモ(子負担/親負担), 親ロン, 親ツモ(全員負担)]
SCORE_TABLE_30 = {
    1: {"ko_ron": 1000, "ko_tsumo": (300, 500), "oya_ron": 1500, "oya_tsumo": 500},
    2: {"ko_ron": 2000, "ko_tsumo": (500, 1000), "oya_ron": 2900, "oya_tsumo": 1000},
    3: {"ko_ron": 3900, "ko_tsumo": (1000, 2000), "oya_ron": 5800, "oya_tsumo": 2000},
    4: {"ko_ron": 7700, "ko_tsumo": (2000, 3900), "oya_ron": 11600, "oya_tsumo": 3900},
    5: {"ko_ron": 8000, "ko_tsumo": (2000, 4000), "oya_ron": 12000, "oya_tsumo": 4000}, # 満貫
    6: {"ko_ron": 12000, "ko_tsumo": (3000, 6000), "oya_ron": 18000, "oya_tsumo": 6000}, # 跳満
    7: {"ko_ron": 12000, "ko_tsumo": (3000, 6000), "oya_ron": 18000, "oya_tsumo": 6000},
    8: {"ko_ron": 16000, "ko_tsumo": (4000, 8000), "oya_ron": 24000, "oya_tsumo": 8000}, # 倍満
    9: {"ko_ron": 16000, "ko_tsumo": (4000, 8000), "oya_ron": 24000, "oya_tsumo": 8000},
    10: {"ko_ron": 16000, "ko_tsumo": (4000, 8000), "oya_ron": 24000, "oya_tsumo": 8000},
    11: {"ko_ron": 24000, "ko_tsumo": (6000, 12000), "oya_ron": 36000, "oya_tsumo": 12000}, # 三倍満
    12: {"ko_ron": 24000, "ko_tsumo": (6000, 12000), "oya_ron": 36000, "oya_tsumo": 12000},
    13: {"ko_ron": 32000, "ko_tsumo": (8000, 16000), "oya_ron": 48000, "oya_tsumo": 16000}, # 役満
}

# 初期状態のセットアップ
if "game_state" not in st.session_state:
    st.session_state.game_state = "setup"

st.title("ひらがジャン 点数計算アプリ")

# --- 1. 初期設定画面 ---
if st.session_state.game_state == "setup":
    st.header("ゲーム設定")
    p0 = st.text_input("東家 (親)", "プレイヤー1")
    p1 = st.text_input("南家", "プレイヤー2")
    p2 = st.text_input("西家", "プレイヤー3")
    p3 = st.text_input("北家", "プレイヤー4")
    
    init_score = st.number_input("初期点数", value=25000, step=1000)
    rate = st.number_input("1000点あたりの金額(円)", value=30, step=10)
    use_rank_point = st.checkbox("順位点あり (+20k/+10k/-10k/-20k)", value=True)
    game_mode = st.radio("ゲーム形式", ["東風戦", "半荘戦"])

    if st.button("ゲーム開始"):
        st.session_state.players = [p0, p1, p2, p3]
        st.session_state.scores = [init_score] * 4
        st.session_state.init_score = init_score
        st.session_state.rate = rate
        st.session_state.use_rank_point = use_rank_point
        st.session_state.game_mode = game_mode
        st.session_state.round_idx = 0  # 0:東1局, 1:東2局...
        st.session_state.honba = 0
        st.session_state.kyotaku = 0
        st.session_state.game_state = "play"
        st.rerun()

# --- 2. 対局画面 ---
elif st.session_state.game_state == "play":
    # 局数の判定
    max_rounds = 4 if st.session_state.game_mode == "東風戦" else 8
    
    if st.session_state.round_idx >= max_rounds:
        st.session_state.game_state = "result"
        st.rerun()

    wind_names = ["東", "南"]
    curr_wind = wind_names[st.session_state.round_idx // 4]
    curr_num = (st.session_state.round_idx % 4) + 1
    oya_idx = st.session_state.round_idx % 4

    st.subheader(f"{curr_wind}{curr_num}局 {st.session_state.honba}本場 | 供託: {st.session_state.kyotaku * 1000}点")
    
    # プレイヤー情報表示
    cols = st.columns(4)
    for i in range(4):
        is_oya = "(親)" if i == oya_idx else ""
        cols[i].metric(f"{st.session_state.players[i]} {is_oya}", f"{st.session_state.scores[i]}点")

    st.divider()
    action = st.radio("結果を選択", ["和了", "流局"], horizontal=True)

    if action == "和了":
        st.markdown("### 和了入力")
        winner = st.selectbox("和了者", [f"{p} {'(親)' if i == oya_idx else ''}" for i, p in enumerate(st.session_state.players)])
        winner_idx = [f"{p} {'(親)' if i == oya_idx else ''}" for i, p in enumerate(st.session_state.players)].index(winner)
        
        win_type = st.radio("あがり方", ["ツモ", "ロン"], horizontal=True)
        loser_idx = None
        if win_type == "ロン":
            loser_candidates = [p for i, p in enumerate(st.session_state.players) if i != winner_idx]
            loser = st.selectbox("放銃者", loser_candidates)
            loser_idx = st.session_state.players.index(loser)

        riichi_players = st.multiselect("リーチした人", st.session_state.players)
        han = st.number_input("翻数", min_value=1, max_value=13, value=1)

        if st.button("次局へ"):
            # リーチ棒の徴収
            for p in riichi_players:
                idx = st.session_state.players.index(p)
                st.session_state.scores[idx] -= 1000
                st.session_state.kyotaku += 1

            # 点数計算
            score_data = SCORE_TABLE_30.get(han, SCORE_TABLE_30[13])
            is_winner_oya = (winner_idx == oya_idx)
            honba_bonus = st.session_state.honba * 300

            if win_type == "ロン":
                base_score = score_data["oya_ron"] if is_winner_oya else score_data["ko_ron"]
                total_pay = base_score + honba_bonus
                st.session_state.scores[loser_idx] -= total_pay
                st.session_state.scores[winner_idx] += total_pay
            else: # ツモ
                if is_winner_oya:
                    pay_each = score_data["oya_tsumo"] + (st.session_state.honba * 100)
                    for i in range(4):
                        if i != winner_idx:
                            st.session_state.scores[i] -= pay_each
                            st.session_state.scores[winner_idx] += pay_each
                else:
                    ko_pay = score_data["ko_tsumo"][0] + (st.session_state.honba * 100)
                    oya_pay = score_data["ko_tsumo"][1] + (st.session_state.honba * 100)
                    for i in range(4):
                        if i == winner_idx:
                            continue
                        elif i == oya_idx:
                            st.session_state.scores[i] -= oya_pay
                            st.session_state.scores[winner_idx] += oya_pay
                        else:
                            st.session_state.scores[i] -= ko_pay
                            st.session_state.scores[winner_idx] += ko_pay

            # 供託総取り
            st.session_state.scores[winner_idx] += st.session_state.kyotaku * 1000
            st.session_state.kyotaku = 0

            # 連荘/親移動判定
            if is_winner_oya:
                st.session_state.honba += 1
            else:
                st.session_state.round_idx += 1
                st.session_state.honba = 0
            st.rerun()

    elif action == "流局":
        st.markdown("### 流局入力")
        tenpai_players = st.multiselect("聴牌（テンパイ）した人", st.session_state.players)
        riichi_players = st.multiselect("リーチした人", st.session_state.players)

        if st.button("次局へ"):
            # リーチ棒の徴収（供託へ）
            for p in riichi_players:
                idx = st.session_state.players.index(p)
                st.session_state.scores[idx] -= 1000
                st.session_state.kyotaku += 1

            # ノーテン罰符（3000点移動）
            num_tenpai = len(tenpai_players)
            if 0 < num_tenpai < 4:
                receive_score = 3000 // num_tenpai
                pay_score = 3000 // (4 - num_tenpai)
                for i, p in enumerate(st.session_state.players):
                    if p in tenpai_players:
                        st.session_state.scores[i] += receive_score
                    else:
                        st.session_state.scores[i] -= pay_score

            # 親のテンパイ判定による連荘/親移動
            oya_player = st.session_state.players[oya_idx]
            st.session_state.honba += 1
            if oya_player not in tenpai_players:
                st.session_state.round_idx += 1
            st.rerun()

# --- 3. 結果発表画面 ---
elif st.session_state.game_state == "result":
    st.header("対局終了 - 最終結果")
    
    # 順位ソート
    results = []
    for i in range(4):
        results.append({"name": st.session_state.players[i], "score": st.session_state.scores[i]})
    results.sort(key=lambda x: x["score"], reverse=True)

    rank_points = [20000, 10000, -10000, -20000] if st.session_state.use_rank_point else [0, 0, 0, 0]

    st.write("### 精算表")
    for rank, res in enumerate(results):
        diff = res["score"] - st.session_state.init_score
        total_point = diff + rank_points[rank]
        money = int((total_point / 1000) * st.session_state.rate)
        
        st.write(f"**第{rank+1}位**: {res['name']} | 最終点数: {res['score']}点 | 差分: {diff:+d} | 精算: {money:+d}円")

    if st.button("タイトルに戻る"):
        st.session_state.game_state = "setup"
        st.rerun()