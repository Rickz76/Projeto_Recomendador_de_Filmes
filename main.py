from flask import Flask, render_template, redirect, request, flash
from flask_login import UserMixin, LoginManager, login_required, login_user, logout_user
import json

# ===================================== Criar app ============================================

app = Flask(__name__)
app.config['SECRET_KEY'] = 'CINE'

# =============================== Configurar LoginManager ============================================

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "home"

# ================================== Classe de usuário ============================================

class User(UserMixin):
    def __init__(self, id, nome, senha):
        self.id = id
        self.nome = nome
        self.senha = senha

# ================================== Carregar usuário ============================================

@login_manager.user_loader
def load_user(user_id):
    with open('usuarios.json', 'r', encoding='utf-8') as f:
        users = json.load(f)
    for user in users:
        if str(user['id']) == str(user_id):
            return User(user['id'], user['nome'], user['senha'])
    return None

# ============================= Carrega filmes ============================================

with open('filmes.json', 'r', encoding='utf-8') as f:
    filmes = json.load(f)

# ============================= IA RECOMENDADOR ============================================

def recomendar_filmes(usuario_id, usuarios):
    usuario = next(u for u in usuarios if u['id'] == usuario_id)

    # Nenhuma avaliação → sem recomendações
    if 'avaliacoes' not in usuario or len(usuario['avaliacoes']) == 0:
        return []

    # Soma notas por gênero
    generos = {}
    for avaliacao in usuario['avaliacoes']:
        filme = next(f for f in filmes if f['id'] == avaliacao['filme_id'])
        genero = filme['genero']
        generos.setdefault(genero, 0)
        generos[genero] += avaliacao['nota']

    # Ordena gêneros por pontuação
    generos_ordenados = sorted(generos.items(), key=lambda x: x[1], reverse=True)

    # Pega os DOIS gêneros favoritos
    top_generos = [g[0] for g in generos_ordenados[:2]]

    # Filtra os filmes desses dois gêneros
    recomendados = [f for f in filmes if f['genero'] in top_generos]

    # Limita para 10 filmes
    return recomendados[:10]


# =============================== Rota da página registrar ============================================

@app.route("/registrar", methods=['GET', 'POST'])
def registrar():
    if request.method == 'GET':
        return render_template("registrar.html")

    # Dados do formulário
    nome = request.form.get("nome")
    senha = request.form.get("senha")

    # Carregar usuários
    with open("usuarios.json", "r", encoding="utf-8") as f:
        usuarios = json.load(f)

    # Verificar se nome já existe
    if any(u['nome'] == nome for u in usuarios):
        flash("Usuário já existe!")
        return redirect("/registrar")

    # Criar novo usuário
    novo_id = max(u["id"] for u in usuarios) + 1

    novo_usuario = {
        "id": novo_id,
        "nome": nome,
        "senha": senha,
        "avaliacoes": []
    }

    usuarios.append(novo_usuario)

    # Salvar
    with open("usuarios.json", "w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=4, ensure_ascii=False)

    flash("Conta criada com sucesso! Faça login.")
    return redirect("/")


# =============================== Rota da página inicial ============================================

@app.route("/")
def home():
    return render_template("login.html")

# ==================================== Rota de login ============================================

@app.route("/login", methods=['POST'])
def login():

    nome = request.form.get('nome')
    senha = request.form.get('senha')

    with open('usuarios.json', 'r', encoding='utf-8') as f:
        users = json.load(f)

    for user in users:
        if user['nome'] == nome and user['senha'] == senha:
            user_obj = User(user['id'], user['nome'], user['senha'])
            login_user(user_obj)
            return redirect(f'/dashboard/{user["id"]}')

    flash('Usuário inválido')
    return redirect('/')

# ================================== Dashboard (Recomendações) ============================================

@app.route("/dashboard/<int:usuario_id>")
@login_required
def dashboard(usuario_id):
    with open('usuarios.json', 'r', encoding='utf-8') as f:
        usuarios = json.load(f)

    usuario = next(u for u in usuarios if u['id'] == usuario_id)

    recomendados = recomendar_filmes(usuario_id, usuarios)

    return render_template(
        "usuarios.html",
        usuario=usuario,
        recomendados=recomendados
    )

# ================================== Página Explorar ============================================

@app.route("/explorar/<int:usuario_id>")
@login_required
def explorar(usuario_id):
    with open('usuarios.json', 'r', encoding='utf-8') as f:
        usuarios = json.load(f)

    usuario = next(u for u in usuarios if u['id'] == usuario_id)

    return render_template(
        "explorar.html",
        filmes=filmes,
        usuario=usuario
    )

# ==================================== Avaliar Filme ============================================

@app.route("/avaliar", methods=['POST'])
@login_required
def avaliar():
    usuario_id = int(request.form['usuario_id'])
    filme_id = int(request.form['filme_id'])
    nota = int(request.form['nota'])

    with open('usuarios.json', 'r', encoding='utf-8') as f:
        usuarios = json.load(f)

    for usuario in usuarios:
        if usuario['id'] == usuario_id:
            if 'avaliacoes' not in usuario:
                usuario['avaliacoes'] = []

            avaliacao_existente = next((a for a in usuario['avaliacoes']
                                        if a['filme_id'] == filme_id), None)
            if avaliacao_existente:
                avaliacao_existente['nota'] = nota
            else:
                usuario['avaliacoes'].append({'filme_id': filme_id, 'nota': nota})
            break

    with open('usuarios.json', 'w', encoding='utf-8') as f:
        json.dump(usuarios, f, indent=4)

    return redirect(f'/explorar/{usuario_id}')

# ==================================== Logout =================================================

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('Você saiu da conta.')
    return redirect('/')

# ==================================== Rodar app ============================================

if __name__ == "__main__":
    app.run(debug=True)
