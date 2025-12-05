import streamlit as st
import random
import google.generativeai as genai
import os
import plotly.graph_objects as go
import re

# ==========================================
# 設定: APIキー読み込み（安全対策版）
# ==========================================
# GitHubに公開しても安全なように、ここにはキーを書きません。
# Streamlit Cloud上では「Secrets」から自動で読み込まれます。
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    # ローカル（自分のPC）でテストする時だけ、ここにキーを入れても良いですが
    # GitHubに上げる前には必ず空文字 "" に戻してください！
    API_KEY = ""

# --- 2文字の単語リスト（約200語） ---
KANJI_WORDS = [
    # --- カッコいい・バトル系 ---
    "悪魔", "天使", "雷電", "波動", "黄金", "深海", "灼熱", "虚無", 
    "旋風", "断罪", "爆発", "銀河", "暗黒", "聖女", "野望", "絶望", 
    "希望", "無限", "時空", "伝説", "反撃", "覚醒", "帝国", "戦車", 
    "妖精", "地獄", "天国", "暴走", "電脳", "刃物", "迷宮", "運命", 
    "革命", "神話", "宇宙", "最強", "虚構", "爆音", "沈黙", "極道", 
    "覇王", "龍神", "魔王", "聖剣", "氷結", "煉獄", "刹那", "崩壊", 
    "創世", "英雄", "邪神", "封印", "禁忌", "召喚", "魔導", "機神", 
    "流星", "彗星", "月光", "太陽", "混沌", "秩序", "支配", "粛清",
    "雷鳴", "疾風", "豪腕", "鉄拳", "無双", "天上", "天下", "将軍",

    # --- 日常・ビジネス・社会系 ---
    "珈琲", "残業", "有給", "睡眠", "会計", "東京", "天気", "電気", 
    "現実", "純白", "課長", "係長", "部長", "社長", "定時", "休日", 
    "年金", "税金", "借金", "貯金", "利子", "現金", "値上", "半額", 
    "割引", "無料", "赤字", "黒字", "倒産", "起業", "面接", "合格", 
    "落選", "遅刻", "早退", "欠席", "謝罪", "炎上", "拡散", "検索", 
    "通信", "圏外", "充電", "故障", "修理", "解約", "契約", "捺印",

    # --- 食べ物・生活用品・シュール系 ---
    "焼肉", "寿司", "納豆", "豆腐", "豚骨", "醤油", "味噌", "激辛", 
    "大盛", "特盛", "完食", "空腹", "満腹", "筋肉", "脂肪", "骨折", 
    "腰痛", "頭痛", "便秘", "下痢", "鼻毛", "脱毛", "増毛", "育毛", 
    "寝癖", "爆睡", "箪笥", "雑巾", "洗剤", "石鹸", "風呂", "温泉", 
    "サウナ", "熱波", "冷水", "整う", "布団", "枕元", "玄関", "便所", 
    "野良", "害虫", "雑草", "野草", "猛獣", "猛虎", "家畜", "社畜",

    # --- 感情・概念・その他 ---
    "初恋", "純情", "失恋", "熱愛", "浮気", "不倫", "離婚", "結婚", 
    "婚活", "妊活", "青春", "反抗", "思春", "更年", "老後", "遺言", 
    "墓場", "葬式", "法事", "仏壇", "神棚", "運勢", "吉凶", "大吉", 
    "大凶", "厄年", "本厄", "後厄", "除霊", "心霊", "幽霊", "妖怪", 
    "怪獣", "未来", "過去", "現在", "歴史", "数学", "物理",
    "哲学", "宗教", "科学", "魔法", "奇跡", "偶然", "必然"
]

def get_available_model_name():
    """環境に合わせて使えるモデルを自動で探す"""
    try:
        if not API_KEY: return None
        genai.configure(api_key=API_KEY)
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                return m.name
    except Exception:
        pass
    return 'gemini-pro'

def create_radar_chart(scores_a, scores_b):
    """レーダーチャートを作成する関数"""
    categories = ['詩的度', '幻想度', '社会批評度', '哲学度', '音韻評価']

    fig = go.Figure()

    # プレイヤーA
    fig.add_trace(go.Scatterpolar(
        r=scores_a,
        theta=categories,
        fill='toself',
        name='プレイヤーA',
        line_color='blue',
        opacity=0.6
    ))

    # プレイヤーB
    fig.add_trace(go.Scatterpolar(
        r=scores_b,
        theta=categories,
        fill='toself',
        name='プレイヤーB',
        line_color='red',
        opacity=0.6
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=True,
        margin=dict(l=40, r=40, t=20, b=20)
    )
    return fig

def judge_four_char_word(word_a, word_b):
    """AIが四字熟語を採点・解説する"""
    if not API_KEY:
        return "【エラー】APIキーが設定されていません。Streamlit CloudのSecretsを設定してください。"

    try:
        genai.configure(api_key=API_KEY)
        valid_model_name = get_available_model_name()
        if not valid_model_name:
            return "【エラー】有効なモデルが見つかりません。APIキーを確認してください。"
            
        model = genai.GenerativeModel(valid_model_name)

        prompt = f"""
        あなたは「架空言語審議会」の審査員です。
        以下の2つの「新しい四字熟語」を5つの観点で数値化し、比較評価してください。

        【Aの作品】「{word_a}」
        【Bの作品】「{word_b}」

        【評価項目】(各100点満点)
        1. 詩的度（美しさ、情緒）
        2. 幻想度（ファンタジー感、スケール感）
        3. 社会批評度（現代社会への皮肉やリアリティ）
        4. 哲学度（深み、考えさせられるか）
        5. 音韻評価（語呂の良さ、リズム）

        【出力フォーマット】
        必ず以下の形式だけを守って出力してください。
        
        [DATA]
        A: 0, 0, 0, 0, 0
        B: 0, 0, 0, 0, 0
        [END_DATA]
        
        [講評]
        (ここに150文字以内で、なぜその数値になったのか、勝者はどちらかの解説を記述。
        見出し記号や点線は使わないこと。)
        """

        response = model.generate_content(prompt)
        text = response.text
        text = text.replace("#", "").replace("---", "").replace("===", "")
        return text

    except Exception as e:
        return f"エラー詳細: {str(e)}"

def extract_scores(text):
    """AIのテキストから点数を抜き出す"""
    scores_a = [50, 50, 50, 50, 50]
    scores_b = [50, 50, 50, 50, 50]
    
    try:
        match_a = re.search(r"A:\s*([\d,\s]+)", text)
        match_b = re.search(r"B:\s*([\d,\s]+)", text)
        
        if match_a:
            scores_a = [int(x.strip()) for x in match_a.group(1).split(',')]
        if match_b:
            scores_b = [int(x.strip()) for x in match_b.group(1).split(',')]
    except Exception:
        pass
    return scores_a, scores_b

def main():
    st.set_page_config(page_title="架空四字熟語バトル", page_icon="🀄")
    
    st.title("🀄 架空四字熟語バトル")
    st.markdown("2つの言葉を合体させて、最強の「四字熟語」を作れ！")
    st.caption("AIが5つの指標（詩的・幻想・社会・哲学・音韻）で分析し、レーダーチャート化します。")

    if 'hand_options' not in st.session_state:
        st.session_state['hand_options'] = random.sample(KANJI_WORDS, 15)

    st.info(f"**今回の手札:**\n\n {' / '.join(st.session_state['hand_options'])}")

    st.divider()

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

    if st.button("分析・採点開始！（AI判定）", type="primary"):
        if word_a == word_b:
            st.warning("⚠️ カブりました！")
            st.write(f"二人とも**「{word_a}」**を選びました。")
        else:
            with st.spinner(f"「{word_a}」と「{word_b}」の成分を分析中..."):
                full_result = judge_four_char_word(word_a, word_b)
            
            scores_a, scores_b = extract_scores(full_result)
            
            st.success("分析完了！")
            
            st.markdown("### 📊 成分分析チャート")
            chart_fig = create_radar_chart(scores_a, scores_b)
            st.plotly_chart(chart_fig, use_container_width=True)
            
            st.markdown("### 📝 AI審査員の講評")
            display_text = re.sub(r"\[DATA\].*?\[END_DATA\]", "", full_result, flags=re.DOTALL)
            st.write(display_text.strip())

    if st.button("素材を配り直す"):
        st.session_state['hand_options'] = random.sample(KANJI_WORDS, 15)
        st.rerun()

if __name__ == "__main__":
    main()
