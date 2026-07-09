import requests
import streamlit as st

API_BASE = st.sidebar.text_input('API Base URL', 'http://127.0.0.1:7800')
category = st.sidebar.selectbox('分类', options=['全部', '商业', '科技'])
days = st.sidebar.slider('最近天数', min_value=1, max_value=30, value=7)
target_date = st.sidebar.date_input('按日期筛选（created_at）', value=None)
min_importance = st.sidebar.slider('最低重要性', min_value=1, max_value=5, value=1)

params = {'days': days}
if category != '全部':
    params['category'] = category

st.title('AI/具身智能资讯浏览')

try:
    res = requests.get(f'{API_BASE}/digest', params=params, timeout=10)
    res.raise_for_status()
    items = res.json().get('items', [])
    if target_date:
        date_text = target_date.isoformat()
        items = [item for item in items if (item.get('created_at', '') or '').startswith(date_text)]
    items = [item for item in items if int(item.get('importance') or 0) >= min_importance]
    st.caption(f'共 {len(items)} 条')

    for item in items:
        with st.container(border=True):
            st.subheader(item.get('title', ''))
            st.write(f"分类：{item.get('category')} | 重要性：{item.get('importance')} | 来源：{item.get('source')}")
            st.write(item.get('ai_summary', ''))
            st.link_button('查看原文', item.get('link', '#'))
except Exception as exc:
    st.error(f'请求失败: {exc}')

