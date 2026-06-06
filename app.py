import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import calendar

# 1. Configuração inicial da página
st.set_page_config(page_title="Meu RPG da Vida Real", page_icon="👑", layout="centered")

# ==========================================
# 🛠️ [Backend: Funções do Banco de Dados]
# ==========================================
def query_db(sql_query, params=()):
    conn = sqlite3.connect("rpg-database.db")
    df = pd.read_sql_query(sql_query, conn, params=params)
    conn.close()
    return df

def run_db_command(sql_command, params=()):
    conn = sqlite3.connect("rpg-database.db")
    cursor = conn.cursor()
    cursor.execute(sql_command, params)
    conn.commit()
    conn.close()

def init_log_table_safety():
    conn = sqlite3.connect("rpg-database.db")
    cursor = conn.cursor()
    
    # A. Tabela de missões master
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS master_quest_db (
        quest_id TEXT PRIMARY KEY,
        quest_name TEXT,
        difficulty TEXT,
        reward_xp INTEGER,
        reward_gold INTEGER,
        frequency INTEGER,
        status TEXT
    )
    """)
    
    # B. Tabela de histórico de missões (로그 테이블)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quest_history_log (
        log_date TEXT PRIMARY KEY,
        day_of_week TEXT,
        completed_ids TEXT,
        total_xp INTEGER,
        total_gold INTEGER
    )
    """)
    
    # 🌟 [구조 개편] C. Tabela do menu de recompensas (status 컬럼 추가)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reward_menu (
        reward_item TEXT PRIMARY KEY,
        price_gold INTEGER,
        status TEXT DEFAULT 'Active'
    )
    """)
    
    # D. Tabela de histórico de compras
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reward_shop_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        purchase_date TEXT,
        reward_item TEXT,
        spent_gold INTEGER
    )
    """)
    
    # 🌟 [신설] E. Tabela de Configuração de Níveis (1~100 레벨 설정 테이블)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS level_config (
        level INTEGER PRIMARY KEY,
        required_xp INTEGER,
        title TEXT
    )
    """)
    
    # 🌟 [신설] F. Tabela de Histórico de Level Up (레벨 도달 마일스톤 날짜 기록 테이블)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS levelup_history (
        level INTEGER PRIMARY KEY,
        achieved_date TEXT
    )
    """)
    
    # G. Dados iniciais das missões (최초 1회 주인님의 실제 정예 11개 퀘스트 기본 주입)
    cursor.executemany("""
    INSERT OR IGNORE INTO master_quest_db VALUES (?, ?, ?, ?, ?, ?, ?)
    """, [
        ('Q260606-01', 'Limpeza geral da casa (청소)', 'H', 50, 25, 7, 'Active'),
        ('Q260606-02', 'Fechamento de contas mensal (결산)', 'N', 30, 15, 11, 'Active'),
        ('Q260606-03', 'Dormir cedo (일찍 잠자기)', 'N', 30, 15, 8, 'Active'),
        ('Q260606-04', 'Ingestão de proteínas adequada (단백질 섭취)', 'N', 30, 15, 8, 'Active'),
        ('Q260606-05', 'Estudar no Duolingo', 'E', 10, 5, 8, 'Active'),
        ('Q260606-06', 'Estudar vocabulário de português (포어 단어 공부)', 'E', 10, 5, 8, 'Active'),
        ('Q260606-07', 'Acumular pontos KBPay', 'E', 10, 5, 8, 'Active'),
        ('Q260606-08', 'Acumular pontos NPay', 'E', 10, 5, 8, 'Active'),
        ('Q260606-09', 'Acumular pontos TossPay', 'E', 10, 5, 8, 'Active'),
        ('Q260606-10', 'Estudar uma página de Educação Física (EF 학습)', 'H', 50, 25, 8, 'Active'),
        ('Q260606-11', 'Escrever uma linha de código (코딩 1줄 작성)', 'H', 50, 25, 8, 'Active')
    ])
    
    # H. Dados iniciais da loja
    cursor.executemany("""
    INSERT OR IGNORE INTO reward_menu VALUES (?, ?, ?)
    """, [
        ('Comer Frango Frito 🍗', 500, 'Active'),
        ('1 Hora de YouTube 📱', 100, 'Active'),
        ('Assistir a um Filme na Netflix 🎬', 200, 'Active'),
        ('Ticket para Dormir até Tarde ⏰', 300, 'Active')
    ])
    
    # I. 데이터베이스 기반 레벨 1~100 자동 규칙 대량 주입 (100만 XP 만렙 리밸런싱 패치)
    level_rules = []
    for lv in range(1, 101):
        if lv == 1: required = 0
        elif lv <= 10: required = (lv - 1) * 500
        elif lv <= 30: required = 5000 + (lv - 10) * 1200
        elif lv <= 60: required = 29000 + (lv - 30) * 5000
        elif lv <= 90: required = 179000 + (lv - 60) * 18000
        else: required = 719000 + (lv - 90) * 31200
        
        if lv == 100: title = "Deus da Alta Performance 🌌"
        elif lv >= 96: title = "Iluminado da Rotina 🧘"
        elif lv >= 91: title = "Ser de Luz Disciplinado ☀️"
        elif lv >= 81: title = "Soberano dos Hábitos 🌟"
        elif lv >= 71: title = "Lenda da Produtividade 📜"
        elif lv >= 61: title = "Conquistador Imparável ⛰️"
        elif lv >= 51: title = "Grande Mestre de Si Mesmo 👑"
        elif lv >= 41: title = "Vanguardista da Mente 🔮"
        elif lv >= 31: title = "Dominador do Tempo ⏳"
        elif lv >= 26: title = "Mestre do Auto-Controle 🧠"
        elif lv >= 21: title = "Comandante da Rotina 🎖️"
        elif lv >= 16: title = "Especialista em Foco 🎯"
        elif lv >= 11: title = "Arquiteto do Hábito 📐"
        elif lv >= 10: title = "Desbravador do Foco 🏔️"
        elif lv >= 9: title = "Caçador de Metas 🏹"
        elif lv >= 8: title = "Guerreiro da Constância 🛡️"
        elif lv >= 7: title = "Construidor de Disciplina 🏗️"
        elif lv >= 6: title = "Explorador de Rotinas 🧭"
        elif lv >= 5: title = "Transcendente da Produtividade 🌌"
        elif lv >= 4: title = "Mestre dos Hábitos ⚡"
        elif lv >= 3: title = "Líder da Rotina ⚔️"
        elif lv >= 2: title = "Praticante Dedicado 🏃"
        else: title = "Iniciante da Vida Saudável 🌱"
        
        level_rules.append((lv, required, title))
        
    cursor.executemany("INSERT OR IGNORE INTO level_config VALUES (?, ?, ?)", level_rules)
    
    # Lv 1 도달 날짜는 최초 실행일로 강제 주입 (마일스톤 첫 단추)
    cursor.execute("INSERT OR IGNORE INTO levelup_history VALUES (1, ?)", (datetime.now().strftime("%Y-%m-%d"),))
    
    conn.commit()
    conn.close()

init_log_table_safety()


# ==========================================
# 📊 [Cálculo de Dados: Status Atual]
# ==========================================
try:
    stats_df = query_db("SELECT SUM(total_xp) as attr_xp, SUM(total_gold) as attr_gold FROM quest_history_log")
    total_accumulated_xp = int(stats_df['attr_xp'].iloc[0]) if pd.notna(stats_df['attr_xp'].iloc[0]) else 0
    total_earned_gold = int(stats_df['attr_gold'].iloc[0]) if pd.notna(stats_df['attr_gold'].iloc[0]) else 0
    
    shop_df = query_db("SELECT SUM(spent_gold) as attr_spent FROM reward_shop_log")
    total_spent_gold = int(shop_df['attr_spent'].iloc[0]) if pd.notna(shop_df['attr_spent'].iloc[0]) else 0
    current_remaining_gold = total_earned_gold - total_spent_gold
except Exception:
    total_accumulated_xp, total_earned_gold, current_remaining_gold = 0, 0, 0

# SQL 기반 실시간 현재 레벨 계산
try:
    lvl_query = "SELECT level, title FROM level_config WHERE required_xp <= ? ORDER BY level DESC LIMIT 1"
    lvl_df = query_db(lvl_query, (total_accumulated_xp,))
    current_level = int(lvl_df['level'].iloc[0])
    character_title = str(lvl_df['title'].iloc[0])
except Exception:
    current_level, character_title = 1, "Iniciante da Vida Saudável 🌱"

# 다음 레벨 정보 및 남은 경험치 계산 연산
try:
    if current_level < 100:
        next_lvl_data = query_db("SELECT required_xp FROM level_config WHERE level = ?", (current_level + 1,))
        next_lvl_xp = int(next_lvl_data['required_xp'].iloc[0])
        xp_needed_for_next = next_lvl_xp - total_accumulated_xp
        current_lvl_base = int(query_db("SELECT required_xp FROM level_config WHERE level = ?", (current_level,))['required_xp'].iloc[0])
        
        # st.progress용 비율 (0.0 ~ 1.0)
        progress_total = next_lvl_xp - current_lvl_base
        progress_current = total_accumulated_xp - current_lvl_base
        progress_ratio = min(max(progress_current / progress_total, 0.0), 1.0)
    else:
        xp_needed_for_next = 0
        progress_ratio = 1.0
except Exception:
    xp_needed_for_next = 0
    progress_ratio = 0.0


# ==========================================
# 🖥️ [Frontend UI: Abas de Navegação]
# ==========================================
# 기획에 맞춘 깔끔한 3개 탭 체제 구축
tab_play, tab_manage, tab_jornada = st.tabs(["🎮 Jogar (플레이)", "⚙️ Gerenciador (종합 관리)", "🧭 Jornada (성장 여정)"])

# ------------------------------------------
# 🎮 TAB 1: 플레이 대시보드 영역
# ------------------------------------------
with tab_play:
    st.subheader("👤 Status do Personagem")
    status_col1, status_col2, status_col3 = st.columns(3)
    with status_col1:
        st.metric("Nível Atual", f"LV. {current_level}")
    with status_col2:
        st.metric("XP Acumulado", f"{total_accumulated_xp} XP")
    with status_col3:
        st.metric("Ouro Disponível", f"{current_remaining_gold} G")
    st.markdown(f"**Seu Título Honorário Atual:** `{character_title}`")
    
    # 🌟 [신설] 시각적 실시간 경험치 게이지 바 출력 구역
    if current_level < 100:
        st.progress(progress_ratio)
        st.caption(f"💡 **Próximo Nível (다음 레벨까지):** `{xp_needed_for_next} XP` 남음")
    else:
        st.success("🌌 **Você atingiu o nível máximo! Deus da Alta Performance.**")

    st.write("---")
    st.subheader("⚙️ Painel de Controle")
    selected_date = st.date_input("Selecione uma data", datetime.now(), key="play_date")

    day_of_week = selected_date.weekday() 
    numbers_weekday = 1 if day_of_week == 6 else day_of_week + 2
    day_of_month = selected_date.day
    _, last_day = calendar.monthrange(selected_date.year, selected_date.month)

    is_month_first = (day_of_month == 1)
    is_month_last = (day_of_month == last_day)

    st.write("---")
    st.subheader("🎯 Missões de Hoje")

    sql_filter = """
    SELECT quest_id, quest_name, reward_xp, reward_gold 
    FROM master_quest_db 
    WHERE status = 'Active' AND (
        frequency = 8 OR 
        frequency = ? OR 
        (? = 1 AND frequency = 10) OR 
        (? = 1 AND frequency = 11)
    )
    """
    today_quests = query_db(sql_filter, (numbers_weekday, is_month_first, is_month_last))

    completed_ids = []
    total_xp = 0
    total_gold = 0

    if not today_quests.empty:
        for index, row in today_quests.iterrows():
            is_done = st.checkbox(f"[{row['quest_id']}] {row['quest_name']} (+{row['reward_xp']} XP / +{row['reward_gold']} G)", key=f"q_{row['quest_id']}")
            if is_done:
                completed_ids.append(row['quest_id'])
                total_xp += row['reward_xp']
                total_gold += row['reward_gold']
    else:
        st.info("Nenhuma missão ativa agendada para hoje. Aproveite para descansar!")

    st.write("---")
    st.subheader("📝 Resumo do Dia")
    st.code(f"Missões Concluídas: {', '.join(completed_ids) if completed_ids else 'Nenhuma'}\n"
            f"Total de XP de Hoje: {total_xp} XP\n"
            f"Total de Ouro de Hoje: {total_gold} Gold", language="text")

    if st.button("💾 Salvar Resultados de Hoje", key="btn_save_daily"):
        if not completed_ids:
            st.warning("⚠️ Você não selecionou nenhuma missão concluída!")
        else:
            try:
                weekday_names = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
                current_day_name = weekday_names[selected_date.weekday()]
                
                sql_insert = """
                INSERT OR REPLACE INTO quest_history_log (log_date, day_of_week, completed_ids, total_xp, total_gold)
                VALUES (?, ?, ?, ?, ?)
                """
                formatted_date = selected_date.strftime("%Y-%m-%d")
                run_db_command(sql_insert, (formatted_date, current_day_name, ", ".join(completed_ids), total_xp, total_gold))
                
                # 🌟 [레벨업 마일스톤 탐지기 작동]
                # 오늘 보상을 더해서 변동된 신규 누적 경험치 계산
                new_accumulated_xp = total_accumulated_xp + total_xp
                new_lvl_df = query_db("SELECT level FROM level_config WHERE required_xp <= ? ORDER BY level DESC LIMIT 1", (new_accumulated_xp,))
                new_level = int(new_lvl_df['level'].iloc[0])
                
                # 만약 레벨이 기존보다 상승했다면 마일스톤 도장 찍기
                if new_level > current_level:
                    for lv_step in range(current_level + 1, new_level + 1):
                        run_db_command("INSERT OR IGNORE INTO levelup_history (level, achieved_date) VALUES (?, ?)", (lv_step, formatted_date))
                    st.balloons()
                    st.success(f"🚀 **LEVEL UP! Você subiu para o LV. {new_level}!**")
                else:
                    st.balloons()
                
                st.success(f"🎉 Resultados do dia [{formatted_date}] salvos com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erro ao salvar: {e}")

    # --- 상점 인터페이스 (Active 상품만 노출되도록 필터링 개편) ---
    st.write("---")
    st.subheader("🛒 Loja de Recompensas Real")
    menu_df = query_db("SELECT reward_item, price_gold FROM reward_menu WHERE status = 'Active'")
    item_list = menu_df['reward_item'].tolist()

    if item_list:
        selected_item = st.selectbox("Escolha sua recompensa:", item_list, key="shop_select")
        item_price = int(menu_df[menu_df['reward_item'] == selected_item]['price_gold'].iloc[0])
        st.info(f"💰 Preço: {item_price} Gold. (Saldo: {current_remaining_gold} G)")
        
        if st.button("💳 Usar Ouro (Comprar Recompensa)", key="btn_buy_reward"):
            if current_remaining_gold < item_price:
                st.error("❌ Ouro insuficiente!")
            else:
                try:
                    purchase_date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    run_db_command("INSERT INTO reward_shop_log (purchase_date, reward_item, spent_gold) VALUES (?, ?, ?)", 
                                   (purchase_date_str, selected_item, item_price))
                    st.snow()
                    st.success(f"🎉 Você comprou '{selected_item}'!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao usar a loja: {e}")
    else:
        st.info("A loja está vazia no momento. Adicione itens na aba do gerenciador.")


# ------------------------------------------
# ⚙️ TAB 2: 종합 관리자 영역 (Missões & Loja Dual Control)
# ------------------------------------------
with tab_manage:
    st.subheader("⚙️ Painel do Controle Geral (종합 제어 관제탑)")
    
    # 상단 서브 선택바: 퀘스트 관리할 것인가 / 상점 관리할 것인가
    sub_menu = st.segmented_control("Selecione o alvo de gerenciamento (관리 대상 선택):", ["🎯 Missões (퀘스트 관리)", "🛒 Loja (상점 메뉴판 관리)"], default="🎯 Missões (퀘스트 관리)")
    
    diff_rewards = {"E": (10, 5), "N": (30, 15), "H": (50, 25)}
    
    # -------------------------------------------------------------
    # 서브메뉴 1: 🎯 Missões (퀘스트 관리)
    # -------------------------------------------------------------
    if "Missões" in sub_menu:
        all_quests = query_db("SELECT quest_id, quest_name, difficulty, reward_xp, reward_gold, frequency, status FROM master_quest_db ORDER BY status ASC, quest_id DESC")
        
        def style_inactive_rows(row):
            return ['color: #A0A0A0; font-style: italic;'] * len(row) if row['status'] == 'Inactive' else [''] * len(row)
        
        st.markdown("### 📜 Lista de Todas as Missões")
        st.dataframe(all_quests.style.apply(style_inactive_rows, axis=1), use_container_width=True)
        
        manage_action = st.radio("Ação:", ["➕ Adicionar Nova Missão", "🔄 Modificar Missão"], horizontal=True, key="m_action")
        
        if "➕" in manage_action:
            st.markdown("##### ➕ Criar Nova Missão")
            today_str = datetime.now().strftime("%y%m%d")
            id_prefix = f"Q{today_str}-"
            try:
                today_count = int(query_db("SELECT COUNT(*) as cnt FROM master_quest_db WHERE quest_id LIKE ?", (f"{id_prefix}%",))['cnt'].iloc[0])
            except Exception: today_count = 0
            auto_generated_id = f"{id_prefix}{today_count + 1:02d}"
            
            st.info(f"🆔 Código Gerado: `{auto_generated_id}`")
            new_name = st.text_input("Nome da Missão", key="q_new_name")
            col_m1, col_m2 = st.columns(2)
            with col_m1: new_diff = st.selectbox("Dificuldade", ["E", "N", "H"], key="q_new_diff")
            with col_m2: new_freq = st.selectbox("Frequência", [("Diário", 8), ("Domingo", 1), ("Segunda", 2), ("Terça", 3), ("Quarta", 4), ("Quinta", 5), ("Sexta", 6), ("Sábado", 7), ("Início do Mês", 10), ("Fim do Mês", 11)], format_func=lambda x: x[0], key="q_new_freq")
            
            xp_reward, gold_reward = diff_rewards[new_diff]
            if st.button("🚀 Registrar Missão", key="q_reg_btn"):
                if not new_name: st.error("Nome obrigatório!")
                else:
                    run_db_command("INSERT INTO master_quest_db VALUES (?, ?, ?, ?, ?, ?, 'Active')", (auto_generated_id, new_name, new_diff, xp_reward, gold_reward, new_freq[1]))
                    st.success("Registrada!")
                    st.rerun()
                    
        else:
            st.markdown("##### 🔄 Modificar Missão")
            quest_options = all_quests['quest_id'].tolist()
            if quest_options:
                target_id = st.selectbox("Selecione o Código:", quest_options, key="q_up_target")
                selected_q = all_quests[all_quests['quest_id'] == target_id].iloc[0]
                col_u1, col_u2 = st.columns(2)
                with col_u1: new_status = st.selectbox("Novo Status:", ["Active", "Inactive"], index=["Active", "Inactive"].index(selected_q['status']), key="q_up_status")
                with col_u2: new_diff = st.selectbox("Nova Dificuldade:", ["E", "N", "H"], index=["E", "N", "H"].index(selected_q['difficulty']), key="q_up_diff")
                
                u_xp, u_gold = diff_rewards[new_diff]
                if st.button("💾 Atualizar Missão", key="q_up_btn"):
                    run_db_command("UPDATE master_quest_db SET status=?, difficulty=?, reward_xp=?, reward_gold=? WHERE quest_id=?", (new_status, new_diff, u_xp, u_gold, target_id))
                    st.success("Atualizada!")
                    st.rerun()

    # -------------------------------------------------------------
    # 🌟 [신설] 서브메뉴 2: 🛒 Loja (상점 메뉴판 관리 대시보드)
    # -------------------------------------------------------------
    else:
        all_rewards = query_db("SELECT reward_item, price_gold, status FROM reward_menu ORDER BY status ASC, price_gold ASC")
        
        def style_shop_rows(row):
            return ['color: #A0A0A0; font-style: italic;'] * len(row) if row['status'] == 'Inactive' else [''] * len(row)
            
        st.markdown("### 📜 Cardápio Completo da Loja (전체 상점 메뉴판)")
        st.dataframe(all_rewards.style.apply(style_shop_rows, axis=1), use_container_width=True)
        
        shop_action = st.radio("Ação da Loja:", ["➕ Adicionar Novo Item", "🔄 Modificar Item Existente"], horizontal=True, key="s_action")
        
        if "➕" in shop_action:
            st.markdown("##### ➕ Criar Novo Item de Recompensa")
            s_new_name = st.text_input("Nome do Item (예: Jogar PlayStation 1 hora)", key="s_new_name")
            s_new_price = st.number_input("Preço em Ouro (Gold)", min_value=1, value=100, step=10, key="s_new_price")
            
            if st.button("🚀 Registrar Item na Loja", key="s_reg_btn"):
                if not s_new_name: st.error("Nome do item obrigatório!")
                else:
                    run_db_command("INSERT OR REPLACE INTO reward_menu VALUES (?, ?, 'Active')", (s_new_name, int(s_new_price)))
                    st.success("Item adicionado com sucesso!")
                    st.rerun()
        else:
            st.markdown("##### 🔄 Modificar Item de Recompensa")
            item_options = all_rewards['reward_item'].tolist()
            if item_options:
                target_item = st.selectbox("Selecione o Item para Modificar:", item_options, key="s_up_target")
                selected_i = all_rewards[all_rewards['reward_item'] == target_item].iloc[0]
                
                col_s1, col_s2 = st.columns(2)
                with col_s1: s_up_status = st.selectbox("Novo Status:", ["Active", "Inactive"], index=["Active", "Inactive"].index(selected_i['status']), key="s_up_status")
                with col_s2: s_up_price = st.number_input("Novo Preço (Gold):", min_value=1, value=int(selected_i['price_gold']), step=10, key="s_up_price")
                
                if st.button("💾 Atualizar Item na Loja", key="s_up_btn"):
                    run_db_command("UPDATE reward_menu SET status=?, price_gold=? WHERE reward_item=?", (s_up_status, int(s_up_price), target_item))
                    st.success("Item da loja atualizado com sucesso!")
                    st.rerun()


# ------------------------------------------
# 🧭 TAB 3: 🌟 [신설] 성장 여정 (Jornada) 영역
# ------------------------------------------
with tab_jornada:
    st.subheader("🧭 Jornada de Crescimento (주인님의 위대한 성장 여정)")
    st.markdown("레벨 1부터 100까지의 전체 마일스톤 지도입니다. 도달한 레벨의 역사적인 날짜 도장을 확인하세요.")
    
    # 1. 지하실의 100개 레벨 설정과 실제 도달 날짜 기록 테이블을 LEFT JOIN 연산으로 융합
    jornada_query = """
        SELECT lc.level, lc.required_xp, lc.title, lh.achieved_date
        FROM level_config lc
        LEFT JOIN levelup_history lh ON lc.level = lh.level
        ORDER BY lc.level DESC
    """
    jornada_df = query_db(jornada_query)
    
    # 2. 결과 가공: 날짜가 있으면 완료 마크, 없으면 미완료 마크 바인딩
    jornada_df['Status'] = jornada_df['achieved_date'].apply(lambda x: "✅ Concluído" if pd.notna(x) else "🔒 Bloqueado")
    jornada_df['Data de Conclusão'] = jornada_df['achieved_date'].apply(lambda x: x if pd.notna(x) else "-")
    
    # 사용할 열만 필터링하여 뷰(View) 가공
    display_jornada = jornada_df[['level', 'required_xp', 'title', 'Status', 'Data de Conclusão']].copy()
    display_jornada.columns = ['Nível', 'XP Necessário', 'Título Honorário', 'Status', 'Data de Conclusão']
    
    # 🎨 3. 현재 위치(Gold), 지나온 길(Light Green), 미래(Gray) 시각적 코팅 스크립트
    def style_jornada_map(row):
        lvl = row['Nível']
        status = row['Status']
        
        if lvl == current_level:
            return ['background-color: #FFEAA7; color: #000000; font-weight: bold;'] * len(row)  # 현재 위치: 황금빛 하이라이트
        elif "Concluído" in status:
            return ['background-color: #E8F5E9; color: #2E7D32;'] * len(row)  # 지나온 길: 연초록색 안전지대
        else:
            return ['color: #B0B0B0; font-style: italic;'] * len(row)  # 미래의 길: 연회색 안개 처리

    # 완성된 100층의 시각적 타임라인 마일스톤 표 출력
    st.dataframe(
        display_jornada.style.apply(style_jornada_map, axis=1), 
        use_container_width=True, 
        height=500
    )