from hana_conection import connect_hana, execute_query

class HanaService:
    def __init__(self):
        self.connection = None

    def connect(self):
        """
        Establece la conexión con SAP HANA
        """
        self.connection = connect_hana()
        return self.connection is not None

    def update_meta_keywords(self, item_code, meta_keywords):
        """
        Actualiza los meta keywords en la base de datos de SAP HANA
        """
        try:
            if not self.connection:
                self.connect()
            
            query = """
                UPDATE MILANPROD.OITM 
                SET "U_meta_keywords" = ?
                WHERE "ItemCode" = ?
            """
            
            cursor = self.connection.cursor()
            cursor.execute(query, (meta_keywords, item_code))
            self.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"❌ Error actualizando meta keywords en HANA: {str(e)}")
            return False 

    def update_meta_title(self, item_code, meta_title):
        """
        Actualiza el meta title en la base de datos de SAP HANA
        """
        try:
            if not self.connection:
                self.connect()
            
            query = """
                UPDATE MILANPROD.OITM 
                SET "U_meta_title" = ?
                WHERE "ItemCode" = ?
            """
            
            cursor = self.connection.cursor()
            cursor.execute(query, (meta_title, item_code))
            self.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"❌ Error actualizando meta title en HANA: {str(e)}")
            return False

    def update_meta_description(self, item_code, meta_description):
        """
        Actualiza la meta descripción en la base de datos de SAP HANA
        """
        try:
            if not self.connection:
                self.connect()
            
            query = """
                UPDATE MILANPROD.OITM 
                SET "U_meta_description" = ?
                WHERE "ItemCode" = ?
            """
            
            cursor = self.connection.cursor()
            cursor.execute(query, (meta_description, item_code))
            self.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"❌ Error actualizando meta descripción en HANA: {str(e)}")
            return False 