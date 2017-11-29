#!/usr/bin/env python3

import os
import pickle
import sqlite3


class DatabaseInit:
    def __init__(self, location_prefix):
        os.makedirs(location_prefix, exist_ok=True)
        database_path = os.path.join(location_prefix, 'Lector.db')

        if not os.path.exists(database_path):
            self.database = sqlite3.connect(database_path)
            self.create_database()

    def create_database(self):
        # TODO
        # Add a separate column for directory tags
        self.database.execute(
            "CREATE TABLE books \
            (id INTEGER PRIMARY KEY, Title TEXT, Author TEXT, Year INTEGER, \
            Path TEXT, Position BLOB, ISBN TEXT, Tags TEXT, Hash TEXT, CoverImage BLOB)")
        self.database.execute(
            "CREATE TABLE directories (id INTEGER PRIMARY KEY, Path TEXT, Name TEXT, Tags TEXT)")
        self.database.commit()
        self.database.close()


class DatabaseFunctions:
    def __init__(self, location_prefix):
        database_path = os.path.join(location_prefix, 'Lector.db')
        self.database = sqlite3.connect(database_path)

    def add_to_database(self, data):
        # data is expected to be a dictionary
        # with keys corresponding to the book hash
        # and corresponding items containing
        # whatever else needs insertion
        # Haha I said insertion

        for i in data.items():
            book_hash = i[0]
            title = i[1]['title']
            author = i[1]['author']
            year = i[1]['year']
            path = i[1]['path']
            cover = i[1]['cover_image']
            isbn = i[1]['isbn']

            sql_command_add = (
                "INSERT INTO books (Title,Author,Year,Path,ISBN,Hash,CoverImage) VALUES(?, ?, ?, ?, ?, ?, ?)")

            cover_insert = None
            if cover:
                cover_insert = sqlite3.Binary(cover)

            self.database.execute(
                sql_command_add,
                [title, author, year,
                 path, isbn, book_hash, cover_insert])

        self.database.commit()
        self.close_database()

    def fetch_data(self, columns, table, selection_criteria, equivalence, fetch_one=False):
        # columns is a tuple that will be passed as a comma separated list
        # table is a string that will be used as is
        # selection_criteria is a dictionary which contains the name of a column linked
        # to a corresponding value for selection

        # Example:
        # Name and AltName are expected to be the same
        # sel_dict = {
        #     'Name': 'sav',
        #     'AltName': 'sav'
        # }
        # data = DatabaseFunctions().fetch_data(('Name',), 'books', sel_dict)
        try:
            column_list = ','.join(columns)
            sql_command_fetch = f"SELECT {column_list} FROM {table}"
            if selection_criteria:
                sql_command_fetch += " WHERE"

                if equivalence == 'EQUALS':
                    for i in selection_criteria.keys():
                        search_parameter = selection_criteria[i]
                        sql_command_fetch += f" {i} = '{search_parameter}' OR"

                elif equivalence == 'LIKE':
                    for i in selection_criteria.keys():
                        search_parameter = "'%" + selection_criteria[i] + "%'"
                        sql_command_fetch += f" {i} LIKE {search_parameter} OR"

                sql_command_fetch = sql_command_fetch[:-3]  # Truncate the last OR

            # book data is returned as a list of tuples
            data = self.database.execute(sql_command_fetch).fetchall()

            if data:
                # Because this is the result of a fetchall(), we need an
                # ugly hack (tm) to get correct results
                if fetch_one:
                    return data[0][0]

                return data
            else:
                return None

        # except sqlite3.OperationalError:
        except KeyError:
            print('SQLite is in rebellion, Commander')

        self.close_database()

    def modify_position(self, hash_position_pairs):
        for i in hash_position_pairs:
            file_hash = i[0]
            position = i[1]

            pickled_position = pickle.dumps(position)

            sql_command = "UPDATE books SET Position = ? WHERE Hash = ?"
            try:
                self.database.execute(sql_command, [sqlite3.Binary(pickled_position), file_hash])
            except sqlite3.OperationalError:
                print('SQLite is in rebellion, Commander')
                return

        self.database.commit()
        self.close_database()

    def delete_from_database(self, file_hashes):
        # file_hashes is expected as a list that will be iterated upon
        # This should enable multiple deletion

        first = file_hashes[0]
        sql_command = f"DELETE FROM books WHERE Hash = '{first}'"

        if len(file_hashes) > 1:
            for i in file_hashes[1:]:
                sql_command += f" OR Hash = '{i}'"

        self.database.execute(sql_command)

        self.database.commit()
        self.close_database()

    def close_database(self):
        self.database.execute("VACUUM")
        self.database.close()
