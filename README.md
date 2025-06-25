# Império Rapidinhas - Sistema de Gestão v2.0

Sistema completo de captura e análise de dados para gestão de rifas online.

## Recursos

- Dashboard gerencial com analytics avançado
- Captura automática de dados
- Relatórios e insights inteligentes
- Sistema multi-usuário com controle de acesso
- Interface responsiva e moderna
- Notificações em tempo real
- Exportação de dados (Excel, PDF)

## Requisitos

- Python 3.8+
- Chrome/Chromium (para captura)
- 1GB RAM mínimo
- 500MB espaço em disco

## Instalação

1. Clone o repositório:
```bash
git clone [seu-repositorio]
cd imperio-rapidinhas
```

2. Crie ambiente virtual:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. Instale dependências:
```bash
pip install -r requirements.txt
```

4. Configure o sistema:
```bash
python run.py install
```

## Configuração

1. Copie `.env.example` para `.env` e configure
2. Execute migrações do banco:
```bash
python run.py db upgrade
```

## Uso

### Iniciar servidor:
```bash
python run.py server
```

### Captura manual:
```bash
python run.py capture
```

### Ver status:
```bash
python run.py status
```

## Dashboard

Acesse: http://localhost:5000
- Login padrão: admin / admin123

## Comandos

- `python run.py --help` - Ver todos comandos
- `python run.py server --port 8080` - Servidor em porta específica
- `python run.py capture --headless` - Captura sem interface
- `python run.py backup` - Fazer backup
- `python run.py clean --days 30` - Limpar dados antigos

## Analytics

O sistema oferece:
- Métricas em tempo real
- Análise de tendências
- Previsões básicas
- Insights automáticos
- Relatórios personalizados

## Segurança

- Senhas criptografadas
- Sessões seguras
- Controle de acesso por role
- Logs de auditoria

## Suporte

Para dúvidas ou problemas, abra uma issue no GitHub.

---
Desenvolvido com amor para Império Rapidinhas
