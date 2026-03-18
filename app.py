
import streamlit as st
from gtts import gTTS
import tempfile
from supabase import create_client
import os

# =============================
# アプリ基本設定
# =============================
st.set_page_config(page_title="Pronunciation Player")
st.title("Pronunciation Player")

# =============================
# Supabase接続（本番用：secrets）
# =============================
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# =============================
# データ操作（CRUD）
# =============================
def load_data():
    res = supabase.table("word_lists").select("name, words").execute()
    return {row["name"]: row["words"] for row in res.data}

def save_new(name, words):
    supabase.table("word_lists").insert({
        "name": name,
        "words": words
    }).execute()

def update_existing(name, words):
    supabase.table("word_lists").update({
        "words": words
    }).eq("name", name).execute()

def delete_list(name):
    supabase.table("word_lists").delete().eq("name", name).execute()

# =============================
# セッション管理
# =============================
if "loaded_words" not in st.session_state:
    st.session_state.loaded_words = []

if "input_count" not in st.session_state:
    st.session_state.input_count = 10

if "input_version" not in st.session_state:
    st.session_state.input_version = 0

if "audio_cache" not in st.session_state:
    st.session_state.audio_cache = {}

if "current_list" not in st.session_state:
    st.session_state.current_list = ""

if "show_new_name_input" not in st.session_state:
    st.session_state.show_new_name_input = False

# =============================
# リセット機能
# =============================
if st.button("🧹 単語をクリア"):
    st.session_state.loaded_words = []
    st.session_state.input_count = 10
    st.session_state.input_version += 1
    st.session_state.current_list = ""
    st.session_state.show_new_name_input = False
    st.rerun()

# =============================
# 単語入力UI
# =============================
st.write("### 単語入力")

words = []

while len(st.session_state.loaded_words) < st.session_state.input_count:
    st.session_state.loaded_words.append("")

for i in range(st.session_state.input_count):
    val = st.text_input(
        f"{i+1}",
        value=st.session_state.loaded_words[i],
        key=f"text_{i}_{st.session_state.input_version}"
    )
    st.session_state.loaded_words[i] = val
    if val.strip():
        words.append(val.strip())

if st.button("＋ 単語を追加"):
    st.session_state.input_count += 5
    st.rerun()

# =============================
# 音声生成（キャッシュ付き）
# =============================
def get_audio(text):
    if text in st.session_state.audio_cache:
        return st.session_state.audio_cache[text]

    tts = gTTS(text=text, lang="en")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tmp.close()
    tts.save(tmp.name)

    st.session_state.audio_cache[text] = tmp.name
    return tmp.name

# =============================
# 発音UI
# =============================
if words:
    st.write("### 発音")

    for i, w in enumerate(words):
        if st.button(w, key=f"play_{i}_{w}"):
            st.audio(get_audio(w))

# =============================
# DBからリスト取得
# =============================
st.write("### 単語リスト")

data = load_data()

mode = "新規モード" if not st.session_state.current_list else f"編集中：{st.session_state.current_list}"
st.write(f"状態：{mode}")

# =============================
# 新規保存
# =============================
if not st.session_state.current_list:

    new_name = st.text_input("新しいリスト名（新規保存）")

    if st.button("新規保存"):
        if new_name and words:
            if new_name in data:
                st.warning("その名前は既に存在します")
            else:
                save_new(new_name, words)
                st.success("新規リストとして保存しました")
                st.rerun()

# =============================
# 編集モード
# =============================
else:

    col1, col2 = st.columns(2)

    with col1:
        if st.button("上書き保存"):
            update_existing(st.session_state.current_list, words)
            st.success("上書き保存しました")
            st.rerun()

    with col2:
        if st.button("別名で保存"):
            st.session_state.show_new_name_input = True

    if st.session_state.show_new_name_input:
        new_name = st.text_input("新しいリスト名を入力")

        if st.button("保存実行"):
            if new_name and words:
                if new_name in data:
                    st.warning("その名前は既に存在します")
                else:
                    save_new(new_name, words)
                    st.success("新しいリストとして保存しました")
                    st.session_state.show_new_name_input = False
                    st.rerun()

# =============================
# リスト選択・削除
# =============================
if data:
    selected = st.selectbox(
        "リスト選択（読み込み）",
        list(data.keys())
    )

    if st.button("読み込み"):
        st.session_state.loaded_words = data[selected].copy()
        st.session_state.input_count = max(10, len(data[selected]))
        st.session_state.input_version += 1
        st.session_state.current_list = selected
        st.session_state.show_new_name_input = False
        st.rerun()

    if st.button("削除"):
        delete_list(selected)
        st.success("削除しました")
        st.session_state.current_list = ""
        st.rerun()

# =============================
# UIスタイル
# =============================
st.markdown("""
<style>
button {
    font-size: 20px !important;
    padding: 10px !important;
}
</style>
""", unsafe_allow_html=True)
