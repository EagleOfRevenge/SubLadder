"""
init_db.py — Sub Ladder v4.0
Script d'initialisation de la base de données MariaDB.

Usage :
    python init_db.py --host 127.0.0.1 --port 3306 --user root --password yourpassword
"""

import argparse
import sys


def init_database(host, port, user, password, database_name="sub_ladder"):
    try:
        import pymysql
    except ImportError:
        print("❌ pymysql n'est pas installé. Executez : pip install pymysql")
        sys.exit(1)

    # Connexion au serveur MariaDB (sans database)
    connection = pymysql.connect(
        host=host,
        port=int(port),
        user=user,
        password=password,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )

    try:
        with connection.cursor() as cursor:
            # Créer la database si elle n'existe pas
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{database_name}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            print(f"✅ Database '{database_name}' prête.")

        # Charger et exécuter le schema.sql
        schema_path = "database/schema.sql"
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        # Se connecter à la database sub_ladder
        connection.close()
        connection = pymysql.connect(
            host=host,
            port=int(port),
            user=user,
            password=password,
            database=database_name,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )

        with connection.cursor() as cursor:
            # Diviser le SQL en instructions individuelles
            # Plus robuste: gérer les statements multi-lignes avec des blocs
            statements = []
            current_stmt = ""
            
            for line in schema_sql.split("\n"):
                line = line.strip()
                if not line or line.startswith("--"):
                    continue
                if line.startswith("USE"):
                    continue
                    
                current_stmt += " " + line
                if line.endswith(";"):
                    stmt_clean = current_stmt.replace(";", "").strip()
                    if stmt_clean:
                        statements.append(stmt_clean)
                    current_stmt = ""
            
            for idx, statement in enumerate(statements, 1):
                if not statement.strip():
                    continue
                try:
                    cursor.execute(statement)
                    print(f"  ✓ [{idx}/{len(statements)}] Table créée")
                except Exception as e:
                    # Ignorer les erreurs sur les tables déjà existantes
                    err_str = str(e)
                    if "already exists" in err_str or "1050" in err_str or "1051" in err_str:
                        print(f"  ⚠️  [{idx}/{len(statements)}] Table déjà existante")
                    elif "1049" in err_str or "Unknown database" in err_str:
                        pass  # Database not yet selected — normal
                    else:
                        print(f"  ❌ Erreur à l'instruction {idx}:")
                        print(f"     {statement[:100]}...")
                        print(f"     {err_str}")
                        raise

        print("✅ Tables créées avec succès !")
        print()
        print("Tables créées :")
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            for t in tables:
                val = list(t.values())[0]
                print(f"  📋 {val}")

    except Exception as e:
        print(f"❌ Erreur : {e}")
        sys.exit(1)
    finally:
        connection.close()


def main():
    parser = argparse.ArgumentParser(description="Initialiser la DB Sub Ladder")
    parser.add_argument("--host", default="127.0.0.1", help="Hôte MariaDB")
    parser.add_argument("--port", default="3306", help="Port MariaDB")
    parser.add_argument("--user", default="root", help="Utilisateur MariaDB")
    parser.add_argument("--password", default="", help="Mot de passe MariaDB")
    parser.add_argument("--database", default="sub_ladder", help="Nom de la database")
    args = parser.parse_args()

    init_database(args.host, args.port, args.user, args.password, args.database)


if __name__ == "__main__":
    main()
