"""
Ponto de entrada principal do Sistema Caixa de Senhas
Desenvolvido por: João Layon
"""

from app import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
