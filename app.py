"""
Sistema Web Caixa de Senhas
Desenvolvido por: João Layon
Sistema completo para gerenciamento de até 5 senhas por carteirinha
Tecnologias: Flask, SQLite3, HTML5, CSS, JavaScript
"""

import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, make_response
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from database import DatabaseManager

# Configuração de logging para debug
logging.basicConfig(level=logging.DEBUG)

# Criação da aplicação Flask
app = Flask(__name__)

# Configuração da chave secreta conforme guidelines
app.secret_key = os.environ.get("SESSION_SECRET", "caixa_senhas_joao_layon_2025")

# Configuração do Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'

# Inicialização do gerenciador de banco de dados
# Para SQLiteCloud, o connection_string será fornecido via variável de ambiente
db_manager = DatabaseManager()

# Classe User para Flask-Login
class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['id'])
        self.username = user_data['username']
        self.nome_completo = user_data['nome_completo']
        self.unidade = user_data['unidade']
        self.tipo_usuario = user_data['tipo_usuario']
    
    def is_admin(self):
        return self.tipo_usuario == 'admin'

@login_manager.user_loader
def load_user(user_id):
    user_data = db_manager.obter_usuario_por_id(int(user_id))
    if user_data:
        return User(user_data)
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Página de login do sistema
    Desenvolvido por João Layon
    """
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Por favor, preencha todos os campos.', 'error')
            return render_template('login.html')
        
        user_data = db_manager.validar_login(username, password)
        if user_data:
            user = User(user_data)
            login_user(user)
            flash(f'Bem-vindo, {user.nome_completo}!', 'success')
            
            # Redirecionar admin para painel admin, operador para página inicial
            if user.is_admin():
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('index'))
        else:
            flash('Usuário ou senha incorretos.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """
    Logout do sistema
    Desenvolvido por João Layon
    """
    logout_user()
    flash('Logout realizado com sucesso.', 'success')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """
    Página inicial do sistema Caixa de Senhas
    Desenvolvido por João Layon
    """
    return render_template('index.html')

@app.route('/adicionar', methods=['POST'])
@login_required
def adicionar_registro():
    """
    Rota para adicionar novo registro de carteirinha com senhas
    Desenvolvido por João Layon
    Valida e salva até 5 senhas por carteirinha
    """
    try:
        # Obter dados do formulário
        carteirinha = request.form.get('carteirinha', '').strip()
        unidade = request.form.get('unidade', '').strip()
        senhas_raw = request.form.get('senhas', '')
        
        # Validação básica
        if not carteirinha:
            flash('Carteirinha é obrigatória!', 'error')
            return redirect(url_for('index'))
        
        if not unidade:
            flash('Unidade é obrigatória!', 'error')
            return redirect(url_for('index'))
        
        # Verificar se operador está tentando criar registro para unidade diferente da sua
        if not current_user.is_admin() and current_user.unidade != unidade and current_user.unidade != 'Ambas':
            flash(f'Você só pode criar registros para a unidade {current_user.unidade}!', 'error')
            return redirect(url_for('index'))
        
        # Processar senhas (vem como string separada por vírgulas do JavaScript)
        senhas = []
        if senhas_raw:
            senhas = [senha.strip() for senha in senhas_raw.split(',') if senha.strip()]
        
        # Validar número máximo de senhas
        if len(senhas) > 5:
            flash('Máximo de 5 senhas permitidas!', 'error')
            return redirect(url_for('index'))
        
        if len(senhas) == 0:
            flash('Pelo menos uma senha deve ser informada!', 'error')
            return redirect(url_for('index'))
        
        # Salvar no banco de dados com ID do usuário atual
        success = db_manager.inserir_registro(carteirinha, unidade, senhas, int(current_user.id))
        
        if success:
            flash(f'Registro salvo com sucesso! Carteirinha: {carteirinha} da unidade {unidade} com {len(senhas)} senha(s).', 'success')
        else:
            flash('Erro ao salvar registro. Tente novamente.', 'error')
            
    except Exception as e:
        logging.error(f"Erro ao adicionar registro: {str(e)}")
        flash('Erro interno do sistema. Tente novamente.', 'error')
    
    return redirect(url_for('index'))

@app.route('/registros')
@login_required
def visualizar_registros():
    """
    Página para visualizar todos os registros salvos
    Desenvolvido por João Layon
    Exibe carteirinhas e suas respectivas senhas com filtros por unidade
    """
    try:
        # Obter filtro de unidade da query string
        unidade_filtro = request.args.get('unidade', '')
        
        # Filtrar por unidade do operador se não for admin
        if not current_user.is_admin() and current_user.unidade != 'Ambas':
            unidade_filtro = current_user.unidade
        
        if unidade_filtro and unidade_filtro in ['Belo Horizonte', 'Contagem']:
            registros = db_manager.obter_registros_por_unidade(unidade_filtro)
        else:
            registros = db_manager.obter_todos_registros()
        
        # Obter estatísticas por unidade
        estatisticas = db_manager.contar_registros_por_unidade()
        
        return render_template('registros.html', 
                             registros=registros, 
                             estatisticas=estatisticas,
                             unidade_filtro=unidade_filtro)
    except Exception as e:
        logging.error(f"Erro ao carregar registros: {str(e)}")
        flash('Erro ao carregar registros.', 'error')
        return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin_dashboard():
    """
    Painel administrativo
    Desenvolvido por João Layon
    Apenas para usuários admin
    """
    if not current_user.is_admin():
        flash('Acesso negado. Apenas administradores podem acessar esta página.', 'error')
        return redirect(url_for('index'))
    
    try:
        usuarios = db_manager.obter_todos_usuarios()
        estatisticas = db_manager.contar_registros_por_unidade()
        total_registros = db_manager.contar_registros()
        
        return render_template('admin.html', 
                             usuarios=usuarios,
                             estatisticas=estatisticas,
                             total_registros=total_registros)
    except Exception as e:
        logging.error(f"Erro ao carregar painel admin: {str(e)}")
        flash('Erro ao carregar dados administrativos.', 'error')
        return redirect(url_for('index'))

@app.route('/admin/criar-usuario', methods=['GET', 'POST'])
@login_required
def criar_usuario():
    """
    Criar novo usuário (apenas admin)
    Desenvolvido por João Layon
    """
    if not current_user.is_admin():
        flash('Acesso negado.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            nome_completo = request.form.get('nome_completo', '').strip()
            unidade = request.form.get('unidade', '').strip()
            tipo_usuario = request.form.get('tipo_usuario', 'operador')
            
            # Validações
            if not all([username, password, nome_completo, unidade]):
                flash('Todos os campos são obrigatórios!', 'error')
                return render_template('criar_usuario.html')
            
            if len(password) < 4:
                flash('Senha deve ter pelo menos 4 caracteres!', 'error')
                return render_template('criar_usuario.html')
            
            # Criar usuário
            success = db_manager.criar_usuario(username, password, nome_completo, unidade, tipo_usuario)
            
            if success:
                flash(f'Usuário {username} criado com sucesso!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Erro ao criar usuário. Username pode já existir.', 'error')
                
        except Exception as e:
            logging.error(f"Erro ao criar usuário: {str(e)}")
            flash('Erro interno do sistema.', 'error')
    
    return render_template('criar_usuario.html')

@app.route('/exportar')
@login_required
def exportar_dados():
    """
    Exportar dados em CSV
    Desenvolvido por João Layon
    """
    try:
        import csv
        import io
        
        # Obter registros baseado no tipo de usuário
        if current_user.is_admin():
            registros = db_manager.obter_todos_registros()
        else:
            registros = db_manager.obter_registros_por_unidade(current_user.unidade)
        
        # Criar CSV em memória
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Cabeçalho
        writer.writerow(['ID', 'Carteirinha', 'Unidade', 'Senhas', 'Data/Hora Criação', 'Usuário ID'])
        
        # Dados
        for registro in registros:
            senhas_str = '; '.join(registro['senhas'])
            writer.writerow([
                registro['id'],
                registro['carteirinha'],
                registro['unidade'],
                senhas_str,
                registro['data_criacao'],
                registro.get('usuario_id', 'N/A')
            ])
        
        # Criar resposta
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename="registros_senhas_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        flash('Dados exportados com sucesso!', 'success')
        return response
        
    except Exception as e:
        logging.error(f"Erro ao exportar dados: {str(e)}")
        flash('Erro ao exportar dados.', 'error')
        return redirect(url_for('visualizar_registros'))

@app.errorhandler(404)
def page_not_found(e):
    """
    Handler para páginas não encontradas
    Desenvolvido por João Layon
    """
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    """
    Handler para erros internos do servidor
    Desenvolvido por João Layon
    """
    logging.error(f"Erro interno: {str(e)}")
    flash('Erro interno do servidor. Tente novamente.', 'error')
    return redirect(url_for('index'))

# Inicializar banco de dados sempre que a aplicação iniciar
db_manager.inicializar_banco()

if __name__ == '__main__':    
    # Executar aplicação na porta 5000 conforme guidelines
    app.run(host='0.0.0.0', port=5000, debug=True)
