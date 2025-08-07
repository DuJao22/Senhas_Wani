"""
Gerenciador de Banco de Dados SQLiteCloud para Sistema Caixa de Senhas
Desenvolvido por: João Layon
Módulo responsável por todas as operações de banco de dados
Utiliza SQLiteCloud para banco na nuvem
"""

import os
import sqlitecloud
import json
import logging
from typing import List, Dict, Optional, Tuple


class DatabaseManager:
    """
    Classe para gerenciar todas as operações com banco SQLiteCloud
    Desenvolvido por João Layon
    """

    def __init__(self, connection_string: str = None):
        """
        Inicializa o gerenciador de banco de dados
        
        Args:
            connection_string (str): String de conexão do SQLiteCloud
        """
        self.connection_string = connection_string or os.environ.get(
            'SQLITECLOUD_CONNECTION_STRING',
            'sqlitecloud://cmq6frwshz.g4.sqlite.cloud:8860/caixa_senhas.db?apikey=Dor8OwUECYmrbcS5vWfsdGpjCpdm9ecSDJtywgvRw8k'
        )
        if not self.connection_string:
            logging.warning(
                "Connection string do SQLiteCloud não encontrada. Por favor, configure SQLITECLOUD_CONNECTION_STRING"
            )
            # Fallback temporário para desenvolvimento local
            self.connection_string = None
        logging.info(f"DatabaseManager inicializado para SQLiteCloud")

    def get_connection(self):
        """
        Cria e retorna uma conexão com o banco SQLiteCloud
        
        Returns:
            sqlitecloud.Connection: Conexão ativa com o banco
        """
        if not self.connection_string:
            raise ValueError(
                "Connection string do SQLiteCloud não configurada. Por favor, defina SQLITECLOUD_CONNECTION_STRING"
            )

        try:
            conn = sqlitecloud.connect(self.connection_string)
            # SQLiteCloud já retorna dados por índice, não precisamos de row_factory
            return conn
        except Exception as e:
            logging.error(f"Erro ao conectar com banco SQLiteCloud: {str(e)}")
            raise

    def inicializar_banco(self) -> bool:
        """
        Cria a tabela 'registros' se ela não existir
        Desenvolvido por João Layon
        
        Returns:
            bool: True se inicialização foi bem-sucedida
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # SQL para criar tabelas conforme especificação

                # Tabela de usuários
                users_table_sql = """
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    nome_completo TEXT NOT NULL,
                    unidade TEXT NOT NULL,
                    tipo_usuario TEXT NOT NULL DEFAULT 'operador',
                    ativo BOOLEAN DEFAULT 1,
                    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ultimo_login TIMESTAMP
                )
                """

                # Tabela de registros atualizada
                registros_table_sql = """
                CREATE TABLE IF NOT EXISTS registros (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    carteirinha TEXT NOT NULL,
                    unidade TEXT NOT NULL,
                    senhas TEXT NOT NULL,
                    usuario_id INTEGER NOT NULL,
                    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
                )
                """

                cursor.execute(users_table_sql)
                cursor.execute(registros_table_sql)

                # Inicializar usuário admin padrão se não existir
                cursor.execute(
                    "SELECT COUNT(*) as count FROM usuarios WHERE tipo_usuario = 'admin'"
                )
                admin_result = cursor.fetchone()
                admin_count = admin_result[0] if admin_result else 0

                if admin_count == 0:
                    from werkzeug.security import generate_password_hash
                    admin_hash = generate_password_hash('20e10')
                    cursor.execute(
                        """
                        INSERT INTO usuarios (username, password_hash, nome_completo, unidade, tipo_usuario)
                        VALUES (?, ?, ?, ?, ?)
                    """, ('admin', admin_hash, 'Administrador do Sistema',
                          'Ambas', 'admin'))
                    logging.info("Usuário admin padrão criado: admin/admin123")

                conn.commit()

                logging.info("Banco de dados inicializado com sucesso")
                return True

        except Exception as e:
            logging.error(f"Erro ao inicializar banco: {str(e)}")
            return False

    def inserir_registro(self, carteirinha: str, unidade: str,
                         senhas: List[str], usuario_id: int) -> bool:
        """
        Insere novo registro de carteirinha com suas senhas
        Desenvolvido por João Layon
        
        Args:
            carteirinha (str): Número ou identificação da carteirinha
            unidade (str): Unidade (Belo Horizonte ou Contagem)
            senhas (List[str]): Lista de senhas (máximo 5)
            usuario_id (int): ID do usuário que está criando o registro
            
        Returns:
            bool: True se inserção foi bem-sucedida
        """
        try:
            # Validar entrada
            if not carteirinha or not unidade or not senhas or not usuario_id:
                logging.error(
                    "Carteirinha, unidade, senhas e usuario_id são obrigatórias"
                )
                return False

            if len(senhas) > 5:
                logging.error("Máximo de 5 senhas permitidas")
                return False

            # Converter senhas para JSON conforme especificação
            senhas_json = json.dumps(senhas, ensure_ascii=False)

            with self.get_connection() as conn:
                cursor = conn.cursor()

                insert_sql = """
                INSERT INTO registros (carteirinha, unidade, senhas, usuario_id)
                VALUES (?, ?, ?, ?)
                """

                cursor.execute(insert_sql,
                               (carteirinha, unidade, senhas_json, usuario_id))
                conn.commit()

                logging.info(
                    f"Registro inserido: Carteirinha {carteirinha} da unidade {unidade} com {len(senhas)} senhas"
                )
                return True

        except Exception as e:
            logging.error(f"Erro ao inserir registro: {str(e)}")
            return False

    def obter_todos_registros(self) -> List[Dict]:
        """
        Obtém todos os registros salvos no banco
        Desenvolvido por João Layon
        
        Returns:
            List[Dict]: Lista de registros com carteirinha e senhas decodificadas
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                select_sql = """
                SELECT id, carteirinha, unidade, senhas, usuario_id, data_criacao
                FROM registros
                ORDER BY data_criacao DESC
                """

                cursor.execute(select_sql)
                rows = cursor.fetchall()

                registros = []
                for row in rows:
                    try:
                        # Decodificar senhas de JSON para lista
                        senhas = json.loads(row[3])

                        registro = {
                            'id': row[0],
                            'carteirinha': row[1],
                            'unidade': row[2],
                            'senhas': senhas,
                            'usuario_id': row[4],
                            'data_criacao': row[5],
                            'total_senhas': len(senhas)
                        }
                        registros.append(registro)

                    except (json.JSONDecodeError, TypeError, ValueError) as e:
                        logging.warning(
                            f"Erro ao decodificar senhas do registro {row[0]}: {str(e)}"
                        )
                        continue

                logging.info(f"Obtidos {len(registros)} registros do banco")
                return registros

        except Exception as e:
            logging.error(f"Erro ao obter registros: {str(e)}")
            return []

    def obter_registro_por_id(self, registro_id: int) -> Optional[Dict]:
        """
        Obtém um registro específico pelo ID
        Desenvolvido por João Layon
        
        Args:
            registro_id (int): ID do registro
            
        Returns:
            Optional[Dict]: Registro encontrado ou None
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                select_sql = """
                SELECT id, carteirinha, unidade, senhas, usuario_id, data_criacao
                FROM registros
                WHERE id = ?
                """

                cursor.execute(select_sql, (registro_id, ))
                row = cursor.fetchone()

                if row:
                    senhas = json.loads(row[3])
                    return {
                        'id': row[0],
                        'carteirinha': row[1],
                        'unidade': row[2],
                        'senhas': senhas,
                        'usuario_id': row[4],
                        'data_criacao': row[5],
                        'total_senhas': len(senhas)
                    }

                return None

        except Exception as e:
            logging.error(f"Erro ao obter registro por ID: {str(e)}")
            return None

    def contar_registros(self) -> int:
        """
        Conta o total de registros no banco
        Desenvolvido por João Layon
        
        Returns:
            int: Número total de registros
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as total FROM registros")
                result = cursor.fetchone()
                return result[0] if result else 0

        except Exception as e:
            logging.error(f"Erro ao contar registros: {str(e)}")
            return 0

    def obter_registros_por_unidade(self, unidade: str) -> List[Dict]:
        """
        Obtém todos os registros de uma unidade específica
        Desenvolvido por João Layon
        
        Args:
            unidade (str): Nome da unidade (Belo Horizonte ou Contagem)
            
        Returns:
            List[Dict]: Lista de registros da unidade especificada
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                select_sql = """
                SELECT id, carteirinha, unidade, senhas, usuario_id, data_criacao
                FROM registros
                WHERE unidade = ?
                ORDER BY data_criacao DESC
                """

                cursor.execute(select_sql, (unidade, ))
                rows = cursor.fetchall()

                registros = []
                for row in rows:
                    try:
                        # Decodificar senhas de JSON para lista
                        senhas = json.loads(row[3])

                        registro = {
                            'id': row[0],
                            'carteirinha': row[1],
                            'unidade': row[2],
                            'senhas': senhas,
                            'usuario_id': row[4],
                            'data_criacao': row[5],
                            'total_senhas': len(senhas)
                        }
                        registros.append(registro)

                    except (json.JSONDecodeError, TypeError, ValueError) as e:
                        logging.warning(
                            f"Erro ao decodificar senhas do registro {row[0]}: {str(e)}"
                        )
                        continue

                logging.info(
                    f"Obtidos {len(registros)} registros da unidade {unidade}")
                return registros

        except Exception as e:
            logging.error(f"Erro ao obter registros por unidade: {str(e)}")
            return []

    def contar_registros_por_unidade(self) -> Dict[str, int]:
        """
        Conta registros agrupados por unidade
        Desenvolvido por João Layon
        
        Returns:
            Dict[str, int]: Contagem de registros por unidade
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                count_sql = """
                SELECT unidade, COUNT(*) as total
                FROM registros
                GROUP BY unidade
                ORDER BY unidade
                """

                cursor.execute(count_sql)
                rows = cursor.fetchall()

                contagem = {}
                for row in rows:
                    contagem[row[2]] = row[1]

                logging.info(f"Contagem por unidade: {contagem}")
                return contagem

        except Exception as e:
            logging.error(f"Erro ao contar registros por unidade: {str(e)}")
            return {}

    def criar_usuario(self,
                      username: str,
                      password: str,
                      nome_completo: str,
                      unidade: str,
                      tipo_usuario: str = 'operador') -> bool:
        """
        Cria um novo usuário no sistema
        Desenvolvido por João Layon
        
        Args:
            username (str): Nome de usuário único
            password (str): Senha do usuário
            nome_completo (str): Nome completo do usuário
            unidade (str): Unidade do usuário
            tipo_usuario (str): Tipo do usuário ('admin' ou 'operador')
            
        Returns:
            bool: True se usuário foi criado com sucesso
        """
        try:
            from werkzeug.security import generate_password_hash

            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Verificar se username já existe
                cursor.execute(
                    "SELECT COUNT(*) as count FROM usuarios WHERE username = ?",
                    (username, ))
                result = cursor.fetchone()
                if (result[0] if result else 0) > 0:
                    logging.error(f"Username {username} já existe")
                    return False

                # Criar hash da senha
                password_hash = generate_password_hash(password)

                insert_sql = """
                INSERT INTO usuarios (username, password_hash, nome_completo, unidade, tipo_usuario)
                VALUES (?, ?, ?, ?, ?)
                """

                cursor.execute(insert_sql,
                               (username, password_hash, nome_completo,
                                unidade, tipo_usuario))
                conn.commit()

                logging.info(f"Usuário {username} criado com sucesso")
                return True

        except Exception as e:
            logging.error(f"Erro ao criar usuário: {str(e)}")
            return False

    def validar_login(self, username: str, password: str) -> Optional[Dict]:
        """
        Valida login do usuário
        Desenvolvido por João Layon
        
        Args:
            username (str): Nome de usuário
            password (str): Senha
            
        Returns:
            Optional[Dict]: Dados do usuário se login válido, None caso contrário
        """
        try:
            from werkzeug.security import check_password_hash

            with self.get_connection() as conn:
                cursor = conn.cursor()

                select_sql = """
                SELECT id, username, password_hash, nome_completo, unidade, tipo_usuario, ativo
                FROM usuarios
                WHERE username = ? AND ativo = 1
                """

                cursor.execute(select_sql, (username, ))
                user = cursor.fetchone()

                if user and check_password_hash(user[2], password):
                    # Atualizar último login
                    cursor.execute(
                        """
                        UPDATE usuarios SET ultimo_login = CURRENT_TIMESTAMP 
                        WHERE id = ?
                    """, (user[0], ))
                    conn.commit()

                    return {
                        'id': user[0],
                        'username': user[1],
                        'nome_completo': user[3],
                        'unidade': user[4],
                        'tipo_usuario': user[5]
                    }

                return None

        except Exception as e:
            logging.error(f"Erro ao validar login: {str(e)}")
            return None

    def obter_usuario_por_id(self, user_id: int) -> Optional[Dict]:
        """
        Obtém dados do usuário pelo ID
        Desenvolvido por João Layon
        
        Args:
            user_id (int): ID do usuário
            
        Returns:
            Optional[Dict]: Dados do usuário ou None
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                select_sql = """
                SELECT id, username, nome_completo, unidade, tipo_usuario, ativo, data_criacao, ultimo_login
                FROM usuarios
                WHERE id = ?
                """

                cursor.execute(select_sql, (user_id, ))
                user = cursor.fetchone()

                if user:
                    return {
                        'id': user[0],
                        'username': user[1],
                        'nome_completo': user[2],
                        'unidade': user[3],
                        'tipo_usuario': user[4],
                        'ativo': user[5],
                        'data_criacao': user[6],
                        'ultimo_login': user[7]
                    }

                return None

        except Exception as e:
            logging.error(f"Erro ao obter usuário por ID: {str(e)}")
            return None

    def obter_todos_usuarios(self) -> List[Dict]:
        """
        Obtém todos os usuários do sistema
        Desenvolvido por João Layon
        
        Returns:
            List[Dict]: Lista de usuários
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                select_sql = """
                SELECT id, username, nome_completo, unidade, tipo_usuario, ativo, data_criacao, ultimo_login
                FROM usuarios
                ORDER BY data_criacao DESC
                """

                cursor.execute(select_sql)
                rows = cursor.fetchall()

                usuarios = []
                for row in rows:
                    usuarios.append({
                        'id': row[0],
                        'username': row[1],
                        'nome_completo': row[2],
                        'unidade': row[3],
                        'tipo_usuario': row[4],
                        'ativo': row[5],
                        'data_criacao': row[6],
                        'ultimo_login': row[7]
                    })

                return usuarios

        except Exception as e:
            logging.error(f"Erro ao obter usuários: {str(e)}")
            return []
