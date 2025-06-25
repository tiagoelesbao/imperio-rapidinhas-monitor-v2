"""
Serviço de Analytics e Relatórios Gerenciais
"""
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
import pandas as pd
import numpy as np
from app.models import Capture, Rifa, User, ActivityLog, Report, db
import json
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

class AnalyticsService:
    """Serviço de análise de dados e geração de relatórios"""
    
    def __init__(self):
        self.reports_dir = Path('data/reports')
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuração de visualização
        plt.style.use('dark_background')
        sns.set_palette("husl")
    
    def get_dashboard_metrics(self, period='today'):
        """Retorna métricas principais para o dashboard"""
        # Define período
        if period == 'today':
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == 'week':
            start_date = datetime.now() - timedelta(days=7)
        elif period == 'month':
            start_date = datetime.now() - timedelta(days=30)
        else:
            start_date = None
        
        # Query base
        query = Capture.query
        if start_date:
            query = query.filter(Capture.timestamp >= start_date)
        
        # Métricas agregadas
        metrics = {
            'total_capturas': query.count(),
            'total_rifas': db.session.query(func.sum(Capture.total_rifas)).scalar() or 0,
            'arrecadacao_total': db.session.query(func.sum(Capture.arrecadado_total)).scalar() or 0,
            'titulos_vendidos': db.session.query(func.sum(Capture.titulos_total)).scalar() or 0,
            'ticket_medio': 0,
            'taxa_sucesso': 0,
            'crescimento': 0
        }
        
        # Calcula ticket médio
        if metrics['titulos_vendidos'] > 0:
            metrics['ticket_medio'] = metrics['arrecadacao_total'] / metrics['titulos_vendidos']
        
        # Taxa de sucesso das capturas
        capturas_sucesso = query.filter(Capture.status == 'success').count()
        if metrics['total_capturas'] > 0:
            metrics['taxa_sucesso'] = (capturas_sucesso / metrics['total_capturas']) * 100
        
        # Calcula crescimento
        if period == 'today':
            yesterday = datetime.now() - timedelta(days=1)
            yesterday_start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            yesterday_end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            yesterday_total = db.session.query(func.sum(Capture.arrecadado_total))\
                .filter(and_(Capture.timestamp >= yesterday_start, 
                           Capture.timestamp <= yesterday_end)).scalar() or 0
            
            if yesterday_total > 0:
                metrics['crescimento'] = ((metrics['arrecadacao_total'] - yesterday_total) / yesterday_total) * 100
        
        return metrics
    
    def get_rifas_performance(self, limit=10):
        """Análise de performance das rifas"""
        # Top rifas por arrecadação
        top_rifas = db.session.query(
            Rifa.titulo,
            func.sum(Rifa.arrecadado_total).label('total'),
            func.avg(Rifa.ticket_medio).label('ticket_medio'),
            func.sum(Rifa.vendas_total).label('vendas')
        ).group_by(Rifa.titulo)\
         .order_by(func.sum(Rifa.arrecadado_total).desc())\
         .limit(limit).all()
        
        return [{
            'titulo': r.titulo,
            'arrecadacao': float(r.total),
            'ticket_medio': float(r.ticket_medio),
            'vendas': int(r.vendas)
        } for r in top_rifas]
    
    def get_sales_timeline(self, days=30):
        """Timeline de vendas"""
        start_date = datetime.now() - timedelta(days=days)
        
        # Dados por dia
        daily_data = db.session.query(
            func.date(Capture.timestamp).label('date'),
            func.sum(Capture.arrecadado_total).label('total'),
            func.sum(Capture.titulos_total).label('titulos')
        ).filter(Capture.timestamp >= start_date)\
         .group_by(func.date(Capture.timestamp))\
         .order_by(func.date(Capture.timestamp)).all()
        
        return [{
            'date': str(d.date),
            'arrecadacao': float(d.total),
            'titulos': int(d.titulos)
        } for d in daily_data]
    
    def get_hourly_pattern(self):
        """Padrão de vendas por hora"""
        hourly_data = db.session.query(
            func.strftime('%H', Capture.timestamp).label('hour'),
            func.avg(Capture.arrecadado_total).label('avg_total')
        ).group_by(func.strftime('%H', Capture.timestamp))\
         .order_by('hour').all()
        
        return [{
            'hour': int(h.hour),
            'avg_arrecadacao': float(h.avg_total)
        } for h in hourly_data]
    
    def generate_performance_report(self, start_date=None, end_date=None):
        """Gera relatório completo de performance"""
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Coleta dados
        captures = Capture.query.filter(
            and_(Capture.timestamp >= start_date,
                 Capture.timestamp <= end_date)
        ).all()
        
        if not captures:
            return None
        
        # Prepara dados para análise
        data = []
        for capture in captures:
            data.append({
                'timestamp': capture.timestamp,
                'arrecadacao': capture.arrecadado_total,
                'titulos': capture.titulos_total,
                'vendas': capture.vendas_total,
                'ticket_medio': capture.ticket_medio,
                'rifas_ativas': capture.rifas_ativas
            })
        
        df = pd.DataFrame(data)
        df['date'] = df['timestamp'].dt.date
        df['weekday'] = df['timestamp'].dt.day_name()
        df['hour'] = df['timestamp'].dt.hour
        
        # Análises
        report = {
            'periodo': {
                'inicio': start_date.isoformat(),
                'fim': end_date.isoformat(),
                'dias': (end_date - start_date).days
            },
            'resumo': {
                'total_arrecadado': float(df['arrecadacao'].sum()),
                'total_titulos': int(df['titulos'].sum()),
                'total_vendas': int(df['vendas'].sum()),
                'ticket_medio_geral': float(df['arrecadacao'].sum() / df['titulos'].sum()) if df['titulos'].sum() > 0 else 0,
                'media_diaria': float(df.groupby('date')['arrecadacao'].sum().mean())
            },
            'tendencias': {
                'crescimento_percentual': self._calculate_growth_rate(df),
                'melhor_dia_semana': df.groupby('weekday')['arrecadacao'].sum().idxmax(),
                'melhor_horario': int(df.groupby('hour')['arrecadacao'].mean().idxmax()),
                'previsao_proximos_dias': self._forecast_sales(df)
            },
            'insights': self._generate_insights(df),
            'graficos': self._generate_charts(df)
        }
        
        # Salva relatório
        report_id = f"performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        report_path = self.reports_dir / f"{report_id}.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # Salva no banco
        db_report = Report(
            name=f"Relatório de Performance - {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}",
            type='performance',
            start_date=start_date,
            end_date=end_date,
            file_path=str(report_path)
        )
        db_report.set_data(report)
        db.session.add(db_report)
        db.session.commit()
        
        return report
    
    def _calculate_growth_rate(self, df):
        """Calcula taxa de crescimento"""
        daily_totals = df.groupby('date')['arrecadacao'].sum()
        if len(daily_totals) < 2:
            return 0
        
        # Regressão linear simples
        x = np.arange(len(daily_totals))
        y = daily_totals.values
        slope, _ = np.polyfit(x, y, 1)
        
        # Taxa de crescimento percentual
        growth_rate = (slope / daily_totals.mean()) * 100
        return float(growth_rate)
    
    def _forecast_sales(self, df, days=7):
        """Previsão simples de vendas"""
        daily_totals = df.groupby('date')['arrecadacao'].sum()
        
        if len(daily_totals) < 7:
            return []
        
        # Média móvel simples
        ma7 = daily_totals.rolling(window=7).mean().iloc[-1]
        
        # Previsão básica
        forecast = []
        for i in range(days):
            date = df['date'].max() + timedelta(days=i+1)
            forecast.append({
                'date': str(date),
                'previsao': float(ma7),
                'min': float(ma7 * 0.8),
                'max': float(ma7 * 1.2)
            })
        
        return forecast
    
    def _generate_insights(self, df):
        """Gera insights automáticos"""
        insights = []
        
        # Insight 1: Melhor performance
        best_day = df.loc[df['arrecadacao'].idxmax()]
        insights.append({
            'tipo': 'performance',
            'titulo': 'Melhor Dia',
            'descricao': f"O melhor dia foi {best_day['timestamp'].strftime('%d/%m/%Y')} com R$ {best_day['arrecadacao']:,.2f}"
        })
        
        # Insight 2: Padrão semanal
        weekly_pattern = df.groupby('weekday')['arrecadacao'].mean()
        best_weekday = weekly_pattern.idxmax()
        worst_weekday = weekly_pattern.idxmin()
        
        insights.append({
            'tipo': 'padrao',
            'titulo': 'Padrão Semanal',
            'descricao': f"{best_weekday} é o melhor dia da semana, enquanto {worst_weekday} tem menor performance"
        })
        
        # Insight 3: Tendência
        growth = self._calculate_growth_rate(df)
        if growth > 5:
            trend = "crescimento forte"
        elif growth > 0:
            trend = "crescimento moderado"
        elif growth > -5:
            trend = "estável"
        else:
            trend = "declínio"
        
        insights.append({
            'tipo': 'tendencia',
            'titulo': 'Tendência Atual',
            'descricao': f"As vendas mostram {trend} com variação de {growth:.1f}% ao dia"
        })
        
        return insights
    
    def _generate_charts(self, df):
        """Gera gráficos em base64"""
        charts = {}
        
        # Gráfico 1: Timeline
        plt.figure(figsize=(10, 6))
        daily_data = df.groupby('date')['arrecadacao'].sum()
        plt.plot(daily_data.index, daily_data.values, marker='o')
        plt.title('Arrecadação Diária')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100)
        buffer.seek(0)
        charts['timeline'] = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        # Gráfico 2: Por hora
        plt.figure(figsize=(10, 6))
        hourly_data = df.groupby('hour')['arrecadacao'].mean()
        plt.bar(hourly_data.index, hourly_data.values)
        plt.title('Média de Arrecadação por Hora')
        plt.xlabel('Hora do Dia')
        plt.tight_layout()
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100)
        buffer.seek(0)
        charts['hourly'] = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return charts
    
    def get_user_activity_report(self):
        """Relatório de atividade dos usuários"""
        # Atividade por usuário
        user_activity = db.session.query(
            User.username,
            func.count(ActivityLog.id).label('total_actions'),
            func.max(ActivityLog.timestamp).label('last_activity')
        ).join(ActivityLog)\
         .group_by(User.username)\
         .order_by(func.count(ActivityLog.id).desc()).all()
        
        return [{
            'usuario': u.username,
            'total_acoes': u.total_actions,
            'ultima_atividade': u.last_activity.isoformat() if u.last_activity else None
        } for u in user_activity]
    
    def export_to_excel(self, report_data, filename=None):
        """Exporta relatório para Excel"""
        if not filename:
            filename = f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        filepath = self.reports_dir / filename
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Resumo
            summary_df = pd.DataFrame([report_data['resumo']])
            summary_df.to_excel(writer, sheet_name='Resumo', index=False)
            
            # Timeline
            if 'timeline' in report_data:
                timeline_df = pd.DataFrame(report_data['timeline'])
                timeline_df.to_excel(writer, sheet_name='Timeline', index=False)
            
            # Performance rifas
            if 'rifas_performance' in report_data:
                rifas_df = pd.DataFrame(report_data['rifas_performance'])
                rifas_df.to_excel(writer, sheet_name='Rifas', index=False)
        
        return str(filepath)