import streamlit as st
import random
import google.generativeai as genai
import os

# ==========================================
# 設定: あなたのAPIキー
# ==========================================
API_KEY = "AIzaSyDNmz5Hh-Yuj96ztJ1i6MxoXrjcHgreIKk"

# --- 2文字の単語リスト（素材） ---
KANJI_WORDS = [
    "悪魔", "天使", "雷電", "波動", "黄金", "深海", "灼熱", "虚無", 
    "旋風", "断罪", "珈琲", "筋肉", "爆発", "銀河", "初恋", "忍者",
    "暗黒", "聖女", "野望", "絶望", "希望", "無限", "時空", "伝説",
    "焼肉", "会計", "残業", "有給", "睡眠", "反撃", "覚醒", "帝国",
    "戦車", "妖精", "東京", "地獄", "天国", "暴走", "純情", "電脳",
    "天気", "刃物", "虹色", "電気", "迷宮", "運命", "革命", "神話",
    "宇宙", "最強", "虚構", "現実", "爆音", "沈黙", "極道", "純白"
]

def get_available_model_name():
    """環境に合わせて使えるモデルを自動で探す"""
    try:
        genai.configure(api_key=API_KEY)
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                return m.name
    except Exception:
        pass
    return 'gemini-pro'

def judge_four_char_word(word_a, word_b):
    """
    AIが四字熟語を採点し、理論的に解説する関数
    """
    try:
        genai.configure(api_key=API_KEY)
        valid_model_name = get_available_model_name()
        model = genai.GenerativeModel(valid_model_name)

        # プロンプト修正：採点の「根拠」を理論的に説明するように指示
        prompt = f"""
        あなたは論理的かつ厳格な「造語審議委員会の審査員」です。
        2人のプレイヤーが作成した「新しい四字熟語」を分析し、採点してください。

        【プレイヤーAの作品】
        「{word_a}」

        【プレイヤーBの作品】
        「{word_b}」

        【採点ロジック】
        以下の3点を分析し、合計100点で評価してください。
        1. 意味の拡張性（単語同士の組み合わせによる化学反応、意外性）
        2. 視覚的強度（文字として並んだ時のパワー）
        3. 音韻的快感（声に出した時のリズム）

        【出力フォーマット】
        ※見出し記号（#）や区切り線（---）は使用禁止です。
        
        【採点結果】
        A: [0〜100] 点
        B: [0〜100] 点
        
        【勝者】
        [プレイヤーA または プレイヤーB]
        
        【分析レポート】
        [プレイヤーAの得点理由]
        [なぜその点数なのか、語句の構成や対比効果（コントラスト）について理論的に解説]

        [プレイヤーBの得点理由]
        [なぜその点数なのか、Aと比較して優れている点や劣っている点を理論的に解説]
        """

        response = model.generate_content(prompt)
        text = response.text
        
        # 安全策：見出し記号や点線を強制削除
        text = text.replace("#", "").replace("---", "").replace("===", "")
        return text

    except Exception as e:
        return f"エラー詳細: {str(e)}\n(モデル: {valid_model_name})"

def main():
    st.set_page_config(page_title="架空四字熟語バトル", page_icon="🀄")
    
    st.title("🀄 架空四字熟語バトル")
    st.markdown("2つの言葉を合体させて、最強の「四字熟語」を作れ！")
    st.caption("AIが「意味の拡張性」「視覚的強度」「音韻的快感」から理論的に採点します。")

    # 手札の生成
    if 'hand_options' not in st.session_state:
        st.session_state['hand_options'] = random.sample(KANJI_WORDS, 12)

    # --- 素材の表示 ---
    st.info(f"**今回の素材リスト:**\n\n {' / '.join(st.session_state['hand_options'])}")

    st.divider()

    # --- プレイヤーの選択エリア ---
    col1, col2 = st.columns(2)

    options = st.session_state['hand_options']

    with col1:
        st.subheader("プレイヤーA")
        part_a_1 = st.selectbox("前の言葉 (A)", options, key="a1")
        part_a_2 = st.selectbox("後の言葉 (A)", options, key="a2")
        
        word_a = part_a_1 + part_a_2
        st.metric(label="完成", value=word_a)
    
    with col2:
        st.subheader("プレイヤーB")
        part_b_1 = st.selectbox("前の言葉 (B)", options, key="b1")
        part_b_2 = st.selectbox("後の言葉 (B)", options, key="b2")
        
        word_b = part_b_1 + part_b_2
        st.metric(label="完成", value=word_b)

    st.divider()

    # --- 判定ボタン ---
    if st.button("採点開始！（AI判定）", type="primary"):
        
        if word_a == word_b:
            st.warning("⚠️ カブりました！")
            st.write(f"二人とも**「{word_a}」**を選びました。")
            st.write("違う組み合わせを作って再挑戦してください。")
        
        else:
            with st.spinner(f"「{word_a}」と「{word_b}」の構成要素を解析中..."):
                result = judge_four_char_word(word_a, word_b)
            
            st.success("解析完了")
            st.markdown("### 📝 AI審査員の分析レポート")
            # 結果表示
            st.write(result)

    # リセットボタン
    if st.button("素材を配り直す"):
        st.session_state['hand_options'] = random.sample(KANJI_WORDS, 12)
        st.rerun()

if __name__ == "__main__":
    main()