# -*- coding: Shift-JIS -*-
import logging
import mysql.connector
import config

db_name=config.DB
user_name=config.USER_NAME
host_name=config.HOST
user_password=config.PASS

# MySQL�ڑ����
db_config = {
    "host": host_name,  # �z�X�g��
    "user": user_name,       # ���[�U��
    "password": user_password,  # �p�X���[�h
    "database": db_name  # �f�[�^�x�[�X��
}

class DbQuery():
    def quryexcute(self,query,values):
        try:
            # MySQL�f�[�^�x�[�X�ɐڑ�
            connection = mysql.connector.connect(**db_config)

            if connection.is_connected():
                # �o�[�W���������擾
                cursor = connection.cursor()
                logging.info("Connected to MySQL Server")


                #query="INSERT INTO botseqtable(guild_id,channel_id) VALUES(%s,%s)"
                #values = (1076845818407026758,1076849137007472690)
                cmpleate_query = cursor.execute(query,values)
                logging.info(f"�N�G�����{query}")

                query_value = cursor.fetchall()
                connection.commit();

                return query_value

        except mysql.connector.Error as e:
            print("Error:", e)
            logging.error(e)
            connection.rollback();
            # �G���[�����������ꍇ�̏����������ɒǉ�
            # ��: �G���[���O�̏o�́A�G���[���b�Z�[�W�̒ʒm�A�ʂ̃A�N�V�����̎��s�Ȃ�

        finally:
            # �ڑ����N���[�Y
            if connection is not None and connection.is_connected():
                cursor.close()
                connection.close()
                logging.info("Connection closed")
