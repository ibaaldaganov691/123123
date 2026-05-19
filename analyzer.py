import matplotlib.pyplot as plt
import pandas as pd
from db_handler import get_weekly_stats, get_monthly_stats, get_insights

def generate_weekly_chart(telegram_id, filename='weekly_chart.png'):
    df = get_weekly_stats(telegram_id)
    if df.empty:
        return None
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df['date'], df['mood'], marker='o', label='Настроение', color='#FF6B6B')
    ax.plot(df['date'], df['work_hours'], marker='s', label='Часы работы', color='#4ECDC4')
    ax.plot(df['date'], df['sleep_hours'], marker='^', label='Часы сна', color='#FFE66D')
    
    ax.set_title('Динамика за неделю')
    ax.set_xlabel('Дата')
    ax.set_ylabel('Значение')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.5)
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    return filename

def generate_insight_text(telegram_id):
    df = get_insights(telegram_id)
    if df.empty:
        return "Нет данных для анализа."
    
    best_mood_row = df.loc[df['mood'].idxmax()]
    worst_mood_row = df.loc[df['mood'].idxmin()]
    
    insight = f"""
🔍 Ваши инсайты:

При настроении {best_mood_row['mood']} вы в среднем работали {best_mood_row['avg_work']:.1f} ч и спали {best_mood_row['avg_sleep']:.1f} ч.
При настроении {worst_mood_row['mood']} — {worst_mood_row['avg_work']:.1f} ч работы и {worst_mood_row['avg_sleep']:.1f} ч сна.

Возможно, больше сна → лучше настроение? Или наоборот? Следите за закономерностями!
"""
    return insight.strip()