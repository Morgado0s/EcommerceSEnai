from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import bcrypt
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave-secreta-trabalho-escolar'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Extensões permitidas para upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db = SQLAlchemy(app)

# Modelos do Banco de Dados
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    imagem = db.Column(db.String(200), default='produto-default.jpg')
    descricao = db.Column(db.Text)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    total = db.Column(db.Float, nullable=False)
    data_pedido = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pendente')

class ItemPedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Float, nullable=False)

# Rotas Principais
@app.route('/')
def index():
    categoria = request.args.get('categoria', '')
    busca = request.args.get('busca', '')
    
    query = Produto.query
    
    if categoria:
        query = query.filter(Produto.categoria.ilike(f'%{categoria}%'))
    
    if busca:
        query = query.filter(Produto.nome.ilike(f'%{busca}%'))
    
    produtos = query.all()
    categorias = db.session.query(Produto.categoria).distinct().all()
    categorias = [cat[0] for cat in categorias]
    
    return render_template('index.html', produtos=produtos, categorias=categorias)

# Rotas de Autenticação
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and bcrypt.checkpw(senha.encode('utf-8'), usuario.senha):
            session['usuario_id'] = usuario.id
            session['usuario_nome'] = usuario.nome
            session['is_admin'] = usuario.is_admin
            flash('Login realizado com sucesso!', 'success')
            
            if usuario.is_admin:
                return redirect(url_for('admin'))
            return redirect(url_for('index'))
        else:
            flash('Email ou senha incorretos!', 'error')
    
    return render_template('login.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        
        # Verificar se email já existe
        if Usuario.query.filter_by(email=email).first():
            flash('Email já cadastrado!', 'error')
            return render_template('cadastro.html')
        
        # Criptografar senha
        senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt())
        
        # Criar usuário
        usuario = Usuario(nome=nome, email=email, senha=senha_hash)
        db.session.add(usuario)
        db.session.commit()
        
        flash('Cadastro realizado com sucesso!', 'success')
        return redirect(url_for('login'))
    
    return render_template('cadastro.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('index'))

# Rotas do Carrinho
@app.route('/carrinho')
def carrinho():
    if 'carrinho' not in session:
        session['carrinho'] = []
    
    carrinho_produtos = []
    total = 0
    
    for item in session['carrinho']:
        produto = Produto.query.get(item['produto_id'])
        if produto:
            item_total = produto.preco * item['quantidade']
            carrinho_produtos.append({
                'produto': produto,
                'quantidade': item['quantidade'],
                'total': item_total
            })
            total += item_total
    
    return render_template('carrinho.html', carrinho=carrinho_produtos, total=total)

@app.route('/adicionar_carrinho/<int:produto_id>')
def adicionar_carrinho(produto_id):
    if 'carrinho' not in session:
        session['carrinho'] = []
    
    # Verificar se produto já está no carrinho
    for item in session['carrinho']:
        if item['produto_id'] == produto_id:
            item['quantidade'] += 1
            session.modified = True
            flash('Quantidade atualizada no carrinho!', 'success')
            return redirect(url_for('index'))
    
    # Adicionar novo produto
    session['carrinho'].append({'produto_id': produto_id, 'quantidade': 1})
    session.modified = True
    flash('Produto adicionado ao carrinho!', 'success')
    return redirect(url_for('index'))

@app.route('/remover_carrinho/<int:produto_id>')
def remover_carrinho(produto_id):
    if 'carrinho' in session:
        session['carrinho'] = [item for item in session['carrinho'] if item['produto_id'] != produto_id]
        session.modified = True
        flash('Produto removido do carrinho!', 'success')
    return redirect(url_for('carrinho'))

@app.route('/finalizar_pedido', methods=['POST'])
def finalizar_pedido():
    if 'usuario_id' not in session:
        flash('Você precisa estar logado para finalizar o pedido!', 'error')
        return redirect(url_for('login'))
    
    if 'carrinho' not in session or not session['carrinho']:
        flash('Seu carrinho está vazio!', 'error')
        return redirect(url_for('carrinho'))
    
    # Calcular total do pedido
    total = 0
    for item in session['carrinho']:
        produto = Produto.query.get(item['produto_id'])
        if produto:
            total += produto.preco * item['quantidade']
    
    # Criar pedido
    pedido = Pedido(usuario_id=session['usuario_id'], total=total)
    db.session.add(pedido)
    db.session.flush()  # Para obter o ID do pedido
    
    # Criar itens do pedido
    for item in session['carrinho']:
        produto = Produto.query.get(item['produto_id'])
        if produto:
            item_pedido = ItemPedido(
                pedido_id=pedido.id,
                produto_id=produto.id,
                quantidade=item['quantidade'],
                preco_unitario=produto.preco
            )
            db.session.add(item_pedido)
    
    db.session.commit()
    
    # Limpar carrinho
    session['carrinho'] = []
    session.modified = True
    
    flash(f'Pedido #{pedido.id} finalizado com sucesso! Total: R$ {total:.2f}', 'success')
    return redirect(url_for('index'))

# Área Administrativa
@app.route('/admin')
def admin():
    if not session.get('is_admin'):
        flash('Acesso negado!', 'error')
        return redirect(url_for('index'))
    
    produtos = Produto.query.all()
    usuarios = Usuario.query.count()
    pedidos = Pedido.query.count()
    
    return render_template('admin.html', produtos=produtos, usuarios=usuarios, pedidos=pedidos)

# Rota para upload de imagens
@app.route('/upload_imagem', methods=['POST'])
def upload_imagem():
    if not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Acesso negado'})
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Adicionar timestamp para evitar conflitos
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{int(datetime.now().timestamp())}{ext}"
        
        # Criar diretório se não existir
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        return jsonify({'success': True, 'filename': filename})
    
    return jsonify({'success': False, 'message': 'Tipo de arquivo não permitido'})

@app.route('/admin/produto/novo', methods=['GET', 'POST'])
def novo_produto():
    if not session.get('is_admin'):
        flash('Acesso negado!', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        nome = request.form['nome']
        preco = float(request.form['preco'])
        categoria = request.form['categoria']
        descricao = request.form['descricao']
        imagem = request.form.get('imagem', 'produto-default.jpg')
        
        produto = Produto(nome=nome, preco=preco, categoria=categoria, descricao=descricao, imagem=imagem)
        db.session.add(produto)
        db.session.commit()
        
        flash('Produto criado com sucesso!', 'success')
        return redirect(url_for('admin'))
    
    return render_template('produto_form.html')

@app.route('/admin/produto/editar/<int:produto_id>', methods=['GET', 'POST'])
def editar_produto(produto_id):
    if not session.get('is_admin'):
        flash('Acesso negado!', 'error')
        return redirect(url_for('index'))
    
    produto = Produto.query.get_or_404(produto_id)
    
    if request.method == 'POST':
        produto.nome = request.form['nome']
        produto.preco = float(request.form['preco'])
        produto.categoria = request.form['categoria']
        produto.descricao = request.form['descricao']
        produto.imagem = request.form.get('imagem', produto.imagem)
        
        db.session.commit()
        
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('admin'))
    
    return render_template('produto_form.html', produto=produto)

@app.route('/admin/produto/deletar/<int:produto_id>')
def deletar_produto(produto_id):
    if not session.get('is_admin'):
        flash('Acesso negado!', 'error')
        return redirect(url_for('index'))
    
    produto = Produto.query.get_or_404(produto_id)
    db.session.delete(produto)
    db.session.commit()
    
    flash('Produto deletado com sucesso!', 'success')
    return redirect(url_for('admin'))

# Inicialização do Banco
def init_db():
    with app.app_context():
        db.create_all()
        
        # Criar usuário admin se não existir
        if not Usuario.query.filter_by(email='admin@admin.com').first():
            senha_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
            admin = Usuario(nome='Administrador', email='admin@admin.com', senha=senha_hash, is_admin=True)
            db.session.add(admin)
        
        # Criar produtos de exemplo se não existirem
        if not Produto.query.first():
            produtos_exemplo = [
                Produto(nome='Smartphone Samsung', preco=899.99, categoria='Eletrônicos', descricao='Smartphone com 128GB'),
                Produto(nome='Notebook Dell', preco=2499.99, categoria='Eletrônicos', descricao='Notebook i5 8GB RAM'),
                Produto(nome='Camiseta Básica', preco=29.99, categoria='Roupas', descricao='Camiseta 100% algodão'),
                Produto(nome='Tênis Esportivo', preco=199.99, categoria='Calçados', descricao='Tênis para corrida'),
                Produto(nome='Livro Python', preco=59.99, categoria='Livros', descricao='Aprenda Python do zero'),
                Produto(nome='Fone Bluetooth', preco=149.99, categoria='Eletrônicos', descricao='Fone sem fio com cancelamento de ruído')
            ]
            
            for produto in produtos_exemplo:
                db.session.add(produto)
        
        db.session.commit()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)